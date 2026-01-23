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
    MASTER AI ENGINE (v7.5): Balanced Evidence Edition.
    Evaluates "Claims" by weighing official guidelines against database evidence.
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
            return "Habari! I am your CBC Assistant. How can I help you today?"

        # 2. Perform Evidence-Based Search
        # We increase retrieval for "Claims" or "Purpose" questions to get both sides
        search_count = 15
        if any(word in user_query.lower() for word in ["claim", "purpose", "work", "achieving", "crisis"]):
            search_count = 20
        
        context = self.retriever.find_relevant_context(user_query, history_context=last_bot_message, n_results=search_count)
        
        # 3. EVIDENCE-BASED SYSTEM PROMPT
        system_prompt = f"""
{KnowledgeBase.get_system_prompt()}
TODAY: {today}

---
DATABASE EVIDENCE:
{context or "NO DATA FOUND."}
---

CLAIMS EVALUATION PROTOCOL:
- If asked "Does it do what it claims?", reason within the context of the CBC system's goals vs. the data in the database.
- GOALS: Emphasize the shift from exams to skills and the placement of 1.13 million learners.
- REALITY: Contrast this with the "placement crisis" and "design flaws" mentioned in the database (e.g., 60,000 rejected transfers, "black-box" decision making).
- STRUCTURE: 
  1. Brief summary of the system's claim/purpose.
  2. Bullet points of evidence (numbers/facts) showing what is working.
  3. Bullet points of evidence showing the "crisis" or areas failing to meet claims.
  4. Final synthesis: A clear, organized, and brief conclusion.
- LIMIT: Max 200 words. No AI-talk.
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
                        "temp": 0.1
                    }, timeout=25)
                else:
                    resp = requests.post(self.GROQ_URL, headers={"Authorization": f"Bearer {key}"}, json={
                        "model": p["model"], "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temperature": 0.1
                    }, timeout=15)

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content") or data.get("output") or data.get("message")
            except: continue

        return "Connection busy. Please refresh the page."
