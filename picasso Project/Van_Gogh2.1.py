import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from PIL import Image, ImageDraw, ImageTk
import random
import math
from collections import deque

class GradientPicker(tk.Toplevel):
    """High-performance Gradient Picker using PhotoImage bitmasking."""
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("🎨 Gradient Color Picker")
        self.geometry("400x480")
        self.resizable(False, False)
        self.callback = callback
        self.selected_color = "#000000"
        
        self.canvas_w, self.canvas_h = 360, 300
        self.gradient_canvas = tk.Canvas(self, width=self.canvas_w, height=self.canvas_h, bg="white", relief="sunken", bd=2)
        self.gradient_canvas.pack(padx=20, pady=20)
        
        # Use PhotoImage for instant rendering instead of 100k line objects
        self.img = tk.PhotoImage(width=self.canvas_w, height=self.canvas_h)
        self.gradient_canvas.create_image((self.canvas_w//2, self.canvas_h//2), image=self.img)
        self.draw_gradient_fast()
        
        self.gradient_canvas.bind("<Button-1>", self.pick_color)
        
        # Preview UI
        preview_frame = tk.Frame(self)
        preview_frame.pack(pady=10)
        tk.Label(preview_frame, text="Selected:").pack(side=tk.LEFT)
        self.color_preview = tk.Canvas(preview_frame, width=60, height=30, bg=self.selected_color, relief="raised", bd=2)
        self.color_preview.pack(side=tk.LEFT, padx=10)
        self.color_label = tk.Label(preview_frame, text=self.selected_color, font=("Courier", 12, "bold"))
        self.color_label.pack(side=tk.LEFT)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="✓ Select Color", bg="#27ae60", fg="white", width=15,
                  command=self.confirm_selection).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", bg="#e74c3c", fg="white", width=10,
                  command=self.destroy).pack(side=tk.LEFT, padx=5)

    def draw_gradient_fast(self):
        """Generates a full HSV map in a single pass."""
        pixels = ""
        for y in range(self.canvas_h):
            row = "{"
            for x in range(self.canvas_w):
                h = x / self.canvas_w
                s = 1.0 - (y / self.canvas_h)
                # Convert HSV to Hex
                i = int(h * 6); f = (h * 6) - i; p = 1.0 * (1 - s); q = 1.0 * (1 - s * f); t = 1.0 * (1 - s * (1 - f))
                r, g, b = [(1.0, t, p), (q, 1.0, p), (p, 1.0, t), (p, q, 1.0), (t, p, 1.0), (1.0, p, q)][i % 6]
                row += f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x} '
            pixels += row + "} "
        self.img.put(pixels)

    def pick_color(self, event):
        x, y = max(0, min(event.x, self.canvas_w-1)), max(0, min(event.y, self.canvas_h-1))
        rgb = "#%02x%02x%02x" % self.img.get(x, y)
        self.selected_color = rgb
        self.color_preview.config(bg=rgb)
        self.color_label.config(text=rgb.upper())

    def confirm_selection(self):
        self.callback(self.selected_color)
        self.destroy()

class Layer:
    def __init__(self, name, canvas):
        self.name = name
        self.canvas = canvas
        self.items = []
        self.visible = True

    def add_item(self, item):
        self.items.append(item)

    def set_visibility(self, visible):
        self.visible = visible
        state = "normal" if visible else "hidden"
        for item in self.items:
            try: self.canvas.itemconfig(item, state=state)
            except: pass

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro 2026 - Refined Edition")
        self.root.geometry("1300x850")

        # Application State
        self.current_color = "#000000"
        self.current_tool = "pen"
        self.undo_stack = deque(maxlen=25)
        self.current_action_group = [] 
        
        # Tools & Settings
        self.pen_width = tk.IntVar(value=3)
        self.opacity = tk.DoubleVar(value=1.0)
        self.font_size = tk.IntVar(value=16)
        self.font_family = tk.StringVar(value="Arial")
        
        self.setup_ui()
        
        # Layer System
        self.layers = [Layer("Background", self.canvas), Layer("Main", self.canvas), Layer("Top", self.canvas)]
        self.active_layer_idx = 1 # Default to Main
        
        # Internal State for Drawing
        self.start_x = self.start_y = None
        self.last_x = self.last_y = None
        self.temp_item = None

    def setup_ui(self):
        # --- Top Toolbar ---
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=60, pady=5)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="↶ Undo", bg="#e67e22", fg="white", command=self.undo).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="🗑 Clear", bg="#e74c3c", fg="white", command=self.clear_canvas).pack(side=tk.LEFT)

        self.status_label = tk.Label(top_bar, text="Tool: Pen | Color: #000000", bg="#2c3e50", fg="white", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # --- Sidebar ---
        sidebar = tk.Frame(self.root, bg="#34495e", width=200, padx=10, pady=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Tools Section
        tk.Label(sidebar, text="TOOLS", bg="#34495e", fg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0,5))
        for t in [("✏ Pen", "pen"), ("🧽 Eraser", "eraser"), ("💨 Spray", "spray"), ("🔤 Text", "text")]:
            tk.Button(sidebar, text=t[0], bg="#2c3e50", fg="white", command=lambda v=t[1]: self.set_tool(v)).pack(fill=tk.X, pady=2)

        # Shapes
        tk.Label(sidebar, text="SHAPES", bg="#34495e", fg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(15,5))
        for s in [("Rect", "rect"), ("Circle", "circle"), ("Star", "star")]:
            tk.Button(sidebar, text=s[0], bg="#2c3e50", fg="white", command=lambda v=s[1]: self.set_tool(v)).pack(fill=tk.X, pady=2)

        # Size Slider
        tk.Label(sidebar, text="SIZE", bg="#34495e", fg="#ecf0f1").pack(anchor="w", pady=(15,0))
        tk.Scale(sidebar, variable=self.pen_width, from_=1, to=50, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0).pack(fill=tk.X)

        # Color
        tk.Label(sidebar, text="COLOR", bg="#34495e", fg="#ecf0f1").pack(anchor="w", pady=(15,5))
        self.color_btn = tk.Button(sidebar, text="Pick Color", bg="black", fg="white", command=self.open_color_picker)
        self.color_btn.pack(fill=tk.X)

        # --- Canvas Area ---
        self.canvas = tk.Canvas(self.root, bg="white", cursor="crosshair", relief="flat")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def set_tool(self, tool):
        self.current_tool = tool
        self.update_status()

    def update_status(self):
        self.status_label.config(text=f"Tool: {self.current_tool.capitalize()} | Color: {self.current_color}")

    def open_color_picker(self):
        GradientPicker(self.root, self.set_color)

    def set_color(self, color):
        self.current_color = color
        self.color_btn.config(bg=color)
        self.update_status()

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.last_x, self.last_y = event.x, event.y
        self.current_action_group = [] # Clear for new stroke
        
        if self.current_tool == "text":
            self.place_text(event)

    def on_drag(self, event):
        w = self.pen_width.get()
        
        if self.current_tool == "pen":
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                          fill=self.current_color, width=w, capstyle=tk.ROUND, smooth=True)
            self.current_action_group.append(item)
            self.layers[self.active_layer_idx].add_item(item)
            self.last_x, self.last_y = event.x, event.y
            
        elif self.current_tool == "eraser":
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                          fill="white", width=w*2, capstyle=tk.ROUND)
            self.current_action_group.append(item)
            self.layers[self.active_layer_idx].add_item(item)
            self.last_x, self.last_y = event.x, event.y

        elif self.current_tool in ["rect", "circle"]:
            if self.temp_item: self.canvas.delete(self.temp_item)
            if self.current_tool == "rect":
                self.temp_item = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline=self.current_color, width=w)
            else:
                self.temp_item = self.canvas.create_oval(self.start_x, self.start_y, event.x, event.y, outline=self.current_color, width=w)

    def on_release(self, event):
        if self.temp_item:
            self.current_action_group.append(self.temp_item)
            self.layers[self.active_layer_idx].add_item(self.temp_item)
            self.temp_item = None
        
        if self.current_action_group:
            self.undo_stack.append(list(self.current_action_group))

    def place_text(self, event):
        text_str = simpledialog.askstring("Text Tool", "Enter text:", parent=self.root)
        if text_str:
            item = self.canvas.create_text(event.x, event.y, text=text_str, fill=self.current_color,
                                          font=(self.font_family.get(), self.font_size.get()), anchor=tk.NW)
            self.undo_stack.append([item])
            self.layers[self.active_layer_idx].add_item(item)

    def undo(self):
        if self.undo_stack:
            last_group = self.undo_stack.pop()
            for item in last_group:
                self.canvas.delete(item)

    def clear_canvas(self):
        if messagebox.askyesno("Clear All", "Are you sure you want to clear the canvas?"):
            self.canvas.delete("all")
            self.undo_stack.clear()

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()