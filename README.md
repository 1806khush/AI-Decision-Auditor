AI Decision Auditor

LLM-powered compliance & bias auditor for consumer lending decisions — compares Few-Shot vs RAG+CoT prompting strategies with precision/recall evaluation, ChromaDB retrieval, and an interactive Streamlit dashboard.

FE524 – Prompt Engineering Lab · Stevens Institute of Technology · Spring 2026
Aania Adap · Khush Mehta

Overview
Financial institutions process thousands of loan decisions every day, each carrying compliance and fairness obligations under laws like the Equal Credit Opportunity Act (ECOA). Manual review is slow, inconsistent, and doesn't scale.
AI Decision Auditor automates this process using an LLM. Given a loan officer's decision and written rationale, it:

Returns a compliance verdict (Compliant / Non-Compliant)
Assigns a 0–100 compliance score
Identifies the specific policy clauses violated
Flags any bias language in the rationale (references to age, gender, race, etc.)

Two distinct prompting strategies are implemented and benchmarked head-to-head.

Results
MetricFew-ShotRAG + CoTCompliance Precision0.9380.733Compliance Recall0.8330.611Compliance F10.8820.667Bias Precision0.9620.897Bias Recall0.9621.000Bias F10.9620.945Clause F10.4910.130Avg Tokens / Decision2,150962
Key finding: Few-Shot wins on accuracy (88.2% compliance F1). RAG + CoT uses 55% fewer tokens — making it far more cost-efficient at scale, with competitive bias detection (94.5% F1).

Project Structure
ai-decision-auditor/
├── app.py                        # Streamlit landing page
├── pages/
│   ├── 1_Audit.py                # Per-decision audit inspector
│   ├── 2_Dashboard.py            # Metrics, charts, confusion matrices
│   └── 3_Explorer.py             # Filterable table of all 35 decisions
├── utils/
│   └── helpers.py                # Shared loaders, formatters, CSS
├── src/
│   ├── ingest.py                 # Chunk policy → embed → store in ChromaDB
│   ├── auditor.py                # Run both strategies on all decisions
│   └── evaluate.py               # Compute metrics, generate plots
├── Data/
│   ├── lending_policy.md         # Synthetic fair-lending policy (6 sections)
│   ├── loan_decisions.csv        # 35 labeled decisions (31 features each)
│   └── generate_decisions.py     # Script to regenerate the dataset
├── eval/
│   ├── outputs_few_shot.csv      # LLM audit results — Few-Shot strategy
│   ├── outputs_rag_cot.csv       # LLM audit results — RAG + CoT strategy
│   ├── metrics_comparison.csv    # Precision / Recall / F1 for both strategies
│   ├── strategy_comparison.png   # F1 bar chart
│   └── confusion_*.png           # Confusion matrices (compliance + bias)
├── requirements.txt
└── .env.example

Prompting Strategies
Few-Shot
The full 6-section lending policy is embedded in the system prompt alongside 3 worked examples (compliant and non-compliant decisions with full explanations). The model audits each decision in a single self-contained call.

~2,150 tokens per decision
Higher accuracy from richer context
Best for high-stakes, low-volume auditing

RAG + Chain-of-Thought
At inference time, the top-5 most semantically relevant policy clauses are retrieved from a ChromaDB vector store using the decision text as a query. A chain-of-thought instruction guides the model to reason step-by-step before returning a verdict.

~960 tokens per decision (55% fewer)
Scales cost-efficiently to large volumes
Best for high-throughput screening


Setup
1. Clone the repo
bashgit clone https://github.com/1806khush/AI-Decision-Auditor.git
cd AI-Decision-Auditor
2. Create a virtual environment
bashpython -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
3. Install dependencies
bashpip install -r requirements.txt
4. Add your OpenAI API key
bashcp .env.example .env
# Edit .env and set: OPENAI_API_KEY=sk-...

Usage
Run these steps in order from the project/ directory.
Step 1 — Build the vector store
bashpython src/ingest.py
Chunks Data/lending_policy.md, generates embeddings via OpenAI Ada-002, and persists a ChromaDB collection to disk.
Step 2 — Run the auditor
bashpython auditor.py
Runs both Few-Shot and RAG+CoT strategies on all 35 decisions. Writes results to eval/outputs_few_shot.csv and eval/outputs_rag_cot.csv.
Step 3 — Evaluate
bashpython evaluate.py
Computes precision, recall, and F1 for compliance detection, bias detection, and clause identification. Generates confusion matrices and a comparison chart in eval/.
Step 4 — Launch the app
bashstreamlit run app.py
Opens the interactive Streamlit dashboard at http://localhost:8501.

App Pages
PageDescriptionAuditSelect any of the 35 decisions. Side-by-side Few-Shot vs RAG+CoT results with score bars, clause tags, bias flags, and agreement indicator.DashboardAll 9 evaluation metrics, F1 comparison chart, confusion matrices, and token cost breakdown.ExplorerBrowse and filter all 35 decisions by compliance status, bias presence, decision type, and loan type.

Tech Stack
LayerToolsLLMOpenAI GPT-4oEmbeddingsOpenAI text-embedding-ada-002Vector StoreChromaDBOrchestrationLangChainEvaluationscikit-learn, pandasVisualizationmatplotlibFrontendStreamlitLanguagePython 3.10+

Dataset
35 synthetic loan decision records, each with 31 features including:

Applicant profile: age, gender, race, credit score, income, DTI ratio
Loan details: amount, type (secured/unsecured), collateral, co-signer, term, rate offered
Officer output: decision (Approved/Denied), written rationale
Ground truth labels: compliance verdict, violated clauses, bias present, bias description

Approximately 51% of decisions contain policy violations or bias flags, reflecting realistic audit conditions.
