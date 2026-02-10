import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from cert_utils import cargar_certificado

def seleccionar_certificado():
    ruta = filedialog.askopenfilename(
        title="Seleccionar archivo .p12",
        filetypes=[("Certificados PKCS#12", "*.p12 *.pfx")]
    )
    if not ruta:
        return

    clave = simpledialog.askstring("Contraseña", "Introduce la clave del certificado:", show="*")

    try:
        resultado = cargar_certificado(ruta, clave)
        texto.delete("1.0", tk.END)
        texto.insert(tk.END, resultado)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el certificado:\n{e}")

# Ventana principal
root = tk.Tk()
root.title("Visor de Certificados .p12")
root.geometry("700x500")

frame = tk.Frame(root)
frame.pack(pady=10)

btn = tk.Button(frame, text="Cargar certificado .p12", command=seleccionar_certificado)
btn.pack()

texto = tk.Text(root, wrap="word")
texto.pack(expand=True, fill="both", padx=10, pady=10)

root.mainloop()
