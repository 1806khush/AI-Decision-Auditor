# How to Run the AI Decision Auditor

## First-Time Setup (do this once)

```bash
git clone https://github.com/YOUR-USERNAME/ai-decision-auditor.git
cd ai-decision-auditor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create an `env_fe524c` file in the project root with your OpenAI API key:

```
OPENAI_API_KEY=sk-your-key-here
```

---

## Running the Pipeline

Every time you open a new terminal, activate the virtual environment first:

```bash
cd ai-decision-auditor
source venv/bin/activate
```

### Step 1: Build the vector store

```bash
python src/ingest.py
```

This loads the policy document, chunks it, and stores embeddings in ChromaDB.
Only needs to run once, unless you change `data/lending_policy.md`.

### Step 2: Run the auditor

Run one strategy at a time:

```bash
python src/auditor.py --strategy few_shot
python src/auditor.py --strategy rag_cot
```

Or run both at once:

```bash
python src/auditor.py --strategy both
```

This audits all decisions in `data/loan_decisions.csv` and saves results to:
- `eval/outputs_few_shot.csv`
- `eval/outputs_rag_cot.csv`

### Step 3: Evaluate

```bash
python src/evaluate.py
```

This compares auditor outputs against ground truth labels and generates:
- `eval/metrics_comparison.csv` — comparison table
- `eval/strategy_comparison.png` — bar chart
- `eval/confusion_compliance_*.png` — confusion matrices
- `eval/confusion_bias_*.png` — confusion matrices

---

## Starting Fresh

If you need to re-run everything from scratch:

```bash
rm -rf chroma_db eval
python src/ingest.py
python src/auditor.py --strategy both
python src/evaluate.py
```

---

## Troubleshooting

**"No module named ..."**
→ Make sure venv is activated: `source venv/bin/activate`

**"api_key client option must be set"**
→ Make sure `env_fe524c` is in the project root folder

**"model not found"**
→ Your OpenAI project may not have access to that model. Check `auditor.py` uses `gpt-4o-mini` and `ingest.py` uses `text-embedding-3-small`

**Want to change the number of decisions?**
→ Edit `data/generate_decisions.py`, then run `python data/generate_decisions.py` to regenerate the CSV
