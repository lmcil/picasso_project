"""
Contact Book Application - Console Version
A simple CRUD (Create, Read, Update, Delete) application for managing contacts.

This application allows users to:
- Add new contacts with Name, Phone, Address, and Email
- View all saved contacts
- Search for contacts by name
- Delete contacts
- Store data persistently in a JSON file

Author: Student Developer
Course: Introduction to Python
File: contact_book.py
"""

import json  # Used to read and write JSON files
import os    # Used to check if files exist
import re    # Regular expressions for validation


class ContactBook:
    """
    Main class that handles all contact book operations.
    This class manages contacts and their storage in a JSON file.
    """
    
    def __init__(self, filename="contacts.json"):
        """
        Initialize the contact book.
        
        Args:
            filename (str): Name of the JSON file to store contacts.
                           Default is "contacts.json"
        
        The __init__ method runs automatically when we create a ContactBook object.
        It sets up the filename and loads existing contacts from the file.
        """
        self.filename = filename  # Store the filename for later use
        self.contacts = []        # Empty list to hold all contact dictionaries
        self.load_contacts()      # Load existing contacts from file (if any)
    
    def load_contacts(self):
        """
        Load contacts from the JSON file into memory.
        
        This method reads the contacts.json file and loads all saved contacts
        into the self.contacts list. If the file doesn't exist yet, it starts
        with an empty list.
        
        Requirement 1 & 7: Load persisted data from JSON file
        """
        # Check if the JSON file exists
        if os.path.exists(self.filename):
            try:
                # Open the file in read mode
                with open(self.filename, 'r') as file:
                    # Load JSON data and convert it to a Python list
                    self.contacts = json.load(file)
                print(f"✓ Loaded {len(self.contacts)} contact(s) from {self.filename}")
            except json.JSONDecodeError:
                # If the file is corrupted or empty, start with empty list
                print(f"⚠ Warning: {self.filename} is corrupted. Starting fresh.")
                self.contacts = []
            except Exception as e:
                # Catch any other errors that might occur
                print(f"⚠ Error loading contacts: {e}")
                self.contacts = []
        else:
            # File doesn't exist yet, so start with empty list
            print(f"ℹ {self.filename} not found. Starting with empty contact list.")
            self.contacts = []
    
    def save_contacts(self):
        """
        Save all contacts to the JSON file.
        
        This method writes the entire self.contacts list to the JSON file,
        ensuring data persists even after the program closes.
        
        Requirement 1 & 7: Persist data in JSON file
        """
        try:
            # Open file in write mode (creates file if it doesn't exist)
            with open(self.filename, 'w') as file:
                # Convert Python list to JSON and write to file
                # indent=4 makes the JSON file human-readable with nice formatting
                json.dump(self.contacts, file, indent=4)
            print(f"✓ Contacts saved to {self.filename}")
        except Exception as e:
            # If saving fails, let the user know
            print(f"✗ Error saving contacts: {e}")
    
    def validate_name(self, name):
        """
        Validate that a name contains only letters and spaces.
        
        Args:
            name (str): The name to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Requirement 6: Reject improper data (names with numbers)
        """
        # Check if name is empty or only spaces
        if not name or not name.strip():
            return False
        
        # Regular expression: ^ means start, $ means end
        # [a-zA-Z ] means only uppercase, lowercase letters, and spaces
        # + means one or more characters
        # This pattern ensures only letters and spaces are allowed
        pattern = r'^[a-zA-Z ]+$'
        
        # re.match returns a match object if pattern matches, None otherwise
        return re.match(pattern, name) is not None
    
    def validate_phone(self, phone):
        """
        Validate that a phone number contains only digits and optional dashes/spaces.
        
        Args:
            phone (str): The phone number to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Requirement 6: Reject improper data (numbers with non-digits)
        """
        # Check if phone is empty
        if not phone or not phone.strip():
            return False
        
        # Remove common separators (spaces, dashes, parentheses)
        # This allows formats like: 123-456-7890, (123) 456-7890, 123 456 7890
        clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Check if what's left is all digits and has reasonable length
        return clean_phone.isdigit() and 10 <= len(clean_phone) <= 15
    
    def validate_email(self, email):
        """
        Validate that an email has a basic valid format.
        
        Args:
            email (str): The email address to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Requirement 5: Error handling for invalid data
        """
        # Check if email is empty
        if not email or not email.strip():
            return False
        
        # Basic email pattern: something@something.something
        # This is a simplified pattern - real email validation is very complex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        return re.match(pattern, email) is not None
    
    def add_contact(self):
        """
        Add a new contact to the contact book.
        
        This method prompts the user for contact information, validates it,
        and saves it to the contacts list and JSON file.
        
        Requirement 1: Add contact with Name, Phone, Address, Email
        """
        print("\n" + "="*50)
        print("ADD NEW CONTACT")
        print("="*50)
        
        # Get and validate name (Requirement 6: validation)
        while True:
            name = input("Enter Name: ").strip()
            if self.validate_name(name):
                break  # Valid name, exit the loop
            else:
                # Show error message and ask again
                print("✗ Invalid name. Please use only letters and spaces.")
        
        # Get and validate phone number (Requirement 6: validation)
        while True:
            phone = input("Enter Phone Number: ").strip()
            if self.validate_phone(phone):
                break  # Valid phone, exit the loop
            else:
                # Show error message and ask again
                print("✗ Invalid phone number. Please use only digits (and optional dashes/spaces).")
        
        # Get address (no strict validation needed for address)
        address = input("Enter Address: ").strip()
        
        # Get and validate email (Requirement 5: error handling)
        while True:
            email = input("Enter Email: ").strip()
            if self.validate_email(email):
                break  # Valid email, exit the loop
            else:
                # Show error message and ask again
                print("✗ Invalid email format. Please enter a valid email (e.g., user@example.com).")
        
        # Create a dictionary to represent the contact
        # Dictionary is like a container with key-value pairs
        contact = {
            "name": name,
            "phone": phone,
            "address": address,
            "email": email
        }
        
        # Add the contact dictionary to our list of contacts
        self.contacts.append(contact)
        
        # Save to JSON file immediately (Requirement 1: persistent storage)
        self.save_contacts()
        
        print(f"\n✓ Contact '{name}' added successfully!")
    
    def view_contacts(self):
        """
        Display all contacts in a formatted list.
        
        Requirement 2: View list of all contacts
        """
        print("\n" + "="*50)
        print("ALL CONTACTS")
        print("="*50)
        
        # Check if there are any contacts to display
        if not self.contacts:
            print("No contacts found. Add some contacts first!")
            return
        
        # Loop through each contact and display its information
        # enumerate() gives us both the index and the contact
        for index, contact in enumerate(self.contacts, start=1):
            # Print contact number and details
            print(f"\n[{index}] {contact['name']}")
            print(f"    📞 Phone: {contact['phone']}")
            print(f"    🏠 Address: {contact['address']}")
            print(f"    📧 Email: {contact['email']}")
        
        # Print total count at the end
        print(f"\n{'='*50}")
        print(f"Total: {len(self.contacts)} contact(s)")
    
    def search_contact(self):
        """
        Search for a contact by name.
        
        This method allows partial name matching (case-insensitive).
        For example, searching "john" will find "John Doe".
        
        Requirement 4: Search for specific contact
        """
        print("\n" + "="*50)
        print("SEARCH CONTACT")
        print("="*50)
        
        # Get search term from user
        search_term = input("Enter name to search: ").strip()
        
        # Check if search term is empty
        if not search_term:
            print("✗ Please enter a name to search.")
            return
        
        # Find all contacts that match the search term
        # We use .lower() to make the search case-insensitive
        # 'in' checks if search_term is contained in the contact's name
        found_contacts = [
            contact for contact in self.contacts 
            if search_term.lower() in contact['name'].lower()
        ]
        
        # Display results
        if found_contacts:
            print(f"\n✓ Found {len(found_contacts)} contact(s):")
            
            # Display each found contact
            for index, contact in enumerate(found_contacts, start=1):
                print(f"\n[{index}] {contact['name']}")
                print(f"    📞 Phone: {contact['phone']}")
                print(f"    🏠 Address: {contact['address']}")
                print(f"    📧 Email: {contact['email']}")
        else:
            # No matches found
            print(f"✗ No contacts found matching '{search_term}'")
    
    def delete_contact(self):
        """
        Delete a contact by name.
        
        This method searches for a contact by exact name match and removes it.
        
        Requirement 3: Delete contact by name
        """
        print("\n" + "="*50)
        print("DELETE CONTACT")
        print("="*50)
        
        # First, show all contacts so user knows what's available
        if not self.contacts:
            print("No contacts to delete.")
            return
        
        # Display current contacts
        print("\nCurrent contacts:")
        for index, contact in enumerate(self.contacts, start=1):
            print(f"[{index}] {contact['name']}")
        
        # Get the name of contact to delete
        name_to_delete = input("\nEnter the exact name of contact to delete: ").strip()
        
        # Check if name is empty
        if not name_to_delete:
            print("✗ Please enter a name.")
            return
        
        # Search for the contact with exact name match (case-insensitive)
        # We'll use a flag to track if we found and deleted the contact
        contact_found = False
        
        # Loop through contacts to find matching name
        for i, contact in enumerate(self.contacts):
            # Compare names (case-insensitive)
            if contact['name'].lower() == name_to_delete.lower():
                # Found the contact! Ask for confirmation
                print(f"\nFound: {contact['name']}")
                print(f"Phone: {contact['phone']}")
                
                # Ask user to confirm deletion
                confirm = input("\nAre you sure you want to delete? (yes/no): ").strip().lower()
                
                if confirm in ['yes', 'y']:
                    # Remove contact from list
                    deleted_contact = self.contacts.pop(i)
                    
                    # Save updated list to file
                    self.save_contacts()
                    
                    print(f"✓ Contact '{deleted_contact['name']}' deleted successfully!")
                    contact_found = True
                else:
                    print("✗ Deletion cancelled.")
                    contact_found = True
                
                break  # Exit loop after finding the contact
        
        # If we went through all contacts and didn't find a match
        if not contact_found:
            print(f"✗ No contact found with name '{name_to_delete}'")
    
    def display_menu(self):
        """
        Display the main menu options to the user.
        
        Requirement 5: Display menu options
        """
        print("\n" + "="*50)
        print("CONTACT BOOK - MAIN MENU")
        print("="*50)
        print("1. Add Contact")
        print("2. View All Contacts")
        print("3. Search Contact")
        print("4. Delete Contact")
        print("5. Exit")
        print("="*50)
    
    def run(self):
        """
        Main program loop.
        
        This method displays the menu and handles user choices.
        It keeps running until the user chooses to exit.
        
        Requirement 5: Menu-driven interface
        """
        # Print welcome message
        print("\n" + "🔖"*25)
        print("WELCOME TO CONTACT BOOK")
        print("🔖"*25)
        
        # Main program loop - runs forever until user exits
        while True:
            # Display the menu
            self.display_menu()
            
            # Get user's choice
            choice = input("\nEnter your choice (1-5): ").strip()
            
            # Execute the appropriate function based on user's choice
            # This is called a "dispatch" pattern
            if choice == '1':
                self.add_contact()
            elif choice == '2':
                self.view_contacts()
            elif choice == '3':
                self.search_contact()
            elif choice == '4':
                self.delete_contact()
            elif choice == '5':
                # Exit the program
                print("\n" + "="*50)
                print("Thank you for using Contact Book!")
                print(f"Your contacts are saved in {self.filename}")
                print("="*50)
                break  # Exit the while loop, ending the program
            else:
                # Invalid choice
                print("\n✗ Invalid choice. Please enter a number between 1 and 5.")
            
            # Pause before showing menu again (optional)
            # This makes it easier to read the output
            input("\nPress Enter to continue...")


# This is the entry point of the program
# The code below only runs if this file is run directly (not imported)
if __name__ == "__main__":
    # Create a ContactBook object
    # This automatically loads any existing contacts from contacts.json
    contact_book = ContactBook()
    
    # Start the main program loop
    contact_book.run()