import customtkinter as ctk
from PIL import ImageGrab, Image
from tkinter import Canvas, Toplevel, filedialog
import io
import win32clipboard
import time

class SnipTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("SnipTranslator")
        self.root.geometry("500x85")
        self.snipped_image = None
        self.snip_overlay = None
        self.rect = None
        self.delay_options = []
        self.main_ui()
        # Opening timing so that delay button is optional
        self.selected_delay = 0

    # UI
    def main_ui(self):
        # Snip
        self.snip_button = ctk.CTkButton(self.root, text="Snip", font=("", 15), width=100, height=40,command=self.start_snip)
        self.snip_button.grid(row=0, column=1, sticky="n")

        # Delay with dropdown from 1-5 seconds
        self.delay_button = ctk.CTkOptionMenu(self.root, values=["No Delay","1", "2", "3", "4", "5"], font=("", 15), width=100, height=40, command=self.delay_snip)
        self.delay_button.grid(row=0, column=2, sticky="n")
        # Set default value
        self.delay_button.set("Delay")

        # Save
        self.save_button = ctk.CTkButton(self.root, text="Save", font=("", 15), width=100, height=40, command=self.save_snip)
        self.save_button.grid(row=0, column=3, sticky="n")

        # Clipboard
        self.copy_button = ctk.CTkButton(self.root, text="Copy", font=("", 15), width=100, height=40, command=self.clipboard_snip)
        self.copy_button.grid(row=0, column=4, sticky="n")

        # Label to display the captured image
        self.label = ctk.CTkLabel(self.root, text="")
        self.label.grid(row=1, column=0, columnspan=5, pady=10)

    # Start snip process
    def start_snip(self):
        # Hide main window so that it does not block anything
        self.root.withdraw()

        # Get delay timing
        time.sleep(self.selected_delay)

        # Cover screen with grey overlay
        self.snip_overlay = Toplevel()
        self.snip_overlay.attributes('-fullscreen', True, '-alpha', 0.4, '-topmost', True)
        self.snip_overlay.configure(bg='grey')
        self.snip_overlay.overrideredirect(True)

        # Canvas for drawing
        self.canvas = Canvas(self.snip_overlay, cursor="cross", bg="gray", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Mouse click event when snipping
        self.canvas.bind("<ButtonPress-1>", self.button_press)
        self.canvas.bind("<B1-Motion>", self.mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.button_release)

    # Start drawing box with user mouse click
    def button_press(self, event):
        # Starting point
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red",width=1)

    def mouse_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def button_release(self, event):
        if self.rect:
            # Ensure coordinates are sorted to get the correct top-left and bottom-right corners
            x1, x2 = sorted([self.start_x, event.x])
            y1, y2 = sorted([self.start_y, event.y])

            # Hide overlay and capture the selected screen area
            self.snip_overlay.withdraw()
            self.snipped_image = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            self.snip_overlay.destroy()
            self.snip_overlay = None

            # Makes the window resize based on snip taken but make sure it does not become smaller than main
            snip_width, snip_height = self.snipped_image.size
            self.root.geometry(f"{max(snip_width, 400)}x{max(snip_height, 85)}")
            self.root.deiconify()
            self.ctk_image = ctk.CTkImage(light_image=self.snipped_image, size=(snip_width, snip_height))
            self.label.configure(image=self.ctk_image)
            self.save_button.configure(state="normal")
            self.copy_button.configure(state="normal")

    # Add delay to snip:
    def delay_snip(self, choice):
        if choice == "No Delay":
            self.selected_delay = 0
        else:
            self.selected_delay = int(choice)
        self.delay_button.set("Delay")
        # print(f"Delay: {choice}")

    # Save snipped image to file
    def save_snip(self):
        if self.snipped_image:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png", filetypes=[("PNG File", "*.png"), ("JPEG File", "*.jpg"), ("All files", "*.*")]
            )
            if file_path:
                self.snipped_image.save(file_path)
                # print(f"Saved to {file_path}")

    # Copy image to clipboard *For windows only*
    def clipboard_snip(self):
        if self.snipped_image:
            output = io.BytesIO()
            self.snipped_image.save(output, format="PNG")
            data = output.getvalue()
            CF_PNG = win32clipboard.RegisterClipboardFormat("PNG")

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(CF_PNG, data)
            win32clipboard.CloseClipboard()



if __name__ == "__main__":
    root = ctk.CTk()
    app = SnipTranslator(root)
    root.mainloop()