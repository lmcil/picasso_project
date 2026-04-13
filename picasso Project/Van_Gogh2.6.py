import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
import json
from collections import deque

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro 2026 - Layer Master")
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
        self.layers = [] 
        self.active_layer_idx = 0
        
        self.setup_ui()
        # Initialize with one base layer
        self.add_new_layer("Base Layer")

    def setup_ui(self):
        # --- Top Toolbar ---
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=50)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="💾 Save", command=self.save_project).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="📂 Load", command=self.load_project).pack(side=tk.LEFT)
        tk.Button(top_bar, text="↶ Undo", bg="#e67e22", fg="white", command=self.undo).pack(side=tk.LEFT, padx=20)

        self.status_label = tk.Label(top_bar, text="Tool: Pen", bg="#2c3e50", fg="white", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # --- Sidebar ---
        sidebar = tk.Frame(self.root, bg="#34495e", width=240, padx=10, pady=10)
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

        # --- NEW LAYER CONTROLS ---
        tk.Label(sidebar, text="LAYERS", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,5))
        
        # Layer Action Buttons
        layer_ctrl_frame = tk.Frame(sidebar, bg="#34495e")
        layer_ctrl_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(layer_ctrl_frame, text="➕ Add", bg="#27ae60", fg="white", font=("Arial", 8, "bold"), 
                  command=self.add_new_layer).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        tk.Button(layer_ctrl_frame, text="🗑 Delete", bg="#c0392b", fg="white", font=("Arial", 8, "bold"), 
                  command=self.delete_active_layer).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Layer List Container
        self.layer_ui_frame = tk.Frame(sidebar, bg="#2c3e50")
        self.layer_ui_frame.pack(fill=tk.BOTH, expand=True)

        # --- Canvas ---
        self.canvas = tk.Canvas(self.root, bg="white", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

    # --- Layer Operations ---
    def add_new_layer(self, name=None):
        if not name:
            name = f"Layer {len(self.layers) + 1}"
        
        new_layer = {"name": name, "items": [], "visible": True}
        # Add to the top of the stack (logical end)
        self.layers.append(new_layer)
        self.active_layer_idx = len(self.layers) - 1
        self.refresh_layer_ui()

    def delete_active_layer(self):
        if len(self.layers) <= 1:
            messagebox.showwarning("Layer Error", "Cannot delete the last remaining layer.")
            return
        
        if messagebox.askyesno("Delete Layer", f"Permanently delete '{self.layers[self.active_layer_idx]['name']}' and all its contents?"):
            # Delete all items on this layer from the canvas
            for item in self.layers[self.active_layer_idx]["items"]:
                self.canvas.delete(item)
            
            # Remove from list
            self.layers.pop(self.active_layer_idx)
            
            # Adjust active index so it's not out of bounds
            if self.active_layer_idx >= len(self.layers):
                self.active_layer_idx = len(self.layers) - 1
            
            self.refresh_layer_ui()

    def refresh_layer_ui(self):
        for widget in self.layer_ui_frame.winfo_children():
            widget.destroy()
        
        # Display reverse order (Top layer visually at top)
        for i in range(len(self.layers)-1, -1, -1):
            layer = self.layers[i]
            is_active = (i == self.active_layer_idx)
            bg = "#3498db" if is_active else "#34495e"
            
            f = tk.Frame(self.layer_ui_frame, bg=bg, pady=2)
            f.pack(fill=tk.X, pady=1)
            
            # Selection label
            lbl = tk.Label(f, text=layer["name"], bg=bg, fg="white", width=16, anchor="w", font=("Arial", 9))
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_layer(idx))
            
            # Visibility toggle
            v_icon = "👁" if layer["visible"] else "✖"
            tk.Button(f, text=v_icon, width=2, font=("Arial", 7), bg="#2c3e50", fg="white",
                      command=lambda idx=i: self.toggle_visibility(idx)).pack(side=tk.RIGHT, padx=2)

    def select_layer(self, idx):
        self.active_layer_idx = idx
        self.refresh_layer_ui()
        self.status_label.config(text=f"Tool: {self.current_tool.capitalize()} | Active: {self.layers[idx]['name']}")

    def toggle_visibility(self, idx):
        self.layers[idx]["visible"] = not self.layers[idx]["visible"]
        state = "normal" if self.layers[idx]["visible"] else "hidden"
        for item in self.layers[idx]["items"]:
            self.canvas.itemconfig(item, state=state)
        self.refresh_layer_ui()

    # --- Tool Logic ---
    def on_press(self, event):
        self.last_x, self.last_y = event.x, event.y
        if not self.layers[self.active_layer_idx]["visible"]:
            return # Don't draw on hidden layers
            
        if self.current_tool == "text":
            self.open_text_editor(event.x, event.y)
        elif self.current_tool == "fill":
            self.apply_fill()

    def on_drag(self, event):
        if not self.layers[self.active_layer_idx]["visible"]:
            return
            
        if self.current_tool in ["pen", "eraser"]:
            color = self.current_color if self.current_tool == "pen" else "white"
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                          fill=color, width=self.pen_width.get(), 
                                          capstyle=tk.ROUND, smooth=True)
            self.register_item(item)
            self.last_x, self.last_y = event.x, event.y

    def apply_fill(self):
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        item = self.canvas.create_rectangle(-5, -5, w+5, h+5, fill=self.current_color, outline="")
        self.register_item(item)
        self.canvas.tag_lower(item)

    def register_item(self, item):
        self.layers[self.active_layer_idx]["items"].append(item)
        self.undo_stack.append(item)
        
        # Enforce Z-Index: ensure items in higher layers stay on top
        for i in range(len(self.layers)):
            for layer_item in self.layers[i]["items"]:
                self.canvas.tag_raise(layer_item)

    def open_text_editor(self, x, y):
        msg = simpledialog.askstring("Text Tool", "Enter text:")
        if msg:
            item = self.canvas.create_text(x, y, text=msg, fill=self.current_color,
                                          font=(self.font_family.get(), self.font_size.get()), anchor=tk.NW)
            self.register_item(item)

    # --- Utilities ---
    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.current_color = color
            self.color_btn.config(bg=color)

    def set_tool(self, tool):
        self.current_tool = tool
        self.select_layer(self.active_layer_idx)

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
            data = [{"name": l["name"], "visible": l["visible"], "items": []} for l in self.layers]
            with open(path, "w") as f: json.dump(data, f)

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Project", "*.json")])
        if path:
            self.canvas.delete("all")
            self.layers = []
            self.add_new_layer("Loaded Project")

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()