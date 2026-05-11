# app.py - streamlit demo for the AI Decision Auditor
# run with: streamlit run app.py

import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI Decision Auditor", layout="wide")

# white background, dark text
st.markdown("""<style>
    .stApp { background-color: #ffffff; }
    .stApp, .stApp * { color: #1a1a1a !important; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #0f172a !important; }
    .stApp .stCaption p { color: #64748b !important; }
    .stTabs [data-baseweb="tab"] { color: #1a1a1a !important; }
    .stSelectbox label, .stSelectbox div { color: #1a1a1a !important; }
    [data-testid="stMetricValue"] { color: #1a1a1a !important; }
    [data-testid="stMetricLabel"] { color: #64748b !important; }
</style>""", unsafe_allow_html=True)

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
EVAL_DIR = os.path.join(ROOT, "eval")

st.title("AI Decision Auditor")
st.caption("FE524 - Prompt Engineering Lab | Aania Adap, Khush Mehta")

decisions = pd.read_csv(os.path.join(DATA_DIR, "loan_decisions.csv"))
fs_out = pd.read_csv(os.path.join(EVAL_DIR, "outputs_few_shot.csv"))
rc_out = pd.read_csv(os.path.join(EVAL_DIR, "outputs_rag_cot.csv"))
metrics = pd.read_csv(os.path.join(EVAL_DIR, "metrics_comparison.csv"))

# color helpers - using inline styles so they actually render
GREEN = "color:#16a34a !important;font-weight:600"
RED = "color:#dc2626 !important;font-weight:600"
YELLOW = "color:#d97706 !important;font-weight:600"


def compliance_flag(val):
    v = str(val).strip()
    if v == "Yes":
        return f'<span style="{GREEN}">✅ Compliant</span>'
    return f'<span style="{RED}">🚩 Non-Compliant</span>'


def bias_flag(val):
    v = str(val).strip()
    if v == "No":
        return f'<span style="{GREEN}">✅ No Bias</span>'
    return f'<span style="{YELLOW}">⚠️ Bias Detected</span>'


def clause_flag(val):
    if pd.isna(val) or not str(val).strip():
        return f'<span style="{GREEN}">None</span>'
    return f'<span style="{RED}">{val}</span>'


def score_flag(val):
    try:
        s = float(val)
    except:
        return f'<span style="{YELLOW}">N/A</span>'
    if s >= 70:
        return f'<span style="{GREEN}">{s:.0f}/100</span>'
    elif s >= 40:
        return f'<span style="{YELLOW}">{s:.0f}/100</span>'
    return f'<span style="{RED}">{s:.0f}/100</span>'


tab1, tab2, tab3 = st.tabs(["Audit", "Metrics", "Data"])

# ---- TAB 1: audit a single decision ----
with tab1:
    st.subheader("Inspect a Decision")

    ids = decisions["decision_id"].tolist()
    names = decisions["applicant_name"].tolist()
    options = [f"{d} - {n}" for d, n in zip(ids, names)]
    selected = st.selectbox("Pick a decision", options)
    dec_id = selected.split(" - ")[0]

    row = decisions[decisions.decision_id == dec_id].iloc[0]

    st.markdown(f"**Applicant:** {row.applicant_name}, {row.age}, {row.gender}, {row.race}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Credit Score", row.credit_score)
    c2.metric("Income", f"${int(row.income):,}")
    c3.metric("DTI", f"{row.dti_ratio}%")
    c4.metric("Loan", f"${int(row.loan_amount):,}")

    st.markdown(f"**Decision:** {row.decision} | **Rate:** {row.rate_offered}% | **Term:** {row.term_months} mo | **Officer:** {row.officer}")
    st.markdown(f"**Rationale:** _{row.rationale}_")

    st.divider()

    # ground truth
    st.markdown("#### Ground Truth")
    gt1, gt2, gt3 = st.columns(3)
    gt1.markdown(f"Compliance: {compliance_flag(row.compliant)}", unsafe_allow_html=True)
    gt2.markdown(f"Bias: {bias_flag(row.bias_present)}", unsafe_allow_html=True)
    gt3.markdown(f"Violated: {clause_flag(row.violated_clauses)}", unsafe_allow_html=True)

    if pd.notna(row.bias_description) and str(row.bias_description).strip():
        st.markdown(f'<span style="{YELLOW}">📝 {row.bias_description}</span>', unsafe_allow_html=True)

    st.divider()

    # model outputs
    st.markdown("#### Model Outputs")
    left, right = st.columns(2)

    fs_row = fs_out[fs_out.decision_id == dec_id]
    rc_row = rc_out[rc_out.decision_id == dec_id]

    def show_result(col, label, result_df):
        with col:
            st.markdown(f"**{label}**")
            if len(result_df) == 0:
                st.warning("No result")
                return
            r = result_df.iloc[0]
            st.markdown(f"Compliance: {compliance_flag(r.compliant)}", unsafe_allow_html=True)
            st.markdown(f"Score: {score_flag(r.compliance_score)}", unsafe_allow_html=True)
            st.markdown(f"Bias: {bias_flag(r.bias_present)}", unsafe_allow_html=True)
            st.markdown(f"Clauses: {clause_flag(r.violated_clauses)}", unsafe_allow_html=True)
            st.markdown(f"Tokens: `{int(r.tokens_used):,}`")
            with st.expander("Explanation"):
                st.write(r.explanation)

    show_result(left, "🔵 Few-Shot", fs_row)
    show_result(right, "🟢 RAG + CoT", rc_row)

    # agreement check
    if len(fs_row) and len(rc_row):
        fs_v = str(fs_row.iloc[0].compliant).strip()
        rc_v = str(rc_row.iloc[0].compliant).strip()
        st.divider()
        if fs_v == rc_v:
            st.success("Both strategies agree on the verdict.")
        else:
            st.warning("Strategies disagree on the verdict.")

# ---- TAB 2: metrics ----
with tab2:
    st.subheader("Strategy Comparison")

    fs = metrics[metrics.strategy == "few_shot"].iloc[0]
    rc = metrics[metrics.strategy == "rag_cot"].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Few-Shot Compliance F1", f"{fs.compliance_f1:.3f}")
    c2.metric("RAG+CoT Compliance F1", f"{rc.compliance_f1:.3f}")
    c3.metric("Token Savings (RAG)", f"{(1 - rc.avg_tokens/fs.avg_tokens)*100:.0f}%")

    st.divider()
    st.markdown("**Full Metrics**")
    st.dataframe(metrics, use_container_width=True)

    st.divider()
    chart = os.path.join(EVAL_DIR, "strategy_comparison.png")
    if os.path.exists(chart):
        st.image(chart, caption="F1 Comparison")

    st.divider()
    st.markdown("**Confusion Matrices**")
    c1, c2 = st.columns(2)
    for name, col in [("few_shot", c1), ("rag_cot", c2)]:
        with col:
            for kind in ["compliance", "bias"]:
                p = os.path.join(EVAL_DIR, f"confusion_{kind}_{name}.png")
                if os.path.exists(p):
                    st.image(p, caption=f"{name} - {kind}")

# ---- TAB 3: data ----
with tab3:
    st.subheader("All Decisions")

    col_filter = st.selectbox("Filter", ["All", "Compliant", "Non-Compliant", "Bias"])
    df = decisions.copy()
    if col_filter == "Compliant":
        df = df[df.compliant == "Yes"]
    elif col_filter == "Non-Compliant":
        df = df[df.compliant == "No"]
    elif col_filter == "Bias":
        df = df[df.bias_present == "Yes"]

    st.markdown(f"Showing **{len(df)}** records")
    st.dataframe(
        df[["decision_id", "applicant_name", "credit_score", "income",
            "loan_amount", "decision", "rate_offered", "compliant",
            "bias_present", "violated_clauses"]],
        use_container_width=True,
        height=400,
    )
