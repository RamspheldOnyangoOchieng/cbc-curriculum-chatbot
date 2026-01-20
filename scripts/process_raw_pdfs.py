
import os
import subprocess
import sys

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"Failed to install {package}: {e}")

try:
    import pdfplumber
except ImportError:
    print("pdfplumber not found. Installing...")
    install_package("pdfplumber")
    import pdfplumber

def process_pdfs():
    raw_dir = os.path.abspath("data/raw")
    processed_dir = os.path.abspath("data/processed")

    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    print("Checking for PDFs to process...")

    for filename in os.listdir(raw_dir):
        if filename.endswith(".pdf"):
            base_name = filename.replace('.pdf', '')
            pdf_path = os.path.join(raw_dir, filename)
            txt_path = os.path.join(processed_dir, base_name + ".txt")
            
            # Check if file exists and is valid (size > 100 bytes)
            if os.path.exists(txt_path):
                if os.path.getsize(txt_path) > 100:
                    print(f"Skipping {filename} (already processed and valid).")
                    continue
                else:
                    print(f"Reprocessing {filename} (existing txt file is too small).")
            else:
                print(f"Processing new file: {filename}...")

            try:
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                
                if len(text.strip()) == 0:
                    print(f"Warning: No text extracted from {filename}. It might be an image scan.")
                
                with open(txt_path, 'w', encoding='utf-8') as txt_file:
                    txt_file.write(text)
                
                print(f"Saved text to: {txt_path} ({len(text)} chars)")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    process_pdfs()
