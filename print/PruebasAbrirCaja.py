import tkinter as tk
from tkinter import ttk, messagebox
import win32print
import threading
import time
import sys


class CajonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Cajón de Dinero")
        self.root.geometry("600x650")
        self.root.resizable(True, True)

        # Diccionario de comandos
        self.COMANDOS_CAJON = {
            # Epson
            "EPSON_TM_T88": b"\x1b\x70\x00\x32\xfa",  # Epson TM-T88 (conector 1)
            "EPSON_TM_T88_ALT": b"\x1b\x70\x01\x32\xfa",  # Epson TM-T88 (conector 2)
            "EPSON_TM_T20": b"\x1b\x70\x00\x19\xfa",  # Epson TM-T20
            "EPSON_TM_U220": b"\x1b\x70\x00\x32\x64",  # Epson TM-U220
            "EPSON_TM_P20": b"\x1b\x70\x00\x28\x64",  # Epson TM-P20
            "EPSON_TM_H6000": b"\x1b\x70\x00\x32\xc8",  # Epson TM-H6000
            "EPSON_TM_L90": b"\x1b\x70\x00\x32\x64",  # Epson TM-L90
            # Star Micronics
            "STAR_TSP100": b"\x07",  # Star TSP100 (simple bell)
            "STAR_TSP650": b"\x1b\x07\x01\x01",  # Star TSP650
            "STAR_TSP700": b"\x1b\x07\x01\x00\x01\x01",  # Star TSP700
            "STAR_TSP800": b"\x1b\x07\x01\x00\x01\x01",  # Star TSP800
            "STAR_SP500": b"\x1b\x42\x01\x14\x14",  # Star SP500
            "STAR_SM_S200": b"\x1b\x70\x00\x32\x64",  # Star SM-S200
            # 2Connect
            "2CONNECT_CD": b"\x1b\x70\x00\x19\xfa",  # 2Connect estándar
            "2CONNECT_NC": b"\x1b\x70\x01\x28\x64",  # 2Connect alternativo
            "2CONNECT_P": b"\x1b\x70\x00\x32\x64",  # 2Connect Pro
            # Genérico
            "GENERIC": b"\x1b\x70\x00\x19\xfa",  # Comando genérico ESC/POS
        }

        # Variables
        self.impresora_seleccionada = tk.StringVar()
        self.comando_seleccionado = tk.StringVar()
        self.status_text = tk.StringVar(value="Listo para probar comandos.")
        self.mostrar_hex = tk.BooleanVar(value=True)
        self.comando_personalizado = tk.StringVar()

        # Configuración de estilos
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", font=("Segoe UI", 10))
        self.style.configure("TLabel", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 9), foreground="blue")
        self.style.configure("Success.TLabel", foreground="green")
        self.style.configure("Error.TLabel", foreground="red")

        # Crear la interfaz
        self.crear_interfaz()

        # Cargar impresoras al iniciar
        self.actualizar_impresoras()

        # Actualizar lista de comandos
        self.actualizar_lista_comandos()

    def crear_interfaz(self):
        # Marco principal con padding
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        titulo_label = ttk.Label(
            main_frame, text="Control de Cajón de Dinero", style="Header.TLabel"
        )
        titulo_label.pack(pady=(0, 20))

        # Marco para impresoras
        impresoras_frame = ttk.LabelFrame(
            main_frame, text="Selección de Impresora", padding="10 10 10 10"
        )
        impresoras_frame.pack(fill=tk.X, pady=(0, 10))

        # Botón actualizar y lista de impresoras
        refresh_button = ttk.Button(
            impresoras_frame, text="↻ Actualizar", command=self.actualizar_impresoras
        )
        refresh_button.pack(side=tk.TOP, anchor=tk.E, pady=(0, 5))

        self.impresoras_listbox = tk.Listbox(
            impresoras_frame, height=6, font=("Segoe UI", 10), selectmode=tk.SINGLE
        )
        self.impresoras_listbox.pack(fill=tk.X, expand=True)
        self.impresoras_listbox.bind("<<ListboxSelect>>", self.on_impresora_select)

        # Marco para scrollbar de impresoras
        scrollbar = ttk.Scrollbar(
            self.impresoras_listbox,
            orient=tk.VERTICAL,
            command=self.impresoras_listbox.yview,
        )
        self.impresoras_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Etiqueta de impresora seleccionada
        self.impresora_label = ttk.Label(
            impresoras_frame, text="Impresora seleccionada: Ninguna"
        )
        self.impresora_label.pack(pady=(5, 0), anchor=tk.W)

        # Marco para comandos
        comandos_frame = ttk.LabelFrame(
            main_frame, text="Selección de Comando", padding="10 10 10 10"
        )
        comandos_frame.pack(fill=tk.X, pady=(0, 10))

        # Lista de comandos
        comandos_label = ttk.Label(comandos_frame, text="Comandos predefinidos:")
        comandos_label.pack(anchor=tk.W, pady=(0, 5))

        self.comandos_listbox = tk.Listbox(
            comandos_frame, height=8, font=("Segoe UI", 10), selectmode=tk.SINGLE
        )
        self.comandos_listbox.pack(fill=tk.X, expand=True)
        self.comandos_listbox.bind("<<ListboxSelect>>", self.on_comando_select)

        # Marco para scrollbar de comandos
        scrollbar_cmd = ttk.Scrollbar(
            self.comandos_listbox,
            orient=tk.VERTICAL,
            command=self.comandos_listbox.yview,
        )
        self.comandos_listbox.configure(yscrollcommand=scrollbar_cmd.set)
        scrollbar_cmd.pack(side=tk.RIGHT, fill=tk.Y)

        # Etiqueta de comando seleccionado
        self.comando_label = ttk.Label(
            comandos_frame, text="Comando seleccionado: Ninguno"
        )
        self.comando_label.pack(pady=(5, 0), anchor=tk.W)

        # Marco para comando personalizado
        custom_frame = ttk.LabelFrame(
            main_frame, text="Comando Personalizado", padding="10 10 10 10"
        )
        custom_frame.pack(fill=tk.X, pady=(0, 10))

        # Entrada para comando personalizado
        custom_label = ttk.Label(
            custom_frame,
            text="Introduce comando en formato hexadecimal (ej. 1B 70 00 32 FA):",
        )
        custom_label.pack(anchor=tk.W, pady=(0, 5))

        self.custom_entry = ttk.Entry(
            custom_frame, textvariable=self.comando_personalizado, font=("Consolas", 10)
        )
        self.custom_entry.pack(fill=tk.X, pady=(0, 5))

        # Botón para usar comando personalizado
        custom_button = ttk.Button(
            custom_frame,
            text="Usar Comando Personalizado",
            command=self.usar_comando_personalizado,
        )
        custom_button.pack(fill=tk.X)

        # Marco para acciones
        actions_frame = ttk.LabelFrame(
            main_frame, text="Acciones", padding="10 10 10 10"
        )
        actions_frame.pack(fill=tk.X, pady=(0, 10))

        # Botones de acción
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        enviar_btn = ttk.Button(
            btn_frame, text="Enviar Comando", command=self.enviar_comando
        )
        enviar_btn.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)

        probar_todos_btn = ttk.Button(
            btn_frame,
            text="Probar Todos los Comandos",
            command=self.probar_todos_comandos,
        )
        probar_todos_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        # Marco para registro
        log_frame = ttk.LabelFrame(
            main_frame, text="Registro de Actividad", padding="10 10 10 10"
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        # Área de texto para log
        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Scrollbar para el log
        log_scrollbar = ttk.Scrollbar(
            self.log_text, orient=tk.VERTICAL, command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Barra de estado
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_text, style="Status.TLabel"
        )
        self.status_label.pack(side=tk.LEFT)

        # Versión
        version_label = ttk.Label(status_frame, text="v1.0", style="Status.TLabel")
        version_label.pack(side=tk.RIGHT)

    def actualizar_impresoras(self):
        """Actualiza la lista de impresoras disponibles"""
        try:
            self.log("Actualizando lista de impresoras...")
            self.impresoras_listbox.delete(0, tk.END)

            # Obtener lista de impresoras e impresora predeterminada
            impresoras = [printer[2] for printer in win32print.EnumPrinters(2)]
            impresora_predeterminada = win32print.GetDefaultPrinter()

            # Agregar impresoras a la lista
            for i, impresora in enumerate(impresoras):
                if impresora == impresora_predeterminada:
                    self.impresoras_listbox.insert(
                        tk.END, f"{impresora} (Predeterminada)"
                    )
                else:
                    self.impresoras_listbox.insert(tk.END, impresora)

            self.log(f"Se encontraron {len(impresoras)} impresoras.")
            self.actualizar_estado("Lista de impresoras actualizada.")
        except Exception as e:
            self.log(f"Error al actualizar impresoras: {e}", error=True)
            self.actualizar_estado(f"Error: {e}", error=True)

    def actualizar_lista_comandos(self):
        """Actualiza la lista de comandos disponibles"""
        self.comandos_listbox.delete(0, tk.END)

        # Organizar comandos por categoría
        categorias = {
            "EPSON": [k for k in self.COMANDOS_CAJON.keys() if k.startswith("EPSON")],
            "STAR": [k for k in self.COMANDOS_CAJON.keys() if k.startswith("STAR")],
            "2CONNECT": [
                k for k in self.COMANDOS_CAJON.keys() if k.startswith("2CONNECT")
            ],
            "GENERIC": ["GENERIC"],
        }

        # Insertar comandos en la lista
        for categoria, comandos in categorias.items():
            self.comandos_listbox.insert(tk.END, f"--- {categoria} ---")
            for comando in comandos:
                if self.mostrar_hex.get():
                    hex_str = " ".join(
                        [f"{b:02X}" for b in self.COMANDOS_CAJON[comando]]
                    )
                    self.comandos_listbox.insert(tk.END, f"{comando} [{hex_str}]")
                else:
                    self.comandos_listbox.insert(tk.END, comando)

    def on_impresora_select(self, event):
        """Manejador de evento cuando se selecciona una impresora"""
        try:
            idx = self.impresoras_listbox.curselection()[0]
            impresora = self.impresoras_listbox.get(idx)

            # Quitar "(Predeterminada)" si está presente
            if "(Predeterminada)" in impresora:
                impresora = impresora.replace(" (Predeterminada)", "")

            self.impresora_seleccionada.set(impresora)
            self.impresora_label.config(text=f"Impresora seleccionada: {impresora}")
            self.log(f"Impresora seleccionada: {impresora}")
        except (IndexError, Exception) as e:
            # No hay selección o error
            pass

    def on_comando_select(self, event):
        """Manejador de evento cuando se selecciona un comando"""
        try:
            idx = self.comandos_listbox.curselection()[0]
            comando_texto = self.comandos_listbox.get(idx)

            # Ignorar categorías
            if comando_texto.startswith("---"):
                return

            # Extraer nombre del comando (quitar la parte hexadecimal)
            comando = (
                comando_texto.split(" [")[0] if "[" in comando_texto else comando_texto
            )

            self.comando_seleccionado.set(comando)

            # Mostrar en formato hexadecimal
            hex_str = " ".join([f"{b:02X}" for b in self.COMANDOS_CAJON[comando]])
            self.comando_label.config(
                text=f"Comando seleccionado: {comando} [{hex_str}]"
            )
            self.log(f"Comando seleccionado: {comando} [{hex_str}]")
        except (IndexError, Exception) as e:
            # No hay selección o error
            pass

    def usar_comando_personalizado(self):
        """Usa el comando personalizado ingresado"""
        try:
            hex_string = self.comando_personalizado.get().strip()
            if not hex_string:
                self.log("Error: Comando vacío", error=True)
                return

            # Convertir string hexadecimal a bytes
            try:
                # Remover espacios y dividir en pares
                hex_values = hex_string.replace(" ", "")
                if len(hex_values) % 2 != 0:
                    self.log(
                        "Error: La cantidad de dígitos hexadecimales debe ser par",
                        error=True,
                    )
                    return

                # Convertir a bytes
                byte_values = bytes.fromhex(hex_values)

                # Crear nombre para el comando personalizado
                nombre = f"CUSTOM_{hex_string.replace(' ', '_')}"

                # Agregar al diccionario
                self.COMANDOS_CAJON[nombre] = byte_values

                # Seleccionar este comando
                self.comando_seleccionado.set(nombre)
                hex_str = " ".join([f"{b:02X}" for b in byte_values])
                self.comando_label.config(text=f"Comando personalizado: [{hex_str}]")

                # Actualizar lista
                self.actualizar_lista_comandos()
                self.log(f"Comando personalizado creado: {nombre} [{hex_str}]")
            except ValueError:
                self.log(
                    "Error: Formato hexadecimal inválido. Use pares de dígitos hexadecimales (ej: 1B 70 00)",
                    error=True,
                )
        except Exception as e:
            self.log(f"Error al procesar comando personalizado: {e}", error=True)

    def enviar_comando(self):
        """Envía el comando seleccionado a la impresora seleccionada"""
        impresora = self.impresora_seleccionada.get()
        comando = self.comando_seleccionado.get()

        if not impresora:
            self.log("Error: No hay impresora seleccionada", error=True)
            messagebox.showerror("Error", "Seleccione una impresora primero")
            return

        if not comando:
            self.log("Error: No hay comando seleccionado", error=True)
            messagebox.showerror("Error", "Seleccione un comando primero")
            return

        # Iniciar en un hilo separado para no bloquear la interfaz
        threading.Thread(
            target=self._enviar_comando, args=(impresora, comando), daemon=True
        ).start()

    def _enviar_comando(self, impresora, comando):
        """Función auxiliar para enviar comando en un hilo separado"""
        try:
            self.actualizar_estado(f"Enviando {comando} a {impresora}...")
            self.log(f"Enviando comando {comando} a impresora {impresora}")

            # Obtener los bytes del comando
            comando_bytes = self.COMANDOS_CAJON[comando]

            # Imprimir comando en hexadecimal
            hex_str = " ".join([f"{b:02X}" for b in comando_bytes])
            self.log(f"Bytes: {hex_str}")

            # Enviar comando
            handle = win32print.OpenPrinter(impresora)
            try:
                trabajo = win32print.StartDocPrinter(
                    handle, 1, ("Abrir Cajón", None, "RAW")
                )
                try:
                    win32print.StartPagePrinter(handle)
                    win32print.WritePrinter(handle, comando_bytes)
                    win32print.EndPagePrinter(handle)
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)

            self.log(f"Comando enviado con éxito", success=True)
            self.actualizar_estado("Comando enviado con éxito", success=True)
        except Exception as e:
            self.log(f"Error al enviar comando: {e}", error=True)
            self.actualizar_estado(f"Error: {e}", error=True)

    def probar_todos_comandos(self):
        """Prueba todos los comandos disponibles en la impresora seleccionada"""
        impresora = self.impresora_seleccionada.get()

        if not impresora:
            self.log("Error: No hay impresora seleccionada", error=True)
            messagebox.showerror("Error", "Seleccione una impresora primero")
            return

        # Confirmar
        respuesta = messagebox.askyesno(
            "Confirmación",
            f"¿Desea probar todos los comandos disponibles en la impresora {impresora}?\n\n"
            "Esto enviará múltiples comandos intentando abrir el cajón.\n"
            "Se hará una pausa entre cada comando.",
        )

        if respuesta:
            # Iniciar en un hilo separado
            threading.Thread(
                target=self._probar_todos_comandos, args=(impresora,), daemon=True
            ).start()

    def _probar_todos_comandos(self, impresora):
        """Función auxiliar para probar todos los comandos en un hilo separado"""
        try:
            self.actualizar_estado(f"Probando comandos en {impresora}...")
            self.log(f"Iniciando prueba de todos los comandos en impresora {impresora}")

            # Organizar comandos por marca
            categorias = {
                "EPSON": [
                    k for k in self.COMANDOS_CAJON.keys() if k.startswith("EPSON")
                ],
                "STAR": [k for k in self.COMANDOS_CAJON.keys() if k.startswith("STAR")],
                "2CONNECT": [
                    k for k in self.COMANDOS_CAJON.keys() if k.startswith("2CONNECT")
                ],
                "GENERIC": ["GENERIC"],
            }

            # Determinar el orden basado en el nombre de la impresora
            orden_categorias = list(categorias.keys())
            nombre_imp_upper = impresora.upper()

            if "EPSON" in nombre_imp_upper or "TM-" in nombre_imp_upper:
                orden_categorias = ["EPSON", "GENERIC", "STAR", "2CONNECT"]
            elif "STAR" in nombre_imp_upper:
                orden_categorias = ["STAR", "GENERIC", "EPSON", "2CONNECT"]
            elif "2CONNECT" in nombre_imp_upper:
                orden_categorias = ["2CONNECT", "GENERIC", "EPSON", "STAR"]

            # Probar comandos en el orden establecido
            for categoria in orden_categorias:
                self.log(f"Probando comandos de categoría: {categoria}")

                for comando in categorias[categoria]:
                    self.log(f"Probando comando: {comando}")
                    try:
                        # Obtener bytes del comando
                        comando_bytes = self.COMANDOS_CAJON[comando]
                        hex_str = " ".join([f"{b:02X}" for b in comando_bytes])
                        self.log(f"Enviando bytes: {hex_str}")

                        # Enviar comando
                        handle = win32print.OpenPrinter(impresora)
                        try:
                            trabajo = win32print.StartDocPrinter(
                                handle, 1, (f"Prueba {comando}", None, "RAW")
                            )
                            try:
                                win32print.StartPagePrinter(handle)
                                win32print.WritePrinter(handle, comando_bytes)
                                win32print.EndPagePrinter(handle)
                            finally:
                                win32print.EndDocPrinter(handle)
                        finally:
                            win32print.ClosePrinter(handle)

                        self.log(
                            f"Comando {comando} enviado. ¿Se abrió el cajón? Esperando retroalimentación..."
                        )

                        # Esperar para dar tiempo a que el cajón se abra y el usuario lo observe
                        time.sleep(2)

                    except Exception as e:
                        self.log(f"Error al enviar comando {comando}: {e}", error=True)

                    # Esperar un poco entre comandos
                    time.sleep(0.5)

            self.log("Prueba de comandos finalizada", success=True)
            self.actualizar_estado("Prueba de comandos finalizada", success=True)

        except Exception as e:
            self.log(f"Error en prueba de comandos: {e}", error=True)
            self.actualizar_estado(f"Error: {e}", error=True)

    def log(self, mensaje, error=False, success=False):
        """Agrega un mensaje al registro"""
        # Obtener hora actual
        hora = time.strftime("%H:%M:%S")

        # Estilo según tipo de mensaje
        if error:
            tag = "error"
            prefijo = "ERROR"
        elif success:
            tag = "success"
            prefijo = "ÉXITO"
        else:
            tag = "info"
            prefijo = "INFO"

        # Agregar mensaje al log
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{hora}] {prefijo}: {mensaje}\n", tag)
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("success", foreground="green")
        self.log_text.tag_configure("info", foreground="blue")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def actualizar_estado(self, mensaje, error=False, success=False):
        """Actualiza el mensaje de estado"""
        self.status_text.set(mensaje)

        if error:
            self.status_label.configure(style="Error.TLabel")
        elif success:
            self.status_label.configure(style="Success.TLabel")
        else:
            self.status_label.configure(style="Status.TLabel")


# Función principal
def main():
    root = tk.Tk()
    app = CajonApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
