import os
import requests
import time
from .config import Config
from .retriever import CBCRetriever
from .knowledge import KnowledgeBase

class CBCEngine:
    """
    MASTER ENGINE (v5.6): STRICT KNOWLEDGE MODE.
    Forced to use provided fragments or admit lack of data.
    """
    MODELSLAB_URL = "https://modelslab.com/api/v7/llm/chat/completions"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.modelslab_key = os.getenv("MODELSLAB_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.retriever = CBCRetriever()

    def get_chat_response(self, messages: list) -> str:
        user_query = messages[-1].get("content", "")
        context = self.retriever.find_relevant_context(user_query, n_results=12)

        # STRICT SYSTEM PROMPT
        system_prompt = f"""
{KnowledgeBase.get_system_prompt()}

---
DATABASE KNOWLEDGE (THE ONLY TRUTH):
{context or "DATABASE IS EMPTY FOR THIS TOPIC."}
---

STRICT RULES:
1. YOU ARE A ROBOT THAT ONLY SPEAKS USING THE 'DATABASE KNOWLEDGE' ABOVE.
2. DO NOT USE YOUR OWN GENERAL KNOWLEDGE TO INVENT NATIONAL STATISTICS.
3. IF THE DATABASE DOES NOT MENTION THE NUMBERS ASKED (E.G. THE MATH OF PLACEMENT), SAY: "My current database fragments do not contain the specific figures for this. I only have data on [X, Y, Z from context]."
4. IF YOU SEE A 'CRISIS' OR 'DESIGN FLAW' MENTIONED IN THE DATABASE, EXPLORE IT DEEPLY.
5. ALWAYS CITE YOUR SOURCES (e.g. "According to the Kenya Times opinion piece...")
""".strip()

        # SPEED-FIRST FALLBACK
        providers = [
            {"name": "Gemini-2.0-Flash", "model": "gemini-2.0-flash-001", "type": "modelslab"},
            {"name": "Claude-3.5-Sonnet", "model": "claude-3.5-sonnet", "type": "modelslab"},
            {"name": "Groq-Llama-70B", "model": "llama-3.3-70b-versatile", "type": "groq"}
        ]

        for p in providers:
            key = self.groq_key if p["type"] == "groq" else self.modelslab_key
            if not key or key == "your_modelslab_key_here": continue
            
            try:
                if p["type"] == "modelslab":
                    resp = requests.post(self.MODELSLAB_URL, json={
                        "key": key, "model_id": p["model"], 
                        "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temp": 0.05 # Near-zero for total factual accuracy
                    }, timeout=35)
                else:
                    resp = requests.post(self.GROQ_URL, headers={"Authorization": f"Bearer {key}"}, json={
                        "model": p["model"], "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temperature": 0.05
                    }, timeout=20)

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content") or data.get("output") or data.get("message")
            except: continue

        return "Connection Error with CBC Intelligence Engines."
