import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
import json
from collections import deque

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro 2026 - Streamlined Layers")
        self.root.geometry("1400x900")

        # --- Application State ---
        self.current_color = "#000000"
        self.current_tool = "pen"
        self.undo_stack = deque(maxlen=50)
        
        # Layer System
        self.layers = [] 
        self.active_layer_idx = 0
        
        self.setup_ui()
        # Initialize with one base layer
        self.add_new_layer("Background")

    def setup_ui(self):
        # --- Top Toolbar ---
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=50)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="💾 Save Project", command=self.save_project).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="📂 Load Project", command=self.load_project).pack(side=tk.LEFT)
        tk.Button(top_bar, text="↶ Undo", bg="#e67e22", fg="white", command=self.undo).pack(side=tk.LEFT, padx=20)

        # --- Sidebar ---
        sidebar = tk.Frame(self.root, bg="#34495e", width=240, padx=10, pady=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Tools
        tk.Label(sidebar, text="TOOLS", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        for text, mode in [("✏ Pen", "pen"), ("🧽 Eraser", "eraser"), ("🪣 Fill", "fill")]:
            tk.Button(sidebar, text=text, bg="#2c3e50", fg="white", command=lambda v=mode: self.set_tool(v)).pack(fill=tk.X, pady=2)

        # Settings
        tk.Label(sidebar, text="BRUSH SIZE", bg="#34495e", fg="white").pack(anchor="w", pady=(15,0))
        self.pen_width = tk.Scale(sidebar, from_=1, to=100, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0)
        self.pen_width.set(3)
        self.pen_width.pack(fill=tk.X)

        self.color_btn = tk.Button(sidebar, text="Pick Color", bg="black", fg="white", height=2, command=self.pick_color)
        self.color_btn.pack(fill=tk.X, pady=20)

        # Layer Controls
        tk.Label(sidebar, text="LAYERS", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,5))
        
        layer_ctrl_frame = tk.Frame(sidebar, bg="#34495e")
        layer_ctrl_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(layer_ctrl_frame, text="➕ Add", bg="#27ae60", fg="white", font=("Arial", 8, "bold"), 
                  command=self.add_new_layer).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        tk.Button(layer_ctrl_frame, text="🗑 Delete", bg="#c0392b", fg="white", font=("Arial", 8, "bold"), 
                  command=self.delete_active_layer).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.layer_ui_frame = tk.Frame(sidebar, bg="#2c3e50")
        self.layer_ui_frame.pack(fill=tk.BOTH, expand=True)

        # --- Canvas ---
        self.canvas = tk.Canvas(self.root, bg="white", cursor="crosshair", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

    # --- Layer Persistence ---
    def save_project(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Paint Project", "*.json")])
        if not path: return
        
        project_data = []
        for layer in self.layers:
            layer_items = []
            for item_id in layer["items"]:
                item_type = self.canvas.type(item_id)
                item_data = {
                    "type": item_type,
                    "coords": self.canvas.coords(item_id),
                    "options": {
                        "fill": self.canvas.itemcget(item_id, "fill"),
                        "width": self.canvas.itemcget(item_id, "width") if item_type == "line" else ""
                    }
                }
                layer_items.append(item_data)
                
            project_data.append({
                "name": layer["name"],
                "visible": layer["visible"],
                "items": layer_items
            })

        with open(path, "w") as f:
            json.dump(project_data, f, indent=4)
        messagebox.showinfo("Success", "Project saved successfully!")

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("Paint Project", "*.json")])
        if not path: return

        try:
            with open(path, "r") as f:
                project_data = json.load(f)
            
            self.canvas.delete("all")
            self.layers = []
            self.undo_stack.clear()

            for layer_data in project_data:
                self.layers.append({"name": layer_data["name"], "items": [], "visible": layer_data["visible"]})
                current_idx = len(self.layers) - 1
                
                for item in layer_data["items"]:
                    new_id = None
                    opts = item["options"]
                    if item["type"] == "line":
                        new_id = self.canvas.create_line(item["coords"], fill=opts["fill"], width=opts["width"], capstyle=tk.ROUND, smooth=True)
                    elif item["type"] == "rectangle":
                        new_id = self.canvas.create_rectangle(item["coords"], fill=opts["fill"], outline="")
                    
                    if new_id:
                        self.layers[current_idx]["items"].append(new_id)
                        if not layer_data["visible"]:
                            self.canvas.itemconfig(new_id, state="hidden")

            self.active_layer_idx = len(self.layers) - 1
            self.refresh_layer_ui()
            self.enforce_z_index()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project: {e}")

    # --- Layer Management ---
    def add_new_layer(self, name=None):
        if not name:
            name = simpledialog.askstring("Layer Name", "Enter layer name:")
        if not name: return
        
        new_layer = {"name": name, "items": [], "visible": True}
        self.layers.append(new_layer)
        self.active_layer_idx = len(self.layers) - 1
        self.refresh_layer_ui()

    def delete_active_layer(self):
        if len(self.layers) <= 1:
            messagebox.showwarning("Layer Error", "Cannot delete the last remaining layer.")
            return
        
        if messagebox.askyesno("Delete Layer", f"Permanently delete '{self.layers[self.active_layer_idx]['name']}'?"):
            for item in self.layers[self.active_layer_idx]["items"]:
                self.canvas.delete(item)
            self.layers.pop(self.active_layer_idx)
            self.active_layer_idx = max(0, self.active_layer_idx - 1)
            self.refresh_layer_ui()

    def refresh_layer_ui(self):
        for widget in self.layer_ui_frame.winfo_children():
            widget.destroy()
        
        for i in range(len(self.layers)-1, -1, -1):
            layer = self.layers[i]
            is_active = (i == self.active_layer_idx)
            bg = "#3498db" if is_active else "#34495e"
            
            f = tk.Frame(self.layer_ui_frame, bg=bg, pady=2)
            f.pack(fill=tk.X, pady=1)
            
            lbl = tk.Label(f, text=layer["name"], bg=bg, fg="white", width=16, anchor="w", font=("Arial", 9))
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_layer(idx))
            lbl.bind("<Double-Button-1>", lambda e, idx=i: self.rename_layer(idx))
            
            v_icon = "👁" if layer["visible"] else "✖"
            tk.Button(f, text=v_icon, width=2, font=("Arial", 7), bg="#2c3e50", fg="white",
                      command=lambda idx=i: self.toggle_visibility(idx)).pack(side=tk.RIGHT, padx=2)

    def rename_layer(self, idx):
        new_name = simpledialog.askstring("Rename", "New layer name:", initialvalue=self.layers[idx]["name"])
        if new_name:
            self.layers[idx]["name"] = new_name
            self.refresh_layer_ui()

    def select_layer(self, idx):
        self.active_layer_idx = idx
        self.refresh_layer_ui()

    def toggle_visibility(self, idx):
        self.layers[idx]["visible"] = not self.layers[idx]["visible"]
        state = "normal" if self.layers[idx]["visible"] else "hidden"
        for item in self.layers[idx]["items"]:
            self.canvas.itemconfig(item, state=state)
        self.refresh_layer_ui()

    # --- Tool Logic ---
    def on_press(self, event):
        self.last_x, self.last_y = event.x, event.y
        if self.current_tool == "fill":
            self.apply_fill()

    def on_drag(self, event):
        if not self.layers[self.active_layer_idx]["visible"]: return
            
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
        self.enforce_z_index()

    def enforce_z_index(self):
        # Keeps items in higher layers visually above lower layers
        for layer in self.layers:
            for item in layer["items"]:
                self.canvas.tag_raise(item)

    # --- Utilities ---
    def pick_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.current_color = color
            self.color_btn.config(bg=color)

    def set_tool(self, tool):
        self.current_tool = tool

    def undo(self):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.canvas.delete(item)
            for layer in self.layers:
                if item in layer["items"]:
                    layer["items"].remove(item)

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()