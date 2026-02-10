
    import tkinter as tk
    from tkinter import ttk, messagebox

    from tools.rollback_manager import list_snapshots, execute_rollback

    def open_rollback_window(parent, ambiente: str = "DEV"):
        win = tk.Toplevel(parent)
        win.title("Rollback de esquema (mixto)")
        win.geometry("480x260")

        tk.Label(win, text="Seleccione versión a la que desea hacer rollback:", font=("Segoe UI", 10, "bold")).pack(pady=5)

        snapshots = list_snapshots()
        combo_var = tk.StringVar()
        combo = ttk.Combobox(win, textvariable=combo_var, values=snapshots, state="readonly")
        combo.pack(fill="x", padx=10, pady=5)

        mode_var = tk.StringVar(value="mixed")
        tk.Label(win, text="Modo de rollback (estructura / datos):").pack(pady=(10,2))
        rb1 = ttk.Radiobutton(win, text="Sólo estructura", variable=mode_var, value="structure")
        rb2 = ttk.Radiobutton(win, text="Mixto (estructura + posibles datos)", variable=mode_var, value="mixed")
        rb1.pack(anchor="w", padx=20)
        rb2.pack(anchor="w", padx=20)

        def ejecutar():
            ver = combo_var.get()
            if not ver:
                messagebox.showwarning("Atención", "Seleccione una versión.")
                return
            m = mode_var.get()
            if m != "structure":
                # Prompt extra si no es sólo estructura
                if not messagebox.askyesno(
                    "Confirmación",
                    "Ha seleccionado un modo que POTENCIALMENTE puede afectar datos.
"
                    "¿Desea continuar de todas formas?"
                ):
                    return
            res = execute_rollback(ver.replace(".json", ""), ambiente=ambiente, mode=m)
            messagebox.showinfo("Rollback", f"Rollback planificado para versión {res.get('snapshot')} en modo {res.get('mode')}.")

        btn = ttk.Button(win, text="Ejecutar rollback", command=ejecutar)
        btn.pack(pady=15)

        ttk.Button(win, text="Cerrar", command=win.destroy).pack()
