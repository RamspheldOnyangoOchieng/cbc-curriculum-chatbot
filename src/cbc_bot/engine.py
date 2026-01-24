import os
import requests
import time
import re
from datetime import datetime, timedelta, timezone
from .config import Config
from .retriever import CBCRetriever
from .knowledge import KnowledgeBase

class CBCEngine:
    """
    MASTER AI ENGINE (v8.0): Brutal Precision Edition.
    Forces the AI to use specific numbers, labels, and learning areas.
    """
    MODELSLAB_URL = "https://modelslab.com/api/v7/llm/chat/completions"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.modelslab_key = os.getenv("MODELSLAB_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.retriever = CBCRetriever()

    def is_greeting(self, text: str) -> bool:
        greetings = {r'\bhi\b', r'\bhello\b', r'\bhey\b', r'\bhabari\b', r'\bjambo\b', r'\bsasa\b'}
        text = text.lower().strip()
        clean_text = re.sub(r'[?.!,]', '', text)
        return any(re.search(pattern, clean_text) for pattern in greetings) or len(clean_text.split()) <= 1

    def get_chat_response(self, messages: list) -> str:
        user_query = messages[-1].get("content", "")
        
        eat_tz = timezone(timedelta(hours=3))
        now_eat = datetime.now(eat_tz)
        today = now_eat.strftime("%B %d, %Y")
        
        last_bot_message = ""
        if len(messages) > 1:
            last_bot_message = messages[-2].get("content", "")

        # 1. Handle Simple Greetings
        if self.is_greeting(user_query):
            return "Habari! I am your Master CBC Consultant. Tell me specifically what you need to know about Grade 10 pathways or placement."

        # 2. Perform Data-Dense Deep Search
        # Increase n_results to 20 to find all specific subject lists
        context = self.retriever.find_relevant_context(user_query, history_context=last_bot_message, n_results=20)
        
        # 3. DATA-DENSE SYSTEM PROMPT
        system_prompt = f"""
{KnowledgeBase.get_system_prompt()}
[SYSTEM TIME]: {today} EAT

---
SPECIFIC DATABASE EVIDENCE:
{context or "NO DIRECT FRAGMENTS FOUND. USE HARD FACTS FROM SYSTEM PROMPT."}
---

PRECISION PROTOCOL:
1. NO VAGUENESS: Do not say 'it varies'. Say 'According to the 60/20/20 rule...' or 'In the STEM Pure Sciences pathway, students must take Physics, Chemistry...'
2. GRADE DATA: If asked about grades, use the EE1 (90-100%) system explicitly.
3. SUBJECT DATA: Use the 'Orange Book' evidence above to list mandatory subjects for specific careers.
4. SYNTHESIS: Join the dots between the user's career interest (e.g. Engineering) and the specific subjects found in the database.
5. SOURCE CITATION: Refer to 'The Orange Book Addendum (June 2025)' or 'EduPoa Reports' if found in context.
6. BREVITY: Be extremely brief but carry a high 'Data Density'.
""".strip()

        # 4. PROVIDER HIERARCHY
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
                        "temp": 0.0 # ZERO temp for absolute factual strictness
                    }, timeout=30)
                else:
                    resp = requests.post(self.GROQ_URL, headers={"Authorization": f"Bearer {key}"}, json={
                        "model": p["model"], "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temperature": 0.0
                    }, timeout=20)

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content") or data.get("output") or data.get("message")
            except: continue

        return "Consultant Connection Error. Please refresh the CBC Dashboard."
