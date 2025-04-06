import customtkinter as ctk
from PIL import ImageGrab, Image
from tkinter import Canvas, Toplevel, filedialog
import io
import win32clipboard
import time
import pytesseract

# https://customtkinter.tomschimansky.com/documentation/widgets
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class SnipTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("SnipTranslator")
        self.root.geometry("625x40")
        self.root.configure(fg_color="black")
        self.snipped_image = None
        self.snip_overlay = None
        self.rect = None
        self.delay_options = []
        self.main_ui()
        # Opening timing so that delay button is optional
        self.selected_delay = 0

    # UI
    def main_ui(self):
        # Main container frame with background
        menu_frame = ctk.CTkFrame(self.root, height=40,corner_radius=0,fg_color="#E9ECEF")
        menu_frame.grid(row=0, column=0, sticky="nsew", columnspan=7)
        # Makes the menu span full width
        self.root.grid_columnconfigure(0, weight=1)

        button_config = {
            "font" : ("", 15),
            "width" : 100,
            "height" : 40,
            "corner_radius" : 0,
            "text_color": "Black",
            "fg_color" : "#E9ECEF",
            "hover_color" : "#ADB5BD",
        }

        menu_config = {
            "font": ("", 15),
            "width": 100,
            "height": 40,
            "corner_radius": 0,
            "text_color": "Black",
            "fg_color": "#E9ECEF",
            "button_color": "#E9ECEF",
            "button_hover_color": "#ADB5BD",
            "dropdown_fg_color": "Black",
        }

        checkbox_config = {
            "font": ("", 15),
            "width": 100,
            "height": 40,
            "text_color": "Black",
            "fg_color": "#343A40",
            "bg_color" : "#E9ECEF",
            "hover_color": "#ADB5BD",
            "border_color": "#6C757D"
        }

        # Snip
        self.snip_button = ctk.CTkButton(menu_frame, text="Snip", **button_config, command=self.start_snip, )
        self.snip_button.grid(row=0, column=1, sticky="nw")

        # Delay with dropdown from 1-5 seconds
        self.delay_button = ctk.CTkOptionMenu(menu_frame, values=["No Delay","1", "2", "3", "4", "5"], **menu_config, command=self.delay_snip)
        self.delay_button.grid(row=0, column=2, sticky="nw")
        # Set default value
        self.delay_button.set("   Delay")

        # Save
        self.save_button = ctk.CTkButton(menu_frame, text="Save", **button_config, command=self.save_snip)
        self.save_button.grid(row=0, column=3, sticky="nw")

        # Clipboard
        self.copy_button = ctk.CTkButton(menu_frame, text="Copy", **button_config, command=self.clipboard_snip)
        self.copy_button.grid(row=0, column=4, sticky="nw")

        # Detect text in snip and make it so that we can copy text
        self.text_button = ctk.CTkCheckBox(menu_frame, text="To Text", **checkbox_config, command=self.text_detector)
        self.text_button.grid(row=0, column=5, sticky="nw", padx=(10,0))

        # Translate text in the snip
        self.translate_button = ctk.CTkCheckBox(menu_frame, text="Translate", **checkbox_config)
        self.translate_button.grid(row=0, column=6, sticky="nw", padx=(5,0))

        # Label to display the captured image
        self.label = ctk.CTkLabel(self.root, text="")
        self.label.grid(row=1, column=0, columnspan=5, pady=10)

        # Text box to OCR
        self.text_found = ctk.CTkTextbox(self.root, width=500, height=100)
        self.text_found.grid(row=2, column=0, columnspan=7)
        self.text_found.configure(state="disabled")
        # Hide text box
        self.text_found.grid_remove()

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
            self.root.geometry(f"{max(snip_width + 60, 625)}x{max(snip_height + 60, 40)}")
            self.root.deiconify()
            self.ctk_image = ctk.CTkImage(light_image=self.snipped_image, size=(snip_width, snip_height))
            self.label.configure(image=self.ctk_image)
            self.save_button.configure(state="normal")
            self.copy_button.configure(state="normal")

            if self.text_button.get() == 1:
                self.text_detector()

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

    # Detect text in the snipped image
    def text_detector(self):
        if self.text_button.get() == 1:
            self.text_found.grid()
            if self.snipped_image:
                text = pytesseract.image_to_string(self.snipped_image)
                self.text_found.configure(state="normal")  # Enable editing
                self.text_found.delete("0.0", "end")  # Clear previous text
                self.text_found.insert("1.0", text)
                #self.text_found.configure(state="disabled")  # Disable editing maybe
                #print("test")
        else:
            self.text_found.grid_remove()




if __name__ == "__main__":
    root = ctk.CTk()
    app = SnipTranslator(root)
    root.mainloop()