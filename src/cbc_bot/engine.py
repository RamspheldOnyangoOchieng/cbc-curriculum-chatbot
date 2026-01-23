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
    MASTER AI ENGINE (v6.0): Real-Time Chronological Reasoning.
    Optimized for Kenyan Timezone (EAT) and strict deadline awareness.
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
        clean_text = re.sub(r'[?.!,]', '', text)
        return any(re.search(pattern, clean_text) for pattern in greetings) or len(clean_text.split()) <= 1

    def get_chat_response(self, messages: list) -> str:
        user_query = messages[-1].get("content", "")
        
        # Set Timezone to East Africa Time (Kenyan Local Time)
        eat_tz = timezone(timedelta(hours=3))
        now_eat = datetime.now(eat_tz)
        today = now_eat.strftime("%A, %B %d, %Y")
        current_time = now_eat.strftime("%I:%M %p")
        
        # 1. Handle Simple Greetings
        if self.is_greeting(user_query):
            system_prompt = f"Today is {today}. Time: {current_time} EAT. You are a friendly, real-time CBC Assistant. Respond warmly and briefly."
            context = ""
        else:
            # 2. Perform Deep Search
            context = self.retriever.find_relevant_context(user_query, n_results=12)
            
            # 3. ENHANCED CHRONOLOGICAL PROMPT
            system_prompt = f"""
{KnowledgeBase.get_system_prompt()}

[SYSTEM TIME]: {today} | {current_time} EAT

---
CBC KNOWLEDGE BASE (LATEST DATA):
{context or "NO DATA FRAGMENT FOUND FOR THIS QUERY."}
---

CRITICAL REAL-TIME LOGIC:
1. YOU ARE OPERATING IN REAL-TIME. Compare every fact in the database against '{today}'.
2. DEADLINE DETECTION: If a user asks about an event (like 'Admissions' or 'Placement windows') and the database date has passed, you MUST start your answer by clarifying that the official date is over.
3. ADMISSION STATUS: As of {today}, the official Grade 10 reporting (Jan 12) AND the second review window (Jan 6-9) have EXPIRED. Your advice must reflect this (e.g., focus on late transfers, KEMIS reconciliation, or contacting school principals for remaining slots).
4. NO SPECULATION: Do not say 'Admissions are still on' unless the database explicitly mentions an extension that covers {today}.
5. FACT ALIGNMENT: Join the dots. If the client asks about the 'crisis', use the specific numbers from the database (1.13M placed, 60,000 transfers rejected, etc.) to explain the current reality.
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
                    }, timeout=30)
                else:
                    resp = requests.post(self.GROQ_URL, headers={"Authorization": f"Bearer {p_key}" if (p_key := key) else {}}, json={
                        "model": p["model"], "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temperature": 0.1
                    }, timeout=15)

                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content") or data.get("output") or data.get("message")
            except: continue

        return "Habari. I'm having trouble retrieving the latest CBC data. Please try again or check the official MoE portal."
