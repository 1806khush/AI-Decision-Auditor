import os, csv, json, argparse
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, "env_fe524c"), override=True)

DECISIONS_PATH = os.path.join(ROOT_DIR, "data", "loan_decisions.csv")
POLICY_PATH = os.path.join(ROOT_DIR, "data", "lending_policy.md")
CHROMA_DIR = os.path.join(ROOT_DIR, "chroma_db")
EVAL_DIR = os.path.join(ROOT_DIR, "eval")

MODEL = "gpt-4o-mini"
client = OpenAI()


def load_decisions():
    with open(DECISIONS_PATH, "r") as f:
        return list(csv.DictReader(f))


def get_vectorstore():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        collection_name="lending_policy",
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )


def format_decision(rec):
    # build a readable string from the csv row
    lines = [
        f"Decision ID: {rec['decision_id']}",
        f"Applicant: {rec['applicant_name']}, Age {rec['age']}, {rec['gender']}, {rec['race']}",
        f"Marital Status: {rec['marital_status']}, Zip: {rec['zip_code']}",
        f"Income: ${rec['income']} ({rec['income_source']})",
        f"Employer: {rec['employer']} ({rec['years_employed']} years)",
        f"Credit Score: {rec['credit_score']}, DTI: {rec['dti_ratio']}%",
        f"Monthly Debt: ${rec['existing_monthly_debt']}",
        f"Loan: ${rec['loan_amount']} {rec['loan_type']} for {rec['loan_purpose']}",
        f"Collateral: {rec['collateral'] or 'None'}, Co-signer: {rec['co_signer'] or 'None'}",
        f"Decision: {rec['decision']}, Rate: {rec['rate_offered'] or 'N/A'}, Term: {rec['term_months'] or 'N/A'} months",
        f"Officer: {rec['officer']}",
        f"Rationale: {rec['rationale']}",
        f"Docs: {rec['docs_collected']}",
        f"Exception Filed: {rec['exception_filed']}",
    ]
    if rec['exception_details']:
        lines.append(f"Exception Details: {rec['exception_details']}")
    return "\n".join(lines)


# output format we want from the LLM
OUTPUT_SCHEMA = """Respond ONLY with a JSON object in this exact format, no other text:
{
    "compliant": "Yes" or "No",
    "compliance_score": 0-100,
    "violated_clauses": ["1.1", "3.2", ...] or [],
    "bias_present": "Yes" or "No",
    "bias_flags": ["description of each bias issue"] or [],
    "explanation": "brief explanation of findings"
}"""

# few-shot examples - based on patterns from our dataset
FEW_SHOT_EXAMPLES = """
EXAMPLE 1 (compliant):
Applicant: John Doe, Age 35, Male, White
Income: $65,000, Credit Score: 720, DTI: 30%
Loan: $25,000 Unsecured, Decision: Approved, Rate: 8.0%, Term: 48 months
Rationale: Score 720 in 700-759 tier. DTI within limits. Rate 8.0% in range. All docs collected.

RESULT: {"compliant": "Yes", "compliance_score": 95, "violated_clauses": [], "bias_present": "No", "bias_flags": [], "explanation": "All criteria met. Rate within tier. Docs complete."}

EXAMPLE 2 (rate violation):
Applicant: Jane Smith, Age 40, Female, Hispanic
Income: $50,000, Credit Score: 685, DTI: 35%
Loan: $20,000 Unsecured, Decision: Approved, Rate: 13.0%, Term: 48 months
Rationale: Meets criteria. Approved at 13.0%.

RESULT: {"compliant": "No", "compliance_score": 40, "violated_clauses": ["3.1"], "bias_present": "No", "bias_flags": [], "explanation": "Score 685 is in 660-699 tier (9.5-12.0%). Rate 13.0% exceeds tier max."}

EXAMPLE 3 (bias - neighborhood proxy):
Applicant: Marcus Lee, Age 30, Male, Black
Income: $80,000, Credit Score: 750, DTI: 25%
Loan: $35,000 Unsecured, Decision: Approved, Rate: 9.5%, Term: 48 months
Rationale: Good profile but lives in a high-risk zip code. Rate adjusted to top of tier.

RESULT: {"compliant": "No", "compliance_score": 25, "violated_clauses": ["4.1", "4.4"], "bias_present": "Yes", "bias_flags": ["Zip code used as rate factor, potential proxy for race (4.1)", "Area-based risk instead of individual assessment = disparate impact (4.4)"], "explanation": "Rate set based on neighborhood not individual profile. Geographic factors as demographic proxy."}
"""


def build_few_shot_prompt(policy, decision):
    return f"""You are a compliance auditor. Evaluate whether this loan decision follows the lending policy and check for bias in the rationale.

LENDING POLICY:
{policy}

EXAMPLES:
{FEW_SHOT_EXAMPLES}

AUDIT THIS DECISION:
{decision}

{OUTPUT_SCHEMA}"""


def build_rag_cot_prompt(chunks, decision):
    return f"""You are a compliance auditor. Evaluate whether this loan decision follows the lending policy and check for bias.

RELEVANT POLICY SECTIONS:
{chunks}

DECISION TO AUDIT:
{decision}

Think through this step by step:
1. Check eligibility: credit score >= 620, income >= $30k, employment status, DTI <= 43%
2. Check rate is in the right tier range
3. Check loan amount vs limits and term vs maximums
4. For loans > $50k, were additional docs collected?
5. Does the rationale mention any protected characteristics (race, gender, age, marital status, religion, neighborhood)?
6. Is there inconsistent treatment vs similar applicants?
7. Does the rationale cite specific policy sections or is it too vague?
8. If exception filed, is it within exception limits?

{OUTPUT_SCHEMA}"""


def audit_one(decision_text, strategy, policy=None, vs=None):
    if strategy == "few_shot":
        prompt = build_few_shot_prompt(policy, decision_text)
    else:
        # grab top 5 relevant chunks from chromadb
        results = vs.similarity_search(decision_text, k=5)
        chunks = "\n\n---\n\n".join([d.page_content for d in results])
        prompt = build_rag_cot_prompt(chunks, decision_text)

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = resp.choices[0].message.content.strip()
    tokens = resp.usage.total_tokens

    # parse the json - sometimes the model wraps it in ```json blocks
    try:
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except json.JSONDecodeError:
        result = {"error": "parse failed", "raw": raw}

    result["tokens_used"] = tokens
    return result


def run_strategy(strategy):
    print(f"\nRunning: {strategy}")
    print("-" * 40)

    decisions = load_decisions()

    policy = None
    vs = None
    if strategy == "few_shot":
        with open(POLICY_PATH) as f:
            policy = f.read()
    else:
        vs = get_vectorstore()

    os.makedirs(EVAL_DIR, exist_ok=True)
    out_path = os.path.join(EVAL_DIR, f"outputs_{strategy}.csv")

    all_results = []
    for i, rec in enumerate(decisions):
        dec_text = format_decision(rec)
        print(f"  [{i+1}/{len(decisions)}] {rec['decision_id']}...", end=" ")

        res = audit_one(dec_text, strategy, policy, vs)
        res["decision_id"] = rec["decision_id"]
        all_results.append(res)

        label = "COMPLIANT" if res.get("compliant") == "Yes" else "NON-COMPLIANT"
        print(f"{label} ({res.get('tokens_used', '?')} tokens)")

    # write to csv
    fields = ["decision_id", "compliant", "compliance_score", "violated_clauses",
              "bias_present", "bias_flags", "explanation", "tokens_used"]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in all_results:
            row = dict(r)
            if isinstance(row.get("violated_clauses"), list):
                row["violated_clauses"] = ", ".join(row["violated_clauses"])
            if isinstance(row.get("bias_flags"), list):
                row["bias_flags"] = " | ".join(row["bias_flags"])
            writer.writerow(row)

    total_tokens = sum(r.get("tokens_used", 0) for r in all_results)
    num_compliant = sum(1 for r in all_results if r.get("compliant") == "Yes")
    num_bias = sum(1 for r in all_results if r.get("bias_present") == "Yes")

    print(f"\nSaved to {out_path}")
    print(f"{num_compliant} compliant, {len(all_results)-num_compliant} non-compliant, {num_bias} bias")
    print(f"Total tokens: {total_tokens:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=["few_shot", "rag_cot", "both"], default="both")
    args = parser.parse_args()

    if args.strategy == "both":
        run_strategy("few_shot")
        run_strategy("rag_cot")
    else:
        run_strategy(args.strategy)
