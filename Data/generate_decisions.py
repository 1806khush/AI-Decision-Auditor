import json
import random
from pathlib import Path
random.seed(42)

POLICY_CLAUSES = {
    "P-01": "Minimum credit score of 620 required for loan approval.",
    "P-02": "Debt-to-income ratio must not exceed 43%.",
    "P-03": "Minimum annual income of $30,000 required.",
    "P-04": "Loan decisions must not be influenced by race, color, national origin, sex, disability, or familial status.",
    "P-05": "Employment history of at least 12 months with current employer required.",
    "P-06": "Applicants with prior bankruptcy within 7 years are ineligible.",
    "P-07": "Denial must include a written explanation citing specific policy violations.",
    "P-08": "Re-evaluation required if income documentation is incomplete before denial.",
}

def make_record(record_id, compliant, bias_flag, violated_clauses, bias_flags, notes,
                credit_score, income, dti, employment_months,
                has_bankruptcy=False, race=None, sex=None):
    rng = random.Random(record_id)
    return {
        "id":f"LOAN-{str(record_id).zfill(3)}",
        "applicant":{
            "age":rng.randint(22, 65),
            "annual_income_usd":income,
            "credit_score":credit_score,
            "debt_to_income_ratio":dti,
            "employment_months":employment_months,
            "prior_bankruptcy": has_bankruptcy,
            "race": race if race else rng.choice(["White", "Black", "Hispanic", "Asian", "Other"]),
            "sex": sex if sex else rng.choice(["Male", "Female", "Non-binary"]),
        },
        "loan_request": {
            "amount_usd": rng.choice([50000, 75000, 100000, 150000, 200000]),
            "purpose": rng.choice(["Home Purchase", "Refinance", "Home Improvement"]),
        },
        "decision": "Denied" if (not compliant or bias_flag) else "Approved",
        "officer_notes": notes,
        "ground_truth": {
            "compliance_verdict": "non-compliant" if (not compliant or bias_flag) else "compliant",
            "violated_clauses": violated_clauses,
            "bias_flags": bias_flags,
        },
    }
records = [
# COMPLIANT RECORDS (12) 

    make_record(1,  True, False, [], [],
        "Applicant meets all criteria: credit 720, DTI 0.31, income $82k, 24 months employment.",
        credit_score=720, income=82000, dti=0.31, employment_months=24),

    make_record(2,  True, False, [], [],
        "Strong credit profile (760), income $95k, no bankruptcy history.",
        credit_score=760, income=95000, dti=0.28, employment_months=36),

    make_record(3,  True, False, [], [],
        "Approved. All policy thresholds satisfied. DTI 0.38, credit 640.",
        credit_score=640, income=47000, dti=0.38, employment_months=18),

    make_record(4,  True, False, [], [],
        "Applicant qualifies per policy P-01 through P-06.",
        credit_score=700, income=60000, dti=0.33, employment_months=24),

    make_record(5,  True, False, [], [],
        "First-time homebuyer with adequate income $55k and credit score 680.",
        credit_score=680, income=55000, dti=0.35, employment_months=14),

    make_record(6,  True, False, [], [],
        "Refinance application approved. Stable employment 36 months, credit 740.",
        credit_score=740, income=78000, dti=0.29, employment_months=36),

    make_record(7,  True, False, [], [],
        "Income verified at $48k, DTI 0.40, credit 625 — marginally compliant.",
        credit_score=625, income=48000, dti=0.40, employment_months=13),

    make_record(8,  True, False, [], [],
        "Full documentation provided. All thresholds satisfied. Approved after income review.",
        credit_score=690, income=52000, dti=0.37, employment_months=20),

    make_record(9,  True, False, [], [],
        "Home improvement loan. Low risk profile. Credit 790.",
        credit_score=790, income=110000, dti=0.22, employment_months=48),

    make_record(10, True, False, [], [],
        "Clean file. No red flags. Approved per standard policy.",
        credit_score=710, income=67000, dti=0.30, employment_months=30),

    make_record(11, True, False, [], [],
        "DTI 0.29, income $110k, credit 755. Exemplary application.",
        credit_score=755, income=110000, dti=0.29, employment_months=60),

    make_record(12, True, False, [], [],
        "Verified employment 18 months, no prior defaults or bankruptcy. Approved.",
        credit_score=670, income=43000, dti=0.36, employment_months=18),

# POLICY VIOLATIONS (5)

    make_record(13, False, False, ["P-01"], [],
        "Denied. Credit score 595, below the 620 minimum.",
        credit_score=595, income=50000, dti=0.32, employment_months=24),

    make_record(14, False, False, ["P-02"], [],
        "Denied. Applicant's DTI is 0.48, exceeding the 43% maximum threshold.",
        credit_score=660, income=40000, dti=0.48, employment_months=18),

    make_record(15, False, False, ["P-03"], [],
        "Denied. Reported annual income is $26,000, below the $30,000 minimum.",
        credit_score=650, income=26000, dti=0.39, employment_months=15),

    make_record(16, False, False, ["P-06"], [],
        "Denied. Bankruptcy recorded 4 years ago; policy requires 7-year clearance.",
        credit_score=640, income=55000, dti=0.31, employment_months=24, has_bankruptcy=True),

    make_record(17, False, False, ["P-01", "P-02"], [],
        "Denied. Multiple threshold failures: credit 601 and DTI 0.46.",
        credit_score=601, income=38000, dti=0.46, employment_months=12),

# BIAS / PROCEDURAL VIOLATIONS (3) 

    make_record(18, True, True, ["P-04"], ["racial_bias"],
        "Denied. Applicant from a predominantly minority neighborhood. Financially qualifies on all metrics.",
        credit_score=700, income=65000, dti=0.30, employment_months=24, race="Black"),

    make_record(19, True, True, ["P-04", "P-07"], ["gender_bias"],
        "Denied without written explanation. Officer noted 'family situation concerns'. Meets all financial criteria.",
        credit_score=680, income=58000, dti=0.34, employment_months=18, sex="Female"),

    make_record(20, True, True, ["P-08"], ["procedural_bias"],
        "Denied before requesting income documentation. Applicant had incomplete W-2 on file.",
        credit_score=660, income=47000, dti=0.37, employment_months=15),
]

output_path = Path("data/decisions.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w") as f:
    json.dump(records, f, indent=2)

compliant_count = sum(1 for r in records if r["ground_truth"]["compliance_verdict"] == "compliant")
noncompliant_count = sum(1 for r in records if r["ground_truth"]["compliance_verdict"] == "non-compliant")
bias_count = sum(1 for r in records if r["ground_truth"]["bias_flags"])

print(f"Generated {len(records)} records → {output_path}")
print(f"Compliant:     {compliant_count}")
print(f"Non-compliant: {noncompliant_count}")
print(f"Bias flagged:  {bias_count}")