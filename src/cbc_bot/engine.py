import os
import requests
import json
from .config import Config
from .retriever import CBCRetriever
from .knowledge import KnowledgeBase

class CBCEngine:
    """
    MASTER AI ENGINE (v3.0): Orchestrates the 'Word-by-Word' Deep Drill search.
    Designed for precision, speed, and comprehensive content retrieval.
    """
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.retriever = CBCRetriever()

    def get_chat_response(self, messages: list) -> str:
        """
        Executes the Deep Drill retrieval and synthesizes the final response.
        """
        # 1. Get the latest user query
        user_query = messages[-1].get("content", "")
        
        # 2. PERFORM DEEP DRILL
        # This will now automatically handle keyword extraction and parallel search
        context = ""
        if user_query:
            try:
                # We fetch a larger breadth of fragments (n_results=10) 
                # because our Word-by-Word algorithm is now much faster.
                context = self.retriever.find_relevant_context(user_query, n_results=10)
            except Exception as e:
                print(f"Deep Drill Error: {e}")

        # 3. MASTER PROMPT SYNTHESIS
        # We tell the model exactly what it's looking at to improve reasoning.
        system_prompt = f"""
{KnowledgeBase.get_system_prompt()}

---
DATABASE DRILL RESULTS (DEEP SEARCH):
The following fragments have been retrieved from the CBC Knowledge Base using a Word-by-Word Deep Drill algorithm. 
Identify related facts across different fragments and synthesize them into a coherent, expert response.

RETRIEVED DATA:
{context or "NO DIRECT FRAGMENTS FOUND. Answer using general CBC expert knowledge."}
---
""".strip()
        
        # 4. EXECUTE SYNTHESIS (Llama 3.3 70B)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "temperature": 0.2, # Lower temperature = higher factual reliability
            "max_tokens": 1500,
            "top_p": 0.9
        }
        
        try:
            resp = requests.post(self.GROQ_URL, headers=headers, json=payload, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Groq Synthesis Error: {e}")
            return "I apologize, but I encountered a network error while synthesizing the multi-drill results. Please try again."
