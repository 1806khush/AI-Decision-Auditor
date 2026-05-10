"""
utils/helpers.py  --  shared loaders, formatters, CSS + sidebar
"""
import pandas as pd
import streamlit as st
from pathlib import Path

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "Data"
EVAL_DIR = ROOT / "eval"

@st.cache_data
def load_decisions():
    df = pd.read_csv(DATA_DIR / "loan_decisions.csv")
    df["violated_clauses"] = df["violated_clauses"].fillna("")
    df["bias_description"] = df["bias_description"].fillna("")
    df["collateral"]       = df["collateral"].fillna("None")
    df["co_signer"]        = df["co_signer"].fillna("None")
    df["rate_offered"]     = pd.to_numeric(df["rate_offered"], errors="coerce")
    df["term_months"]      = pd.to_numeric(df["term_months"],  errors="coerce")
    return df


@st.cache_data
def load_policy():
    return (DATA_DIR / "lending_policy.md").read_text(encoding="utf-8")


@st.cache_data
def load_eval_output(strategy):
    path = EVAL_DIR / f"outputs_{strategy}.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df["violated_clauses"] = df["violated_clauses"].fillna("")
    df["bias_flags"]       = df["bias_flags"].fillna("")
    df["explanation"]      = df["explanation"].fillna("")
    df["compliance_score"] = pd.to_numeric(df["compliance_score"], errors="coerce").fillna(0)
    df["compliant"]        = df["compliant"].astype(str).str.strip()
    df["bias_present"]     = df["bias_present"].astype(str).str.strip()
    return df


@st.cache_data
def load_metrics():
    path = EVAL_DIR / "metrics_comparison.csv"
    return pd.read_csv(path) if path.exists() else None

def credit_tier(score):
    if score >= 760: return "Tier 1 (760+)",    "5.5-7.0%"
    if score >= 700: return "Tier 2 (700-759)", "7.0-9.5%"
    if score >= 660: return "Tier 3 (660-699)", "9.5-12.0%"
    if score >= 620: return "Tier 4 (620-659)", "12.0-14.5%"
    return "Below Minimum", "N/A"


def score_color(score):
    if score >= 80: return "#16a34a"
    if score >= 55: return "#d97706"
    return "#dc2626"


def verdict_badge(v):
    ok = str(v).strip().lower() == "yes"
    cls = "badge-ok" if ok else "badge-bad"
    txt = "Compliant" if ok else "Non-Compliant"
    sym = "&#10003;" if ok else "&#10007;"
    return f'<span class="{cls} badge">{sym} {txt}</span>'


def bias_badge(b):
    yes = str(b).strip().lower() == "yes"
    if yes:
        return '<span class="badge badge-bias">&#9888; Bias Detected</span>'
    return '<span class="badge badge-ok-soft">&#10003; No Bias</span>'


def clause_tags(clauses):
    items = [c.strip() for c in str(clauses).split(",") if c.strip()]
    if not items:
        return '<span style="color:#94a3b8;font-size:0.85rem">None</span>'
    return " ".join(f'<span class="clause-tag">{c}</span>' for c in items)


def score_bar_html(score):
    color = score_color(float(score))
    pct   = min(max(float(score), 0), 100)
    return (
        '<div style="display:flex;align-items:center;gap:12px;margin:6px 0">'
        '<div style="flex:1;background:#f1f5f9;border-radius:99px;height:8px;overflow:hidden">'
        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:99px"></div>'
        '</div>'
        f'<span style="font-size:1.1rem;font-weight:800;color:{color};min-width:36px">{int(score)}</span>'
        '</div>'
    )

def sidebar_brand():
    with st.sidebar:
        st.markdown(
            '<div style="padding:0.5rem 0 0.15rem">'
            '<span style="font-size:1.05rem;font-weight:800;color:#0f172a">AI Decision Auditor</span>'
            '</div>'
            '<div style="font-size:0.72rem;color:#94a3b8;margin-bottom:0.7rem">'
            'FE524 &middot; Stevens Institute of Technology</div>',
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown(
            '<div style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;'
            'letter-spacing:0.1em;font-weight:700;margin-bottom:6px">Pages</div>',
            unsafe_allow_html=True,
        )
        for icon, label, desc in [
            ("&#128269;", "Audit",     "Inspect any loan decision"),
            ("&#128200;", "Dashboard", "Strategy metrics &amp; charts"),
            ("&#128193;", "Explorer",  "Browse &amp; filter all cases"),
        ]:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:9px;padding:8px 10px;'
                f'border-radius:9px;margin-bottom:4px;background:#f8fafc;border:1px solid #e2e8f0">'
                f'<span style="font-size:1rem;line-height:1">{icon}</span>'
                f'<div>'
                f'<div style="font-size:0.83rem;font-weight:600;color:#1e293b;line-height:1.2">{label}</div>'
                f'<div style="font-size:0.7rem;color:#94a3b8;margin-top:1px">{desc}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        st.divider()
        st.markdown(
            '<div style="font-size:0.71rem;color:#94a3b8;line-height:1.7">'
            'Aania Adap &amp; Khush Mehta<br>Spring 2026</div>',
            unsafe_allow_html=True,
        )


CSS = """<style>
#MainMenu,footer{visibility:hidden}
[data-testid="collapsedControl"]{visibility:visible !important;opacity:1 !important}
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],.main .block-container{
  background-color:#f8fafc !important;color:#0f172a !important}
[data-testid="stSidebar"]{background:#ffffff !important;border-right:1px solid #e2e8f0 !important}
[data-testid="stSidebar"] *{color:#1e293b !important}
[data-testid="stSidebar"] hr{border-color:#e2e8f0 !important}
[data-testid="stSidebarNavLink"]{border-radius:8px !important;margin:2px 8px !important;
  padding:8px 12px !important;font-size:0.88rem !important;font-weight:500 !important;
  color:#374151 !important;transition:background 0.15s,color 0.15s !important}
[data-testid="stSidebarNavLink"]:hover{background:#f1f5f9 !important;color:#0f172a !important}
[data-testid="stSidebarNavLink"][aria-current="page"]{background:#eff6ff !important;
  color:#1d4ed8 !important;font-weight:700 !important}
.stat-card{background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;
  padding:1.25rem 1rem 1rem;text-align:center;
  transition:box-shadow 0.2s,transform 0.2s;box-shadow:0 1px 3px rgba(15,23,42,0.06)}
.stat-card:hover{box-shadow:0 4px 16px rgba(15,23,42,0.10);transform:translateY(-2px)}
.stat-num{font-size:2rem;font-weight:800;color:#0f172a;line-height:1.1;letter-spacing:-0.02em}
.stat-label{font-size:0.7rem;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.08em;margin-top:5px;font-weight:600}
.card{background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;
  padding:1.2rem 1.4rem;margin-bottom:0.9rem;
  box-shadow:0 1px 3px rgba(15,23,42,0.05);color:#0f172a}
.card-accent-green{border-left:4px solid #16a34a}
.card-accent-red{border-left:4px solid #dc2626}
.card-accent-amber{border-left:4px solid #d97706}
.card-accent-blue{border-left:4px solid #3b82f6}
.badge{display:inline-block;padding:4px 12px;border-radius:20px;
  font-size:0.76rem;font-weight:700;letter-spacing:0.02em}
.badge-ok{background:#dcfce7;color:#15803d;border:1px solid #86efac}
.badge-bad{background:#fee2e2;color:#dc2626;border:1px solid #fca5a5}
.badge-bias{background:#fef3c7;color:#92400e;border:1px solid #fcd34d}
.badge-ok-soft{background:#f0fdf4;color:#15803d;border:1px solid #86efac}
.clause-tag{display:inline-block;background:#fef2f2;color:#dc2626;
  border:1px solid #fca5a5;border-radius:6px;padding:2px 8px;
  font-size:0.76rem;font-weight:700;margin:2px}
.page-title{font-size:1.6rem;font-weight:800;color:#0f172a;letter-spacing:-0.02em}
.page-subtitle{font-size:0.88rem;color:#64748b;margin-top:3px;margin-bottom:1.4rem}
.sec-head{font-size:0.67rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.1em;
  font-weight:700;border-bottom:1px solid #f1f5f9;padding-bottom:6px;
  margin-bottom:12px;margin-top:4px}
.field{margin-bottom:0.55rem}
.field-label{font-size:0.67rem;color:#94a3b8;text-transform:uppercase;
  letter-spacing:0.08em;font-weight:600}
.field-val{font-size:0.9rem;color:#1e293b;font-weight:500}
.explanation{background:#f8fafc;border:1px solid #e2e8f0;border-left:3px solid #3b82f6;
  border-radius:0 10px 10px 0;padding:0.7rem 1rem;
  font-size:0.85rem;color:#374151;line-height:1.65}
.divider{border:none;border-top:1px solid #f1f5f9;margin:1rem 0}
.dot-green{display:inline-block;width:8px;height:8px;border-radius:50%;
  background:#16a34a;margin-right:6px;vertical-align:middle}
.dot-red{display:inline-block;width:8px;height:8px;border-radius:50%;
  background:#ef4444;margin-right:6px;vertical-align:middle}
.dot-amber{display:inline-block;width:8px;height:8px;border-radius:50%;
  background:#f59e0b;margin-right:6px;vertical-align:middle}
[data-testid="stSelectbox"] label,[data-testid="stTextInput"] label{
  color:#374151 !important;font-size:0.82rem !important;font-weight:600 !important}
[data-testid="stDataFrame"]{border-radius:10px;overflow:hidden;border:1px solid #e2e8f0}
[data-testid="stExpander"]{border:1px solid #e2e8f0 !important;
  border-radius:10px !important;background:#ffffff !important;margin-bottom:6px !important}
[data-testid="stExpander"]:hover{border-color:#cbd5e1 !important;
  box-shadow:0 2px 8px rgba(15,23,42,0.07) !important}
[data-testid="stButton"] button{border-radius:8px !important;
  font-weight:600 !important;transition:all 0.15s !important}
</style>"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)
