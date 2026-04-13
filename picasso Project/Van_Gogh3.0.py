"""
Professional Virtual Paint Application
A feature-rich paint application with advanced features.

Features:
1. Geometric shapes (rectangle, circle, triangle, line, star)
2. Copy/Paste functionality with selection tool
3. Undo function (last 5 actions)
4. Spray paint tool
5. Save/Load drawings (PNG format)
6. WILDCARD: Rainbow mode + Layer system
7. NEW: Gradient color picker
8. NEW: Layer enable/disable system
9. NEW: Tool size slider (visible at all times)
10. NEW: Text tool for typing
11. NEW: Opacity slider

Author: Student Developer
Compatible with: VS Code, Python 3.x
"""

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, font
from PIL import Image, ImageDraw, ImageTk, ImageGrab
import random
import io
from collections import deque


class GradientPicker(tk.Toplevel):
    """
    Custom gradient color picker window.
    Allows selection from a color gradient.
    """
    
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("🎨 Gradient Color Picker")
        self.geometry("400x450")
        self.resizable(False, False)
        
        self.callback = callback
        self.selected_color = "#000000"
        
        # Create gradient canvas
        self.gradient_canvas = tk.Canvas(self, width=360, height=300, bg="white")
        self.gradient_canvas.pack(padx=20, pady=20)
        
        # Draw gradient
        self.draw_gradient()
        
        # Bind click event
        self.gradient_canvas.bind("<Button-1>", self.pick_color)
        
        # Color preview
        preview_frame = tk.Frame(self)
        preview_frame.pack(pady=10)
        
        tk.Label(preview_frame, text="Selected Color:").pack(side=tk.LEFT, padx=5)
        
        self.color_preview = tk.Canvas(preview_frame, width=100, height=40, bg=self.selected_color)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        
        self.color_label = tk.Label(preview_frame, text=self.selected_color, font=("Arial", 10))
        self.color_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="✓ Select", command=self.confirm_selection,
                 bg="#27ae60", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="✗ Cancel", command=self.destroy,
                 bg="#e74c3c", fg="white", width=12).pack(side=tk.LEFT, padx=5)
    
    def draw_gradient(self):
        """Draw a rainbow gradient with saturation/brightness variation."""
        width = 360
        height = 300
        
        # Create gradient
        for x in range(width):
            # Hue varies horizontally (0-360)
            hue = int((x / width) * 360)
            
            for y in range(height):
                # Saturation and Value vary vertically
                saturation = 100 - int((y / height) * 100)
                value = 100
                
                # Convert HSV to RGB
                color = self.hsv_to_rgb(hue, saturation, value)
                
                self.gradient_canvas.create_line(x, y, x+1, y, fill=color)
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB hex color."""
        s = s / 100.0
        v = v / 100.0
        
        c = v * s
        x = c * (1 - abs((h / 60.0) % 2 - 1))
        m = v - c
        
        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        r = int((r + m) * 255)
        g = int((g + m) * 255)
        b = int((b + m) * 255)
        
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def pick_color(self, event):
        """Pick color from gradient at click position."""
        x, y = event.x, event.y
        
        # Calculate HSV values from position
        hue = int((x / 360) * 360)
        saturation = 100 - int((y / 300) * 100)
        value = 100
        
        self.selected_color = self.hsv_to_rgb(hue, saturation, value)
        
        # Update preview
        self.color_preview.config(bg=self.selected_color)
        self.color_label.config(text=self.selected_color)
    
    def confirm_selection(self):
        """Confirm color selection and close window."""
        self.callback(self.selected_color)
        self.destroy()


class Layer:
    """Represents a drawing layer."""
    
    def __init__(self, name, canvas):
        self.name = name
        self.canvas = canvas
        self.items = []
        self.enabled = True
        self.opacity = 1.0
    
    def add_item(self, item):
        """Add item to this layer."""
        self.items.append(item)
    
    def set_visibility(self, visible):
        """Show or hide all items in this layer."""
        self.enabled = visible
        state = tk.NORMAL if visible else tk.HIDDEN
        for item in self.items:
            try:
                self.canvas.itemconfig(item, state=state)
            except:
                pass


class PaintApp:
    """
    Professional paint application with advanced features.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("🎨 Paint Pro - Advanced Edition")
        self.root.geometry("1400x900")

        # Drawing state
        self.current_color = "black"
        self.pen_width = 3
        self.current_tool = "pen"
        self.current_shape = "rectangle"
        self.opacity = 1.0  # NEW: Opacity control
        
        # Text tool state
        self.text_font_size = 16
        self.text_font_family = "Arial"
        
        # Selection and copy/paste state
        self.selection_rect = None
        self.selected_items = []
        self.clipboard_items = []
        self.clipboard_offset = (0, 0)
        
        # Undo functionality
        self.undo_stack = deque(maxlen=5)
        self.current_action_items = []
        
        # Rainbow mode state
        self.rainbow_mode = False
        self.rainbow_colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
        self.rainbow_index = 0
        
        # Layer system (NEW: Enhanced)
        self.layers = []
        self.current_layer_index = 0
        self.create_default_layers()
        
        # Create UI components
        self.create_widgets()

        # Mouse tracking
        self.last_x, self.last_y = None, None
        self.start_x, self.start_y = None, None
        self.temp_shape = None

    def create_default_layers(self):
        """Create default layers."""
        # We'll create layers after canvas is created
        pass

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
        
        # Now create layers
        self.layers = [
            Layer("Background", self.canvas),
            Layer("Main Drawing", self.canvas),
            Layer("Top Layer", self.canvas)
        ]
        self.current_layer_index = 1  # Default to Main Drawing

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
        
        # File operations
        file_frame = tk.LabelFrame(toolbar, text="File", bg="#2c3e50", fg="white", padx=5, pady=5)
        file_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(file_frame, text="💾 Save", command=self.save_drawing, 
                 bg="#27ae60", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(file_frame, text="📂 Load", command=self.load_drawing,
                 bg="#3498db", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        
        # Edit operations
        edit_frame = tk.LabelFrame(toolbar, text="Edit", bg="#2c3e50", fg="white", padx=5, pady=5)
        edit_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(edit_frame, text="↶ Undo", command=self.undo,
                 bg="#e67e22", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(edit_frame, text="📋 Copy", command=self.copy_selection,
                 bg="#9b59b6", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(edit_frame, text="📌 Paste", command=self.paste_selection,
                 bg="#8e44ad", fg="white", width=8).pack(side=tk.LEFT, padx=2)
        
        # Layer controls (NEW)
        layer_frame = tk.LabelFrame(toolbar, text="Layers", bg="#2c3e50", fg="white", padx=5, pady=5)
        layer_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Label(layer_frame, text="Current:", bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        
        self.layer_var = tk.StringVar(value="Main Drawing")
        self.layer_menu = tk.OptionMenu(layer_frame, self.layer_var, 
                                        "Background", "Main Drawing", "Top Layer",
                                        command=self.change_layer)
        self.layer_menu.config(bg="#34495e", fg="white", width=12)
        self.layer_menu.pack(side=tk.LEFT, padx=2)
        
        self.layer_enabled_var = tk.BooleanVar(value=True)
        self.layer_toggle_btn = tk.Checkbutton(layer_frame, text="Enabled", 
                                              variable=self.layer_enabled_var,
                                              command=self.toggle_layer,
                                              bg="#2c3e50", fg="white", 
                                              selectcolor="#27ae60")
        self.layer_toggle_btn.pack(side=tk.LEFT, padx=2)
        
        # Clear canvas
        tk.Button(toolbar, text="🗑️ Clear All", command=self.clear_canvas,
                 bg="#e74c3c", fg="white", width=12).pack(side=tk.LEFT, padx=10)
        
        # Rainbow mode
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
        sidebar = tk.Frame(parent, bg="#34495e", width=250)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Add scrollbar for sidebar
        canvas_scroll = tk.Canvas(sidebar, bg="#34495e", highlightthickness=0)
        scrollbar = tk.Scrollbar(sidebar, orient="vertical", command=canvas_scroll.yview)
        scrollable_frame = tk.Frame(canvas_scroll, bg="#34495e")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        
        canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        
        canvas_scroll.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tools section
        tools_frame = tk.LabelFrame(scrollable_frame, text="🛠️ Tools", bg="#34495e", 
                                   fg="white", font=("Arial", 10, "bold"))
        tools_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Drawing tools
        tools = [
            ("✏️ Pen", "pen"),
            ("⬜ Select", "select"),
            ("🧽 Eraser", "eraser"),
            ("💨 Spray", "spray"),
            ("◼️ Shapes", "shape"),
            ("🔤 Text", "text")  # NEW: Text tool
        ]
        
        for text, tool in tools:
            btn = tk.Button(tools_frame, text=text, 
                          command=lambda t=tool: self.select_tool(t),
                          bg="#2c3e50", fg="white", width=18)
            btn.pack(pady=2, padx=5)
        
        # Shapes section
        shapes_frame = tk.LabelFrame(scrollable_frame, text="📐 Shapes", bg="#34495e",
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
                          bg="#2c3e50", fg="white", width=18)
            btn.pack(pady=2, padx=5)
        
        # Colors section
        colors_frame = tk.LabelFrame(scrollable_frame, text="🎨 Colors", bg="#34495e",
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
                          width=18)
            btn.pack(pady=2, padx=5)
        
        tk.Button(colors_frame, text="🎨 Custom Color", 
                 command=self.choose_color,
                 bg="#95a5a6", fg="black", width=18).pack(pady=2, padx=5)
        
        # NEW: Gradient Picker
        tk.Button(colors_frame, text="🌈 Gradient Picker", 
                 command=self.open_gradient_picker,
                 bg="#16a085", fg="white", width=18).pack(pady=2, padx=5)
        
        # Tool Size section (NEW: Always visible)
        size_frame = tk.LabelFrame(scrollable_frame, text="📏 Tool Size", bg="#34495e",
                                  fg="white", font=("Arial", 10, "bold"))
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.size_slider = tk.Scale(size_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                                   label="Width", command=self.change_size,
                                   bg="#34495e", fg="white", highlightthickness=0,
                                   length=200)
        self.size_slider.set(self.pen_width)
        self.size_slider.pack(fill=tk.X, padx=5, pady=5)
        
        self.size_display = tk.Label(size_frame, text=f"Current: {self.pen_width}px",
                                     bg="#34495e", fg="white", font=("Arial", 9))
        self.size_display.pack()
        
        # NEW: Opacity slider
        opacity_frame = tk.LabelFrame(scrollable_frame, text="👻 Opacity", bg="#34495e",
                                     fg="white", font=("Arial", 10, "bold"))
        opacity_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.opacity_slider = tk.Scale(opacity_frame, from_=10, to=100, orient=tk.HORIZONTAL,
                                      label="Opacity %", command=self.change_opacity,
                                      bg="#34495e", fg="white", highlightthickness=0,
                                      length=200)
        self.opacity_slider.set(100)
        self.opacity_slider.pack(fill=tk.X, padx=5, pady=5)
        
        self.opacity_display = tk.Label(opacity_frame, text="Current: 100%",
                                       bg="#34495e", fg="white", font=("Arial", 9))
        self.opacity_display.pack()
        
        # Text tool options (NEW)
        text_frame = tk.LabelFrame(scrollable_frame, text="🔤 Text Options", bg="#34495e",
                                  fg="white", font=("Arial", 10, "bold"))
        text_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(text_frame, text="Font Size:", bg="#34495e", fg="white").pack()
        
        self.text_size_slider = tk.Scale(text_frame, from_=8, to=72, orient=tk.HORIZONTAL,
                                        command=self.change_text_size,
                                        bg="#34495e", fg="white", highlightthickness=0)
        self.text_size_slider.set(16)
        self.text_size_slider.pack(fill=tk.X, padx=5)
        
        tk.Label(text_frame, text="Font:", bg="#34495e", fg="white").pack()
        
        self.text_font_var = tk.StringVar(value="Arial")
        font_menu = tk.OptionMenu(text_frame, self.text_font_var,
                                  "Arial", "Helvetica", "Times", "Courier",
                                  "Comic Sans MS", "Verdana")
        font_menu.config(bg="#2c3e50", fg="white")
        font_menu.pack(fill=tk.X, padx=5, pady=5)

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
        elif tool == "text":
            self.canvas.config(cursor="xterm")
        else:
            self.canvas.config(cursor="pencil")

    def select_shape(self, shape):
        """Select a shape to draw."""
        self.current_shape = shape
        self.current_tool = "shape"
        self.update_status()

    def select_color(self, color):
        """Set current drawing color."""
        self.current_color = color
        self.rainbow_mode = False
        self.rainbow_btn.config(text="🌈 Rainbow OFF", bg="#34495e")
        self.update_status()

    def choose_color(self):
        """Open color chooser dialog."""
        color = colorchooser.askcolor()[1]
        if color:
            self.current_color = color
            self.rainbow_mode = False
            self.rainbow_btn.config(text="🌈 Rainbow OFF", bg="#34495e")
            self.update_status()

    def open_gradient_picker(self):
        """Open gradient color picker window (NEW)."""
        GradientPicker(self.root, self.on_gradient_color_selected)

    def on_gradient_color_selected(self, color):
        """Callback when color is selected from gradient picker."""
        self.current_color = color
        self.rainbow_mode = False
        self.rainbow_btn.config(text="🌈 Rainbow OFF", bg="#34495e")
        self.update_status()
        messagebox.showinfo("Color Selected", f"Color set to: {color}")

    def toggle_rainbow(self):
        """Toggle rainbow mode."""
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
        """Update pen width from slider (NEW: with display)."""
        self.pen_width = int(value)
        self.size_display.config(text=f"Current: {self.pen_width}px")

    def change_opacity(self, value):
        """Update opacity from slider (NEW)."""
        self.opacity = int(value) / 100.0
        self.opacity_display.config(text=f"Current: {int(value)}%")

    def change_text_size(self, value):
        """Update text font size (NEW)."""
        self.text_font_size = int(value)

    def change_layer(self, layer_name):
        """Change current drawing layer (NEW)."""
        layer_map = {
            "Background": 0,
            "Main Drawing": 1,
            "Top Layer": 2
        }
        self.current_layer_index = layer_map.get(layer_name, 1)
        
        # Update enabled checkbox
        self.layer_enabled_var.set(self.layers[self.current_layer_index].enabled)
        
        messagebox.showinfo("Layer Changed", f"Now drawing on: {layer_name}")

    def toggle_layer(self):
        """Toggle current layer visibility (NEW)."""
        enabled = self.layer_enabled_var.get()
        self.layers[self.current_layer_index].set_visibility(enabled)
        
        status = "enabled" if enabled else "disabled"
        messagebox.showinfo("Layer Toggle", f"Layer {self.layer_var.get()} {status}")

    def update_status(self):
        """Update status label showing current tool and color."""
        tool_name = self.current_tool.capitalize()
        if self.current_tool == "shape":
            tool_name = f"Shape ({self.current_shape})"
        
        color_text = "Rainbow" if self.rainbow_mode else self.current_color
        opacity_text = f" | Opacity: {int(self.opacity * 100)}%"
        self.status_label.config(text=f"Tool: {tool_name} | Color: {color_text}{opacity_text}")

    def get_color_with_opacity(self, base_color):
        """Convert color to hex with opacity (NEW)."""
        # For simplicity, we'll use stipple pattern for opacity effect
        # True transparency requires PIL/ImageTk
        return base_color

    def on_mouse_press(self, event):
        """Handle mouse press events."""
        self.start_x, self.start_y = event.x, event.y
        self.last_x, self.last_y = event.x, event.y
        self.current_action_items = []
        
        if self.current_tool == "select":
            self.clear_selection()
        elif self.current_tool == "text":
            self.place_text(event)

    def on_mouse_drag(self, event):
        """Handle mouse drag events."""
        if self.current_tool == "pen":
            self.draw_pen(event)
        elif self.current_tool == "eraser":
            self.draw_eraser(event)
        elif self.current_tool == "spray":
            self.draw_spray(event)
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
        
        # Save action to undo stack
        if self.current_action_items:
            self.undo_stack.append(list(self.current_action_items))
            self.current_action_items = []
        
        self.last_x, self.last_y = None, None

    def place_text(self, event):
        """Place text on canvas (NEW)."""
        # Get text input from user
        text = simpledialog.askstring("Text Input", "Enter text to place:",
                                     parent=self.root)
        
        if text:
            color = self.get_next_rainbow_color() if self.rainbow_mode else self.current_color
            font_name = self.text_font_var.get()
            
            # Calculate stipple for opacity effect
            stipple = ""
            if self.opacity < 1.0:
                # Use gray50 for semi-transparent effect
                stipple = "gray50"
            
            text_item = self.canvas.create_text(
                event.x, event.y,
                text=text,
                fill=color,
                font=(font_name, self.text_font_size, "normal"),
                stipple=stipple
            )
            
            self.current_action_items.append(text_item)
            self.layers[self.current_layer_index].add_item(text_item)

    def draw_pen(self, event):
        """Draw with pen tool."""
        if self.last_x and self.last_y:
            color = self.get_next_rainbow_color() if self.rainbow_mode else self.current_color
            
            # Apply opacity using stipple
            stipple = ""
            if self.opacity < 0.5:
                stipple = "gray50"
            elif self.opacity < 0.8:
                stipple = "gray25"
            
            line = self.canvas.create_line(
                self.last_x, self.last_y, event.x, event.y,
                width=self.pen_width, fill=color,
                capstyle=tk.ROUND, smooth=True,
                stipple=stipple
            )
            self.current_action_items.append(line)
            self.layers[self.current_layer_index].add_item(line)
        
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
            self.layers[self.current_layer_index].add_item(line)
        
        self.last_x, self.last_y = event.x, event.y

    def draw_spray(self, event):
        """Draw with spray paint effect."""
        spray_radius = self.pen_width * 3
        num_dots = 20
        
        color = self.get_next_rainbow_color() if self.rainbow_mode else self.current_color
        
        stipple = ""
        if self.opacity < 0.5:
            stipple = "gray75"
        elif self.opacity < 0.8:
            stipple = "gray50"
        
        for _ in range(num_dots):
            dx = random.randint(-spray_radius, spray_radius)
            dy = random.randint(-spray_radius, spray_radius)
            
            x = event.x + dx
            y = event.y + dy
            
            dot_size = random.randint(1, 3)
            dot = self.canvas.create_oval(
                x, y, x + dot_size, y + dot_size,
                fill=color, outline=color, stipple=stipple
            )
            self.current_action_items.append(dot)
            self.layers[self.current_layer_index].add_item(dot)

    def draw_shape_preview(self, event):
        """Show shape preview while dragging."""
        if self.temp_shape:
            self.canvas.delete(self.temp_shape)
        
        color = self.get_next_rainbow_color() if self.rainbow_mode else self.current_color
        
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
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            mid_x = (x1 + x2) / 2
            
            self.temp_shape = self.canvas.create_polygon(
                mid_x, y1, x1, y2, x2, y2,
                outline=color, fill="", width=self.pen_width
            )
        elif self.current_shape == "star":
            points = self.calculate_star_points(
                self.start_x, self.start_y, event.x, event.y
            )
            self.temp_shape = self.canvas.create_polygon(
                points, outline=color, fill="", width=self.pen_width
            )

    def calculate_star_points(self, x1, y1, x2, y2):
        """Calculate points for a 5-pointed star."""
        import math
        
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        radius = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 / 2
        
        points = []
        for i in range(10):
            angle = i * 36 - 90
            r = radius if i % 2 == 0 else radius / 2.5
            x = center_x + r * math.cos(math.radians(angle))
            y = center_y + r * math.sin(math.radians(angle))
            points.extend([x, y])
        
        return points

    def draw_final_shape(self, event):
        """Draw final shape on mouse release."""
        if self.temp_shape:
            self.canvas.delete(self.temp_shape)
            self.temp_shape = None
        
        color = self.current_color
        
        stipple = ""
        if self.opacity < 0.5:
            stipple = "gray50"
        elif self.opacity < 0.8:
            stipple = "gray25"
        
        if self.current_shape == "rectangle":
            shape = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=self.pen_width, stipple=stipple
            )
        elif self.current_shape == "circle":
            shape = self.canvas.create_oval(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=self.pen_width, stipple=stipple
            )
        elif self.current_shape == "line":
            shape = self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y,
                fill=color, width=self.pen_width, stipple=stipple
            )
        elif self.current_shape == "triangle":
            x1, y1 = self.start_x, self.start_y
            x2, y2 = event.x, event.y
            mid_x = (x1 + x2) / 2
            
            shape = self.canvas.create_polygon(
                mid_x, y1, x1, y2, x2, y2,
                outline=color, fill="", width=self.pen_width, stipple=stipple
            )
        elif self.current_shape == "star":
            points = self.calculate_star_points(
                self.start_x, self.start_y, event.x, event.y
            )
            shape = self.canvas.create_polygon(
                points, outline=color, fill="", width=self.pen_width, stipple=stipple
            )
        
        self.current_action_items.append(shape)
        self.layers[self.current_layer_index].add_item(shape)

    def draw_selection_box(self, event):
        """Draw selection rectangle."""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
        
        self.selection_rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline="blue", dash=(5, 5), width=2
        )

    def finalize_selection(self, event):
        """Finalize selection and identify selected items."""
        if not self.selection_rect:
            return
        
        x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
        x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
        
        self.selected_items = []
        for item in self.canvas.find_all():
            if item == self.selection_rect:
                continue
            
            bbox = self.canvas.bbox(item)
            if bbox:
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
        """Copy selected items to clipboard."""
        if not self.selected_items:
            messagebox.showwarning("Copy", "No items selected!\nUse Select tool first.")
            return
        
        self.clipboard_items = []
        
        for item in self.selected_items:
            item_type = self.canvas.type(item)
            coords = self.canvas.coords(item)
            config = self.canvas.itemconfig(item)
            
            self.clipboard_items.append({
                'type': item_type,
                'coords': coords,
                'config': config
            })
        
        if self.clipboard_items:
            first_coords = self.clipboard_items[0]['coords']
            self.clipboard_offset = (first_coords[0], first_coords[1])
        
        messagebox.showinfo("Copy", f"Copied {len(self.clipboard_items)} item(s)")

    def paste_selection(self):
        """Paste clipboard items at new location."""
        if not self.clipboard_items:
            messagebox.showwarning("Paste", "Clipboard is empty!\nCopy something first.")
            return
        
        offset_x, offset_y = 50, 50
        pasted_items = []
        
        for item_data in self.clipboard_items:
            coords = list(item_data['coords'])
            if coords:
                new_coords = []
                for i in range(0, len(coords), 2):
                    new_coords.append(coords[i] + offset_x)
                    new_coords.append(coords[i + 1] + offset_y)
                
                if item_data['type'] == 'line':
                    new_item = self.canvas.create_line(*new_coords)
                elif item_data['type'] == 'rectangle':
                    new_item = self.canvas.create_rectangle(*new_coords)
                elif item_data['type'] == 'oval':
                    new_item = self.canvas.create_oval(*new_coords)
                elif item_data['type'] == 'polygon':
                    new_item = self.canvas.create_polygon(*new_coords)
                elif item_data['type'] == 'text':
                    new_item = self.canvas.create_text(*new_coords)
                
                for key, value in item_data['config'].items():
                    try:
                        if value and value[4]:
                            self.canvas.itemconfig(new_item, **{key: value[4]})
                    except:
                        pass
                
                pasted_items.append(new_item)
                self.layers[self.current_layer_index].add_item(new_item)
        
        if pasted_items:
            self.undo_stack.append(pasted_items)
        
        messagebox.showinfo("Paste", f"Pasted {len(pasted_items)} item(s)")

    def undo(self):
        """Undo last action."""
        if not self.undo_stack:
            messagebox.showinfo("Undo", "Nothing to undo!")
            return
        
        last_action = self.undo_stack.pop()
        
        for item in last_action:
            try:
                self.canvas.delete(item)
            except:
                pass
        
        remaining = len(self.undo_stack)
        messagebox.showinfo("Undo", f"Undone!\n{remaining} action(s) remaining")

    def save_drawing(self):
        """Save drawing to PNG file."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                ps = self.canvas.postscript(colormode='color')
                img = Image.open(io.BytesIO(ps.encode('utf-8')))
                img.save(filename, 'png')
                messagebox.showinfo("Save", f"Drawing saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{str(e)}")

    def load_drawing(self):
        """Load drawing from PNG file."""
        filename = filedialog.askopenfilename(
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.clear_canvas()
                img = Image.open(filename)
                photo = ImageTk.PhotoImage(img)
                item = self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                self.canvas.image = photo
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
            
            # Recreate layers
            self.layers = [
                Layer("Background", self.canvas),
                Layer("Main Drawing", self.canvas),
                Layer("Top Layer", self.canvas)
            ]


if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()