import os
import requests
import asyncio
import re
from typing import List, Set, Dict
from dotenv import load_dotenv

load_dotenv()

class CBCRetriever:
    """
    ULTRA-FAST MASTER RETRIEVER: Optimized for 'Word-by-Word' Deep Drill.
    Uses Massive Parallel Retrieval to ensure no relevant data is missed.
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
        self._coll_id = None

    def get_collection_id(self):
        if self._coll_id: return self._coll_id
        try:
            resp = requests.get(f"{self.base_url}/collections", headers=self.headers)
            resp.raise_for_status()
            for coll in resp.json():
                if coll['name'] == "Curriculumnpdfs":
                    self._coll_id = coll['id']
                    return self._coll_id
        except Exception as e:
            print(f"Error fetching collection ID: {e}")
        return None

    def get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Fetch multiple embeddings in a single high-speed batch call."""
        if not self.hf_token or not texts:
            return []
            
        api_url = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5"
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        # Optimization: Prefix for retrieval tasks
        prefixed = [f"Represent this educational term for retrieval: {t}" for t in texts]
        
        try:
            response = requests.post(api_url, headers=headers, json={"inputs": prefixed, "options": {"wait_for_model": True}})
            response.raise_for_status()
            result = response.json()
            # Handle potential single-item return from HF API
            return result if isinstance(result, list) else [result]
        except Exception as e:
            print(f"Batch Embedding error: {e}")
            return []

    def multi_drill_search(self, vectors: List[List[float]], n_results: int = 4) -> List[str]:
        """
        High-Perf Multi-Search: Queries the database for every vector in the batch simultaneously.
        """
        coll_id = self.get_collection_id()
        if not coll_id or not vectors:
            return []
            
        url = f"{self.base_url}/collections/{coll_id}/query"
        try:
            # Chroma V2 supports batch queries natively in some implementations, 
            # but for standard REST we'll pass multiple embeddings in one call.
            resp = requests.post(url, headers=self.headers, json={
                "query_embeddings": vectors,
                "n_results": n_results,
                "include": ["documents"]
            })
            resp.raise_for_status()
            data = resp.json()
            
            # Smart Dedup and Merging
            unique_docs = []
            seen_content = set()
            
            # Doc groups are returned for each embedding in the batch
            for doc_group in data.get("documents", []):
                for doc in doc_group:
                    if not doc: continue
                    # Use a 'fingerprint' of the first 100 chars to dedup similar chunks
                    fingerprint = doc[:100].strip().lower()
                    if fingerprint not in seen_content:
                        unique_docs.append(doc.strip())
                        seen_content.add(fingerprint)
            
            return unique_docs
        except Exception as e:
            print(f"Multi-Drill Search Error: {e}")
            return []

    def find_relevant_context(self, user_query: str, n_results: int = 5) -> str:
        """
        The 'Word-by-Word' Intelligence Loop:
        1. Breaks query into core keywords + full intent.
        2. Batch embeds all variations.
        3. Parallel searches the whole DB.
        """
        # 1. Keyword Extraction (Cleaning noise words)
        words = re.findall(r'\w+', user_query.lower())
        noise = {'the', 'a', 'an', 'and', 'or', 'to', 'for', 'in', 'on', 'at', 'is', 'of', 'how', 'what', 'can', 'you', 'me', 'tell'}
        keywords = [w for w in words if w not in noise and len(w) > 3]
        
        # 2. Build Search Variations (The 'Word Drill' List)
        search_list = [user_query] # Priority 1: Full Intent
        search_list.extend(keywords[:5]) # Priority 2: Key Content Words (limit to top 5 for speed)
        
        # 3. Get Batch Embeddings
        vectors = self.get_batch_embeddings(search_list)
        if not vectors:
            return ""
            
        # 4. Deep Drill Search
        docs = self.multi_drill_search(vectors, n_results=n_results)
        
        if not docs:
            return ""
            
        # Join with clear delimiters
        return "\n\n---\n\n".join(docs)
