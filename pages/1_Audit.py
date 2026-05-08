import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.helpers import (
    inject_css, sidebar_brand, load_decisions, load_eval_output,
    credit_tier, score_bar_html, verdict_badge, bias_badge, clause_tags,
)

st.set_page_config(page_title="Audit - AI Decision Auditor", page_icon="🔍",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()
sidebar_brand()

st.markdown(
    '<div class="page-title">🔍 Audit</div>'
    '<div class="page-subtitle">Select a loan decision to inspect compliance audit results from both strategies.</div>',
    unsafe_allow_html=True,
)

decisions = load_decisions()
fs_out    = load_eval_output("few_shot")
rc_out    = load_eval_output("rag_cot")

options = [f"{r['decision_id']} - {r['applicant_name']}" for _, r in decisions.iterrows()]
selected = st.selectbox("Choose a decision", options, label_visibility="collapsed")
dec_id   = selected.split(" - ")[0]
dec_row  = decisions[decisions["decision_id"] == dec_id].iloc[0]

st.markdown("<div style='margin-top:0.9rem'></div>", unsafe_allow_html=True)

col_dec, col_res = st.columns([1, 1.6], gap="large")

# ── LEFT: Decision card ───────────────────────────────────────────────────────
with col_dec:
    gt_compliant = str(dec_row.get("compliant", "")).strip()
    gt_bias      = str(dec_row.get("bias_present", "")).strip()
    accent       = "green" if gt_compliant == "Yes" else "red"
    tier_label, tier_range = credit_tier(int(dec_row["credit_score"]))

    st.markdown(f'<div class="card card-accent-{accent}">', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:1.05rem;font-weight:700;color:#0f172a">{dec_row["applicant_name"]}</div>'
        f'<div style="font-size:0.8rem;color:#64748b;margin-bottom:0.75rem">'
        f'{dec_row["decision_id"]} &middot; {dec_row["age"]} yrs &middot; '
        f'{dec_row["gender"]} &middot; {dec_row["race"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="margin-bottom:0.8rem">'
        '<span style="font-size:0.67rem;color:#94a3b8;text-transform:uppercase;'
        'letter-spacing:.08em;font-weight:600">Ground Truth &nbsp;</span>'
        f'{verdict_badge(gt_compliant)} &nbsp; {bias_badge(gt_bias)}</div>',
        unsafe_allow_html=True,
    )

    def field(label, val):
        return (f'<div class="field"><div class="field-label">{label}</div>'
                f'<div class="field-val">{val}</div></div>')

    f1, f2 = st.columns(2)
    with f1:
        st.markdown(field("Credit Score", int(dec_row["credit_score"])), unsafe_allow_html=True)
        st.markdown(field("Income",       f'${int(dec_row["income"]):,}'), unsafe_allow_html=True)
        st.markdown(field("Loan Amount",  f'${int(dec_row["loan_amount"]):,}'), unsafe_allow_html=True)
        st.markdown(field("Loan Type",    dec_row["loan_type"]), unsafe_allow_html=True)
    with f2:
        st.markdown(field("Score Tier",   tier_label), unsafe_allow_html=True)
        st.markdown(field("DTI Ratio",    f'{dec_row["dti_ratio"]}%'), unsafe_allow_html=True)
        rate_str = f'{dec_row["rate_offered"]}%' if pd.notna(dec_row["rate_offered"]) else "N/A"
        st.markdown(field("Rate Offered", rate_str), unsafe_allow_html=True)
        st.markdown(field("Decision",     dec_row["decision"]), unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        '<div class="field-label">Officer Rationale</div>'
        f'<div class="explanation">{dec_row["rationale"]}</div>',
        unsafe_allow_html=True,
    )

    if dec_row["violated_clauses"]:
        st.markdown(
            '<div style="margin-top:0.65rem"></div>'
            '<div class="field-label">Ground Truth Violations</div>'
            + clause_tags(dec_row["violated_clauses"]),
            unsafe_allow_html=True,
        )
    bias_desc = dec_row.get("bias_description", "")
    if bias_desc and str(bias_desc) not in ("", "nan", "None"):
        st.markdown(
            f'<div style="margin-top:0.5rem;font-size:0.8rem;color:#92400e;'
            f'background:#fef3c7;border-radius:7px;padding:6px 9px">'
            f'<b>Bias note:</b> {bias_desc}</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ── RIGHT: Strategy results ───────────────────────────────────────────────────
with col_res:
    st.markdown('<div class="sec-head">Audit Results</div>', unsafe_allow_html=True)

    r_fs = fs_out[fs_out["decision_id"] == dec_id].iloc[0] if fs_out is not None else None
    r_rc = rc_out[rc_out["decision_id"] == dec_id].iloc[0] if rc_out is not None else None

    strat_cols = st.columns(2, gap="medium")
    for (label, row), col in zip([("Few-Shot", r_fs), ("RAG + CoT", r_rc)], strat_cols):
        with col:
            if row is None:
                st.markdown(
                    f'<div class="card"><div class="sec-head">{label}</div>'
                    f'<p style="color:#94a3b8;font-size:0.85rem">No results. Run auditor.py first.</p></div>',
                    unsafe_allow_html=True,
                )
                continue

            score  = float(row["compliance_score"])
            comp   = str(row["compliant"]).strip()
            bias   = str(row["bias_present"]).strip()
            accent = "green" if comp == "Yes" else "red"

            st.markdown(f'<div class="card card-accent-{accent}">', unsafe_allow_html=True)
            st.markdown(
                f'<div style="font-size:0.9rem;font-weight:700;color:#0f172a;margin-bottom:6px">{label}</div>'
                f'{verdict_badge(comp)} &nbsp; {bias_badge(bias)}',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="field-label" style="margin-top:0.8rem">Compliance Score</div>'
                + score_bar_html(score),
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="field-label" style="margin-top:0.65rem">Violated Clauses</div>'
                + clause_tags(str(row["violated_clauses"])),
                unsafe_allow_html=True,
            )

            if bias.lower() == "yes":
                flags_raw = str(row.get("bias_flags", "")).strip()
                if flags_raw:
                    st.markdown('<div class="field-label" style="margin-top:0.65rem">Bias Flags</div>', unsafe_allow_html=True)
                    for flag in flags_raw.split("|"):
                        flag = flag.strip()
                        if flag:
                            st.markdown(
                                f'<div style="font-size:0.79rem;color:#92400e;background:#fef3c7;'
                                f'border-radius:6px;padding:4px 8px;margin:3px 0">&#9888; {flag}</div>',
                                unsafe_allow_html=True,
                            )

            exp = str(row.get("explanation", "")).strip()
            if exp:
                st.markdown(
                    '<div class="field-label" style="margin-top:0.7rem">Explanation</div>'
                    f'<div class="explanation">{exp}</div>',
                    unsafe_allow_html=True,
                )

            tokens = row.get("tokens_used", "--")
            st.markdown(
                f'<div style="font-size:0.71rem;color:#94a3b8;margin-top:0.65rem;text-align:right">'
                f'{int(tokens):,} tokens used</div>',
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    if r_fs is not None and r_rc is not None:
        agree = str(r_fs["compliant"]).strip() == str(r_rc["compliant"]).strip()
        st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
        if agree:
            st.markdown(
                '<div style="font-size:0.82rem;color:#15803d;background:#dcfce7;'
                'border-radius:8px;padding:7px 13px;border:1px solid #86efac">'
                '&#10003; Both strategies agree on verdict</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:0.82rem;color:#92400e;background:#fef3c7;'
                'border-radius:8px;padding:7px 13px;border:1px solid #fcd34d">'
                '&#9889; Strategies disagree &mdash; review carefully</div>',
                unsafe_allow_html=True,
            )
