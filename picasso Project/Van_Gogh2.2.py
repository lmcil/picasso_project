import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from PIL import Image, ImageDraw, ImageTk
import random
import math
import json
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
        
        self.img = tk.PhotoImage(width=self.canvas_w, height=self.canvas_h)
        self.gradient_canvas.create_image((self.canvas_w//2, self.canvas_h//2), image=self.img)
        self.draw_gradient_fast()
        
        self.gradient_canvas.bind("<Button-1>", self.pick_color)
        
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
        pixels = ""
        for y in range(self.canvas_h):
            row = "{"
            for x in range(self.canvas_w):
                h = x / self.canvas_w
                s = 1.0 - (y / self.canvas_h)
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

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro 2026 - Ultra Edition")
        self.root.geometry("1400x900")

        # Application State
        self.current_color = "#000000"
        self.current_tool = "pen"
        self.undo_stack = deque(maxlen=25)
        self.current_action_group = [] 
        
        # Tools & Settings
        self.pen_width = tk.IntVar(value=3)
        self.font_size = tk.IntVar(value=18)
        self.font_family = tk.StringVar(value="Arial")
        
        # Layer System
        self.layers = []
        self.active_layer_idx = 0
        
        self.setup_ui()
        self.add_layer("Base Layer") # Initial Layer

    def setup_ui(self):
        # --- Top Toolbar ---
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=60, pady=5)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="💾 Save Project", bg="#3498db", fg="white", command=self.save_project).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="📂 Load Project", bg="#3498db", fg="white", command=self.load_project).pack(side=tk.LEFT)
        tk.Button(top_bar, text="↶ Undo", bg="#e67e22", fg="white", command=self.undo).pack(side=tk.LEFT, padx=20)
        tk.Button(top_bar, text="🗑 Clear", bg="#e74c3c", fg="white", command=self.clear_canvas).pack(side=tk.LEFT)

        self.status_label = tk.Label(top_bar, text="Tool: Pen | Layer: Base", bg="#2c3e50", fg="white", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # --- Sidebar ---
        sidebar = tk.Frame(self.root, bg="#34495e", width=220, padx=10, pady=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Tools Section
        tk.Label(sidebar, text="TOOLS", bg="#34495e", fg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(0,5))
        for text, mode in [("✏ Pen", "pen"), ("🧽 Eraser", "eraser"), ("🪣 Fill", "fill"), ("🔤 Text", "text")]:
            tk.Button(sidebar, text=text, bg="#2c3e50", fg="white", command=lambda v=mode: self.set_tool(v)).pack(fill=tk.X, pady=2)

        # Size Slider
        tk.Label(sidebar, text="SIZE", bg="#34495e", fg="#ecf0f1").pack(anchor="w", pady=(15,0))
        tk.Scale(sidebar, variable=self.pen_width, from_=1, to=100, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0).pack(fill=tk.X)

        # Color
        tk.Label(sidebar, text="COLOR", bg="#34495e", fg="#ecf0f1").pack(anchor="w", pady=(15,5))
        self.color_btn = tk.Button(sidebar, text="Pick Color", bg="black", fg="white", command=self.open_color_picker)
        self.color_btn.pack(fill=tk.X)

        # Layer Manager UI
        tk.Label(sidebar, text="LAYERS", bg="#34495e", fg="#ecf0f1", font=("Arial", 9, "bold")).pack(anchor="w", pady=(20,5))
        self.layer_list_frame = tk.Frame(sidebar, bg="#2c3e50")
        self.layer_list_frame.pack(fill=tk.BOTH, expand=True)
        tk.Button(sidebar, text="+ Add New Layer", bg="#27ae60", fg="white", command=lambda: self.add_layer()).pack(fill=tk.X, pady=5)

        # --- Canvas Area ---
        self.canvas = tk.Canvas(self.root, bg="white", cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    # --- Layer Features ---
    def add_layer(self, name=None):
        if not name:
            name = f"Layer {len(self.layers) + 1}"
        new_layer = Layer(name, self.canvas)
        self.layers.append(new_layer)
        self.active_layer_idx = len(self.layers) - 1
        self.refresh_layer_ui()

    def refresh_layer_ui(self):
        for widget in self.layer_list_frame.winfo_children():
            widget.destroy()
        
        # Display layers (Top layer at top of UI)
        for i in range(len(self.layers)-1, -1, -1):
            layer = self.layers[i]
            color = "#3498db" if i == self.active_layer_idx else "#34495e"
            frame = tk.Frame(self.layer_list_frame, bg=color, pady=2)
            frame.pack(fill=tk.X, pady=1)
            
            lbl = tk.Label(frame, text=layer.name, bg=color, fg="white", font=("Arial", 8))
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_layer(idx))
            
            vis_btn = tk.Button(frame, text="👁" if layer.visible else "❌", width=2, 
                                command=lambda idx=i: self.toggle_visibility(idx))
            vis_btn.pack(side=tk.RIGHT, padx=2)

    def select_layer(self, idx):
        self.active_layer_idx = idx
        self.refresh_layer_ui()
        self.update_status()

    def toggle_visibility(self, idx):
        self.layers[idx].visible = not self.layers[idx].visible
        state = "normal" if self.layers[idx].visible else "hidden"
        for item in self.layers[idx].items:
            self.canvas.itemconfig(item, state=state)
        self.refresh_layer_ui()

    # --- Tool Implementations ---
    def set_tool(self, tool):
        self.current_tool = tool
        self.update_status()

    def update_status(self):
        layer_name = self.layers[self.active_layer_idx].name if self.layers else "N/A"
        self.status_label.config(text=f"Tool: {self.current_tool.capitalize()} | Layer: {layer_name}")

    def on_press(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.current_action_group = []
        
        if self.current_tool == "text":
            self.open_text_editor(event.x, event.y)
        elif self.current_tool == "fill":
            self.flood_fill(event.x, event.y)

    def on_drag(self, event):
        if self.current_tool in ["pen", "eraser"]:
            color = self.current_color if self.current_tool == "pen" else "white"
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                          fill=color, width=self.pen_width.get(), 
                                          capstyle=tk.ROUND, smooth=True)
            self.current_action_group.append(item)
            self.layers[self.active_layer_idx].add_item(item)
            self.last_x, self.last_y = event.x, event.y

    def on_release(self, event):
        if self.current_action_group:
            self.undo_stack.append(list(self.current_action_group))

    def flood_fill(self, x, y):
        # Simple Canvas Fill: Creates a background rectangle for the current layer
        # Pro tip: True pixel-fill requires PIL, but for vector canvas, this is the standard "background fill"
        item = self.canvas.create_rectangle(-10, -10, self.canvas.winfo_width()+10, self.canvas.winfo_height()+10, 
                                            fill=self.current_color, outline="")
        self.canvas.tag_lower(item) # Send to back of current stack
        self.layers[self.active_layer_idx].add_item(item)
        self.undo_stack.append([item])

    def open_text_editor(self, x, y):
        text_win = tk.Toplevel(self.root)
        text_win.title("Text Settings")
        text_win.geometry("300x200")
        
        tk.Label(text_win, text="Text Content:").pack(pady=5)
        text_entry = tk.Entry(text_win, width=30)
        text_entry.pack()
        text_entry.focus_set()

        tk.Label(text_win, text="Size:").pack(pady=5)
        size_spin = tk.Spinbox(text_win, from_=8, to=200, textvariable=self.font_size)
        size_spin.pack()

        def apply():
            content = text_entry.get()
            if content:
                item = self.canvas.create_text(x, y, text=content, fill=self.current_color,
                                              font=(self.font_family.get(), self.font_size.get()), anchor=tk.NW)
                self.layers[self.active_layer_idx].add_item(item)
                self.undo_stack.append([item])
                text_win.destroy()

        tk.Button(text_win, text="Place Text", command=apply, bg="#27ae60", fg="white").pack(pady=20)

    # --- Save and Load Features ---
    def save_project(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Project", "*.json")])
        if not file_path: return
        
        project_data = []
        for layer in self.layers:
            layer_items = []
            for item in layer.items:
                item_type = self.canvas.type(item)
                opts = {k: self.canvas.itemcget(item, k) for k in ["fill", "width", "text", "font"] if k in self.canvas.itemconfig(item)}
                layer_items.append({
                    "type": item_type,
                    "coords": self.canvas.coords(item),
                    "options": opts
                })
            project_data.append({"name": layer.name, "visible": layer.visible, "items": layer_items})
        
        with open(file_path, "w") as f:
            json.dump(project_data, f)
        messagebox.showinfo("Success", "Project saved successfully!")

    def load_project(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Project", "*.json")])
        if not file_path: return
        
        self.canvas.delete("all")
        self.layers = []
        self.undo_stack.clear()
        
        with open(file_path, "r") as f:
            data = json.load(f)
            
        for layer_data in data:
            new_layer = Layer(layer_data["name"], self.canvas)
            new_layer.visible = layer_data["visible"]
            for item in layer_data["items"]:
                if item["type"] == "line":
                    obj = self.canvas.create_line(item["coords"], **item["options"])
                elif item["type"] == "text":
                    obj = self.canvas.create_text(item["coords"], **item["options"])
                elif item["type"] == "rectangle":
                    obj = self.canvas.create_rectangle(item["coords"], **item["options"])
                new_layer.add_item(obj)
            self.layers.append(new_layer)
        
        self.active_layer_idx = 0
        self.refresh_layer_ui()

    def open_color_picker(self):
        GradientPicker(self.root, self.set_color)

    def set_color(self, color):
        self.current_color = color
        self.color_btn.config(bg=color)

    def undo(self):
        if self.undo_stack:
            last_group = self.undo_stack.pop()
            for item in last_group:
                self.canvas.delete(item)
                # Remove from layer tracking too
                for layer in self.layers:
                    if item in layer.items:
                        layer.items.remove(item)

    def clear_canvas(self):
        if messagebox.askyesno("Clear All", "Are you sure? This deletes all layers!"):
            self.canvas.delete("all")
            self.layers = []
            self.add_layer("Base Layer")
            self.undo_stack.clear()

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()