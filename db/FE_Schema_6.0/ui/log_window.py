
import tkinter as tk

_UI_CALLBACKS = []

def attach_ui_logger(callback):
    _UI_CALLBACKS.append(callback)

def ui_log(msg: str):
    for cb in _UI_CALLBACKS:
        try:
            cb(msg)
        except Exception:
            pass

class LogWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Logs en tiempo real")
        self.geometry("820x420")

        self.text = tk.Text(self, state="disabled", wrap="none")
        self.text.pack(expand=True, fill="both")

    def append(self, msg: str):
        self.text.config(state="normal")
        self.text.insert("end", msg + "\n")
        self.text.see("end")
        self.text.config(state="disabled")
