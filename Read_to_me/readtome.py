"""
STABLE PDF Reader with TTS, Sentence Resume, Closed Captions + OCR Fallback
-----------------------------------------------------------------------------
- Uses pyttsx3 (works on Python 3.14, no compilation issues)
- Extracts text via PyPDF2
- If no text found, falls back to OCR using pytesseract + pdf2image

Dependencies:
pip install PyPDF2 pyttsx3 nltk pytesseract pdf2image pillow

System requirements (Windows):
- Install Tesseract OCR and add to PATH
- Install poppler for pdf2image and add to PATH

First run:
>>> import nltk
>>> nltk.download('punkt')
"""

import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk
from PyPDF2 import PdfReader
import pyttsx3
import nltk

# OCR imports
from pdf2image import convert_from_path
import pytesseract


class PDFReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Reader (Stable + OCR)")
        self.root.geometry("700x450")

        # --- TTS Engine ---
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 180)

        # --- State ---
        self.sentences = []
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.stop_flag = False

        self.thread = None

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(expand=True, fill="both")

        self.file_label = ttk.Label(frame, text="No file loaded")
        self.file_label.pack(pady=5)

        # Captions box
        self.caption = tk.Text(frame, height=8, wrap="word")
        self.caption.pack(fill="both", pady=10)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Load", command=self.load_pdf).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Play", command=self.play).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Pause", command=self.pause).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Resume", command=self.resume).grid(row=0, column=3, padx=5)
        ttk.Button(btn_frame, text="Stop", command=self.stop).grid(row=0, column=4, padx=5)

        self.progress = ttk.Label(frame, text="0 / 0")
        self.progress.pack(pady=5)

        self.status = ttk.Label(frame, text="Idle")
        self.status.pack(pady=5)

    def load_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not file_path:
            return

        self.stop()
        self.file_label.config(text=file_path.split("/")[-1])
        self.status.config(text="Loading...")

        def worker():
            full_text = ""

            try:
                # --- Try normal text extraction ---
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

                # --- OCR fallback if no text ---
                if not full_text.strip():
                    self._set_status("No text found. Running OCR...")
                    images = convert_from_path(file_path)

                    for i, img in enumerate(images):
                        text = pytesseract.image_to_string(img)
                        full_text += text + "\n"
                        self._set_status(f"OCR page {i+1}/{len(images)}")

            except Exception as e:
                print("Error reading PDF:", e)
                self._set_status("Error loading PDF")
                return

            # Tokenize sentences
            self.sentences = nltk.sent_tokenize(full_text)
            self.current_index = 0

            print("Loaded sentences:", len(self.sentences))

            self.root.after(0, self.update_progress)
            self._set_status("Ready")

        threading.Thread(target=worker, daemon=True).start()

    def play(self):
        if not self.sentences or self.is_playing:
            return

        self.stop_flag = False
        self.is_playing = True
        self.is_paused = False

        self.thread = threading.Thread(target=self._read_loop, daemon=True)
        self.thread.start()

    def _read_loop(self):
        while self.current_index < len(self.sentences):
            if self.stop_flag:
                break

            if self.is_paused:
                time.sleep(0.1)
                continue

            sentence = self.sentences[self.current_index]

            # Update captions
            self._update_caption(sentence)

            self.engine.say(sentence)
            self.engine.runAndWait()

            self.current_index += 1
            self.update_progress()

        self.is_playing = False

    def _update_caption(self, text):
        def update():
            self.caption.delete("1.0", tk.END)
            self.caption.insert(tk.END, text)
        self.root.after(0, update)

    def _set_status(self, text):
        self.root.after(0, lambda: self.status.config(text=text))

    def pause(self):
        if self.is_playing:
            self.is_paused = True

    def resume(self):
        if self.is_playing:
            self.is_paused = False

    def stop(self):
        self.stop_flag = True
        self.is_playing = False
        self.is_paused = False
        self.current_index = 0

        try:
            self.engine.stop()
        except Exception:
            pass

        self.update_progress()
        self._update_caption("")
        self._set_status("Stopped")

    def update_progress(self):
        total = len(self.sentences)
        self.progress.config(text=f"{self.current_index} / {total}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFReaderApp(root)
    root.mainloop()
