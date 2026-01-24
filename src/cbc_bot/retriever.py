import os
import requests
import re
from typing import List
from dotenv import load_dotenv

load_dotenv()

class CBCRetriever:
    """
    MASTER ENTITY RETRIEVER (v6.5):
    Specifically optimized for vague queries like "what are these" or "tell me more."
    Automatically extracts technical CBC terms from the conversation history.
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
        api_url = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5"
        try:
            response = requests.post(
                api_url, 
                headers={"Authorization": f"Bearer {self.hf_token}"}, 
                json={"inputs": texts, "options": {"wait_for_model": True}}
            )
            return response.json()
        except: return []

    def find_relevant_context(self, user_query: str, history_context: str = "", n_results: int = 15) -> str:
        """
        Deep Drill with History Awareness.
        """
        # Combine query with previous assistant entities if query is short
        search_query = user_query
        if len(user_query.split()) < 4 and history_context:
            # Extract key CBC terms from previous message (dates, technical terms)
            entities = re.findall(r'(\d+ [A-Z][a-z]+|\d{4}|[A-Z][a-z]+ [A-Z][a-z]+ pathways|placement|reporting|transfer|review window|Senior School)', history_context)
            search_query = f"{user_query} {' '.join(entities[:5])}"

        search_terms = [search_query, user_query]
        # Drill for the specific components
        query_l = search_query.lower()
        if "reporting" in query_l or "these" in query_l:
            search_terms.extend(["Grade 10 reporting date January 12", "placement review window January 6-9"])
        
        if "grade" in query_l or "marks" in query_l or "score" in query_l:
            search_terms.extend(["60/20/20 rule KJSEA KPSEA SBA", "Achievement Levels EE1 EE2 ME1 ME2"])
            
        if "engineer" in query_l or "medicine" in query_l or "stem" in query_l:
            search_terms.extend(["STEM Pure Sciences mandatory subjects", "Orange Book Addendum June 2025 engineering"])
        
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
