ai-decision-auditor/
├── README.md
├── requirements.txt
├── data/
│   ├── lending_policy.md
│   ├── loan_decisions.csv
│   └── generate_decisions.py
├── src/
│   ├── ingest.py          # load policy, chunk it, build ChromaDB
│   ├── auditor.py         # prompts + LLM calls for both strategies
│   └── evaluate.py        # compare outputs vs ground truth, compute metrics
├── prompts/
│   ├── few_shot.txt       # your few-shot prompt template
│   └── rag_cot.txt        # your RAG + chain-of-thought template
├── app.py                 # Streamlit demo
└── results/               # generated after you run evaluation
    ├── comparison_table.csv
    └── confusion_matrix.png
