import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from utils.helpers import inject_css, sidebar_brand, load_decisions, load_metrics

st.set_page_config(
    page_title="AI Decision Auditor",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
sidebar_brand()

st.markdown(
    '<div class="page-title">⚖️ AI Decision Auditor</div>'
    '<div class="page-subtitle">'
    'LLM-powered compliance &amp; bias detection for lending decisions &nbsp;&middot;&nbsp;'
    '<span style="color:#94a3b8">Aania Adap &amp; Khush Mehta &middot; Spring 2026</span>'
    '</div>',
    unsafe_allow_html=True,
)

decisions = load_decisions()
metrics   = load_metrics()

total       = len(decisions)
n_violation = int((decisions["compliant"] == "No").sum())
n_bias      = int((decisions["bias_present"] == "Yes").sum())
best_f1     = f"{metrics['compliance_f1'].max():.2f}" if metrics is not None else "--"

c1, c2, c3, c4 = st.columns(4)
for col, val, color, label in [
    (c1, total,       "#0f172a", "Loan Decisions"),
    (c2, n_violation, "#dc2626", "Policy Violations"),
    (c3, n_bias,      "#d97706", "Bias Cases"),
    (c4, best_f1,     "#3b82f6", "Best Compliance F1"),
]:
    with col:
        st.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-num" style="color:{color}">{val}</div>'
            f'<div class="stat-label">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

left, right = st.columns(2, gap="medium")
with left:
    st.markdown(
        '<div class="card card-accent-blue">'
        '<div class="sec-head">What This Tool Does</div>'
        '<p style="font-size:0.88rem;color:#374151;line-height:1.75;margin:0">'
        'Audits consumer lending decisions against a fair-lending policy using two distinct '
        'prompting strategies. Each decision returns a <b>compliance verdict</b>, a '
        '<b>0-100 score</b>, specific <b>violated policy clauses</b>, and any '
        '<b>bias flags</b> in the rationale.'
        '</p></div>',
        unsafe_allow_html=True,
    )
with right:
    st.markdown(
        '<div class="card card-accent-blue">'
        '<div class="sec-head">Two Prompting Strategies</div>'
        '<div style="font-size:0.87rem;color:#374151;line-height:1.85">'
        '<b>Few-Shot</b> &mdash; Full policy context + 3 worked examples. '
        'Higher accuracy (~2,150 tokens / decision).<br>'
        '<b>RAG + CoT</b> &mdash; Top-5 retrieved policy chunks + step-by-step reasoning. '
        'Leaner, ~55% fewer tokens (~960 / decision).'
        '</div></div>',
        unsafe_allow_html=True,
    )

if metrics is not None:
    st.markdown('<div class="sec-head" style="margin-top:0.25rem">Strategy Snapshot</div>', unsafe_allow_html=True)
    rows = []
    for _, r in metrics.iterrows():
        label = "Few-Shot" if r["strategy"] == "few_shot" else "RAG + CoT"
        rows.append({
            "Strategy":      label,
            "Compliance F1": f"{r['compliance_f1']:.3f}",
            "Bias F1":       f"{r['bias_f1']:.3f}",
            "Clause F1":     f"{r['clause_f1']:.3f}",
            "Avg Tokens":    f"{int(r['avg_tokens']):,}",
            "Total Tokens":  f"{int(r['total_tokens']):,}",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<p style="font-size:0.76rem;color:#cbd5e1;text-align:center">'
    'FE524 &middot; Prompt Engineering Lab &middot; Stevens Institute of Technology &middot; Spring 2026'
    '</p>',
    unsafe_allow_html=True,
)
