import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL_NAME = "llama-3.3-70b-versatile"
    TEMPERATURE = 0.1
    MAX_TOKENS = 1000
    
    # UI Constants
    APP_TITLE = "Kenya CBC/CBE Expert Guide"
    APP_ICON = "🇰🇪"
    
    @staticmethod
    def validate():
        if not Config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in .env file")
