import os
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, ConfusionMatrixDisplay

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_DIR = os.path.join(ROOT_DIR, "eval")
GT_PATH = os.path.join(ROOT_DIR, "data", "loan_decisions.csv")


def to_binary(series):
    # "No" = non-compliant or biased = 1 (the thing we're trying to catch)
    return (series == "No").astype(int)


def get_metrics(y_true, y_pred, name):
    yt = to_binary(y_true)
    yp = to_binary(y_pred)
    p = precision_score(yt, yp, zero_division=0)
    r = recall_score(yt, yp, zero_division=0)
    f1 = f1_score(yt, yp, zero_division=0)
    print(f"  {name}: P={p:.3f} R={r:.3f} F1={f1:.3f}")
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}


def clause_metrics(gt_clauses, pred_clauses):
    # check how well it identifies the specific violated sections
    true_total, pred_total, correct = 0, 0, 0
    for gt, pred in zip(gt_clauses, pred_clauses):
        true_set = set(c.strip() for c in str(gt).split(",") if c.strip())
        pred_set = set(c.strip() for c in str(pred).split(",") if c.strip())
        true_total += len(true_set)
        pred_total += len(pred_set)
        correct += len(true_set & pred_set)

    p = correct / pred_total if pred_total else 0
    r = correct / true_total if true_total else 0
    f1 = 2*p*r / (p+r) if (p+r) else 0
    print(f"  Clause-level: P={p:.3f} R={r:.3f} F1={f1:.3f}")
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}


def save_confusion(y_true, y_pred, title, filename):
    yt = to_binary(y_true)
    yp = to_binary(y_pred)
    cm = confusion_matrix(yt, yp)
    fig, ax = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay(cm, display_labels=["Compliant", "Non-Compliant"]).plot(ax=ax, cmap="Blues")
    ax.set_title(title)
    plt.tight_layout()
    path = os.path.join(EVAL_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved {filename}")


def evaluate(name, pred_path, gt):
    print(f"\n--- {name.upper()} ---")
    pred = pd.read_csv(pred_path)
    pred["compliant"] = pred["compliant"].str.strip()
    pred["bias_present"] = pred["bias_present"].str.strip()
    pred["violated_clauses"] = pred["violated_clauses"].fillna("")
    pred["tokens_used"] = pd.to_numeric(pred["tokens_used"], errors="coerce").fillna(0)

    merged = gt.merge(pred, on="decision_id", suffixes=("_true", "_pred"))

    comp = get_metrics(merged["compliant_true"], merged["compliant_pred"], "Compliance")
    bias = get_metrics(merged["bias_present_true"], merged["bias_present_pred"], "Bias")
    clauses = clause_metrics(merged["violated_clauses_true"], merged["violated_clauses_pred"])

    avg_tok = merged["tokens_used"].mean()
    total_tok = merged["tokens_used"].sum()
    print(f"  Tokens: {avg_tok:.0f} avg, {total_tok:,.0f} total")

    save_confusion(merged["compliant_true"], merged["compliant_pred"],
                   f"{name} - Compliance", f"confusion_compliance_{name}.png")
    save_confusion(merged["bias_present_true"], merged["bias_present_pred"],
                   f"{name} - Bias", f"confusion_bias_{name}.png")

    return {
        "strategy": name,
        "compliance_p": comp["precision"], "compliance_r": comp["recall"], "compliance_f1": comp["f1"],
        "bias_p": bias["precision"], "bias_r": bias["recall"], "bias_f1": bias["f1"],
        "clause_p": clauses["precision"], "clause_r": clauses["recall"], "clause_f1": clauses["f1"],
        "avg_tokens": round(avg_tok), "total_tokens": int(total_tok),
    }


def comparison_chart(results):
    metrics = ["compliance_f1", "bias_f1", "clause_f1"]
    labels = ["Compliance F1", "Bias F1", "Clause F1"]
    fs = [results[0][m] for m in metrics]
    rc = [results[1][m] for m in metrics]

    x = range(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([i - w/2 for i in x], fs, w, label="Few-Shot", color="#4C78A8")
    ax.bar([i + w/2 for i in x], rc, w, label="RAG + CoT", color="#E45756")
    ax.set_ylabel("F1 Score")
    ax.set_title("Strategy Comparison")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.legend()

    for i, (f, r) in enumerate(zip(fs, rc)):
        ax.text(i - w/2, f + 0.02, f"{f:.2f}", ha="center", fontsize=10)
        ax.text(i + w/2, r + 0.02, f"{r:.2f}", ha="center", fontsize=10)

    plt.tight_layout()
    path = os.path.join(EVAL_DIR, "strategy_comparison.png")
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"\nSaved comparison chart to {path}")


def main():
    gt = pd.read_csv(GT_PATH)
    gt = gt[["decision_id", "compliant", "violated_clauses", "bias_present"]].copy()
    gt["compliant"] = gt["compliant"].str.strip()
    gt["bias_present"] = gt["bias_present"].str.strip()
    gt["violated_clauses"] = gt["violated_clauses"].fillna("")
    print(f"Ground truth: {len(gt)} records")

    results = []

    fs_path = os.path.join(EVAL_DIR, "outputs_few_shot.csv")
    rc_path = os.path.join(EVAL_DIR, "outputs_rag_cot.csv")

    if os.path.exists(fs_path):
        results.append(evaluate("few_shot", fs_path, gt))
    if os.path.exists(rc_path):
        results.append(evaluate("rag_cot", rc_path, gt))

    if not results:
        print("No output files found - run auditor.py first")
        return

    # save comparison table
    comp = pd.DataFrame(results)
    comp_path = os.path.join(EVAL_DIR, "metrics_comparison.csv")
    comp.to_csv(comp_path, index=False)
    print(f"\n{'='*50}")
    print(comp.to_string(index=False))
    print(f"\nSaved to {comp_path}")

    if len(results) == 2:
        comparison_chart(results)


if __name__ == "__main__":
    main()
