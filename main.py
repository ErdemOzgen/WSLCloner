import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog, simpledialog
import subprocess
import os
import threading
import re
from pathlib import Path

class WSLClonerApp:
    def __init__(self, master):
        self.master = master
        master.title("WSL Snapshot Cloner")
        master.geometry("700x500")

        # Set the style to darkly theme
        style = ttk.Style("darkly")
        #master.iconbitmap('app_icon.ico')  # Ensure the path is correct
        # Set the application icon
        # Replace 'app_icon.ico' with the path to your icon file
        icon_path = Path(__file__).parent / 'app_icon.ico'
        if icon_path.exists():
            master.iconbitmap(str(icon_path))
        else:
            print("Icon file not found. Using default icon.")

        # Set the window background to match the dark theme
        master.configure(bg=style.colors.inputbg)

        # Create the main frame
        self.frame = ttk.Frame(master, padding=10)
        self.frame.pack(fill=BOTH, expand=True)

        # Treeview to display distros
        self.distro_tree = ttk.Treeview(
            self.frame, columns=("name",), show='tree', bootstyle="dark"
        )
        self.distro_tree.heading("#0", text="WSL Distributions", anchor=W)
        self.distro_tree.pack(side=LEFT, fill=BOTH, expand=True)

        # Scrollbar for the Treeview
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient=VERTICAL, command=self.distro_tree.yview, bootstyle="dark"
        )
        self.scrollbar.pack(side=LEFT, fill=Y)
        self.distro_tree.configure(yscrollcommand=self.scrollbar.set)

        # Buttons Frame
        self.buttons_frame = ttk.Frame(master, padding=10)
        self.buttons_frame.pack(fill=X)

        # Buttons
        self.clone_button = ttk.Button(
            self.buttons_frame, text="Clone Distro", command=self.clone_distro, bootstyle="primary-outline"
        )
        self.clone_button.pack(side=LEFT, padx=5, pady=5)

        self.export_button = ttk.Button(
            self.buttons_frame, text="Export Distro", command=self.export_distro, bootstyle="success-outline"
        )
        self.export_button.pack(side=LEFT, padx=5, pady=5)

        self.import_button = ttk.Button(
            self.buttons_frame, text="Import Distro", command=self.import_distro, bootstyle="info-outline"
        )
        self.import_button.pack(side=LEFT, padx=5, pady=5)

        self.delete_button = ttk.Button(
            self.buttons_frame, text="Delete Distro", command=self.delete_distro, bootstyle="danger-outline"
        )
        self.delete_button.pack(side=LEFT, padx=5, pady=5)

        self.refresh_button = ttk.Button(
            self.buttons_frame, text="Refresh List", command=self.load_distros, bootstyle="warning-outline"
        )
        self.refresh_button.pack(side=LEFT, padx=5, pady=5)

        # Status Label
        self.status_label = ttk.Label(
            master, text="Ready", anchor=W, bootstyle="inverse-dark"
        )
        self.status_label.pack(side=BOTTOM, fill=X)

        # Load distros
        self.load_distros()

    def set_status(self, message):
        self.status_label.config(text=message)
        self.master.update_idletasks()

    def load_distros(self):
        self.set_status("Loading distros...")
        distros = list_distros()
        # Clear the existing items in the Treeview
        for item in self.distro_tree.get_children():
            self.distro_tree.delete(item)
        for index, distro in enumerate(distros):
            self.distro_tree.insert("", END, iid=index, text=distro['name'])
        self.set_status("Distros loaded.")

    def get_selected_distro(self):
        selected_item = self.distro_tree.focus()
        if not selected_item:
            return None
        distro_name = self.distro_tree.item(selected_item, 'text')
        return distro_name

    def clone_distro(self):
        selected = self.get_selected_distro()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a distro to clone.")
            return
        new_name = simpledialog.askstring("Clone Distro", "Enter new distro name:")
        if new_name:
            self.set_status(f"Cloning '{selected}' to '{new_name}'...")
            threading.Thread(target=self.clone_distro_async, args=(selected, new_name)).start()

    def clone_distro_async(self, original_name, new_name):
        try:
            clone_distro(original_name, new_name)
            messagebox.showinfo("Success", f"Distro '{original_name}' cloned as '{new_name}'.")
            self.load_distros()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.set_status("Ready")

    def export_distro(self):
        selected = self.get_selected_distro()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a distro to export.")
            return
        export_path = filedialog.asksaveasfilename(
            defaultextension=".tar", filetypes=[("TAR files", "*.tar")]
        )
        if export_path:
            self.set_status(f"Exporting '{selected}' to '{export_path}'...")
            threading.Thread(target=self.export_distro_async, args=(selected, export_path)).start()

    def export_distro_async(self, distro_name, export_path):
        try:
            export_distro(distro_name, export_path)
            messagebox.showinfo("Success", f"Distro '{distro_name}' exported to '{export_path}'.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.set_status("Ready")

    def import_distro(self):
        import_path = filedialog.askopenfilename(filetypes=[("TAR files", "*.tar")])
        if import_path:
            distro_name = simpledialog.askstring("Import Distro", "Enter name for the imported distro:")
            if distro_name:
                install_location = filedialog.askdirectory()
                if install_location:
                    self.set_status(f"Importing '{distro_name}' from '{import_path}'...")
                    threading.Thread(
                        target=self.import_distro_async,
                        args=(distro_name, install_location, import_path)
                    ).start()
                else:
                    messagebox.showwarning("No Install Location", "Please select an install location.")
            else:
                messagebox.showwarning("No Distro Name", "Please enter a name for the imported distro.")

    def import_distro_async(self, distro_name, install_location, import_path):
        try:
            import_distro(distro_name, install_location, import_path)
            messagebox.showinfo("Success", f"Distro imported as '{distro_name}'.")
            self.load_distros()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.set_status("Ready")

    def delete_distro(self):
        selected = self.get_selected_distro()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a distro to delete.")
            return
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the distro '{selected}'?\nThis action cannot be undone.",
            icon='warning'
        )
        if confirm:
            self.set_status(f"Deleting '{selected}'...")
            threading.Thread(target=self.delete_distro_async, args=(selected,)).start()

    def delete_distro_async(self, distro_name):
        try:
            delete_distro(distro_name)
            messagebox.showinfo("Success", f"Distro '{distro_name}' has been deleted.")
            self.load_distros()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            self.set_status("Ready")

def list_distros():
    result = subprocess.run(['wsl', '--list', '--all'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_bytes = result.stdout

    # Decode with 'utf-16le' to handle encoding issues
    try:
        output = output_bytes.decode('utf-16le').strip()
    except UnicodeDecodeError:
        # Fallback to 'utf-8' if needed
        output = output_bytes.decode('utf-8').strip()

    # Debug print statements
    print("WSL List Output:\n", output)
    lines = output.split('\n')
    distros = []

    # Skip lines until we reach the header separator (line with dashes)
    separator_found = False
    for line in lines:
        line = line.strip()
        if not separator_found:
            if re.match(r'^(-+\s*)+$', line):
                separator_found = True
            continue
        else:
            # Remove any leading/trailing whitespace and asterisks
            name = line.strip().strip('*').strip()
            if name:
                # Remove '(Default)' suffix if present
                name = re.sub(r'\s*\(Default\)$', '', name)
                # Exclude Docker WSL distros
                if name.lower() in ['docker-desktop', 'docker-desktop-data']:
                    continue
                distros.append({'name': name})

    # If separator wasn't found, assume there's no header and parse all lines after the first
    if not separator_found:
        for line in lines[1:]:
            name = line.strip().strip('*').strip()
            if name:
                # Remove '(Default)' suffix if present
                name = re.sub(r'\s*\(Default\)$', '', name)
                # Exclude Docker WSL distros
                if name.lower() in ['docker-desktop', 'docker-desktop-data']:
                    continue
                distros.append({'name': name})

    # Debug print statement
    print("Parsed Distros:", distros)
    return distros


def is_distro_running(distro_name):
    result = subprocess.run(['wsl', '-l', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    output = result.stdout
    lines = output.strip().split('\n')
    # Skip the header line
    for line in lines[1:]:
        # Match lines like:
        # * Ubuntu           Running         2
        #   Debian           Stopped         2
        match = re.match(r'\s*(\*?)\s*(.+?)\s{2,}(\w+)\s+(\d+)', line)
        if match:
            name = match.group(2).strip()
            state = match.group(3).strip()
            if name == distro_name:
                return state.lower() == 'running'
    return False

def clone_distro(original_name, new_name):
    temp_export_path = os.path.join(os.environ.get('TEMP'), f"{original_name}.tar")
    was_running = is_distro_running(original_name)
    if was_running:
        # Stop the distro
        subprocess.run(['wsl', '--terminate', original_name], check=True)
    try:
        # Export the original distro
        subprocess.run(['wsl', '--export', original_name, temp_export_path], check=True)
        # Import as new distro
        install_location = os.path.join("C:\\WSL", new_name)
        os.makedirs(install_location, exist_ok=True)
        subprocess.run(['wsl', '--import', new_name, install_location, temp_export_path], check=True)
    finally:
        # Clean up
        if os.path.exists(temp_export_path):
            os.remove(temp_export_path)
        # If the original distro was running, start it again
        if was_running:
            subprocess.run(['wsl', '-d', original_name, '-e', 'exit'], check=True)

def export_distro(distro_name, export_path):
    subprocess.run(['wsl', '--export', distro_name, export_path], check=True)

def import_distro(distro_name, install_location, import_path):
    subprocess.run(['wsl', '--import', distro_name, install_location, import_path], check=True)

def delete_distro(distro_name):
    subprocess.run(['wsl', '--unregister', distro_name], check=True)

def main():
    app = ttk.Window(themename="darkly")
    WSLClonerApp(app)
    app.mainloop()

if __name__ == "__main__":
    main()
