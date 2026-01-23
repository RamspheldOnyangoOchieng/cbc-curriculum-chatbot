import os
import requests
import json
import time
from .config import Config
from .retriever import CBCRetriever
from .knowledge import KnowledgeBase

class CBCEngine:
    """
    MASTER AI ENGINE (v4.0): Multi-Provider Robust Synthesis.
    Implements a hierarchy of providers for 100% uptime and logic depth.
    Priority: 
    1. ModelsLab (Gemini 2.0 Flash)
    2. ModelsLab (Claude 3.5 Sonnet)
    3. ModelsLab (Gemini 2.5 Pro)
    4. Groq (Llama 3.3 70B)
    """
    MODELSLAB_URL = "https://modelslab.com/api/v7/llm/chat/completions"
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        self.modelslab_key = os.getenv("MODELSLAB_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.retriever = CBCRetriever()

    def get_chat_response(self, messages: list) -> str:
        # 1. Get the latest user query
        user_query = messages[-1].get("content", "")
        
        # 2. PERFORM DEEP DRILL SEARCH
        context = ""
        if user_query:
            try:
                context = self.retriever.find_relevant_context(user_query, n_results=10)
            except Exception as e:
                print(f"Deep Drill Error: {e}")

        # 3. CONSTRUCT SYSTEM PROMPT
        system_prompt = f"""
{KnowledgeBase.get_system_prompt()}

---
CBC KNOWLEDGE BASE FRAGMENTS (VERIFIED DATA):
{context or "NO DIRECT FRAGMENTS FOUND. Use established CBC transition guidelines."}
---

INSTRUCTIONS:
- You are a CBC Master Consultant.
- Use the fragments above to provide specific, data-driven answers.
- If data is missing, admit it politely but provide the best general advice based on KICD standards.
""".strip()

        # 4. FALLBACK LOGIC
        # We try providers in sequence until one succeeds
        providers = [
            {"name": "ModelsLab-Gemini-2.0", "url": self.MODELSLAB_URL, "key": self.modelslab_key, "model": "gemini-2.0-flash-001", "type": "modelslab"},
            {"name": "ModelsLab-Claude-3.5", "url": self.MODELSLAB_URL, "key": self.modelslab_key, "model": "claude-3.5-sonnet", "type": "modelslab"},
            {"name": "ModelsLab-Gemini-2.5-Pro", "url": self.MODELSLAB_URL, "key": self.modelslab_key, "model": "gemini-2.5-pro", "type": "modelslab"},
            {"name": "Groq-Llama-70B", "url": self.GROQ_URL, "key": self.groq_key, "model": "llama-3.3-70b-versatile", "type": "groq"}
        ]

        last_error = ""

        for provider in providers:
            if not provider["key"] or provider["key"] == "your_modelslab_key_here":
                print(f"Skipping {provider['name']}: API Key missing.")
                continue

            print(f"Attempting synthesis with {provider['name']}...")
            
            try:
                if provider["type"] == "modelslab":
                    payload = {
                        "key": provider["key"],
                        "model_id": provider["model"],
                        "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temp": 0.2, # ModelsLab parameter for temperature
                        "max_tokens": 1500
                    }
                    resp = requests.post(provider["url"], json=payload, timeout=40)
                else:
                    # Groq OpenAI-compatible format
                    headers = {
                        "Authorization": f"Bearer {provider['key']}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": provider["model"],
                        "messages": [{"role": "system", "content": system_prompt}] + messages,
                        "temperature": 0.2,
                        "max_tokens": 1500
                    }
                    resp = requests.post(provider["url"], headers=headers, json=payload, timeout=30)

                if resp.status_code == 200:
                    data = resp.json()
                    # Unified parsing: ModelsLab usually mirrors OpenAI or has a 'choices' array
                    # Note: ModelsLab v7 structure might be slightly different, we check both
                    if "choices" in data:
                        return data["choices"][0]["message"]["content"]
                    elif "output" in data:
                        return data["output"]
                    elif "message" in data:
                        return data["message"]
                    else:
                        print(f"Unknown response format from {provider['name']}: {data}")
                        continue
                else:
                    last_error = f"{provider['name']} Error {resp.status_code}: {resp.text}"
                    print(last_error)

            except Exception as e:
                print(f"Error calling {provider['name']}: {e}")
                last_error = str(e)

        return f"All AI providers are currently unavailable. Most recent error: {last_error}"
