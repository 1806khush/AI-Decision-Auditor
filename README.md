# AI Decision Auditor

LLM-powered compliance and bias detection for organizational lending decisions.  
**FE524 – Prompt Engineering Lab | Stevens Institute of Technology | Spring 2026**  
Aania Adap, Khush Mehta

---

## Project Structure

```
ai-decision-auditor/
├── README.md
├── requirements.txt
├── data/
│   ├── lending_policy.md          # synthetic policy document (6 sections)
│   ├── loan_decisions.csv         # 49 labeled decision records
│   └── generate_decisions.py      # script to regenerate the CSV
├── src/
│   ├── ingest.py                  # load policy, chunk it, build ChromaDB
│   ├── auditor.py                 # prompts + LLM calls for both strategies
│   └── evaluate.py                # compare outputs vs ground truth, compute metrics
├── prompts/
│   ├── few_shot.txt               # few-shot prompt template
│   └── rag_cot.txt                # RAG + chain-of-thought prompt template
├── app.py                         # Streamlit demo
└── results/                       # generated after running evaluation
    ├── comparison_table.csv
    └── confusion_matrix.png
```

## Setup

```bash
git clone https://github.com/1806khush/ai-decision-auditor.git
cd ai-decision-auditor
pip install -r requirements.txt
```

## Usage

**Build the vector store:**
```bash
python src/ingest.py
```

**Run the auditor on all decisions:**
```bash
python src/auditor.py
```

**Evaluate against ground truth:**
```bash
python src/evaluate.py
```

**Launch the Streamlit demo:**
```bash
streamlit run app.py
```

## Prompt Engineering Strategies

| Strategy | Description |
|---|---|
| **Few-shot** | Full policy context + 3–5 worked examples of compliant/non-compliant decisions |
| **RAG + CoT** | Top-k relevant policy chunks via ChromaDB + step-by-step reasoning instructions |

## Tech Stack

- Python 3.10+
- OpenAI GPT-4o / GPT-4o-mini
- LangChain + ChromaDB + OpenAI Embeddings
- scikit-learn, pandas, matplotlib
- Streamlit
