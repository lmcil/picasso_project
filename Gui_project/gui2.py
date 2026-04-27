import json
import os
import re
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

class ContactBookGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Contact Book Pro")
        self.root.geometry("800x600")
        
        # --- State Management ---
        self.filename = "contacts.json"
        self.contacts = []
        self.selected_index = None  # Tracks which contact is being edited
        
        self._setup_styles()
        self._build_ui()
        self.load_contacts(self.filename)

    def _setup_styles(self):
        """Define custom styles for the GUI components."""
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        style.configure("Action.TButton", font=("Arial", 10))

    def _build_ui(self):
        """Create the layout: Input fields on top, List/Search on bottom."""
        # Top Frame: Input Fields
        input_frame = ttk.LabelFrame(self.root, text=" Contact Details ", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # Labels and Entry Widgets
        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(input_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Phone:").grid(row=0, column=2, sticky="w")
        self.phone_var = tk.StringVar()
        self.phone_entry = ttk.Entry(input_frame, textvariable=self.phone_var, width=30)
        self.phone_entry.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(input_frame, text="Email:").grid(row=1, column=0, sticky="w")
        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(input_frame, textvariable=self.email_var, width=30)
        self.email_entry.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Address:").grid(row=1, column=2, sticky="w")
        self.address_var = tk.StringVar()
        self.address_entry = ttk.Entry(input_frame, textvariable=self.address_var, width=30)
        self.address_entry.grid(row=1, column=3, padx=5, pady=2)

        # Button Row for Actions
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        self.btn_add = ttk.Button(btn_frame, text="Add Contact", command=self.save_contact_action)
        self.btn_add.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Clear Fields", command=self.clear_inputs).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_contact_action).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Change JSON File", command=self.change_file_dialog).pack(side="left", padx=5)

        # Middle Frame: Search
        search_frame = ttk.Frame(self.root, padding=5)
        search_frame.pack(fill="x", padx=10)
        ttk.Label(search_frame, text="Search Name:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_list())
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side="left", fill="x", expand=True, padx=5)

        # Bottom Frame: The Listview (Treeview)
        list_frame = ttk.Frame(self.root, padding=10)
        list_frame.pack(fill="both", expand=True)

        columns = ("name", "phone", "email", "address")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        self.tree.heading("name", text="Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("email", text="Email")
        self.tree.heading("address", text="Address")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_contact_select)

        # Scrollbar for List
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    # --- Data Logic ---

    def load_contacts(self, filepath):
        """Loads data from JSON and updates the UI."""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    self.contacts = json.load(f)
                self.filename = filepath
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_to_disk(self):
        """Persists the current contacts list to the active JSON file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.contacts, f, indent=4)
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def refresh_list(self):
        """Updates the Treeview based on the contacts list and search filter."""
        # Clear current tree
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        search_term = self.search_var.get().lower()
        
        for index, c in enumerate(self.contacts):
            if search_term in c['name'].lower():
                self.tree.insert("", "end", iid=index, values=(c['name'], c['phone'], c['email'], c['address']))

    # --- Handlers ---

    def save_contact_action(self):
        """Handles both adding a new contact and updating an existing one."""
        name = self.name_var.get().strip()
        phone = self.phone_var.get().strip()
        email = self.email_var.get().strip()
        address = self.address_var.get().strip()

        # Validation logic (Requirements 5 & 6)
        if not re.match(r'^[a-zA-Z ]+$', name):
            return messagebox.showwarning("Input Error", "Name must only contain letters.")
        if not phone.replace('-', '').replace(' ', '').isdigit():
            return messagebox.showwarning("Input Error", "Phone must contain digits.")
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return messagebox.showwarning("Input Error", "Invalid Email format.")

        new_data = {"name": name, "phone": phone, "email": email, "address": address}

        if self.selected_index is not None:
            # Update existing (Requirement: Ability to update existing contact)
            self.contacts[self.selected_index] = new_data
            messagebox.showinfo("Success", "Contact updated successfully!")
        else:
            # Create new
            self.contacts.append(new_data)
            messagebox.showinfo("Success", "Contact added successfully!")

        self.save_to_disk()
        self.clear_inputs()
        self.refresh_list()

    def delete_contact_action(self):
        """Removes the selected contact from the list and JSON."""
        if self.selected_index is None:
            return messagebox.showwarning("Selection", "Please select a contact to delete.")
        
        if messagebox.askyesno("Confirm", "Delete this contact?"):
            self.contacts.pop(self.selected_index)
            self.save_to_disk()
            self.clear_inputs()
            self.refresh_list()

    def change_file_dialog(self):
        """Opens a file dialog to switch to a different JSON file (New Requirement)."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            self.load_contacts(file_path)
            messagebox.showinfo("File Loaded", f"Active file: {os.path.basename(file_path)}")

    def on_contact_select(self, event):
        """When a user clicks a contact in the list, fill the entries for editing."""
        selected_items = self.tree.selection()
        if selected_items:
            # Get the internal index we stored in the iid
            self.selected_index = int(selected_items[0])
            contact = self.contacts[self.selected_index]
            
            self.name_var.set(contact['name'])
            self.phone_var.set(contact['phone'])
            self.email_var.set(contact['email'])
            self.address_var.set(contact['address'])
            self.btn_add.config(text="Update Contact")

    def clear_inputs(self):
        """Resets the form and deselects items."""
        self.name_var.set("")
        self.phone_var.set("")
        self.email_var.set("")
        self.address_var.set("")
        self.selected_index = None
        self.btn_add.config(text="Add Contact")
        self.tree.selection_remove(self.tree.selection())

if __name__ == "__main__":
    root = tk.Tk()
    app = ContactBookGUI(root)
    root.mainloop()