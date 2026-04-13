import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
import json
from collections import deque

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro 2026 - Ultra Edition")
        self.root.geometry("1400x900")

        # Application State
        self.current_color = "#000000"
        self.current_tool = "pen"
        self.undo_stack = deque(maxlen=30)
        
        # Tools & Settings
        self.pen_width = tk.IntVar(value=3)
        self.global_opacity = tk.DoubleVar(value=1.0) # 0.0 to 1.0
        self.font_size = tk.IntVar(value=18)
        
        # Layer System
        self.layers = [] # List of dicts: {"name": str, "items": [], "visible": bool}
        self.active_layer_idx = 0
        
        self.setup_ui()
        self.add_layer("Background") # Bottom Layer
        self.add_layer("Sketch")     # Working Layer

    def setup_ui(self):
        # --- Top Toolbar ---
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=50)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="💾 Save", command=self.save_project).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="📂 Load", command=self.load_project).pack(side=tk.LEFT)
        tk.Button(top_bar, text="↶ Undo", bg="#e67e22", fg="white", command=self.undo).pack(side=tk.LEFT, padx=20)

        self.status_label = tk.Label(top_bar, text="Tool: Pen | Layer: Sketch", bg="#2c3e50", fg="white")
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # --- Sidebar ---
        sidebar = tk.Frame(self.root, bg="#34495e", width=220, padx=10, pady=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Tool Buttons
        tk.Label(sidebar, text="TOOLS", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        for text, mode in [("✏ Pen", "pen"), ("🧽 Eraser", "eraser"), ("🪣 Fill", "fill"), ("🔤 Text", "text")]:
            tk.Button(sidebar, text=text, bg="#2c3e50", fg="white", command=lambda v=mode: self.set_tool(v)).pack(fill=tk.X, pady=2)

        # Size Slider
        tk.Label(sidebar, text="BRUSH SIZE", bg="#34495e", fg="white").pack(anchor="w", pady=(15,0))
        tk.Scale(sidebar, variable=self.pen_width, from_=1, to=100, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0).pack(fill=tk.X)

        # Opacity Slider (The Requested Feature)
        tk.Label(sidebar, text="OPACITY", bg="#34495e", fg="white").pack(anchor="w", pady=(15,0))
        tk.Scale(sidebar, variable=self.global_opacity, from_=0.0, to=1.0, resolution=0.1, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0).pack(fill=tk.X)

        # Color
        tk.Label(sidebar, text="COLOR", bg="#34495e", fg="white").pack(anchor="w", pady=(15,5))
        self.color_btn = tk.Button(sidebar, text="Pick Color", bg="black", fg="white", command=self.pick_color)
        self.color_btn.pack(fill=tk.X)

        # Layer Manager
        tk.Label(sidebar, text="LAYER STACK", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w", pady=(20,5))
        self.layer_ui_frame = tk.Frame(sidebar, bg="#2c3e50")
        self.layer_ui_frame.pack(fill=tk.BOTH, expand=True)
        tk.Button(sidebar, text="+ New Layer", bg="#27ae60", fg="white", command=self.add_layer).pack(fill=tk.X, pady=5)

        # --- Canvas ---
        self.canvas = tk.Canvas(self.root, bg="white", cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

    # --- Layer Logic Fixes ---
    def add_layer(self, name=None):
        if not name:
            name = f"Layer {len(self.layers)}"
        
        # New layers are logically added to the TOP of the stack (index end)
        new_layer = {"name": name, "items": [], "visible": True}
        self.layers.append(new_layer)
        self.active_layer_idx = len(self.layers) - 1
        self.refresh_layer_ui()

    def refresh_layer_ui(self):
        for w in self.layer_ui_frame.winfo_children(): w.destroy()
        
        # Display layers in reverse (Top of stack visually at top of UI)
        for i in range(len(self.layers)-1, -1, -1):
            layer = self.layers[i]
            is_active = (i == self.active_layer_idx)
            bg = "#3498db" if is_active else "#34495e"
            
            f = tk.Frame(self.layer_ui_frame, bg=bg, pady=2)
            f.pack(fill=tk.X, pady=1)
            
            # Clickable name to select layer
            lbl = tk.Label(f, text=layer["name"], bg=bg, fg="white", width=12, anchor="w")
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_layer(idx))
            
            # Visibility toggle
            v_text = "👁" if layer["visible"] else "✖"
            tk.Button(f, text=v_text, width=2, font=("Arial", 7),
                      command=lambda idx=i: self.toggle_layer(idx)).pack(side=tk.RIGHT, padx=2)

    def select_layer(self, idx):
        self.active_layer_idx = idx
        self.refresh_layer_ui()
        self.status_label.config(text=f"Tool: {self.current_tool.capitalize()} | Layer: {self.layers[idx]['name']}")

    def toggle_layer(self, idx):
        self.layers[idx]["visible"] = not self.layers[idx]["visible"]
        state = "normal" if self.layers[idx]["visible"] else "hidden"
        for item in self.layers[idx]["items"]:
            self.canvas.itemconfig(item, state=state)
        self.refresh_layer_ui()

    # --- Tool Logic ---
    def on_press(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.current_stroke = []
        
        if self.current_tool == "fill":
            self.apply_fill()
        elif self.current_tool == "text":
            self.place_text(event.x, event.y)

    def on_drag(self, event):
        if self.current_tool in ["pen", "eraser"]:
            color = self.current_color if self.current_tool == "pen" else "white"
            # Opacity workaround: standard lines don't support alpha, 
            # so we use thin width variation or simulated layers if needed.
            # For this version, opacity primarily affects the 'Fill' and 'Shapes'.
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                          fill=color, width=self.pen_width.get(),
                                          capstyle=tk.ROUND, smooth=True)
            self.register_item(item)
            self.last_x, self.last_y = event.x, event.y

    def apply_fill(self):
        # Opacity applied via stipple patterns or color blending
        # Here we use a standard fill, but register it to the layer
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        # To simulate opacity on fill, we use the "stipple" built-in feature
        stipple_val = ""
        if self.global_opacity.get() < 0.3: stipple_val = "gray12"
        elif self.global_opacity.get() < 0.6: stipple_val = "gray50"
        elif self.global_opacity.get() < 0.9: stipple_val = "gray75"
        
        item = self.canvas.create_rectangle(0, 0, w, h, fill=self.current_color, outline="", stipple=stipple_val)
        self.register_item(item)
        self.canvas.tag_lower(item) # Background style fill

    def register_item(self, item):
        """Adds item to active layer and manages stack order."""
        self.layers[self.active_layer_idx]["items"].append(item)
        self.undo_stack.append(item)
        
        # Fix Layer Ordering: Ensure items in higher layers are always raised above lower ones
        for i in range(len(self.layers)):
            for layer_item in self.layers[i]["items"]:
                self.canvas.tag_raise(layer_item)

    # --- Standard Utils ---
    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.current_color = color
            self.color_btn.config(bg=color)

    def set_tool(self, tool):
        self.current_tool = tool
        self.select_layer(self.active_layer_idx)

    def place_text(self, x, y):
        msg = simpledialog.askstring("Text", "Enter text:")
        if msg:
            item = self.canvas.create_text(x, y, text=msg, fill=self.current_color, font=("Arial", self.font_size.get()))
            self.register_item(item)

    def undo(self):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.canvas.delete(item)
            for layer in self.layers:
                if item in layer["items"]:
                    layer["items"].remove(item)

    def save_project(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            data = []
            for layer in self.layers:
                data.append({"name": layer["name"], "visible": layer["visible"], 
                             "items": [self.canvas.coords(i) for i in layer["items"]]})
            with open(path, "w") as f: json.dump(data, f)

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.canvas.delete("all")
            with open(path, "r") as f: data = json.load(f)
            self.layers = []
            for l_data in data:
                new_l = {"name": l_data["name"], "items": [], "visible": l_data["visible"]}
                for coords in l_data["items"]:
                    # Basic reconstruction
                    it = self.canvas.create_line(coords, fill="black")
                    new_l["items"].append(it)
                self.layers.append(new_l)
            self.refresh_layer_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()