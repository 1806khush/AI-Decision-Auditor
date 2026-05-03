# ingest.py - loads the policy doc into ChromaDB for retrieval
# run this once before using auditor.py

import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, "env_fe524c"), override=True)

POLICY_PATH = os.path.join(ROOT_DIR, "data", "lending_policy.md")
CHROMA_DIR = os.path.join(ROOT_DIR, "chroma_db")

def main():
    loader = TextLoader(POLICY_PATH, encoding="utf-8")
    docs = loader.load()

    # 500 chunk size works well bc policy sections are short
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(docs)
    print(f"Split policy into {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        chunks, embeddings,
        collection_name="lending_policy",
        persist_directory=CHROMA_DIR,
    )
    print(f"Saved to {CHROMA_DIR}/")

    # sanity check - make sure retrieval pulls the right sections
    for q in ["minimum credit score?", "docs for loans above $50k?", "prohibited factors?"]:
        results = vectorstore.similarity_search(q, k=3)
        print(f"\nQuery: '{q}'")
        for i, doc in enumerate(results):
            print(f"  [{i+1}] {doc.page_content[:120].replace(chr(10), ' ')}...")

    print("\nDone!")

if __name__ == "__main__":
    main()
