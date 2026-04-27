import customtkinter as ctk
from tkinter import filedialog, messagebox
import edge_tts
import asyncio
import threading
import os
import pygame
from pypdf import PdfReader
from mutagen.mp3 import MP3
import time

# Initialize pygame mixer for audio playback
pygame.mixer.init()

class AudioReader(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Vision Assist - PDF to Speech")
        self.geometry("600x450")
        ctk.set_appearance_mode("dark")
        
        # State variables
        self.file_path = None
        self.is_paused = False
        self.temp_mp3 = "output_speech.mp3"
        self.audio_length = 0
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        self.label_title = ctk.CTkLabel(self, text="PDF Audio Reader", font=("Arial", 24, "bold"))
        self.label_title.pack(pady=20)

        # File Display (Option 5)
        self.label_file = ctk.CTkLabel(self, text="No file loaded", font=("Arial", 12, "italic"))
        self.label_file.pack(pady=5)

        # Voice Selection (Option 1)
        self.voice_var = ctk.StringVar(value="en-US-GuyNeural")
        self.voice_menu = ctk.CTkOptionMenu(self, values=[
            "en-US-GuyNeural", "en-US-AriaNeural", "en-GB-SoniaNeural", "en-AU-ThomasNeural"
        ], variable=self.voice_var)
        self.voice_menu.pack(pady=10)

        # Playback Controls
        self.btn_frame = ctk.CTkFrame(self)
        self.btn_frame.pack(pady=20)

        self.btn_load = ctk.CTkButton(self.btn_frame, text="Load PDF", command=self.load_pdf)
        self.btn_load.grid(row=0, column=0, padx=10)

        self.btn_pause = ctk.CTkButton(self.btn_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.btn_pause.grid(row=0, column=1, padx=10)

        self.btn_stop = ctk.CTkButton(self.btn_frame, text="Stop", command=self.stop_audio, state="disabled")
        self.btn_stop.grid(row=0, column=2, padx=10)

        # Progress Slider (Option 4)
        self.slider = ctk.CTkSlider(self, from_=0, to=100, command=self.seek_audio)
        self.slider.set(0)
        self.slider.pack(pady=10, padx=40, fill="x")

        # Time Display (Option 3)
        self.label_time = ctk.CTkLabel(self, text="00:00 / 00:00")
        self.label_time.pack(pady=5)

        # Theme Toggle (Option 2)
        self.theme_btn = ctk.CTkButton(self, text="Toggle Light/Dark", command=self.toggle_theme, fg_color="gray")
        self.theme_btn.pack(side="bottom", pady=20)

    # --- Logic Methods ---

    def toggle_theme(self):
        mode = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(mode)

    def load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if path:
            self.file_path = path
            self.label_file.configure(text=f"Current: {os.path.basename(path)}")
            # Start the extraction and TTS in a separate thread to keep UI alive
            threading.Thread(target=self.process_pdf, daemon=True).start()

    def process_pdf(self):
        try:
            reader = PdfReader(self.file_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() + " "
            
            if not full_text.strip():
                messagebox.showerror("Error", "Could not extract text from this PDF.")
                return

            # Run the async TTS
            asyncio.run(self.generate_tts(full_text))
            self.start_playback()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process PDF: {e}")

    async def generate_tts(self, text):
        communicate = edge_tts.Communicate(text, self.voice_var.get())
        await communicate.save(self.temp_mp3)

    def start_playback(self):
        pygame.mixer.music.load(self.temp_mp3)
        
        # Get length for the slider
        audio = MP3(self.temp_mp3)
        self.audio_length = audio.info.length
        self.slider.configure(from_=0, to=self.audio_length)
        
        pygame.mixer.music.play()
        self.btn_pause.configure(state="normal", text="Pause")
        self.btn_stop.configure(state="normal")
        self.update_progress()

    def toggle_pause(self):
        if not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.btn_pause.configure(text="Resume")
        else:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.btn_pause.configure(text="Pause")

    def stop_audio(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self.btn_pause.configure(state="disabled")
        self.btn_stop.configure(state="disabled")
        self.slider.set(0)
        self.label_time.configure(text="00:00 / 00:00")

    def seek_audio(self, value):
        # Pygame mixer set_pos is relative to the start in seconds
        pygame.mixer.music.play(start=float(value))

    def update_progress(self):
        if pygame.mixer.music.get_busy():
            # get_pos is in milliseconds
            current_time = pygame.mixer.music.get_pos() / 1000
            self.slider.set(current_time)
            
            # Formatting time strings
            cur_min, cur_sec = divmod(int(current_time), 60)
            total_min, total_sec = divmod(int(self.audio_length), 60)
            self.label_time.configure(text=f"{cur_min:02}:{cur_sec:02} / {total_min:02}:{total_sec:02}")
            
            # Schedule next update
            self.after(1000, self.update_progress)

if __name__ == "__main__":
    app = AudioReader()
    app.mainloop()