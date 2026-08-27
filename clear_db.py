from rag import RAGHandler
import os

def main():
    print("Initializing RAG Handler...")
    rag = RAGHandler()
    
    print("Resetting Collection (Wiping old data)...")
    rag.reset_collection()
    
    # We will purposely NOT re-ingest the dummy products.txt file.
    # We will rely on the Crawler for fresh data or the User might run crawler.py next.
    
    print("Reset Complete. Database is clean.")

if __name__ == "__main__":
    main()
