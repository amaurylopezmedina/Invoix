import tkinter as tk
from tkinter import ttk
from config_gui import ConfigGUI

def main():
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()