import os
import requests
import json
import time
from .config import Config
from .retriever import CBCRetriever
from .knowledge import KnowledgeBase

class CBCEngine:
    """
    MASTER AI ENGINE (v5.0): Lightning Reasoning Edition.
    Prioritizes ultra-fast 'Flash' models that support deep reasoning.
    Priority:
    1. Gemini 2.0 Flash (Lightning Speed + Deep Reasoning)
    2. Claude 3.5 Sonnet (Elite Reasoning - Fallback if Gemini is slow)
    3. Groq Llama 3.3 (Extreme Speed Fallback)
    """
    MODELSLAB_URL = "https://modelslab.com/api/v7/llm/chat/completions"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.modelslab_key = os.getenv("MODELSLAB_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.retriever = CBCRetriever()

    def get_chat_response(self, messages: list) -> str:
        user_query = messages[-1].get("content", "")
        
        # 1. OPTIMIZED DEEP DRILL (Fast Batch Search)
        context = ""
        if user_query:
            try:
                # Still using 10 results for depth, but retrieved via parallel batch
                context = self.retriever.find_relevant_context(user_query, n_results=10)
            except Exception as e:
                print(f"Retrieval Error: {e}")

        # 2. CONCISE REASONING PROMPT (For Speed)
        # We use a focused 'Flash' prompt that triggers reasoning without verbosity.
        system_prompt = f"""
{KnowledgeBase.get_system_prompt()}

---
CBC DATABASE FRAGMENTS:
{context or "NO DIRECT FRAGMENTS FOUND."}
---

INSTRUCTION: 
Reason through the fragments and the user question. Connect related data points instantly. 
Provide a definitive, expert answer. Be concise but logically thorough.
If the database contains the answer, prioritize that over general knowledge.
""".strip()

        # 3. SPEED-FIRST PROVIDER HIERARCHY
        providers = [
            # Gemini 2.0 Flash is the sweet spot: Sub-second response + strong reasoning
            {"name": "Gemini-2.0-Flash", "model": "gemini-2.0-flash-001", "type": "modelslab"},
            {"name": "Claude-3.5-Sonnet", "model": "claude-3.5-sonnet", "type": "modelslab"},
            {"name": "Groq-Llama-70B", "model": "llama-3.3-70b-versatile", "type": "groq"}
        ]

        last_error = ""
        for provider in providers:
            p_key = self.groq_key if provider.get("type") == "groq" else self.modelslab_key
            if not p_key or p_key == "your_modelslab_key_here": continue

            try:
                start_time = time.time()
                if provider.get("type") == "groq":
                    resp = requests.post(self.GROQ_URL, headers={"Authorization": f"Bearer {p_key}"}, json={
                        "model": provider["model"],
                        "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temperature": 0.1,
                    }, timeout=20)
                else:
                    resp = requests.post(self.MODELSLAB_URL, json={
                        "key": p_key,
                        "model_id": provider["model"],
                        "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temp": 0.1,
                        "max_tokens": 1500
                    }, timeout=30)

                if resp.status_code == 200:
                    elapsed = time.time() - start_time
                    print(f"✅ Response from {provider['name']} in {elapsed:.2f}s")
                    data = resp.json()
                    res_content = data.get("choices", [{}])[0].get("message", {}).get("content") or data.get("output") or data.get("message")
                    if res_content: return res_content
                
                print(f"⚠️ {provider['name']} slow/failed ({resp.status_code}). Trying next...")
            except Exception as e:
                print(f"❌ {provider['name']} error: {e}")
                last_error = str(e)

        return f"CBC Engine Timeout. Error: {last_error}"
