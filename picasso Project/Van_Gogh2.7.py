import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
from tkinter import ttk
import json
from collections import deque

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro 2026 - Studio Edition")
        self.root.geometry("1500x950")

        # --- State ---
        self.current_color = "#000000"
        self.current_tool = "pen"
        self.selected_text_id = None
        self.undo_stack = deque(maxlen=50)
        
        # Layer System
        self.layers = [] 
        self.active_layer_idx = 0
        
        self.setup_ui()
        self.add_new_layer("Background")

    def setup_ui(self):
        # --- Top Toolbar ---
        top_bar = tk.Frame(self.root, bg="#2c3e50", height=50)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        tk.Button(top_bar, text="💾 Save Project", command=self.save_project).pack(side=tk.LEFT, padx=10)
        tk.Button(top_bar, text="📂 Load Project", command=self.load_project).pack(side=tk.LEFT)
        tk.Button(top_bar, text="↶ Undo", bg="#e67e22", fg="white", command=self.undo).pack(side=tk.LEFT, padx=20)

        # --- Left Sidebar (Tools & Layers) ---
        sidebar = tk.Frame(self.root, bg="#34495e", width=240, padx=10, pady=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="DRAW TOOLS", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w")
        for text, mode in [("✏ Pen", "pen"), ("🧽 Eraser", "eraser"), ("🔤 Text Tool", "text"), ("🪣 Fill", "fill")]:
            tk.Button(sidebar, text=text, bg="#2c3e50", fg="white", command=lambda v=mode: self.set_tool(v)).pack(fill=tk.X, pady=2)

        tk.Label(sidebar, text="BRUSH SIZE", bg="#34495e", fg="white").pack(anchor="w", pady=(10,0))
        self.pen_width = tk.Scale(sidebar, from_=1, to=100, orient=tk.HORIZONTAL, bg="#34495e", fg="white", highlightthickness=0)
        self.pen_width.set(3)
        self.pen_width.pack(fill=tk.X)

        self.color_btn = tk.Button(sidebar, text="Pick Color", bg="black", fg="white", height=2, command=self.pick_color)
        self.color_btn.pack(fill=tk.X, pady=15)

        tk.Label(sidebar, text="LAYERS", bg="#34495e", fg="white", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,5))
        l_btns = tk.Frame(sidebar, bg="#34495e")
        l_btns.pack(fill=tk.X)
        tk.Button(l_btns, text="➕ Add", command=self.add_new_layer, bg="#27ae60", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(l_btns, text="🗑 Del", command=self.delete_active_layer, bg="#c0392b", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        self.layer_ui_frame = tk.Frame(sidebar, bg="#2c3e50")
        self.layer_ui_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # --- Right Sidebar (Text Editor) ---
        self.text_sidebar = tk.Frame(self.root, bg="#ecf0f1", width=250, padx=10, pady=10)
        self.text_sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(self.text_sidebar, text="TEXT MANAGER", bg="#ecf0f1", font=("Arial", 10, "bold")).pack(pady=5)
        self.text_entry = tk.Text(self.text_sidebar, height=4, width=25)
        self.text_entry.pack(pady=5)
        self.text_entry.bind("<KeyRelease>", lambda e: self.update_text_obj())

        tk.Label(self.text_sidebar, text="Font Family", bg="#ecf0f1").pack(anchor="w")
        self.font_family = ttk.Combobox(self.text_sidebar, values=["Arial", "Courier", "Times", "Verdana"])
        self.font_family.set("Arial")
        self.font_family.pack(fill=tk.X)
        self.font_family.bind("<<ComboboxSelected>>", lambda e: self.update_text_obj())

        tk.Label(self.text_sidebar, text="Font Size", bg="#ecf0f1").pack(anchor="w")
        self.text_size_var = tk.IntVar(value=20)
        self.text_size_spin = tk.Spinbox(self.text_sidebar, from_=8, to=200, textvariable=self.text_size_var, command=self.update_text_obj)
        self.text_size_spin.pack(fill=tk.X)

        # --- Canvas ---
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)

    # --- Layer Persistence Logic ---
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
                        "tags": self.canvas.gettags(item_id)
                    }
                }
                # Add specific properties based on type
                if item_type == "line":
                    item_data["options"]["width"] = self.canvas.itemcget(item_id, "width")
                elif item_type == "text":
                    item_data["options"]["text"] = self.canvas.itemcget(item_id, "text")
                    item_data["options"]["font"] = self.canvas.itemcget(item_id, "font")
                
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
                        new_id = self.canvas.create_line(item["coords"], fill=opts["fill"], width=opts["width"], capstyle=tk.ROUND, smooth=True, tags=opts["tags"])
                    elif item["type"] == "rectangle":
                        new_id = self.canvas.create_rectangle(item["coords"], fill=opts["fill"], outline="", tags=opts["tags"])
                    elif item["type"] == "text":
                        new_id = self.canvas.create_text(item["coords"], text=opts["text"], fill=opts["fill"], font=opts["font"], tags=opts["tags"], anchor=tk.NW)
                    
                    if new_id:
                        self.layers[current_idx]["items"].append(new_id)
                        if not layer_data["visible"]:
                            self.canvas.itemconfig(new_id, state="hidden")

            self.active_layer_idx = len(self.layers) - 1
            self.refresh_layer_ui()
            self.enforce_z_index()
            messagebox.showinfo("Success", "Project loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project: {e}")

    # --- Layer Controls ---
    def add_new_layer(self, name=None):
        if not name:
            name = simpledialog.askstring("Layer Name", "Enter layer name:")
        if not name: return
        self.layers.append({"name": name, "items": [], "visible": True})
        self.active_layer_idx = len(self.layers) - 1
        self.refresh_layer_ui()

    def delete_active_layer(self):
        if len(self.layers) <= 1: return
        for item in self.layers[self.active_layer_idx]["items"]:
            self.canvas.delete(item)
        self.layers.pop(self.active_layer_idx)
        self.active_layer_idx = max(0, self.active_layer_idx - 1)
        self.refresh_layer_ui()

    def refresh_layer_ui(self):
        for w in self.layer_ui_frame.winfo_children(): w.destroy()
        for i in range(len(self.layers)-1, -1, -1):
            bg = "#3498db" if i == self.active_layer_idx else "#34495e"
            f = tk.Frame(self.layer_ui_frame, bg=bg, pady=2)
            f.pack(fill=tk.X, pady=1)
            lbl = tk.Label(f, text=self.layers[i]["name"], bg=bg, fg="white", width=15, anchor="w")
            lbl.pack(side=tk.LEFT, padx=5)
            lbl.bind("<Button-1>", lambda e, idx=i: self.select_layer(idx))
            lbl.bind("<Double-Button-1>", lambda e, idx=i: self.rename_layer(idx))

    def rename_layer(self, idx):
        new_name = simpledialog.askstring("Rename", "New name:", initialvalue=self.layers[idx]["name"])
        if new_name:
            self.layers[idx]["name"] = new_name
            self.refresh_layer_ui()

    def select_layer(self, idx):
        self.active_layer_idx = idx
        self.refresh_layer_ui()

    # --- Tool & Interaction Logic ---
    def on_press(self, event):
        self.last_x, self.last_y = event.x, event.y
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        
        if "text_obj" in tags:
            self.selected_text_id = item[0]
            self.load_text_to_editor()
        elif self.current_tool == "text":
            self.create_text_obj(event.x, event.y)
        elif self.current_tool == "fill":
            self.apply_fill()
        else:
            self.selected_text_id = None

    def create_text_obj(self, x, y):
        txt_id = self.canvas.create_text(x, y, text="New Text", fill=self.current_color, 
                                        font=("Arial", 20), tags=("text_obj",), anchor=tk.NW)
        self.selected_text_id = txt_id
        self.register_item(txt_id)
        self.load_text_to_editor()

    def load_text_to_editor(self):
        if not self.selected_text_id: return
        content = self.canvas.itemcget(self.selected_text_id, "text")
        self.text_entry.delete("1.0", tk.END)
        self.text_entry.insert("1.0", content)

    def update_text_obj(self):
        if not self.selected_text_id: return
        new_txt = self.text_entry.get("1.0", "end-1c")
        new_font = (self.font_family.get(), self.text_size_var.get())
        self.canvas.itemconfig(self.selected_text_id, text=new_txt, font=new_font)

    def on_drag(self, event):
        if not self.layers[self.active_layer_idx]["visible"]: return
        if self.current_tool in ["pen", "eraser"]:
            color = self.current_color if self.current_tool == "pen" else "white"
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                          fill=color, width=self.pen_width.get(), capstyle=tk.ROUND, smooth=True)
            self.register_item(item)
            self.last_x, self.last_y = event.x, event.y
        elif self.selected_text_id:
            self.canvas.coords(self.selected_text_id, event.x, event.y)

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
        for layer in self.layers:
            for item in layer["items"]:
                self.canvas.tag_raise(item)

    def set_tool(self, tool): self.current_tool = tool
    def pick_color(self):
        c = colorchooser.askcolor()[1]
        if c: 
            self.current_color = c
            self.color_btn.config(bg=c)

    def undo(self):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.canvas.delete(item)
            for l in self.layers:
                if item in l["items"]: l["items"].remove(item)

if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()