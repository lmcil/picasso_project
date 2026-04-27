"""
Vision Assist - PDF to Speech Reader
Converted to use standard tkinter (no customtkinter needed)

Features:
- Load and read PDF files aloud
- Multiple voice options
- Playback controls (play, pause, stop)
- Progress slider with seek functionality
- Time display
- Light/Dark theme toggle
- Current file display

Requirements:
    pip install edge-tts pygame pypdf mutagen

Author: Student Developer
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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


class AudioReader(tk.Tk):
    """
    PDF to Speech application using standard tkinter.
    Reads PDF files aloud using text-to-speech.
    """
    
    def __init__(self):
        super().__init__()

        self.title("Vision Assist - PDF to Speech")
        self.geometry("700x550")
        self.configure(bg="#1e1e1e")  # Dark background
        
        # State variables
        self.file_path = None
        self.is_paused = False
        self.temp_mp3 = "output_speech.mp3"
        self.audio_length = 0
        self.is_playing = False
        self.dark_mode = True
        
        # Color schemes
        self.colors = {
            'dark': {
                'bg': '#1e1e1e',
                'fg': '#ffffff',
                'button_bg': '#0078d4',
                'button_fg': '#ffffff',
                'frame_bg': '#2d2d2d',
                'accent': '#0078d4'
            },
            'light': {
                'bg': '#f0f0f0',
                'fg': '#000000',
                'button_bg': '#0078d4',
                'button_fg': '#ffffff',
                'frame_bg': '#ffffff',
                'accent': '#0078d4'
            }
        }
        
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Create all UI elements."""
        
        # Header
        self.label_title = tk.Label(
            self, 
            text="📖 PDF Audio Reader", 
            font=("Arial", 28, "bold")
        )
        self.label_title.pack(pady=20)

        # File Display (Option 5)
        self.file_frame = tk.Frame(self)
        self.file_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(
            self.file_frame, 
            text="Current File:", 
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        self.label_file = tk.Label(
            self.file_frame, 
            text="No file loaded", 
            font=("Arial", 10, "italic"),
            fg="#888888"
        )
        self.label_file.pack(side=tk.LEFT, padx=5)

        # Voice Selection Section (Option 1)
        voice_frame = tk.LabelFrame(
            self, 
            text="🎙️ Voice Selection", 
            font=("Arial", 11, "bold"),
            padx=20, 
            pady=10
        )
        voice_frame.pack(pady=15, padx=30, fill=tk.X)
        
        self.voice_var = tk.StringVar(value="en-US-GuyNeural")
        
        voices = [
            "en-US-GuyNeural (Male - US)",
            "en-US-AriaNeural (Female - US)",
            "en-GB-SoniaNeural (Female - UK)",
            "en-AU-ThomasNeural (Male - Australia)"
        ]
        
        # Map display names to actual voice IDs
        self.voice_map = {
            "en-US-GuyNeural (Male - US)": "en-US-GuyNeural",
            "en-US-AriaNeural (Female - US)": "en-US-AriaNeural",
            "en-GB-SoniaNeural (Female - UK)": "en-GB-SoniaNeural",
            "en-AU-ThomasNeural (Male - Australia)": "en-AU-ThomasNeural"
        }
        
        self.voice_menu = ttk.Combobox(
            voice_frame, 
            values=voices,
            state="readonly",
            font=("Arial", 10),
            width=35
        )
        self.voice_menu.set("en-US-GuyNeural (Male - US)")
        self.voice_menu.pack(pady=5)

        # Playback Controls
        controls_frame = tk.LabelFrame(
            self,
            text="🎮 Playback Controls",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        controls_frame.pack(pady=15, padx=30, fill=tk.X)
        
        self.btn_frame = tk.Frame(controls_frame)
        self.btn_frame.pack(pady=10)

        # Load PDF Button
        self.btn_load = tk.Button(
            self.btn_frame, 
            text="📂 Load PDF", 
            command=self.load_pdf,
            font=("Arial", 11, "bold"),
            width=12,
            height=2,
            cursor="hand2"
        )
        self.btn_load.grid(row=0, column=0, padx=8)

        # Pause/Resume Button
        self.btn_pause = tk.Button(
            self.btn_frame, 
            text="⏸️ Pause", 
            command=self.toggle_pause,
            font=("Arial", 11, "bold"),
            width=12,
            height=2,
            state="disabled",
            cursor="hand2"
        )
        self.btn_pause.grid(row=0, column=1, padx=8)

        # Stop Button
        self.btn_stop = tk.Button(
            self.btn_frame, 
            text="⏹️ Stop", 
            command=self.stop_audio,
            font=("Arial", 11, "bold"),
            width=12,
            height=2,
            state="disabled",
            cursor="hand2"
        )
        self.btn_stop.grid(row=0, column=2, padx=8)

        # Progress Section
        progress_frame = tk.LabelFrame(
            self,
            text="⏱️ Progress",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=15
        )
        progress_frame.pack(pady=15, padx=30, fill=tk.X)
        
        # Time Display (Option 3)
        self.label_time = tk.Label(
            progress_frame, 
            text="00:00 / 00:00",
            font=("Arial", 12, "bold")
        )
        self.label_time.pack(pady=5)

        # Progress Slider (Option 4)
        self.slider = tk.Scale(
            progress_frame,
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL,
            command=self.seek_audio,
            showvalue=False,
            length=500,
            sliderlength=20
        )
        self.slider.set(0)
        self.slider.pack(pady=10, padx=20, fill=tk.X)

        # Theme Toggle (Option 2)
        self.theme_btn = tk.Button(
            self, 
            text="🌓 Toggle Light/Dark Mode", 
            command=self.toggle_theme,
            font=("Arial", 10, "bold"),
            cursor="hand2",
            width=25,
            height=2
        )
        self.theme_btn.pack(side="bottom", pady=20)

        # Status bar
        self.status_label = tk.Label(
            self,
            text="Ready to load PDF",
            font=("Arial", 9, "italic"),
            anchor="w"
        )
        self.status_label.pack(side="bottom", fill=tk.X, padx=10, pady=5)

    def apply_theme(self):
        """Apply current theme colors to all widgets."""
        theme = 'dark' if self.dark_mode else 'light'
        colors = self.colors[theme]
        
        # Main window
        self.configure(bg=colors['bg'])
        
        # Labels
        self.label_title.configure(bg=colors['bg'], fg=colors['fg'])
        self.file_frame.configure(bg=colors['bg'])
        self.label_file.configure(bg=colors['bg'], fg='#888888')
        self.label_time.configure(bg=colors['frame_bg'], fg=colors['fg'])
        self.status_label.configure(bg=colors['bg'], fg='#888888')
        
        # Buttons
        for btn in [self.btn_load, self.btn_pause, self.btn_stop]:
            btn.configure(
                bg=colors['button_bg'],
                fg=colors['button_fg'],
                activebackground=colors['accent']
            )
        
        self.theme_btn.configure(
            bg='#555555' if self.dark_mode else '#cccccc',
            fg='white' if self.dark_mode else 'black'
        )
        
        # Frames
        self.btn_frame.configure(bg=colors['frame_bg'])
        
        # Slider
        self.slider.configure(
            bg=colors['frame_bg'],
            troughcolor=colors['bg'],
            activebackground=colors['accent']
        )

    def toggle_theme(self):
        """Toggle between light and dark mode (Option 2)."""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        mode = "Dark" if self.dark_mode else "Light"
        self.update_status(f"Switched to {mode} mode")

    def update_status(self, message):
        """Update status bar message."""
        self.status_label.configure(text=message)

    def load_pdf(self):
        """Load a PDF file and start processing (Option 5)."""
        path = filedialog.askopenfilename(
            title="Select a PDF file",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        
        if path:
            self.file_path = path
            filename = os.path.basename(path)
            self.label_file.configure(text=filename)
            self.update_status(f"Loading: {filename}")
            
            # Disable load button while processing
            self.btn_load.configure(state="disabled", text="Processing...")
            
            # Start the extraction and TTS in a separate thread
            threading.Thread(target=self.process_pdf, daemon=True).start()

    def process_pdf(self):
        """Extract text from PDF and generate speech."""
        try:
            self.update_status("Extracting text from PDF...")
            
            # Read PDF
            reader = PdfReader(self.file_path)
            full_text = ""
            
            for i, page in enumerate(reader.pages):
                self.update_status(f"Reading page {i+1}/{len(reader.pages)}...")
                full_text += page.extract_text() + " "
            
            if not full_text.strip():
                messagebox.showerror("Error", "Could not extract text from this PDF.")
                self.btn_load.configure(state="normal", text="📂 Load PDF")
                self.update_status("Ready to load PDF")
                return

            # Generate speech
            self.update_status("Generating speech... This may take a moment.")
            
            # Get the actual voice ID from the selected display name
            selected_display = self.voice_menu.get()
            voice_id = self.voice_map[selected_display]
            
            asyncio.run(self.generate_tts(full_text, voice_id))
            
            # Start playback on main thread
            self.after(0, self.start_playback)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process PDF:\n{str(e)}")
            self.btn_load.configure(state="normal", text="📂 Load PDF")
            self.update_status("Error occurred - Ready to try again")

    async def generate_tts(self, text, voice):
        """Generate speech from text using edge-tts (Option 1)."""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(self.temp_mp3)

    def start_playback(self):
        """Start playing the generated audio."""
        try:
            pygame.mixer.music.load(self.temp_mp3)
            
            # Get audio length for the slider (Option 4)
            audio = MP3(self.temp_mp3)
            self.audio_length = audio.info.length
            self.slider.configure(from_=0, to=self.audio_length)
            
            # Start playback
            pygame.mixer.music.play()
            self.is_playing = True
            
            # Enable controls
            self.btn_pause.configure(state="normal", text="⏸️ Pause")
            self.btn_stop.configure(state="normal")
            self.btn_load.configure(state="normal", text="📂 Load PDF")
            
            self.update_status("Playing audio...")
            self.update_progress()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play audio:\n{str(e)}")
            self.btn_load.configure(state="normal", text="📂 Load PDF")
            self.update_status("Playback error - Ready to try again")

    def toggle_pause(self):
        """Pause or resume audio playback."""
        if not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.btn_pause.configure(text="▶️ Resume")
            self.update_status("Paused")
        else:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.btn_pause.configure(text="⏸️ Pause")
            self.update_status("Playing audio...")

    def stop_audio(self):
        """Stop audio playback and reset controls."""
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        
        self.is_playing = False
        self.is_paused = False
        
        self.btn_pause.configure(state="disabled", text="⏸️ Pause")
        self.btn_stop.configure(state="disabled")
        self.slider.set(0)
        self.label_time.configure(text="00:00 / 00:00")
        
        self.update_status("Stopped - Ready to load PDF")

    def seek_audio(self, value):
        """Seek to a specific position in the audio (Option 4)."""
        if self.is_playing:
            # Stop current playback
            pygame.mixer.music.stop()
            # Start from new position
            pygame.mixer.music.play(start=float(value))
            
            # If it was paused, pause again
            if self.is_paused:
                pygame.mixer.music.pause()

    def update_progress(self):
        """Update progress slider and time display (Options 3 & 4)."""
        if pygame.mixer.music.get_busy() or self.is_paused:
            # Get current position in seconds
            current_time = pygame.mixer.music.get_pos() / 1000
            
            # Update slider position
            if not self.is_paused:
                self.slider.set(current_time)
            
            # Format time strings (Option 3)
            cur_min, cur_sec = divmod(int(current_time), 60)
            total_min, total_sec = divmod(int(self.audio_length), 60)
            
            time_text = f"{cur_min:02}:{cur_sec:02} / {total_min:02}:{total_sec:02}"
            self.label_time.configure(text=time_text)
            
            # Schedule next update
            self.after(1000, self.update_progress)
        else:
            # Playback finished
            if self.is_playing:
                self.stop_audio()
                self.update_status("Playback completed")

    def destroy(self):
        """Clean up when closing the application."""
        # Stop audio if playing
        if self.is_playing:
            pygame.mixer.music.stop()
        
        # Delete temporary MP3 file
        if os.path.exists(self.temp_mp3):
            try:
                os.remove(self.temp_mp3)
            except:
                pass
        
        super().destroy()


if __name__ == "__main__":
    app = AudioReader()
    app.mainloop()