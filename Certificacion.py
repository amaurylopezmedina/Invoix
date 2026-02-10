import tkinter as tk
from tkinter import ttk

class VentanaPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Mi Aplicación")
        
        # Maximizar la ventana
        self.root.state('zoomed')  # En Windows esto maximiza la ventana
        
        # Crear un frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Crear los 5 botones
        self.boton1 = ttk.Button(main_frame, text="Botón 1", command=self.funcion_boton1)
        self.boton1.grid(row=0, column=0, padx=5, pady=5)
        
        self.boton2 = ttk.Button(main_frame, text="Botón 2", command=self.funcion_boton2)
        self.boton2.grid(row=1, column=0, padx=5, pady=5)
        
        self.boton3 = ttk.Button(main_frame, text="Botón 3", command=self.funcion_boton3)
        self.boton3.grid(row=2, column=0, padx=5, pady=5)
        
        self.boton4 = ttk.Button(main_frame, text="Botón 4", command=self.funcion_boton4)
        self.boton4.grid(row=3, column=0, padx=5, pady=5)
        
        self.boton5 = ttk.Button(main_frame, text="Botón 5", command=self.funcion_boton5)
        self.boton5.grid(row=4, column=0, padx=5, pady=5)

    # Aquí defines las funciones para cada botón
    def funcion_boton1(self):
        # Agrega aquí el código que quieres que ejecute el botón 1
        print("Botón 1 presionado")
    
    def funcion_boton2(self):
        # Agrega aquí el código que quieres que ejecute el botón 2
        print("Botón 2 presionado")
    
    def funcion_boton3(self):
        # Agrega aquí el código que quieres que ejecute el botón 3
        print("Botón 3 presionado")
    
    def funcion_boton4(self):
        # Agrega aquí el código que quieres que ejecute el botón 4
        print("Botón 4 presionado")
    
    def funcion_boton5(self):
        # Agrega aquí el código que quieres que ejecute el botón 5
        print("Botón 5 presionado")

# Crear y ejecutar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = VentanaPrincipal(root)
    root.mainloop()