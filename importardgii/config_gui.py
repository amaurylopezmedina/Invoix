import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import threading
import sys
import traceback
from crear_ambas_tablas import crear_ambas_tablas
from importacion_datos import importar_excel_a_sqlserver


import pandas as pd
import pyodbc

# Importamos config_loader si existe, o creamos funciones básicas si no
try:
    import config_loader
except ImportError:
    # Definiciones básicas si no existe config_loader
    CONFIG_FILE = 'config.json'
    
    # Configuración por defecto
    DEFAULT_CONFIG = {
        "RUTA_ARCHIVO_EXCEL": "",
        "SERVIDOR_SQL": "127.0.0.1",
        "BASE_DATOS_SQL": "FECertASESYS",
        "USUARIO_SQL": "sistema",
        "PASSWORD_SQL": "@@sistema",
        "TRUSTED_CONNECTION": False,
        "NOMBRE_HOJA": "ECF",
        "COLUMNA_FIN_ENCABEZADO": "MontoTotalOtraMoneda",
        "COLUMNA_INICIO_DETALLE": "NumeroLinea[1]",
        "NUMERO_MAXIMO_DETALLES": 62,
        "VALOR_NULO": "#e"
    }
    
    def load_config():
        """
        Carga la configuración desde el archivo JSON.
        Si el archivo no existe, crea uno con la configuración por defecto.
        
        Returns:
            dict: Configuración cargada
        """
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Asegurar que todas las claves existan
                    for key in DEFAULT_CONFIG:
                        if key not in config:
                            config[key] = DEFAULT_CONFIG[key]
                    return config
            else:
                # Crear archivo de configuración por defecto
                save_config(DEFAULT_CONFIG)
                return DEFAULT_CONFIG
        except Exception as e:
            print(f"Error al cargar la configuración: {str(e)}")
            return DEFAULT_CONFIG
    
    def save_config(config):
        """
        Guarda la configuración en el archivo JSON.
        
        Args:
            config (dict): Configuración a guardar
        """
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            print(f"Configuración guardada en {CONFIG_FILE}")
        except Exception as e:
            print(f"Error al guardar la configuración: {str(e)}")
    
    def update_config_variables():
        """Función vacía para compatibilidad"""
        pass

# PARTE 1: Clase ConfigGUI y métodos básicos
class ConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuración de Importación de Excel de la DGII para Certificacion a SQL Server")
        self.root.geometry("750x600")
        self.root.resizable(True, True)
        self.root.state('zoomed')
        
        # Cargar la configuración
        try:
            self.config = config_loader.load_config()
        except:
            self.config = load_config()
        
        # Crear frame principal
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crear pestañas
        self.tab_general = ttk.Frame(self.notebook)
        self.tab_db = ttk.Frame(self.notebook)
        self.tab_excel = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_general, text="General")
        self.notebook.add(self.tab_db, text="Base de Datos")
        self.notebook.add(self.tab_excel, text="Configuración Excel")
        
        # Frame para botones de acción
        action_frame = ttk.Frame(main_frame, padding="10")
        action_frame.pack(fill=tk.X, pady=15)  # Aumentado el pady

        # Estilo personalizado para botones más grandes
        style = ttk.Style()
        style.configure("Big.TButton", padding=(10, 10), font=('Helvetica', 10, 'bold'))
        style.configure("Import.TButton", padding=(10, 10), font=('Helvetica', 10, 'bold'), background='#4CAF50')
        
        # Crear los componentes de la GUI
        self.create_general_tab()
        self.create_db_tab()
        self.create_excel_tab()
        
        # Botones de acción
        ttk.Button(action_frame, text="Guardar Configuración", command=self.save_config, 
                style="Big.TButton").pack(side=tk.LEFT, padx=5, pady=8, ipady=5)
        ttk.Button(action_frame, text="Probar Conexión BD", command=self.test_db_connection, 
                style="Big.TButton").pack(side=tk.LEFT, padx=5, pady=8, ipady=5)
        ttk.Button(action_frame, text="Verificar Excel", command=self.verify_excel, 
                style="Big.TButton").pack(side=tk.LEFT, padx=5, pady=8, ipady=5)
        ttk.Button(action_frame, text="Ejecutar Importación", command=self.run_import_process, 
                style="Import.TButton").pack(side=tk.LEFT, padx=5, pady=8, ipady=5)
        ttk.Button(action_frame, text="Salir", command=root.destroy, 
                style="Big.TButton").pack(side=tk.RIGHT, padx=10, pady=8, ipady=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_file(self):
        """Abrir diálogo para seleccionar archivo Excel"""
        filename = filedialog.askopenfilename(
            initialdir=os.path.dirname(self.config["RUTA_ARCHIVO_EXCEL"]) if self.config["RUTA_ARCHIVO_EXCEL"] else "/",
            title="Seleccionar archivo Excel",
            filetypes=(("Archivos Excel", "*.xlsx *.xls"), ("Todos los archivos", "*.*"))
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
            self.status_var.set(f"Archivo seleccionado: {os.path.basename(filename)}")
    
    def toggle_auth(self):
        """Habilitar/deshabilitar campos de autenticación SQL"""
        if self.auth_var.get():  # Autenticación Windows
            self.user_entry.config(state=tk.DISABLED)
            self.pass_entry.config(state=tk.DISABLED)
        else:  # Autenticación SQL
            self.user_entry.config(state=tk.NORMAL)
            self.pass_entry.config(state=tk.NORMAL)
    
    def save_config(self):
        """Guardar la configuración en el archivo JSON"""
        try:
            # Actualizar el diccionario de configuración con los valores actuales
            self.config["RUTA_ARCHIVO_EXCEL"] = self.file_entry.get()
            self.config["SERVIDOR_SQL"] = self.server_entry.get()
            self.config["BASE_DATOS_SQL"] = self.db_entry.get()
            self.config["TRUSTED_CONNECTION"] = self.auth_var.get()
            self.config["USUARIO_SQL"] = self.user_entry.get()
            self.config["PASSWORD_SQL"] = self.pass_entry.get()
            self.config["NOMBRE_HOJA"] = self.sheet_entry.get()
            self.config["COLUMNA_FIN_ENCABEZADO"] = self.end_header_entry.get()
            self.config["COLUMNA_INICIO_DETALLE"] = self.start_detail_entry.get()
            
            try:
                self.config["NUMERO_MAXIMO_DETALLES"] = int(self.max_details_entry.get())
            except ValueError:
                messagebox.showerror("Error", "El número máximo de detalles debe ser un número entero.")
                return
            
            self.config["VALOR_NULO"] = self.valor_nulo_entry.get()
            
            # Guardar la configuración
            try:
                config_loader.save_config(self.config)
                # Actualizar variables globales
                config_loader.update_config_variables()
            except:
                save_config(self.config)
            
            self.status_var.set("Configuración guardada correctamente")
            messagebox.showinfo("Éxito", "Configuración guardada correctamente.")
        except Exception as e:
            self.status_var.set(f"Error al guardar la configuración: {str(e)}")
            messagebox.showerror("Error", f"Error al guardar la configuración: {str(e)}")

# PARTE 2: Métodos para crear las pestañas y verificar Excel
    def create_general_tab(self):
        """Crear pestaña general"""
        frame = ttk.LabelFrame(self.tab_general, text="Archivo Excel", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Ruta del archivo Excel
        ttk.Label(frame, text="Ruta del archivo Excel:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_entry = ttk.Entry(frame, width=50)
        self.file_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=5, padx=5)
        self.file_entry.insert(0, self.config["RUTA_ARCHIVO_EXCEL"])
        
        browse_btn = ttk.Button(frame, text="Examinar...", command=self.browse_file)
        browse_btn.grid(row=0, column=2, pady=5)
        
        # Valor nulo
        ttk.Label(frame, text="Valor nulo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.valor_nulo_entry = ttk.Entry(frame)
        self.valor_nulo_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        self.valor_nulo_entry.insert(0, self.config["VALOR_NULO"])
        
        # Descripción
        desc_frame = ttk.LabelFrame(self.tab_general, text="Información", padding="10")
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        desc_text = """
        Esta aplicación permite configurar e importar datos desde un archivo Excel a una base de datos SQL Server.
        
        Pasos:
        1. Configure la ruta del archivo Excel.
        2. Configure la conexión a la base de datos SQL Server.
        3. Configure los parámetros de importación del Excel.
        4. Guarde la configuración y ejecute la importación desde el programa principal.
        
        Los datos se importarán a las tablas Encabezado y Detalle en SQL Server.
        """
        
        desc_label = ttk.Label(desc_frame, text=desc_text, wraplength=500, justify=tk.LEFT)
        desc_label.pack(fill=tk.BOTH, expand=True)
    
    def create_db_tab(self):
        """Crear pestaña de base de datos"""
        frame = ttk.LabelFrame(self.tab_db, text="Conexión SQL Server", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Servidor
        ttk.Label(frame, text="Servidor:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_entry = ttk.Entry(frame, width=30)
        self.server_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        self.server_entry.insert(0, self.config["SERVIDOR_SQL"])
        
        # Base de datos
        ttk.Label(frame, text="Base de datos:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.db_entry = ttk.Entry(frame, width=30)
        self.db_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        self.db_entry.insert(0, self.config["BASE_DATOS_SQL"])
        
        # Autenticación
        auth_frame = ttk.LabelFrame(frame, text="Autenticación", padding="5")
        auth_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E, pady=5)
        
        self.auth_var = tk.BooleanVar(value=self.config["TRUSTED_CONNECTION"])
        self.windows_auth = ttk.Radiobutton(auth_frame, text="Autenticación Windows", 
                                          variable=self.auth_var, value=True, 
                                          command=self.toggle_auth)
        self.sql_auth = ttk.Radiobutton(auth_frame, text="Autenticación SQL Server", 
                                      variable=self.auth_var, value=False,
                                      command=self.toggle_auth)
        
        self.windows_auth.grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)
        self.sql_auth.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)
        
        # Usuario y contraseña SQL
        self.user_label = ttk.Label(auth_frame, text="Usuario:")
        self.user_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        self.user_entry = ttk.Entry(auth_frame, width=20)
        self.user_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        self.user_entry.insert(0, self.config["USUARIO_SQL"])
        
        self.pass_label = ttk.Label(auth_frame, text="Contraseña:")
        self.pass_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pass_entry = ttk.Entry(auth_frame, width=20, show="*")
        self.pass_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        self.pass_entry.insert(0, self.config["PASSWORD_SQL"])
        
        # Inicializar el estado de autenticación
        self.toggle_auth()
    
    def create_excel_tab(self):
        """Crear pestaña de configuración de Excel"""
        frame = ttk.LabelFrame(self.tab_excel, text="Configuración de Importación", padding="10")
        frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Nombre de hoja
        ttk.Label(frame, text="Nombre de hoja:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.sheet_entry = ttk.Entry(frame, width=30)
        self.sheet_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        self.sheet_entry.insert(0, self.config["NOMBRE_HOJA"])
        
        # Columna fin encabezado
        ttk.Label(frame, text="Columna fin encabezado:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.end_header_entry = ttk.Entry(frame, width=30)
        self.end_header_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        self.end_header_entry.insert(0, self.config["COLUMNA_FIN_ENCABEZADO"])
        
        # Columna inicio detalle
        ttk.Label(frame, text="Columna inicio detalle:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.start_detail_entry = ttk.Entry(frame, width=30)
        self.start_detail_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        self.start_detail_entry.insert(0, self.config["COLUMNA_INICIO_DETALLE"])
        
        # Número máximo de detalles
        ttk.Label(frame, text="Número máximo de detalles:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.max_details_entry = ttk.Spinbox(frame, from_=1, to=1000, width=10)
        self.max_details_entry.grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        self.max_details_entry.delete(0, tk.END)
        self.max_details_entry.insert(0, self.config["NUMERO_MAXIMO_DETALLES"])
        
        # Frame de información de Excel
        excel_info_frame = ttk.LabelFrame(self.tab_excel, text="Información del Excel", padding="10")
        excel_info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Crear un Treeview para mostrar información del Excel
        self.excel_info_tree = ttk.Treeview(excel_info_frame, columns=("Value"), show="headings")
        self.excel_info_tree.heading("Value", text="Valor")
        self.excel_info_tree.column("Value", width=400)
        self.excel_info_tree.pack(fill=tk.BOTH, expand=True)
        
        # Botón para cargar información del Excel
        ttk.Button(excel_info_frame, text="Cargar información del Excel", 
                  command=self.load_excel_info).pack(pady=10)

    def verify_excel(self):
        """Verificar el archivo Excel"""
        file_path = self.file_entry.get()
        
        if not file_path or not os.path.exists(file_path):
            self.status_var.set("Error: Archivo Excel no encontrado")
            messagebox.showerror("Error", "Archivo Excel no encontrado. Por favor, seleccione un archivo válido.")
            return
        
        try:
            self.status_var.set(f"Verificando archivo Excel: {os.path.basename(file_path)}")
            
            # Verificar si el archivo es un Excel válido
            sheet_name = self.sheet_entry.get() or "ECF"
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except ValueError:
                # Si la hoja específica no existe, mostrar las hojas disponibles
                xls = pd.ExcelFile(file_path)
                sheets = xls.sheet_names
                
                messagebox.showwarning("Hoja no encontrada", 
                                       f"La hoja '{sheet_name}' no existe en el archivo.\n\nHojas disponibles: {', '.join(sheets)}")
                return
            
            # Verificar si las columnas clave existen
            headers = list(df.columns)
            
            columna_fin_encabezado = self.end_header_entry.get()
            columna_inicio_detalle = self.start_detail_entry.get()
            
            fin_encabezado_existe = columna_fin_encabezado in headers
            inicio_detalle_existe = columna_inicio_detalle in headers
            
            # Mostrar información del Excel
            self.excel_info_tree.delete(*self.excel_info_tree.get_children())
            
            self.excel_info_tree.insert("", "end", values=("Nombre archivo", os.path.basename(file_path)))
            self.excel_info_tree.insert("", "end", values=("Ruta completa", file_path))
            self.excel_info_tree.insert("", "end", values=("Nombre hoja", sheet_name))
            self.excel_info_tree.insert("", "end", values=("Número de filas", len(df)))
            self.excel_info_tree.insert("", "end", values=("Número de columnas", len(headers)))
            self.excel_info_tree.insert("", "end", values=("Columna fin encabezado existe", "Sí" if fin_encabezado_existe else "No"))
            self.excel_info_tree.insert("", "end", values=("Columna inicio detalle existe", "Sí" if inicio_detalle_existe else "No"))
            
            if not fin_encabezado_existe or not inicio_detalle_existe:
                mensaje = "Advertencia: "
                if not fin_encabezado_existe:
                    mensaje += f"La columna fin encabezado '{columna_fin_encabezado}' no existe en el Excel. "
                if not inicio_detalle_existe:
                    mensaje += f"La columna inicio detalle '{columna_inicio_detalle}' no existe en el Excel."
                    
                messagebox.showwarning("Columnas no encontradas", mensaje)
            else:
                self.status_var.set("Verificación del Excel completada con éxito")
                messagebox.showinfo("Excel válido", "El archivo Excel es válido y contiene las columnas necesarias.")
                
        except Exception as e:
            self.status_var.set(f"Error al verificar el Excel: {str(e)}")
            messagebox.showerror("Error", f"Error al verificar el archivo Excel:\n{str(e)}")

# PARTE 3: Métodos para cargar información del Excel y pruebas de conexión
    def load_excel_info(self):
        """Cargar información detallada del Excel"""
        file_path = self.file_entry.get()
        
        if not file_path or not os.path.exists(file_path):
            self.status_var.set("Error: Archivo Excel no encontrado")
            messagebox.showerror("Error", "Archivo Excel no encontrado. Por favor, seleccione un archivo válido.")
            return
        
        try:
            self.status_var.set(f"Cargando información del Excel: {os.path.basename(file_path)}")
            
            # Leer el Excel
            sheet_name = self.sheet_entry.get() or "ECF"
            
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except ValueError:
                # Si la hoja específica no existe, mostrar las hojas disponibles
                xls = pd.ExcelFile(file_path)
                sheets = xls.sheet_names
                
                messagebox.showwarning("Hoja no encontrada", 
                                       f"La hoja '{sheet_name}' no existe en el archivo.\n\nHojas disponibles: {', '.join(sheets)}")
                return
            
            # Limpiar el treeview
            self.excel_info_tree.delete(*self.excel_info_tree.get_children())
            
            # Información básica
            self.excel_info_tree.insert("", "end", values=("Nombre archivo", os.path.basename(file_path)))
            self.excel_info_tree.insert("", "end", values=("Ruta completa", file_path))
            self.excel_info_tree.insert("", "end", values=("Nombre hoja", sheet_name))
            self.excel_info_tree.insert("", "end", values=("Número de filas", len(df)))
            self.excel_info_tree.insert("", "end", values=("Número de columnas", len(df.columns)))
            
            # Identificar columnas de encabezado y detalle
            headers = list(df.columns)
            columna_fin_encabezado = self.end_header_entry.get()
            columna_inicio_detalle = self.start_detail_entry.get()
            
            fin_encabezado_existe = columna_fin_encabezado in headers
            inicio_detalle_existe = columna_inicio_detalle in headers
            
            self.excel_info_tree.insert("", "end", values=("Columna fin encabezado existe", "Sí" if fin_encabezado_existe else "No"))
            self.excel_info_tree.insert("", "end", values=("Columna inicio detalle existe", "Sí" if inicio_detalle_existe else "No"))
            
            # Identificar bloques de detalle
            bloques_detalle = {}
            for col in headers:
                if '[' in col and ']' in col:
                    try:
                        nombre_base = col.split('[')[0]
                        indice = int(col.split('[')[1].split(']')[0])
                        
                        if indice not in bloques_detalle:
                            bloques_detalle[indice] = []
                        
                        bloques_detalle[indice].append(col)
                    except (ValueError, IndexError):
                        pass
            
            num_bloques = len(bloques_detalle)
            self.excel_info_tree.insert("", "end", values=("Número de bloques detalle", num_bloques))
            
            if num_bloques > 0:
                max_indice = max(bloques_detalle.keys()) if bloques_detalle else 0
                self.excel_info_tree.insert("", "end", values=("Rango de bloques", f"[1] a [{max_indice}]"))
                
                # Mostrar algunos ejemplos de columnas en cada bloque
                for i, indice in enumerate(sorted(bloques_detalle.keys())[:5]):  # Mostrar solo los primeros 5 bloques
                    cols = bloques_detalle[indice][:5]  # Mostrar solo las primeras 5 columnas de cada bloque
                    self.excel_info_tree.insert("", "end", values=(f"Bloque [{indice}] - Columnas (primeras 5)", ", ".join(cols)))
            
            self.status_var.set("Información del Excel cargada con éxito")
            
        except Exception as e:
            self.status_var.set(f"Error al cargar información del Excel: {str(e)}")
            messagebox.showerror("Error", f"Error al cargar información del Excel:\n{str(e)}")
    
    def test_db_connection(self):
        """Probar la conexión a la base de datos"""
        try:
            self.status_var.set("Probando conexión a la base de datos...")
            
            servidor = self.server_entry.get()
            base_datos = self.db_entry.get()
            trusted_connection = self.auth_var.get()
            usuario = self.user_entry.get()
            password = self.pass_entry.get()
            
            if trusted_connection:
                conn_str = f'DRIVER={{SQL Server}};SERVER={servidor};DATABASE={base_datos};Trusted_Connection=yes;'
            else:
                conn_str = f'DRIVER={{SQL Server}};SERVER={servidor};DATABASE={base_datos};UID={usuario};PWD={password}'
            
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Verificar tablas
            cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
            tablas = [row[0] for row in cursor.fetchall()]
            
            tiene_encabezado = "FEEncabezado" in tablas
            tiene_detalle = "FEDetalle" in tablas
            
            # Contar registros
            if tiene_encabezado:
                cursor.execute("SELECT COUNT(*) FROM FEEncabezado")
                count_encabezado = cursor.fetchone()[0]
            else:
                count_encabezado = 0
            
            if tiene_detalle:
                cursor.execute("SELECT COUNT(*) FROM FEDetalle")
                count_detalle = cursor.fetchone()[0]
            else:
                count_detalle = 0
            
            # Verificar columnas si las tablas existen
            if tiene_encabezado:
                cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FEEncabezado'")
                num_cols_encabezado = cursor.fetchone()[0]
            else:
                num_cols_encabezado = 0
                
            if tiene_detalle:
                cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FEDetalle'")
                num_cols_detalle = cursor.fetchone()[0]
            else:
                num_cols_detalle = 0
            
            conn.close()
            
            # Mostrar resultados
            mensaje = f"Conexión exitosa a {base_datos} en {servidor}\n\n"
            mensaje += f"Tabla Encabezado: {'Existe' if tiene_encabezado else 'No existe'}"
            if tiene_encabezado:
                mensaje += f" ({count_encabezado} registros, {num_cols_encabezado} columnas)\n"
            else:
                mensaje += "\n"
            
            mensaje += f"Tabla Detalle: {'Existe' if tiene_detalle else 'No existe'}"
            if tiene_detalle:
                mensaje += f" ({count_detalle} registros, {num_cols_detalle} columnas)"
            
            # Sugerencias
            if not tiene_encabezado or not tiene_detalle:
                mensaje += "\n\nSugerencia: Ejecute primero el script crear_ambas_tablas.py para crear las tablas necesarias."
            
            self.status_var.set("Conexión a la base de datos exitosa")
            messagebox.showinfo("Conexión exitosa", mensaje)
            
        except Exception as e:
            self.status_var.set(f"Error al conectar con la base de datos: {str(e)}")
            messagebox.showerror("Error de conexión", f"Error al conectar con la base de datos:\n{str(e)}")
            
    def run_import_process(self):
        """Ejecutar el proceso de importación de datos"""
        # Primero guardar la configuración actual
        self.save_config()
        
        # Verificar que el archivo Excel existe
        ruta_archivo = self.file_entry.get()
        if not ruta_archivo or not os.path.exists(ruta_archivo):
            self.status_var.set("Error: Archivo Excel no encontrado")
            messagebox.showerror("Error", "Archivo Excel no encontrado. Por favor, seleccione un archivo válido.")
            return
        
        # Confirmar la operación
        if not messagebox.askyesno("Confirmar importación", 
                                "¿Está seguro de ejecutar el proceso de importación?\n\n"
                                "Esto creará las tablas si no existen y realizará la importación de datos.\n"
                                "La operación puede tardar varios minutos según el tamaño del archivo."):
            return

        # Crear una ventana de progreso
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Importación en progreso")
        progress_window.geometry("1000x600")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Configurar la ventana de progreso
        progress_frame = ttk.Frame(progress_window, padding="20")
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(progress_frame, text="Importación de datos en progreso...", 
                font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        # Crear un widget Text para mostrar el progreso
        log_text = tk.Text(progress_frame, height=10, width=60)
        log_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbar para el texto
        scrollbar = ttk.Scrollbar(log_text, command=log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.config(yscrollcommand=scrollbar.set)
        
        # Botón para cerrar (inicialmente deshabilitado)
        close_button = ttk.Button(progress_frame, text="Cerrar", command=progress_window.destroy)
        close_button.pack(pady=10)
        close_button.config(state=tk.DISABLED)
        
        # Función para redirigir la salida de la consola al widget Text
        class TextRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget
                self.buffer = ""
                
            def write(self, string):
                self.buffer += string
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)
                self.text_widget.update()
                
            def flush(self):
                pass
        
        # Función para ejecutar el proceso de importación en un hilo separado
        def run_import_thread():
            # Obtener los parámetros de configuración
            parametros = {
                'ruta_archivo': self.file_entry.get(),
                'servidor': self.server_entry.get(),
                'base_datos': self.db_entry.get(),
                'usuario': self.user_entry.get(),
                'password': self.pass_entry.get(),
                'trusted_connection': self.auth_var.get()
            }
            
            # Redirigir la salida estándar
            old_stdout = sys.stdout
            sys.stdout = TextRedirector(log_text)
            
            success = True
            try:
                # Código de importación
                print(f"Iniciando proceso de importación desde {os.path.basename(parametros['ruta_archivo'])}")
                print("\n1. Creando/verificando tablas en la base de datos...")
                
                crear_ambas_tablas(
                    parametros['servidor'],
                    parametros['base_datos'],
                    parametros['usuario'],
                    parametros['password'],
                    parametros['trusted_connection']
                )
                
                print("\n2. Importando datos desde Excel...")
                importar_excel_a_sqlserver(
                    ruta_archivo_excel=parametros['ruta_archivo'],
                    servidor=parametros['servidor'],
                    base_datos=parametros['base_datos'],
                    usuario=parametros['usuario'],
                    password=parametros['password'],
                    trusted_connection=parametros['trusted_connection']
                )
                
                print("\nProceso completado exitosamente.")
            except Exception as e:
                success = False
                print(f"\nERROR: {str(e)}")
                traceback.print_exc(file=sys.stdout)
            finally:
                # Restaurar la salida estándar
                sys.stdout = old_stdout
                
                # Actualizar la interfaz para mostrar el resultado
                self.root.after(0, lambda: self._update_import_ui(success, close_button))
        
        # Iniciar el hilo
        import_thread = threading.Thread(target=run_import_thread)
        import_thread.daemon = True
        import_thread.start()

    def _update_import_ui(self, success, close_button):
        """Actualizar la interfaz después de la importación"""
        close_button.config(state=tk.NORMAL)
        
        if success:
            self.status_var.set("Importación completada exitosamente")
        else:
            self.status_var.set("Error en la importación. Vea los detalles en la ventana de progreso.")         

# Función para ejecutar la aplicación de forma independiente
def main():
    root = tk.Tk()
    app = ConfigGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()