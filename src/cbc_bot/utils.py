import PyPDF2
import os

def extract_pdf_text(pdf_path):
    """Extracts text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def process_all_pdfs(raw_dir="data/raw", processed_dir="data/processed"):
    """Processes all PDFs in a directory and saves them as text files."""
    os.makedirs(processed_dir, exist_ok=True)
    if not os.path.exists(raw_dir):
        print(f"Directory {raw_dir} does not exist.")
        return

    for filename in os.listdir(raw_dir):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(raw_dir, filename)
            # Replace spaces and special characters in output filename for better compatibility
            safe_filename = filename.replace(".pdf", ".txt").replace(" ", "_").replace("–", "-")
            output_path = os.path.join(processed_dir, safe_filename)
            
            # Re-process if file doesn't exist OR is empty
            should_process = not os.path.exists(output_path) or os.path.getsize(output_path) == 0
            
            if should_process:
                print(f"Extracting: {filename}...")
                text = extract_pdf_text(input_path)
                if text.strip():
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(text)
                    print(f"Successfully extracted: {filename} -> {safe_filename}")
                else:
                    print(f"Warning: No text extracted from {filename}. It might be a scanned image.")
