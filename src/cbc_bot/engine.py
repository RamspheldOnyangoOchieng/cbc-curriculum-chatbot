import os
import requests
import time
import re
from .config import Config
from .retriever import CBCRetriever
from .knowledge import KnowledgeBase

class CBCEngine:
    """
    MASTER AI ENGINE (v5.7): Social Intelligence Edition.
    Handles greetings naturally while remaining strict on factual data.
    """
    MODELSLAB_URL = "https://modelslab.com/api/v7/llm/chat/completions"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.modelslab_key = os.getenv("MODELSLAB_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.retriever = CBCRetriever()

    def is_greeting(self, text: str) -> bool:
        """Detects if the message is just a greeting/small talk."""
        greetings = {r'\bhi\b', r'\bhello\b', r'\bhey\b', r'\bhabari\b', r'\bjambo\b', r'\bsasa\b'}
        text = text.lower().strip()
        # Remove punctuation for check
        clean_text = re.sub(r'[?.!,]', '', text)
        return any(re.search(pattern, clean_text) for pattern in greetings) or len(clean_text.split()) <= 2

    def get_chat_response(self, messages: list) -> str:
        user_query = messages[-1].get("content", "")
        
        # 1. Handle Simple Greetings Instantly
        if self.is_greeting(user_query):
            system_prompt = "You are a friendly CBC Assistant. The user just said hello. Respond warmly, briefly (max 1 sentence), and stay in character. Do not list categories."
            context = ""
        else:
            # 2. Perform Deep Search for actual questions
            context = self.retriever.find_relevant_context(user_query, n_results=12)
            system_prompt = f"""
{KnowledgeBase.get_system_prompt()}

---
DATABASE KNOWLEDGE:
{context or "DATABASE IS EMPTY FOR THIS TOPIC."}
---

STRICT RULES:
1. USE THE DATABASE ABOVE FOR ALL FACTS. 
2. BE CONCISE. If the answer is 2 sentences, don't write 5.
3. If numbers or crisis details are missing, admit it. 
4. Always mention your source (e.g., 'Per the Kenya Times piece...').
""".strip()

        # 3. SPEED-FIRST PROVIDER HIERARCHY
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
                        "temp": 0.2
                    }, timeout=30)
                else:
                    resp = requests.post(self.GROQ_URL, headers={"Authorization": f"Bearer {key}"}, json={
                        "model": p["model"], "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temperature": 0.2
                    }, timeout=15)

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content") or data.get("output") or data.get("message")
            except: continue

        return "Habari! I'm having a slight connection issue. How can I help you with CBC?"
