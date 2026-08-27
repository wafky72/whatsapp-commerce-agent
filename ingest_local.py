from rag import RAGHandler
import os

def main():
    print("Initializing RAG Handler...")
    rag = RAGHandler()
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    faqs_path = os.path.join(base_path, "data", "faqs.txt")
    products_path = os.path.join(base_path, "data", "products.txt")
    
    print(f"Ingesting FAQs from {faqs_path}...")
    rag.ingest_data(faqs_path, "faq")
    
    print(f"Ingesting Products from {products_path}...")
    rag.ingest_data(products_path, "product")
    
    print("Done!")

if __name__ == "__main__":
    main()
