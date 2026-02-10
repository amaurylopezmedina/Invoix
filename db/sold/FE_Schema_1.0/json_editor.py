
import json, tkinter as tk
from tkinter import filedialog, messagebox

def open_json():
    path = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
    if not path: return
    with open(path, 'r', encoding='utf-8') as f:
        text.delete("1.0", tk.END)
        text.insert(tk.END, f.read())
    root.current_path = path

def save_json():
    if not hasattr(root, 'current_path'):
        return
    with open(root.current_path, 'w', encoding='utf-8') as f:
        f.write(text.get("1.0", tk.END))
    messagebox.showinfo("Guardado", "JSON guardado correctamente")

root = tk.Tk()
root.title("Editor de Schema JSON FE")

text = tk.Text(root, wrap="none")
text.pack(expand=True, fill="both")

menu = tk.Menu(root)
menu.add_command(label="Abrir", command=open_json)
menu.add_command(label="Guardar", command=save_json)
root.config(menu=menu)

root.mainloop()
