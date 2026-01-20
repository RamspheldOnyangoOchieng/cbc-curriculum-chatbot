
import os
import pdfplumber

def debug_pdf(filename):
    pdf_path = os.path.join("data/raw", filename)
    print(f" debugging {pdf_path}...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            for i, page in enumerate(pdf.pages[:3]):
                text = page.extract_text()
                chars = len(text) if text else 0
                images = page.images
                print(f"Page {i+1}: extracted {chars} characters. Found {len(images)} images.")
                if chars == 0 and len(images) > 0:
                    print(f"  -> Page {i+1} appears to be an image scan.")
                    
    except Exception as e:
        print(f"Error: {e}")

debug_pdf("2026_REGISTRATION_CIRCULAR_FOR_NAIROBI_–_KNEC.pdf")
