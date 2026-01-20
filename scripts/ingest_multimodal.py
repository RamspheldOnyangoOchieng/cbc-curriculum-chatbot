
import os
import sys
import subprocess
import shutil

# Force UTF-8 for Windows console
sys.stdout.reconfigure(encoding='utf-8')


# --- Dependency Check & Installation ---
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

REQUIRED_PACKAGES = [
    "easyocr", "pdfplumber", "pypdfium2", "openai-whisper", "moviepy", "torch", "numpy"
]

def check_dependencies():
    print("Checking dependencies...")
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"Installing missing package: {package}...")
            try:
                install(package)
            except Exception as e:
                print(f"Error installing {package}: {e}")

# --- Imports (Lazy loading to avoid startup errors) ---

def ingest_all():
    import easyocr
    import pdfplumber
    import pypdfium2 as pdfium
    import whisper
    import moviepy.video.io.VideoFileClip as VideoFileClip
    # For moviepy 2.x, imports changed drastically. Fallback logic:
    try:
        from moviepy import VideoFileClip
    except ImportError:
        try:
             from moviepy.editor import VideoFileClip
        except ImportError:
             import moviepy.video.io.VideoFileClip as VideoFileClip
    import torch
    import numpy as np
    from PIL import Image

    # Initialize generic models
    # GPU check for faster processing
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    print("Loading OCR Model (this may take a moment)...")
    ocr_reader = easyocr.Reader(['en'], gpu=(device=="cuda"))
    
    # Whisper model is loaded on demand to save memory if no audio files exist
    whisper_model = None 

    raw_dir = os.path.abspath("data/raw")
    processed_dir = os.path.abspath("data/processed")
    
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    print(f"Scanning {raw_dir} for multi-modal content...")

    for filename in os.listdir(raw_dir):
        file_path = os.path.join(raw_dir, filename)
        base_name, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        txt_path = os.path.join(processed_dir, base_name + ".txt")
        
        # Skip if effectively processed (size > 100 bytes)
        if os.path.exists(txt_path) and os.path.getsize(txt_path) > 100:
            print(f"Skipping {filename} (already processed).")
            continue

        print(f"Processing: {filename}")
        final_text = ""

        try:
            # --- PDF HANDLING ---
            if ext == ".pdf":
                # 1. Try Text Extraction
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            final_text += extracted + "\n"
                
                # 2. If Text Extraction Failed (Scanned PDF), use OCR
                if len(final_text.strip()) < 50:
                    print(f"  -> minimal text found in PDF using standard extraction. Switching to OCR...")
                    final_text = "" # Reset
                    
                    pdf = pdfium.PdfDocument(file_path)
                    n_pages = len(pdf)
                    for page_number in range(n_pages):
                        print(f"  -> OCR Page {page_number+1}/{n_pages}...")
                        page = pdf[page_number]
                        bitmap = page.render(scale=2) # 2x scale for better OCR
                        pil_image = bitmap.to_pil()
                        
                        # EasyOCR works on numpy arrays
                        img_np = np.array(pil_image)
                        results = ocr_reader.readtext(img_np, detail=0)
                        page_text = "\n".join(results)
                        final_text += page_text + "\n"
                        
            # --- IMAGE HANDLING ---
            elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
                print(f"  -> Performing OCR on image...")
                results = ocr_reader.readtext(file_path, detail=0)
                final_text = " ".join(results)

            # --- AUDIO/VIDEO HANDLING ---
            elif ext in [".mp3", ".wav", ".m4a", ".mp4", ".mov", ".avi"]:
                print(f"  -> Transcribing media file...")
                if whisper_model is None:
                    print("  -> Loading Whisper Model (base)...")
                    whisper_model = whisper.load_model("base", device=device)
                
                # For video, extract audio first if needed, but Whisper handles many formats directly via ffmpeg
                # However, moviepy is safer for extraction if generic ffmpeg isn't in path
                temp_audio = "temp_audio.mp3"
                target_file = file_path
                
                if ext in [".mp4", ".mov", ".avi"]:
                    print("  -> Extracting audio track from video...")
                    video = VideoFileClip(file_path)
                    video.audio.write_audiofile(temp_audio, verbose=False, logger=None)
                    target_file = temp_audio
                
                result = whisper_model.transcribe(target_file)
                final_text = result["text"]
                
                if os.path.exists("temp_audio.mp3"):
                    os.remove("temp_audio.mp3")

            # --- UNSUPPORTED ---
            else:
                print(f"Skipping {filename}: Unsupported format for now.")
                continue

            # --- SAVE RESULTS ---
            if final_text.strip():
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(final_text)
                print(f"  -> Success! Saved {len(final_text)} chars to {base_name}.txt")
            else:
                print(f"  -> Warning: No content extracted from {filename}")

        except Exception as e:
            print(f"ERROR processing {filename}: {e}")

if __name__ == "__main__":
    # Ensure dependencies are present
    try:
        import easyocr
        import whisper
    except ImportError:
        check_dependencies()
    
    ingest_all()
