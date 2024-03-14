import tkinter as tk
from tkinter import scrolledtext, messagebox
import pandas as pd
from main import configure_start
import threading
import logging

logger = logging.getLogger(__name__)

class Application(tk.Tk):
    """
    Application class for the CSV application GUI.
    """
    def __init__(self, file_path: str) -> None:
        """
        Initialize the Application class.
        :param file_path: Path to the CSV file.
        """
        super().__init__()
        self.title('CSV Application')
        self.geometry('1000x1000')
        self.file_path = file_path
        self.driver = None

        # GUI elements
        self.create_widgets()

    def create_widgets(self) -> None:
        """
        Create GUI widgets.
        :return: None
        """
        # Button to load CSV file
        self.load_button = tk.Button(self, text='Load CSV', command=self.load_csv)
        self.load_button.pack()

        # Fields for entering URL and password
        self.label_url = tk.Label(self, text="Enter URL:")
        self.label_url.pack()
        self.url_entry = tk.Entry(self, width=50)
        self.url_entry.pack()

        self.label_password = tk.Label(self, text="Enter Password:")
        self.label_password.pack()
        self.password_entry = tk.Entry(self, show="*", width=50)
        self.password_entry.pack()

        self.log_button = tk.Button(self, text='Configure CSV', command=self.configure)
        self.log_button.pack()

        # Area for displaying logs
        self.csv_area = scrolledtext.ScrolledText(self, state='disabled', height=30, width=120)
        self.csv_area.pack()

        # Other UI elements
        self.close_button = tk.Button(self, text='Close window', command=self.close_browser)
        self.close_button.pack()

    def load_csv(self) -> None:
        """
        Load and display CSV data.
        :return: None
        """
        try:
            pd.set_option('display.max_columns', None)  # Display all columns
            pd.set_option('display.width', 1000)  # Increase display width
            df = pd.read_csv(self.file_path, sep=';')
            messagebox.showinfo("Success", "CSV file has been loaded.")
            self.csv_area.config(state='normal')
            self.csv_area.delete(1.0, tk.END)  # Clear the area before inserting new data
            self.csv_area.insert(tk.END, str(df) + '\n')
            self.csv_area.config(state='disabled')
            logging.info("CSV file has been loaded.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            logging.error(f"Error loading CSV file: {e}")

    def configure(self, **kwargs) -> None:
        """
        Configure the CSV application.
        :param kwargs: Additional parameters.
        :return: None
        """
        url = self.url_entry.get()
        password = self.password_entry.get()
        file_path = self.file_path

        def run_configuration():
            try:
                self.driver = configure_start(url, password, file_path)
                if self.driver:
                    messagebox.showinfo("Success", "Configuration successfully completed.")
                    logging.info("Configuration successfully completed.")
                else:
                    messagebox.showerror("Error", "Configuration failed.")
                    logging.error("Configuration failed.")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred during configuration: {e}")
                logging.error(f"Error during configuration: {e}")

        config_thread = threading.Thread(target=run_configuration)
        config_thread.start()

    def close_browser(self) -> None:
        """
        Close the browser window.
        :return: None
        """
        if self.driver:
            self.driver.quit()
            self.driver = None

if __name__ == "__main__":
    app = Application('data/PowerTags.csv')
    app.mainloop()
