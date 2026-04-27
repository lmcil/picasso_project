"""
PDF Text-to-Speech Reader with GUI, Pause/Resume, Stop/Load,
WAV output, and sub-chunked audio to avoid memory issues.

Dependencies:
    pip install PyPDF2 pyttsx3 pygame-ce

Notes:
    - pygame-ce is imported as 'pygame' (drop-in replacement).
    - Audio is generated as small WAV chunks (subsections of pages),
      so pygame.mixer never has to load a huge file into memory.
"""

import os
import threading
import tempfile

import tkinter as tk
from tkinter import filedialog, messagebox

import PyPDF2
import pyttsx3
import pygame


class PDFTTSApp:
    """
    Main application class encapsulating GUI, PDF handling, TTS generation,
    and audio playback logic.
    """

    # Max characters per audio chunk (roughly ~1 minute of speech)
    MAX_CHARS_PER_CHUNK = 1500

    def __init__(self, root: tk.Tk):
        """
        Initialize the GUI, state variables, and audio subsystem.

        :param root: The root Tkinter window.
        """
        self.root = root
        self.root.title("PDF Text-to-Speech Reader")

        # Initialize pygame mixer for audio playback.
        pygame.mixer.init()

        # State variables
        self.current_pdf_path = None          # Path to the currently loaded PDF
        self.audio_chunks = []                # List of small WAV files (sub-chunks)
        self.current_chunk_index = 0          # Index of the currently playing chunk
        self.is_playing = False               # True if audio is currently playing
        self.is_paused = False                # True if audio is currently paused
        self.is_generating_audio = False      # True while TTS audio is being generated

        # Build the GUI
        self._build_gui()

    # -------------------------------------------------------------------------
    # GUI construction
    # -------------------------------------------------------------------------

    def _build_gui(self):
        """
        Build and lay out all GUI widgets: labels, buttons, etc.
        """
        # Top frame for file controls
        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=tk.X)

        # Label showing currently loaded file
        self.file_label = tk.Label(
            top_frame,
            text="No PDF loaded",
            anchor="w"
        )
        self.file_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Button to load/select a PDF file
        load_button = tk.Button(
            top_frame,
            text="Load PDF",
            command=self.on_load_pdf_clicked
        )
        load_button.pack(side=tk.RIGHT, padx=(5, 0))

        # Middle frame for playback controls
        controls_frame = tk.Frame(self.root, padx=10, pady=10)
        controls_frame.pack(fill=tk.X)

        # Play/Resume button
        self.play_button = tk.Button(
            controls_frame,
            text="Play",
            width=10,
            command=self.on_play_clicked,
            state=tk.DISABLED  # Disabled until audio is ready
        )
        self.play_button.grid(row=0, column=0, padx=5)

        # Pause button
        self.pause_button = tk.Button(
            controls_frame,
            text="Pause",
            width=10,
            command=self.on_pause_clicked,
            state=tk.DISABLED
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        # Stop button
        self.stop_button = tk.Button(
            controls_frame,
            text="Stop",
            width=10,
            command=self.on_stop_clicked,
            state=tk.DISABLED
        )
        self.stop_button.grid(row=0, column=2, padx=5)

        # Status label to show progress (e.g., "Generating audio...", "Playing", etc.)
        self.status_label = tk.Label(
            self.root,
            text="Load a PDF to begin.",
            anchor="w",
            padx=10,
            pady=5
        )
        self.status_label.pack(fill=tk.X)

        # Optional: a small text box to show some info or instructions
        info_text = tk.Text(self.root, height=6, wrap="word")
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        info_text.insert(
            tk.END,
            "Instructions:\n"
            "1. Click 'Load PDF' and choose a PDF file.\n"
            "2. Wait for the app to generate audio from the PDF.\n"
            "3. Use Play, Pause, and Stop to control playback.\n"
            "4. You can stop playback and load another file at any time.\n"
        )
        info_text.config(state=tk.DISABLED)

    # -------------------------------------------------------------------------
    # Event handlers for GUI buttons
    # -------------------------------------------------------------------------

    def on_load_pdf_clicked(self):
        """
        Handler for the 'Load PDF' button.
        Opens a file dialog, sets the current PDF path, and starts audio generation.
        """
        # Stop any current playback and clean up previous audio
        self._stop_playback_internal()
        self._cleanup_audio_chunks()

        # Ask user to select a PDF file
        file_path = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf")]
        )

        if not file_path:
            # User cancelled the dialog
            return

        self.current_pdf_path = file_path
        self.file_label.config(text=os.path.basename(file_path))

        # Disable playback controls while generating new audio
        self._set_controls_state(play=False, pause=False, stop=False)
        self.status_label.config(text="Generating audio from PDF...")

        # Start TTS generation in a background thread so the GUI stays responsive
        thread = threading.Thread(target=self._generate_audio_from_pdf, daemon=True)
        thread.start()

    def on_play_clicked(self):
        """
        Handler for the 'Play' button.
        If audio is paused, resume; otherwise start playback from the current chunk.
        """
        if not self.audio_chunks:
            messagebox.showwarning("No audio", "No audio has been generated yet.")
            return

        # If currently paused, resume playback
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.status_label.config(text="Resumed playback.")
            # Continue monitoring playback
            self._monitor_playback()
        else:
            # Start playback from the current chunk index
            self.current_chunk_index = max(0, self.current_chunk_index)
            self._play_current_chunk()

        # Update button states
        self._set_controls_state(play=True, pause=True, stop=True)

    def on_pause_clicked(self):
        """
        Handler for the 'Pause' button.
        Pauses playback if currently playing.
        """
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.status_label.config(text="Playback paused.")

    def on_stop_clicked(self):
        """
        Handler for the 'Stop' button.
        Stops playback and resets state.
        """
        self._stop_playback_internal()
        self.status_label.config(text="Playback stopped.")

    # -------------------------------------------------------------------------
    # Core logic: PDF reading and TTS generation (WAV + sub-chunking)
    # -------------------------------------------------------------------------

    def _generate_audio_from_pdf(self):
        """
        Extract text from the currently loaded PDF and generate multiple
        small WAV audio files (sub-chunks) using pyttsx3.

        Strategy:
            - Read the PDF page by page.
            - For each page, split text into smaller segments (MAX_CHARS_PER_CHUNK).
            - Queue each segment as a separate WAV file via pyttsx3.save_to_file().
            - Run the TTS engine once to synthesize all queued chunks.
            - Store the list of chunk file paths in self.audio_chunks.

        This runs in a background thread.
        """
        if not self.current_pdf_path:
            return

        self.is_generating_audio = True
        self.audio_chunks = []
        self.current_chunk_index = 0

        try:
            with open(self.current_pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)

                # Initialize TTS engine in this thread
                engine = pyttsx3.init()
                engine.setProperty("rate", 160)
                engine.setProperty("volume", 0.9)

                for page_index, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text() or ""
                    except Exception:
                        text = ""

                    text = text.strip()
                    if not text:
                        continue  # Skip empty pages

                    # Break long pages into smaller sub-chunks
                    segments = [
                        text[i:i + self.MAX_CHARS_PER_CHUNK]
                        for i in range(0, len(text), self.MAX_CHARS_PER_CHUNK)
                    ]

                    for segment in segments:
                        # Create a small temp WAV file for this segment
                        fd, temp_path = tempfile.mkstemp(suffix=".wav")
                        os.close(fd)

                        # Queue this segment's text to be saved to temp_path
                        engine.save_to_file(segment, temp_path)
                        self.audio_chunks.append(temp_path)

                if not self.audio_chunks:
                    # No text found in any page
                    self._update_status_from_thread("No readable text found in PDF.")
                    self.is_generating_audio = False
                    return

                # Actually synthesize all queued audio
                engine.runAndWait()

            # Update GUI from main thread
            self._update_status_from_thread("Audio generation complete. Ready to play.")
            self._enable_play_controls_from_thread()

        except Exception as e:
            self._update_status_from_thread(f"Error generating audio: {e}")
        finally:
            self.is_generating_audio = False

    # -------------------------------------------------------------------------
    # Playback helpers (chunked playback)
    # -------------------------------------------------------------------------

    def _play_current_chunk(self):
        """
        Load and play the current audio chunk based on self.current_chunk_index.
        If there are no more chunks, stop playback and update status.
        """
        if self.current_chunk_index >= len(self.audio_chunks):
            # Finished all chunks
            self.is_playing = False
            self.is_paused = False
            self._set_controls_state(play=True, pause=False, stop=False)
            self.status_label.config(text="Finished playback.")
            return

        chunk_path = self.audio_chunks[self.current_chunk_index]

        try:
            pygame.mixer.music.load(chunk_path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.is_paused = False
            self.status_label.config(
                text=f"Playing chunk {self.current_chunk_index + 1} of {len(self.audio_chunks)}."
            )
            # Start monitoring playback to know when this chunk ends
            self._monitor_playback()
        except pygame.error as e:
            messagebox.showerror("Playback error", f"Could not play audio: {e}")
            self.is_playing = False
            self.is_paused = False

    def _monitor_playback(self):
        """
        Periodically check if the current chunk has finished playing.
        If finished and not paused, advance to the next chunk.
        This uses Tkinter's after() instead of a blocking loop.
        """
        if not self.is_playing or self.is_paused:
            # Either stopped or paused; do not advance
            return

        if not pygame.mixer.music.get_busy():
            # Current chunk finished; move to the next one
            self.current_chunk_index += 1
            self._play_current_chunk()
        else:
            # Still playing; check again after a short delay
            self.root.after(200, self._monitor_playback)

    # -------------------------------------------------------------------------
    # Helper methods for playback and GUI state
    # -------------------------------------------------------------------------

    def _stop_playback_internal(self):
        """
        Stop audio playback and reset playback-related state variables.
        Does not modify the currently loaded PDF or generated audio files.
        """
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            # If mixer is not playing anything, ignore
            pass

        self.is_playing = False
        self.is_paused = False
        self.current_chunk_index = 0

        # Update button states: only Play is enabled if we have audio
        if self.audio_chunks:
            self._set_controls_state(play=True, pause=False, stop=False)
        else:
            self._set_controls_state(play=False, pause=False, stop=False)

    def _set_controls_state(self, play: bool, pause: bool, stop: bool):
        """
        Enable or disable playback control buttons.

        :param play: True to enable Play button, False to disable.
        :param pause: True to enable Pause button, False to disable.
        :param stop: True to enable Stop button, False to disable.
        """
        self.play_button.config(state=tk.NORMAL if play else tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL if pause else tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL if stop else tk.DISABLED)

    def _update_status_from_thread(self, message: str):
        """
        Thread-safe way to update the status label from a background thread.

        :param message: Text to display in the status label.
        """
        self.root.after(0, lambda: self.status_label.config(text=message))

    def _enable_play_controls_from_thread(self):
        """
        Thread-safe way to enable Play and Stop buttons after audio generation.
        """
        def enable():
            self._set_controls_state(play=True, pause=False, stop=False)

        self.root.after(0, enable)

    def _cleanup_audio_chunks(self):
        """
        Delete all temporary audio chunk files and clear the list.
        """
        for path in self.audio_chunks:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        self.audio_chunks = []
        self.current_chunk_index = 0

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup(self):
        """
        Cleanup resources before exiting the application:
            - Stop playback.
            - Remove temporary audio files.
            - Quit pygame mixer.
        """
        self._stop_playback_internal()
        self._cleanup_audio_chunks()
        pygame.mixer.quit()


def main():
    """
    Entry point for the application.
    Creates the Tkinter root window, instantiates the app, and starts the main loop.
    """
    root = tk.Tk()
    app = PDFTTSApp(root)

    # Ensure cleanup is called when the window is closed
    def on_close():
        app.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.geometry("600x400")
    root.mainloop()


if __name__ == "__main__":
    main()
    