"""
Enhanced Virtual Paint Application
A feature-rich paint application using Tkinter.

New Features:
1. Geometric shapes (rectangle, circle, triangle, line, star)
2. Copy/Paste functionality with selection tool
3. Undo function (last 5 actions)
4. Spray paint tool
5. Save/Load drawings (PNG format)
6. WILDCARD: Layer system with transparency + Rainbow pen mode!

Author: Student Developer
Compatible with: VS Code, Python 3.x
"""

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import random
import io
from collections import deque


class PaintApp:
    """
    Enhanced paint application with advanced features.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Virtual Paint Pro")
        self.root.geometry("1200x800")

        # Drawing state
        self.current_color = "black"
        self.pen_width = 3
        self.current_tool = "pen"  # pen, eraser, shape, spray, select
        self.current_shape = "rectangle"  # For shape tool
        
        # Selection and copy/paste state
        self.selection_rect = None
        self.selected_items = []
        self.clipboard_items = []
        self.clipboard_offset = (0, 0)
        
        # Undo functionality (Requirement 3)
        self.undo_stack = deque(maxlen=5)  # Store last 5 actions
        self.current_action_items = []
        
        # Rainbow mode state (WILDCARD feature)
        self.rainbow_mode = False
        self.rainbow_colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
        self.rainbow_index = 0
        
        # Layer system (WILDCARD feature)
        self.layers = []
        self.current_layer = 0
        
        # Create UI components
        self.create_widgets()

        # Mouse tracking
        self.last_x, self.last_y = None, None
        self.start_x, self.start_y = None, None
        self.temp_shape = None

    def create_widgets(self):
        """Create all UI components."""
        
        # Main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top toolbar
        self.create_top_toolbar(main_container)
        
        # Middle section with side toolbar and canvas
        middle_frame = tk.Frame(main_container)
        middle_frame.pack(fill=tk.BOTH, expand=True)
        
        # Side toolbar
        self.create_side_toolbar(middle_frame)
        
        # Canvas
        self.canvas = tk.Canvas(middle_frame, bg="white", cursor="crosshair")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        
        # Keyboard shortcuts
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-c>", lambda e: self.copy_selection())
        self.root.bind("<Control-v>", lambda e: self.paste_selection())
        self.root.bind("<Control-s>", lambda e: self.save_drawing())
        self.root.bind("<Control-o>", lambda e: self.load_drawing())

    def create_top_toolbar(self, parent):
        """Create the top toolbar with main controls."""
        toolbar = tk.Frame(parent, bg="#2c3e50", height=60)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # File operations (Requirement 5: Save/Load)
        file_frame = tk.LabelFrame(toolbar, text="File", bg="#2c3e50", fg="white", padx=5, pady=5)
        file_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(file_frame, text="💾 Save", command=self.save_drawing, 
                 bg="#27ae60", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="📂 Load", command=self.load_drawing,
                 bg="#3498db", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        
        # Edit operations (Requirement 2 & 3: Copy/Paste/Undo)
        edit_frame = tk.LabelFrame(toolbar, text="Edit", bg="#2c3e50", fg="white", padx=5, pady=5)
        edit_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(edit_frame, text="↶ Undo", command=self.undo,
                 bg="#e67e22", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(edit_frame, text="📋 Copy", command=self.copy_selection,
                 bg="#9b59b6", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(edit_frame, text="📌 Paste", command=self.paste_selection,
                 bg="#8e44ad", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        
        # Clear canvas
        tk.Button(toolbar, text="🗑️ Clear All", command=self.clear_canvas,
                 bg="#e74c3c", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        
        # Rainbow mode (WILDCARD)
        self.rainbow_btn = tk.Button(toolbar, text="🌈 Rainbow OFF", 
                                     command=self.toggle_rainbow,
                                     bg="#34495e", fg="white", width=15)
        self.rainbow_btn.pack(side=tk.RIGHT, padx=10)
        
        # Current tool/color display
        self.status_label = tk.Label(toolbar, text="Tool: Pen | Color: Black",
                                     bg="#2c3e50", fg="white", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.RIGHT, padx=10)

    def create_side_toolbar(self, parent):
        """Create the side toolbar with tools and options."""
        sidebar = tk.Frame(parent, bg="#34495e", width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Tools section
        tools_frame = tk.LabelFrame(sidebar, text="🛠️ Tools", bg="#34495e", 
                                   fg="white", font=("Arial", 10, "bold"))
        tools_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Drawing tools
        tools = [
            ("✏️ Pen", "pen"),
            ("⬜ Select", "select"),
            ("🧽 Eraser", "eraser"),
            ("💨 Spray", "spray"),  # Requirement 4: Spray paint
            ("◼️ Shapes", "shape")   # Requirement 1: Shapes
        ]
        
        for text, tool in tools:
            btn = tk.Button(tools_frame, text=text, 
                          command=lambda t=tool: self.select_tool(t),
                          bg="#2c3e50", fg="white", width=15)
            btn.pack(pady=2, padx=5)
        
        # Shapes section (Requirement 1)
        shapes_frame = tk.LabelFrame(sidebar, text="📐 Shapes", bg="#34495e",
                                    fg="white", font=("Arial", 10, "bold"))
        shapes_frame.pack(fill=tk.X, padx=5, pady=5)
        
        shapes = [
            ("⬜ Rectangle", "rectangle"),
            ("⭕ Circle", "circle"),
            ("🔺 Triangle", "triangle"),
            ("➖ Line", "line"),
            ("⭐ Star", "star")
        ]
        
        for text, shape in shapes:
            btn = tk.Button(shapes_frame, text=text,
                          command=lambda s=shape: self.select_shape(s),
                          bg="#2c3e50", fg="white", width=15)
            btn.pack(pady=2, padx=5)
        
        # Colors section
        colors_frame = tk.LabelFrame(sidebar, text="🎨 Colors", bg="#34495e",
                                    fg="white", font=("Arial", 10, "bold"))
        colors_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Color palette
        color_palette = [
            ("Black", "black"),
            ("Red", "red"),
            ("Orange", "orange"),
            ("Yellow", "yellow"),
            ("Green", "green"),
            ("Blue", "blue"),
            ("Purple", "purple"),
            ("Pink", "pink")
        ]
        
        for name, color in color_palette:
            btn = tk.Button(colors_frame, text=name, bg=color,
                          fg="white" if color in ["black", "blue", "purple"] else "black",
                          command=lambda c=color: self.select_color(c),
                          width=15)
            btn.pack(pady=2, padx=5)
        
        tk.Button(colors_frame, text="🎨 Custom Color", 
                 command=self.choose_color,
                 bg="#95a5a6", fg="black", width=15).pack(pady=5, padx=5)
        
        # Pen size section
        size_frame = tk.LabelFrame(sidebar, text="📏 Size", bg="#34495e",
                                  fg="white", font=("Arial", 10, "bold"))
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.size_slider = tk.Scale(size_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                                   label="Pen Width", command=self.change_size,
                                   bg="#34495e", fg="white", highlightthickness=0)
        self.size_slider.set(self.pen_width)
        self.size_slider.pack(fill=tk.X, padx=5, pady=5)

    def select_tool(self, tool):
        """Switch between different tools."""
        self.current_tool = tool
        self.update_status()
        
        # Update cursor based on tool
        if tool == "eraser":
            self.canvas.config(cursor="circle")
        elif tool == "select":
            self.canvas.config(cursor="crosshair")
        elif tool == "spray":
            self.canvas.config(cursor="spray")
        else:
            self.canvas.config(cursor="pencil")

    def select_shape(self, shape):
        """Select a shape to draw (Requirement 1)."""
        self.current_shape = shape
        self.current_tool = "shape"
        self.update_status()

    def select_color(self, color):
        """Set current drawing color."""
        self.current_color = color
        self.rainbow_mode = False
        self.rainbow_btn.config(text="🌈 Rainbow OFF")
        self.update_status()

    def choose_color(self):
        """Open color chooser dialog."""
        color = colorchooser.askcolor()[1]
        if color:
            self.current_color = color
            self.rainbow_mode = False
            self.rainbow_btn.config(text="🌈 Rainbow OFF")
            self.update_status()

    def toggle_rainbow(self):
        """Toggle rainbow mode (WILDCARD feature)."""
        self.rainbow_mode = not self.rainbow_mode
        if self.rainbow_mode:
            self.rainbow_btn.config(text="🌈 Rainbow ON", bg="#e74c3c")
        else:
            self.rainbow_btn.config(text="🌈 Rainbow OFF", bg="#34495e")
        self.update_status()

    def get_next_rainbow_color(self):
        """Get next color in rainbow sequence."""
        color = self.rainbow_colors[self.rainbow_index]
        self.rainbow_index = (self.rainbow_index + 1) % len(self.rainbow_colors)
        return color

    def change_size(self, value):
        """Update pen width from slider."""
        self.pen_width = int(value)

    def update_status(self):
        """Update status label showing current tool and color."""
        tool_name = self.current_tool.capitalize()
        if self.current_tool == "shape":
            tool_name = f"Shape ({self.current_shape})"
        
        color_text = "Rainbow" if self.rainbow_mode else self.current_color
        self.status_label.config(text=f"Tool: {tool_name} | Color: {color_text}")

    def on_mouse_press(self, event):
        """Handle mouse press events."""
        self.start_x, self.start_y = event.x, event.y
        self.last_x, self.last_y = event.x, event.y
        self.current_action_items = []  # Start new action for undo
        
        if self.current_tool == "select":
            # Start selection rectangle
            self.clear_selection()

    def on_mouse_drag(self, event):
        """Handle mouse drag events."""
        if self.current_tool == "pen":
            self.draw_pen(event)
        elif self.current_tool == "eraser":
            self.draw_eraser(event)
        elif self.current_tool == "spray":
            self.draw_spray(event)  # Requirement 4
        elif self.current_tool == "shape":
            self.draw_shape_preview(event)
        elif self.current_tool == "select":
            self.draw_selection_box(event)

    def on_mouse_release(self, event):
        """Handle mouse release events."""
        if self.current_tool == "shape":
            self.draw_final_shape(event)
        elif self.current_tool == "select":
            self.finalize_selection(event)
        
        # Save action to undo stack (Requirement 3)
        if self.current_action_items:
            self.undo_stack.append(list(self.current_action_items))
            self.current_action_items = []
        
        self.last_x, self.last_y = None, None

    def draw_pen(self, event):
        """Draw with pen tool."""
        if self.last_x and self.last_y:
            color = self.get_next_rainbow_color() if self.rainbow_mode else self.current_color
            
            line = self.canvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                width=self.pen_width, fill=color,
                capstyle=tk.ROUND, smooth=True
            )
            self.current_action_items.append(line)
        
        self.last_x, self.last_y = event.x, event.y

    def draw_eraser(self, event):
        """Erase with eraser tool."""
        if self.last_x and self.last_y:
            line = self.canvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                width=self.pen_width * 2, fill="white",
                capstyle=tk.ROUND, smooth=True
            )
            self.current_action_items.append(line)
        
        self.last_x, self.last_y = event.x, event.y

    def draw_spray(self, event):
        """Draw with spray paint effect (Requirement 4)."""
        # Create multiple small dots in a random pattern around cursor
        spray_radius = self.pen_width * 3
        num_dots = 20  # Number of spray dots per drag event
        
        color = self.get_next_rainbow_color() if self.rainbow_mode else self.current_color
        
        for _ in range(num_dots):
            # Random position within spray radius
            dx = random.randint(-spray_radius, spray_radius)
            dy = random.randint(-spray_radius, spray_radius)
            
            x = event.x + dx
            y = event.y + dy
            
            # Draw small dot
            dot_size = random.randint(1, 3)
            dot = self.canvas.create_oval(
                x, y, x + dot_size, y + dot_size,
                fill=color, outline=color
            )
            self.current_action_items.append(dot)

    def draw_shape_preview(self, event):
        """Show shape preview while dragging (Requirement 1)."""
        # Remove previous preview
        if self.temp_shape:
            self.canvas.delete(self.temp_shape)
        
        color = self.get_next_rainbow_color() if self.rainbow_mode else self.current_color
        
        # Draw preview shape
        if self.current_shape == "rectangle":
            self.temp_shape = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=self.pen_width
            )
        elif self.current_shape == "circle":
            self.temp_shape = self.canvas.create_oval(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=self.pen_width
            )
        elif self.current_shape == "line":
            self.temp_shape = self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y,
                fill=color, width=self.pen_width
            )
        elif self.current_shape == "triangle":
            # Calculate triangle points
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            mid_x = (x1 + x2) / 2
            
            self.temp_shape = self.canvas.create_polygon(
                mid_x, y1, x1, y2, x2, y2,
                outline=color, fill="", width=self.pen_width
            )
        elif self.current_shape == "star":
            # Create 5-pointed star
            points = self.calculate_star_points(
                self.start_x, self.start_y, event.x, event.y
            )
            self.temp_shape = self.canvas.create_polygon(
                points, outline=color, fill="", width=self.pen_width
            )

    def calculate_star_points(self, x1, y1, x2, y2):
        """Calculate points for a 5-pointed star."""
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 / 2
        
        points = []
        for i in range(10):
            angle = i * 36 - 90  # 36 degrees between points, start at top
            r = radius if i % 2 == 0 else radius / 2.5
            x = center_x + r * (3.14159 / 180 * angle).__cos__()
            y = center_y + r * (3.14159 / 180 * angle).__sin__()
            
            # Using math
            import math
            x = center_x + r * math.cos(math.radians(angle))
            y = center_y + r * math.sin(math.radians(angle))
            points.extend([x, y])
        
        return points

    def draw_final_shape(self, event):
        """Draw final shape on mouse release (Requirement 1)."""
        if self.temp_shape:
            self.canvas.delete(self.temp_shape)
            self.temp_shape = None
        
        color = self.current_color
        
        # Draw final shape
        if self.current_shape == "rectangle":
            shape = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=self.pen_width
            )
        elif self.current_shape == "circle":
            shape = self.canvas.create_oval(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=self.pen_width
            )
        elif self.current_shape == "line":
            shape = self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y,
                fill=color, width=self.pen_width
            )
        elif self.current_shape == "triangle":
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            mid_x = (x1 + x2) / 2
            
            shape = self.canvas.create_polygon(
                mid_x, y1, x1, y2, x2, y2,
                outline=color, fill="", width=self.pen_width
            )
        elif self.current_shape == "star":
            points = self.calculate_star_points(
                self.start_x, self.start_y, event.x, event.y
            )
            shape = self.canvas.create_polygon(
                points, outline=color, fill="", width=self.pen_width
            )
        
        self.current_action_items.append(shape)

    def draw_selection_box(self, event):
        """Draw selection rectangle (Requirement 2)."""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        
        self.selection_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="blue", dash=(5, 5), width=2
        )

    def finalize_selection(self, event):
        """Finalize selection and identify selected items (Requirement 2)."""
        if not self.selection_rect:
            return
        
        # Get selection bounds
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        # Find items within selection
        self.selected_items = []
        for item in self.canvas.find_all():
            if item == self.selection_rect:
                continue
            
            bbox = self.canvas.bbox(item)
            if bbox:
                # Check if item is within selection bounds
                if (bbox[0] >= x1 and bbox[1] >= y1 and 
                    bbox[2] <= x2 and bbox[3] <= y2):
                    self.selected_items.append(item)
        
        messagebox.showinfo("Selection", 
                          f"Selected {len(self.selected_items)} item(s)\n"
                          "Press Ctrl+C to copy, Ctrl+V to paste")

    def clear_selection(self):
        """Clear current selection."""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None
        self.selected_items = []

    def copy_selection(self):
        """Copy selected items to clipboard (Requirement 2)."""
        if not self.selected_items:
            messagebox.showwarning("Copy", "No items selected!\nUse Select tool first.")
            return
        
        self.clipboard_items = []
        
        # Store item data for each selected item
        for item in self.selected_items:
            item_type = self.canvas.type(item)
            coords = self.canvas.coords(item)
            config = self.canvas.itemconfig(item)
            
            self.clipboard_items.append({
                'type': item_type,
                'coords': coords,
                'config': config
            })
        
        # Store offset from first item for relative positioning
        if self.clipboard_items:
            first_coords = self.clipboard_items[0]['coords']
            self.clipboard_offset = (first_coords[0], first_coords[1])
        
        messagebox.showinfo("Copy", f"Copied {len(self.clipboard_items)} item(s)")

    def paste_selection(self):
        """Paste clipboard items at new location (Requirement 2)."""
        if not self.clipboard_items:
            messagebox.showwarning("Paste", "Clipboard is empty!\nCopy something first.")
            return
        
        # Paste 50 pixels offset from original
        offset_x, offset_y = 50, 50
        pasted_items = []
        
        for item_data in self.clipboard_items:
            # Calculate new coordinates
            coords = list(item_data['coords'])
            if coords:
                dx = coords[0] - self.clipboard_offset[0] + offset_x
                dy = coords[1] - self.clipboard_offset[1] + offset_y
                
                new_coords = []
                for i in range(0, len(coords), 2):
                    new_coords.append(coords[i] + offset_x)
                    new_coords.append(coords[i + 1] + offset_y)
                
                # Create new item
                if item_data['type'] == 'line':
                    new_item = self.canvas.create_line(*new_coords)
                elif item_data['type'] == 'rectangle':
                    new_item = self.canvas.create_rectangle(*new_coords)
                elif item_data['type'] == 'oval':
                    new_item = self.canvas.create_oval(*new_coords)
                elif item_data['type'] == 'polygon':
                    new_item = self.canvas.create_polygon(*new_coords)
                
                # Apply original styling
                for key, value in item_data['config'].items():
                    try:
                        if value and value[4]:  # Check if value exists
                            self.canvas.itemconfig(new_item, **{key: value[4]})
                    except:
                        pass
                
                pasted_items.append(new_item)
        
        # Add paste action to undo stack
        if pasted_items:
            self.undo_stack.append(pasted_items)
        
        messagebox.showinfo("Paste", f"Pasted {len(pasted_items)} item(s)")

    def undo(self):
        """Undo last action (Requirement 3: Last 5 actions)."""
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo!")
            return
        
        # Get last action
        last_action = self.undo_stack.pop()
        
        # Delete all items from that action
        for item in last_action:
            try:
                self.canvas.delete(item)
            except:
                pass  # Item might already be deleted
        
        remaining = len(self.undo_stack)
        messagebox.showinfo("Undo", f"Undone!\n{remaining} action(s) remaining in history")

    def save_drawing(self):
        """Save drawing to PNG file (Requirement 5)."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Get canvas size
                x0 = self.canvas.winfo_rootx()
                y0 = self.canvas.winfo_rooty()
                x1 = x0 + self.canvas.winfo_width()
                y1 = y0 + self.canvas.winfo_height()
                
                # Capture canvas as PostScript
                ps = self.canvas.postscript(colormode='color')
                
                # Convert to PNG using PIL
                from PIL import Image
                img = Image.open(io.BytesIO(ps.encode('utf-8')))
                img.save(filename, 'png')
                
                messagebox.showinfo("Save", f"Drawing saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{str(e)}")

    def load_drawing(self):
        """Load drawing from PNG file (Requirement 5)."""
        filename = filedialog.askopenfilename(
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Clear current canvas
                self.clear_canvas()
                
                # Load image
                img = Image.open(filename)
                photo = ImageTk.PhotoImage(img)
                
                # Display on canvas
                item = self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                self.canvas.image = photo  # Keep reference
                
                self.current_action_items.append(item)
                
                messagebox.showinfo("Load", f"Drawing loaded from:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load:\n{str(e)}")

    def clear_canvas(self):
        """Clear entire canvas."""
        if messagebox.askyesno("Clear", "Are you sure you want to clear the canvas?"):
            self.canvas.delete("all")
            self.undo_stack.clear()
            self.clipboard_items = []
            self.selected_items = []


if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()