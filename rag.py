import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

class RAGHandler:
    def __init__(self, persistence_path="chroma_db"):
        self.client = chromadb.PersistentClient(path=persistence_path)
        
        # Use Local Embeddings (Sentence Transformers) to save OpenAI quota/avoid 429 errors
        # This uses 'all-MiniLM-L6-v2' by default which is free and runs locally.
        try:
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        except Exception as e:
            print(f"Error loading local embeddings: {e}. Fallback to default.")
            self.embedding_fn = None # ChromaDB uses default if None, which is also SentenceTransformer

        self.collection = self.client.get_or_create_collection(
            name="dental_commerce_bot",
            embedding_function=self.embedding_fn
        )

    def reset_collection(self):
        """
        Deletes the entire collection to start fresh.
        """
        try:
            self.client.delete_collection("dental_commerce_bot")
            self.collection = self.client.get_or_create_collection(
                name="dental_commerce_bot",
                embedding_function=self.embedding_fn
            )
            print("Collection reset successfully.")
        except Exception as e:
            print(f"Error resetting collection: {e}")

    def ingest_data(self, file_path, tag):
        """
        Ingest data from a text file into the vector store.
        Each paragraph or block is treated as a document.
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Simple splitting by double newlines for this demo format
        chunks = content.split('\n\n')
        
        ids = [f"{tag}_{i}" for i in range(len(chunks))]
        metadatas = [{"source": tag} for _ in range(len(chunks))]
        
        # Filter empty chunks
        valid_chunks = []
        valid_ids = []
        valid_metadatas = []
        
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                valid_chunks.append(chunk.strip())
                valid_ids.append(ids[i])
                valid_metadatas.append(metadatas[i])

        if valid_chunks:
            self.collection.upsert(
                documents=valid_chunks,
                ids=valid_ids,
                metadatas=valid_metadatas
            )
            print(f"Ingested {len(valid_chunks)} chunks from {file_path}")

    def ingest_text(self, text, metadata):
        """
        Ingest raw text directly.
        metadata: dict, e.g. {"source": "url", "title": "..."}
        """
        import uuid
        if not text.strip():
            return

        # Simple chunking
        # Ideally, we should suggest overlapping, but for now splitting by newlines or paragraphs is safe
        chunks = [c.strip() for c in text.split('\n\n') if c.strip()]
        
        if not chunks:
            return

        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [metadata for _ in chunks]
        
        self.collection.upsert(
            documents=chunks,
            ids=ids,
            metadatas=metadatas
        )
        print(f"Ingested {len(chunks)} chunks from {metadata.get('source', 'unknown')}")

    def query(self, query_text, n_results=3):
        """
        Retrieve relevant context for a query.
        """
        if not self.embedding_fn:
            return []

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        # Flatten results
        return results['documents'][0] if results['documents'] else []

    def initialize_demo_data(self):
        """
        Helper to load the demo data if collection is empty or for refresh.
        """
        base_path = os.path.dirname(os.path.abspath(__file__))
        products_path = os.path.join(base_path, "data", "products.txt")
        faqs_path = os.path.join(base_path, "data", "faqs.txt")
        
        self.ingest_data(products_path, "product")
        self.ingest_data(faqs_path, "faq")
