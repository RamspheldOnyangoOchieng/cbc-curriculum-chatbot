import requests
import json
from .config import Config
from .retriever import CBCRetriever

class CBCEngine:
    API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self):
        Config.validate()
        self.api_key = Config.GROQ_API_KEY
        self.retriever = CBCRetriever()

    def get_chat_response(self, messages):
        """
        Retrieves context and sends message history to Groq.
        """
        # 1. Extract the last user message for retrieval
        user_query = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        
        # 2. Get relevant context from ChromaDB
        context = ""
        if user_query:
            try:
                context = self.retriever.find_relevant_context(user_query)
            except Exception as e:
                print(f"Retrieval error: {e}")

        # 3. Augment the last user message with context (if found)
        if context:
            # We don't want to modify the actual session history in a permanent way here, 
            # so we create a temporary message list for the API call.
            api_messages = messages[:-1]
            last_msg = messages[-1].copy()
            last_msg["content"] = f"Context from CBC Knowledge Base:\n{context}\n\nUser Question: {last_msg['content']}"
            api_messages.append(last_msg)
        else:
            api_messages = messages

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": Config.MODEL_NAME,
            "messages": api_messages,
            "max_tokens": Config.MAX_TOKENS,
            "temperature": Config.TEMPERATURE,
            "top_p": 0.9
        }
        
        try:
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code == 401:
                return "Error: Invalid API Key. Please check your .env file."
            elif status_code == 429:
                return "Error: Rate limit exceeded. Please wait a moment."
            return f"Error: {str(e)}"
        except Exception as e:
            return f"Error: An unexpected error occurred: {str(e)}"
