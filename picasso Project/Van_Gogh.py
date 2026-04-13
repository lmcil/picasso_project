import tkinter as tk
from tkinter import colorchooser

class PaintApp:
    """
    A simple paint application using Tkinter.

    Features:
    - Draw with mouse
    - Multiple color selection (red, green, blue, black + custom)
    - Adjustable pen width
    - Eraser tool
    - Clear canvas
    - Visual feedback for selected color
    - Resizable window
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Paint App")
        self.root.geometry("800x600")

        # Current drawing state
        self.current_color = "black"
        self.pen_width = 3
        self.eraser_on = False

        # Create UI components
        self.create_widgets()

        # Mouse tracking
        self.last_x, self.last_y = None, None

    def create_widgets(self):
        """Create toolbar and canvas."""

        # Toolbar frame
        self.toolbar = tk.Frame(self.root, bg="lightgray", height=50)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Color buttons
        self.create_color_button("Black", "black")
        self.create_color_button("Red", "red")
        self.create_color_button("Green", "green")
        self.create_color_button("Blue", "blue")

        # Custom color chooser
        tk.Button(self.toolbar, text="Custom", command=self.choose_color).pack(side=tk.LEFT, padx=5)

        # Eraser button
        tk.Button(self.toolbar, text="Eraser", command=self.use_eraser).pack(side=tk.LEFT, padx=5)

        # Clear button
        tk.Button(self.toolbar, text="Clear", command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

        # Pen size slider
        self.size_slider = tk.Scale(self.toolbar, from_=1, to=20, orient=tk.HORIZONTAL,
                                    label="Pen Size", command=self.change_size)
        self.size_slider.set(self.pen_width)
        self.size_slider.pack(side=tk.RIGHT, padx=10)

        # Current color label
        self.color_label = tk.Label(self.toolbar, text="Current: Black", bg="lightgray")
        self.color_label.pack(side=tk.RIGHT, padx=10)

        # Canvas
        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse events
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)

    def create_color_button(self, name, color):
        """Helper to create color buttons."""
        tk.Button(self.toolbar, text=name,
                  command=lambda c=color: self.select_color(c)).pack(side=tk.LEFT, padx=2)

    def select_color(self, color):
        """Set current drawing color."""
        self.current_color = color
        self.eraser_on = False
        self.update_color_label()

    def choose_color(self):
        """Open color chooser dialog."""
        color = colorchooser.askcolor()[1]
        if color:
            self.current_color = color
            self.eraser_on = False
            self.update_color_label()

    def use_eraser(self):
        """Activate eraser tool."""
        self.eraser_on = True
        self.update_color_label("Eraser")

    def change_size(self, value):
        """Update pen width from slider."""
        self.pen_width = int(value)

    def clear_canvas(self):
        """Clear entire canvas."""
        self.canvas.delete("all")

    def update_color_label(self, override=None):
        """Update UI label showing current tool/color."""
        if override:
            text = f"Current: {override}"
        else:
            text = f"Current: {self.current_color}"
        self.color_label.config(text=text)

    def start_draw(self, event):
        """Record starting point for drawing."""
        self.last_x, self.last_y = event.x, event.y

    def draw(self, event):
        """
        Draw on canvas as mouse moves.

        Uses line segments between last and current position
        for smooth drawing.
        """
        if self.last_x and self.last_y:
            color = "white" if self.eraser_on else self.current_color

            self.canvas.create_line(
                self.last_x, self.last_y,
                event.x, event.y,
                width=self.pen_width,
                fill=color,
                capstyle=tk.ROUND,
                smooth=True
            )

        self.last_x, self.last_y = event.x, event.y

    def stop_draw(self, event):
        """Reset tracking when mouse released."""
        self.last_x, self.last_y = None, None


if __name__ == "__main__":
    root = tk.Tk()
    app = PaintApp(root)
    root.mainloop()
