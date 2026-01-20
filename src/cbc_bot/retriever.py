import os
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

class CBCRetriever:
    def __init__(self):
        # Initialize LOCAL Chroma Client
        db_path = "./chroma_db"
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection_name = "Curriculumnpdfs"
        self.collection = self.client.get_collection(name=self.collection_name)
        
        # Initialize Embedding Model (Must match ingestion)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def find_relevant_context(self, query, n_results=3):
        """Finds the most relevant snippets from the CBC knowledge base."""
        query_embedding = self.model.encode([query]).tolist()
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        
        # Combine documents into a single context string
        context = "\n\n".join(results["documents"][0])
        return context
