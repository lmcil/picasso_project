import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
import json
from collections import deque

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro 2026 - High Performance")
        self.root.geometry("1400x900")

        # --- Application State ---
        self.current_color = "#000000"
        self.current_tool = "pen"
        self.undo_stack = deque(maxlen=50)
        
        # Tools & Settings
        self.pen_width = tk.IntVar(value=3)
        self.font_size = tk.IntVar(value=18)
        self.font_family = tk.StringVar(value="Arial")
        
        # Layer System
        self.layers = [] # List of dicts: {"name": str, "items": [], "visible": bool}
        self.active_layer_idx = 0
        
        self.setup_ui()
        # Create default layers
        self.add_layer("Background")
        self.add_layer("Layer 1")

    def setup_ui(self):
        # --- Top Toolbar ---
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=50)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="💾 Save Project", command=self.save_project).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="📂 Load Project", command=self.load_project).pack(side=tk.LEFT)
        tk.Button(top_bar, text="↶ Undo", bg="#e67e22", fg="white", command=self.undo).pack(side=tk.LEFT, padx=20)
        tk.Button(top_bar, text="🗑 Clear All", bg="#e74c3c", fg="white", command=self.clear_all).pack(side=tk.LEFT)

        self.status_label = tk.Label(top_bar, text="Tool: Pen | Layer: Layer 1", bg="#2c3e50", fg="white", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # --- Sidebar ---
        sidebar = tk.Frame(self.root, bg="#34495e", width=220, padx=10, pady=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Tools
        tk.Label(sidebar, text="TOOLS", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        for text, mode in [("✏ Pen", "pen"), ("🧽 Eraser", "eraser"), ("🪣 Fill", "fill"), ("🔤 Text", "text")]:
            tk.Button(sidebar, text=text, bg="#2c3e50", fg="white", command=lambda v=mode: self.set_tool(v)).pack(fill=tk.X, pady=2)

        # Settings
        tk.Label(sidebar, text="BRUSH SIZE", bg="#34495e", fg="white").pack(anchor="w", pady=(15,0))
        tk.Scale(sidebar, variable=self.pen_width, from_=1, to=100, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0).pack(fill=tk.X)

        self.color_btn = tk.Button(sidebar, text="Pick Color", bg="black", fg="white", height=2, command=self.pick_color)
        self.color_btn.pack(fill=tk.X, pady=20)

        # Layer Stack UI
        tk.Label(sidebar, text="LAYER STACK", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,5))
        self.layer_ui_frame = tk.Frame(sidebar, bg="#2c3e50")
        self.layer_ui_frame.pack(fill=tk.BOTH, expand=True)
        tk.Button(sidebar, text="+ New Layer", bg="#27ae60", fg="white", command=self.add_layer).pack(fill=tk.X, pady=5)

        # --- Canvas ---
        self.canvas = tk.Canvas(self.root, bg="white", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

    # --- Layer Management ---
    def add_layer(self, name=None):
        if not name:
            name = f"Layer {len(self.layers)}"
        new_layer = {"name": name, "items": [], "visible": True}
        self.layers.append(new_layer)
        self.active_layer_idx = len(self.layers) - 1
        self.refresh_layer_ui()

    def refresh_layer_ui(self):
        for widget in self.layer_ui_frame.winfo_children():
            widget.destroy()
        
        # Display layers in visual order (Top index at top of UI)
        for i in range(len(self.layers)-1, -1, -1):
            layer = self.layers[i]
            is_active = (i == self.active_layer_idx)
            bg = "#3498db" if is_active else "#34495e"
            
            f = tk.Frame(self.layer_ui_frame, bg=bg, pady=2)
            f.pack(fill=tk.X, pady=1)
            
            lbl = tk.Label(f, text=layer["name"], bg=bg, fg="white", width=12, anchor="w")
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_layer(idx))
            
            v_btn = tk.Button(f, text="👁" if layer["visible"] else "✖", width=2, font=("Arial", 7),
                              command=lambda idx=i: self.toggle_visibility(idx))
            v_btn.pack(side=tk.RIGHT, padx=2)

    def select_layer(self, idx):
        self.active_layer_idx = idx
        self.refresh_layer_ui()
        self.status_label.config(text=f"Tool: {self.current_tool.capitalize()} | Layer: {self.layers[idx]['name']}")

    def toggle_visibility(self, idx):
        self.layers[idx]["visible"] = not self.layers[idx]["visible"]
        state = "normal" if self.layers[idx]["visible"] else "hidden"
        for item in self.layers[idx]["items"]:
            self.canvas.itemconfig(item, state=state)
        self.refresh_layer_ui()

    # --- Tool Logic ---
    def on_press(self, event):
        self.last_x, self.last_y = event.x, event.y
        if self.current_tool == "text":
            self.open_text_editor(event.x, event.y)
        elif self.current_tool == "fill":
            self.apply_fill()

    def on_drag(self, event):
        if self.current_tool in ["pen", "eraser"]:
            color = self.current_color if self.current_tool == "pen" else "white"
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                          fill=color, width=self.pen_width.get(), 
                                          capstyle=tk.ROUND, smooth=True)
            self.register_item(item)
            self.last_x, self.last_y = event.x, event.y

    def apply_fill(self):
        # High-performance rectangle fill for active layer
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        item = self.canvas.create_rectangle(-5, -5, w+5, h+5, fill=self.current_color, outline="")
        self.register_item(item)
        # We ensure the fill stays at the bottom of its specific layer
        self.canvas.tag_lower(item)

    def register_item(self, item):
        """Adds item to layer and maintains the visual stack order."""
        self.layers[self.active_layer_idx]["items"].append(item)
        self.undo_stack.append(item)
        
        # Enforce Z-Index: ensure items in higher layers are always above lower ones
        for i in range(len(self.layers)):
            for layer_item in self.layers[i]["items"]:
                self.canvas.tag_raise(layer_item)

    def open_text_editor(self, x, y):
        text_win = tk.Toplevel(self.root)
        text_win.title("Text Editor")
        tk.Label(text_win, text="Content:").pack(pady=5)
        entry = tk.Entry(text_win, width=30)
        entry.pack(padx=10)
        entry.focus_set()

        def apply():
            txt = entry.get()
            if txt:
                item = self.canvas.create_text(x, y, text=txt, fill=self.current_color,
                                              font=(self.font_family.get(), self.font_size.get()), anchor=tk.NW)
                self.register_item(item)
                text_win.destroy()
        
        tk.Button(text_win, text="Place", command=apply).pack(pady=10)

    # --- Persistence & Utilities ---
    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.current_color = color
            self.color_btn.config(bg=color)

    def set_tool(self, tool):
        self.current_tool = tool
        self.refresh_layer_ui()

    def undo(self):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.canvas.delete(item)
            for layer in self.layers:
                if item in layer["items"]:
                    layer["items"].remove(item)

    def clear_all(self):
        if messagebox.askyesno("Clear All", "Delete all layers and start over?"):
            self.canvas.delete("all")
            self.layers = []
            self.undo_stack.clear()
            self.add_layer("Background")
            self.add_layer("Layer 1")

    def save_project(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            data = []
            for layer in self.layers:
                layer_items = []
                for item in layer["items"]:
                    layer_items.append({
                        "type": self.canvas.type(item),
                        "coords": self.canvas.coords(item),
                        "options": {k: self.canvas.itemcget(item, k) for k in ["fill", "width", "text", "font"] if k in self.canvas.itemconfig(item)}
                    })
                data.append({"name": layer["name"], "visible": layer["visible"], "items": layer_items})
            with open(path, "w") as f:
                json.dump(data, f)

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Project", "*.json")])
        if path:
            self.canvas.delete("all")
            self.layers = []
            with open(path, "r") as f:
                data = json.load(f)
            for l_data in data:
                new_layer = {"name": l_data["name"], "items": [], "visible": l_data["visible"]}
                for item in l_data["items"]:
                    if item["type"] == "line":
                        obj = self.canvas.create_line(item["coords"], **item["options"])
                    elif item["type"] == "text":
                        obj = self.canvas.create_text(item["coords"], **item["options"])
                    elif item["type"] == "rectangle":
                        obj = self.canvas.create_rectangle(item["coords"], **item["options"])
                    new_layer["items"].append(obj)
                self.layers.append(new_layer)
            self.refresh_layer_ui()

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()