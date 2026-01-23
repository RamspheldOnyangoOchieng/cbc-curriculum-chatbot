import os
import requests
import re
from typing import List
from dotenv import load_dotenv

load_dotenv()

class CBCRetriever:
    """
    MASTER ALIGNMENT RETRIEVER (v5.5):
    Ensures search vectors perfectly match ingested document vectors.
    """
    def __init__(self):
        self.host = os.getenv('CHROMA_HOST', 'https://api.trychroma.com').rstrip('/')
        self.api_key = os.getenv('CHROMA_API_KEY')
        self.tenant = os.getenv('CHROMA_TENANT')
        self.database = os.getenv('CHROMA_DATABASE')
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        
        self.headers = {
            "x-chroma-token": self.api_key,
            "Content-Type": "application/json"
        }
        self.base_url = f"{self.host}/api/v2/tenants/{self.tenant}/databases/{self.database}"

    def get_collection_id(self):
        try:
            resp = requests.get(f"{self.base_url}/collections", headers=self.headers)
            resp.raise_for_status()
            for coll in resp.json():
                if coll['name'] == "Curriculumnpdfs":
                    return coll['id']
        except: return None

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Aligned Embedding: No instruction prefix is used here to match 
        the standard ingestion format of the BGE model.
        """
        api_url = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5"
        try:
            response = requests.post(
                api_url, 
                headers={"Authorization": f"Bearer {self.hf_token}"}, 
                json={"inputs": texts, "options": {"wait_for_model": True}}
            )
            return response.json()
        except: return []

    def find_relevant_context(self, user_query: str, n_results: int = 12) -> str:
        """
        Multi-Drill Search with deduping.
        """
        # Expand query for better placement/crisis detection
        search_terms = [user_query]
        words = re.findall(r'\w+', user_query.lower())
        important = [w for w in words if len(w) > 4]
        search_terms.extend(important[:3])

        vectors = self.get_embeddings(search_terms)
        coll_id = self.get_collection_id()
        if not coll_id or not vectors: return ""

        try:
            resp = requests.post(f"{self.base_url}/collections/{coll_id}/query", headers=self.headers, json={
                "query_embeddings": vectors,
                "n_results": n_results,
                "include": ["documents", "metadatas"]
            })
            data = resp.json()
            
            unique_docs = []
            seen = set()
            for group in data.get("documents", []):
                for doc in group:
                    if not doc: continue
                    fingerprint = doc[:50].lower()
                    if fingerprint not in seen:
                        unique_docs.append(doc)
                        seen.add(fingerprint)
            
            return "\n\n---\n\n".join(unique_docs)
        except: return ""
