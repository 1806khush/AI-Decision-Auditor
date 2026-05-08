import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from PIL import Image
from utils.helpers import inject_css, sidebar_brand, load_metrics, EVAL_DIR

st.set_page_config(page_title="Dashboard - AI Decision Auditor", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()
sidebar_brand()

st.markdown(
    '<div class="page-title">📊 Dashboard</div>'
    '<div class="page-subtitle">Side-by-side evaluation metrics for both prompting strategies across 35 labeled decisions.</div>',
    unsafe_allow_html=True,
)

metrics = load_metrics()
if metrics is None:
    st.warning("No metrics found. Run `python src/evaluate.py` first.")
    st.stop()

fs = metrics[metrics["strategy"] == "few_shot"].iloc[0]
rc = metrics[metrics["strategy"] == "rag_cot"].iloc[0]
BLUE, PURPLE = "#3b82f6", "#8b5cf6"

# ── Compliance cards ──────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">Compliance Detection</div>', unsafe_allow_html=True)
for cols, pairs in [
    (st.columns(6), [
        ("FS Precision",  fs["compliance_p"],  BLUE),
        ("FS Recall",     fs["compliance_r"],  BLUE),
        ("FS F1",         fs["compliance_f1"], BLUE),
        ("RAG Precision", rc["compliance_p"],  PURPLE),
        ("RAG Recall",    rc["compliance_r"],  PURPLE),
        ("RAG F1",        rc["compliance_f1"], PURPLE),
    ]),
]:
    for col, (label, val, c) in zip(cols, pairs):
        with col:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-num" style="color:{c};font-size:1.45rem">{val:.3f}</div>'
                f'<div class="stat-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

st.markdown("<div style='margin-top:0.9rem'></div>", unsafe_allow_html=True)

# ── Bias cards ────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">Bias Detection</div>', unsafe_allow_html=True)
for cols, pairs in [
    (st.columns(6), [
        ("FS Precision",  fs["bias_p"],  BLUE),
        ("FS Recall",     fs["bias_r"],  BLUE),
        ("FS F1",         fs["bias_f1"], BLUE),
        ("RAG Precision", rc["bias_p"],  PURPLE),
        ("RAG Recall",    rc["bias_r"],  PURPLE),
        ("RAG F1",        rc["bias_f1"], PURPLE),
    ]),
]:
    for col, (label, val, c) in zip(cols, pairs):
        with col:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-num" style="color:{c};font-size:1.45rem">{val:.3f}</div>'
                f'<div class="stat-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

st.markdown("<div style='margin-top:1.4rem'></div>", unsafe_allow_html=True)

# ── Chart + table ─────────────────────────────────────────────────────────────
chart_col, table_col = st.columns([1.2, 1], gap="large")

with chart_col:
    st.markdown('<div class="sec-head">F1 Score Comparison</div>', unsafe_allow_html=True)
    p = EVAL_DIR / "strategy_comparison.png"
    if p.exists():
        st.image(Image.open(p), use_container_width=True)
    else:
        chart_df = pd.DataFrame({
            "Metric":    ["Compliance F1", "Bias F1", "Clause F1"],
            "Few-Shot":  [fs["compliance_f1"], fs["bias_f1"], fs["clause_f1"]],
            "RAG + CoT": [rc["compliance_f1"], rc["bias_f1"], rc["clause_f1"]],
        }).set_index("Metric")
        st.bar_chart(chart_df, color=[BLUE, PURPLE])

with table_col:
    st.markdown('<div class="sec-head">Full Metrics Table</div>', unsafe_allow_html=True)
    rows = []
    for lbl, key in [
        ("Compliance Precision", "compliance_p"),
        ("Compliance Recall",    "compliance_r"),
        ("Compliance F1",        "compliance_f1"),
        ("Bias Precision",       "bias_p"),
        ("Bias Recall",          "bias_r"),
        ("Bias F1",              "bias_f1"),
        ("Clause Precision",     "clause_p"),
        ("Clause Recall",        "clause_r"),
        ("Clause F1",            "clause_f1"),
    ]:
        rows.append({
            "Metric":    lbl,
            "Few-Shot":  f"{fs[key]:.3f}",
            "RAG + CoT": f"{rc[key]:.3f}",
            "Winner":    "Few-Shot" if fs[key] >= rc[key] else "RAG+CoT",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.markdown("<div style='margin-top:0.9rem'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-head">Token Cost</div>', unsafe_allow_html=True)
    ta, tb = st.columns(2)
    with ta:
        st.markdown(
            f'<div class="card card-accent-blue" style="text-align:center">'
            f'<div class="stat-num" style="font-size:1.3rem;color:{BLUE}">{int(fs["avg_tokens"]):,}</div>'
            f'<div class="stat-label">Few-Shot avg</div>'
            f'<div style="font-size:0.74rem;color:#94a3b8;margin-top:4px">Total: {int(fs["total_tokens"]):,}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with tb:
        savings = round((1 - rc["avg_tokens"] / fs["avg_tokens"]) * 100)
        st.markdown(
            f'<div class="card card-accent-blue" style="text-align:center">'
            f'<div class="stat-num" style="font-size:1.3rem;color:{PURPLE}">{int(rc["avg_tokens"]):,}</div>'
            f'<div class="stat-label">RAG+CoT avg</div>'
            f'<div style="font-size:0.74rem;color:#16a34a;margin-top:4px">&#8595; {savings}% cheaper</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Confusion matrices ────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:1.4rem'></div>", unsafe_allow_html=True)
st.markdown('<div class="sec-head">Confusion Matrices</div>', unsafe_allow_html=True)

cm_files = [
    ("Few-Shot - Compliance", "confusion_compliance_few_shot.png"),
    ("Few-Shot - Bias",       "confusion_bias_few_shot.png"),
    ("RAG+CoT - Compliance",  "confusion_compliance_rag_cot.png"),
    ("RAG+CoT - Bias",        "confusion_bias_rag_cot.png"),
]
cm_cols = st.columns(4, gap="small")
for col, (title, fname) in zip(cm_cols, cm_files):
    with col:
        st.markdown(
            f'<div style="font-size:0.76rem;color:#64748b;text-align:center;'
            f'margin-bottom:5px;font-weight:600">{title}</div>',
            unsafe_allow_html=True,
        )
        p = EVAL_DIR / fname
        if p.exists():
            st.image(Image.open(p), use_container_width=True)
        else:
            st.markdown(
                '<div style="background:#f8fafc;border:1px dashed #e2e8f0;border-radius:8px;'
                'padding:2rem;text-align:center;color:#94a3b8;font-size:0.8rem">Not found</div>',
                unsafe_allow_html=True,
            )
