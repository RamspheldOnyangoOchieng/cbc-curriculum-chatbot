# scripts/process_data.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from cbc_bot.utils import process_all_pdfs

if __name__ == "__main__":
    print("Extracting text from PDFs in data/raw/...")
    process_all_pdfs()
    print("Done! Check data/processed/")