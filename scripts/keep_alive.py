import requests
import time
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# The URL of your Render backend
BACKEND_URL = os.getenv("PYTHON_BACKEND_URL", "https://cbc-curriculum-chatbot.onrender.com")
# Interval in seconds (4 minutes = 240 seconds)
INTERVAL = 240 

def ping_server():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- Render Keep-Alive Started ---")
    print(f"Target: {BACKEND_URL}")
    
    while True:
        try:
            # We use a simple GET request to the root or a health check endpoint
            response = requests.get(BACKEND_URL, timeout=10)
            
            if response.status_code == 200:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ Ping Success (200 OK)")
            else:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Ping returned status: {response.status_code}")
                
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ Ping Failed: {e}")
        
        # Wait before next ping
        time.sleep(INTERVAL)

if __name__ == "__main__":
    ping_server()
