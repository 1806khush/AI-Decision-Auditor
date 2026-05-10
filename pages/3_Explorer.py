import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.helpers import (
    inject_css, sidebar_brand, load_decisions, load_eval_output,
    verdict_badge, bias_badge, clause_tags, score_bar_html, credit_tier,
)

st.set_page_config(page_title="Explorer - AI Decision Auditor", page_icon="🗂",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()
sidebar_brand()

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sec-head" style="margin-top:0.5rem">Filters</div>', unsafe_allow_html=True)
    filter_compliance = st.selectbox("Compliance", ["All", "Compliant", "Non-Compliant"])
    filter_bias       = st.selectbox("Bias",       ["All", "Bias Present", "No Bias"])
    filter_decision   = st.selectbox("Decision",   ["All", "Approved", "Denied"])
    filter_loan_type  = st.selectbox("Loan Type",  ["All", "Unsecured", "Secured"])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="page-title">🗂 Explorer</div>'
    '<div class="page-subtitle">Browse, filter, and expand all 35 labeled loan decisions with audit results.</div>',
    unsafe_allow_html=True,
)

# ── Load + merge ──────────────────────────────────────────────────────────────
decisions = load_decisions()
fs_out    = load_eval_output("few_shot")
rc_out    = load_eval_output("rag_cot")

if fs_out is not None:
    decisions = decisions.merge(
        fs_out[["decision_id","compliant","compliance_score","violated_clauses","bias_present","bias_flags","explanation"]],
        on="decision_id", suffixes=("","_fs"), how="left",
    ).rename(columns={
        "compliant_fs":"fs_compliant","compliance_score":"fs_score",
        "violated_clauses_fs":"fs_clauses","bias_present_fs":"fs_bias",
        "bias_flags":"fs_bias_flags","explanation":"fs_explanation",
    })
else:
    for c in ["fs_compliant","fs_score","fs_clauses","fs_bias","fs_bias_flags","fs_explanation"]:
        decisions[c] = None

if rc_out is not None:
    decisions = decisions.merge(
        rc_out[["decision_id","compliant","compliance_score","violated_clauses","bias_present","bias_flags","explanation"]],
        on="decision_id", suffixes=("","_rc"), how="left",
    ).rename(columns={
        "compliant_rc":"rc_compliant","compliance_score":"rc_score",
        "violated_clauses_rc":"rc_clauses","bias_present_rc":"rc_bias",
        "bias_flags":"rc_bias_flags","explanation":"rc_explanation",
    })
else:
    for c in ["rc_compliant","rc_score","rc_clauses","rc_bias","rc_bias_flags","rc_explanation"]:
        decisions[c] = None

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = decisions.copy()
if filter_compliance == "Compliant":     filtered = filtered[filtered["compliant"] == "Yes"]
elif filter_compliance == "Non-Compliant": filtered = filtered[filtered["compliant"] == "No"]
if filter_bias == "Bias Present":        filtered = filtered[filtered["bias_present"] == "Yes"]
elif filter_bias == "No Bias":           filtered = filtered[filtered["bias_present"] == "No"]
if filter_decision != "All":             filtered = filtered[filtered["decision"] == filter_decision]
if filter_loan_type != "All":            filtered = filtered[filtered["loan_type"] == filter_loan_type]

# ── Summary cards ─────────────────────────────────────────────────────────────
n_total     = len(filtered)
n_violation = int((filtered["compliant"] == "No").sum())
n_bias_ct   = int((filtered["bias_present"] == "Yes").sum())

c1, c2, c3 = st.columns(3)
for col, val, color, label in [
    (c1, n_total,     "#0f172a", "Showing"),
    (c2, n_violation, "#dc2626", "Violations"),
    (c3, n_bias_ct,   "#d97706", "Bias Cases"),
]:
    with col:
        st.markdown(
            f'<div class="stat-card"><div class="stat-num" style="color:{color}">{val}</div>'
            f'<div class="stat-label">{label}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)

if filtered.empty:
    st.info("No decisions match the current filters.")
    st.stop()

# ── Decision rows ─────────────────────────────────────────────────────────────
for _, row in filtered.iterrows():
    gt_ok   = str(row["compliant"]).strip()
    gt_bias = str(row["bias_present"]).strip()
    rate_str = f'{row["rate_offered"]}%' if pd.notna(row["rate_offered"]) else "-"
    tier_label, _ = credit_tier(int(row["credit_score"]))
    verdict_icon = "✗" if gt_ok == "No" else "✓"
    bias_icon    = " ⚠" if gt_bias == "Yes" else ""

    with st.expander(
        f'{row["decision_id"]} — {row["applicant_name"]}  {verdict_icon}{bias_icon}',
        expanded=False,
    ):
        top_l, top_r = st.columns([1, 2], gap="medium")

        with top_l:
            st.markdown('<div class="sec-head">Decision Details</div>', unsafe_allow_html=True)

            def f(lbl, val):
                return (f'<div class="field"><div class="field-label">{lbl}</div>'
                        f'<div class="field-val">{val}</div></div>')

            g1, g2 = st.columns(2)
            with g1:
                st.markdown(f("Credit Score", int(row["credit_score"])),        unsafe_allow_html=True)
                st.markdown(f("Income",        f'${int(row["income"]):,}'),      unsafe_allow_html=True)
                st.markdown(f("DTI",           f'{row["dti_ratio"]}%'),           unsafe_allow_html=True)
                st.markdown(f("Loan Amount",   f'${int(row["loan_amount"]):,}'), unsafe_allow_html=True)
            with g2:
                st.markdown(f("Score Tier",  tier_label),       unsafe_allow_html=True)
                st.markdown(f("Loan Type",   row["loan_type"]), unsafe_allow_html=True)
                st.markdown(f("Decision",    row["decision"]),  unsafe_allow_html=True)
                st.markdown(f("Rate",        rate_str),         unsafe_allow_html=True)

            st.markdown(
                '<div class="field-label" style="margin-top:0.4rem">Ground Truth</div>'
                f'{verdict_badge(gt_ok)} &nbsp; {bias_badge(gt_bias)}',
                unsafe_allow_html=True,
            )
            if row.get("violated_clauses"):
                st.markdown(
                    '<div class="field-label" style="margin-top:0.5rem">Violated Clauses</div>'
                    + clause_tags(row["violated_clauses"]),
                    unsafe_allow_html=True,
                )
            st.markdown(
                '<div class="field-label" style="margin-top:0.5rem">Rationale</div>'
                f'<div class="explanation">{row["rationale"]}</div>',
                unsafe_allow_html=True,
            )

        with top_r:
            st.markdown('<div class="sec-head">Audit Results</div>', unsafe_allow_html=True)
            a_col, b_col = st.columns(2, gap="small")

            for col, (strat_lbl, s_comp, s_score, s_clauses, s_bias, s_flags, s_exp) in zip(
                [a_col, b_col],
                [
                    ("Few-Shot",  row.get("fs_compliant"), row.get("fs_score"),
                     row.get("fs_clauses"), row.get("fs_bias"),
                     row.get("fs_bias_flags"), row.get("fs_explanation")),
                    ("RAG + CoT", row.get("rc_compliant"), row.get("rc_score"),
                     row.get("rc_clauses"), row.get("rc_bias"),
                     row.get("rc_bias_flags"), row.get("rc_explanation")),
                ],
            ):
                with col:
                    if pd.isna(s_score):
                        st.markdown(
                            f'<div style="font-size:0.82rem;color:#94a3b8">{strat_lbl}: no results</div>',
                            unsafe_allow_html=True,
                        )
                        continue
                    accent = "green" if str(s_comp).strip() == "Yes" else "red"
                    st.markdown(f'<div class="card card-accent-{accent}" style="padding:0.9rem 1rem">', unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="font-size:0.83rem;font-weight:700;color:#0f172a;margin-bottom:5px">{strat_lbl}</div>'
                        f'{verdict_badge(s_comp)} &nbsp; {bias_badge(s_bias)}',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        '<div class="field-label" style="margin-top:7px">Score</div>'
                        + score_bar_html(float(s_score)),
                        unsafe_allow_html=True,
                    )
                    if str(s_clauses).strip():
                        st.markdown(
                            '<div class="field-label">Clauses</div>' + clause_tags(str(s_clauses)),
                            unsafe_allow_html=True,
                        )
                    if str(s_bias).strip().lower() == "yes" and str(s_flags).strip():
                        for flag in str(s_flags).split("|"):
                            if flag.strip():
                                st.markdown(
                                    f'<div style="font-size:0.75rem;color:#92400e;background:#fef3c7;'
                                    f'border-radius:5px;padding:3px 7px;margin:2px 0">&#9888; {flag.strip()}</div>',
                                    unsafe_allow_html=True,
                                )
                    if str(s_exp).strip():
                        st.markdown(
                            '<div class="field-label" style="margin-top:5px">Explanation</div>'
                            f'<div class="explanation" style="font-size:0.8rem">{s_exp}</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
