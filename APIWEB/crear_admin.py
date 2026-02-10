"""
Script para crear o verificar usuarios administradores en la base de datos
"""
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_connection
from api import hash_password

def listar_usuarios():
    """Lista todos los usuarios en la base de datos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, username, tipo_usuario, nombre_completo, correo, EmpresaId
            FROM usuariosj
            ORDER BY tipo_usuario, username
        """)
        
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not usuarios:
            print("\n[X] No hay usuarios en la base de datos")
            return
        
        print("\n" + "="*80)
        print("USUARIOS EN LA BASE DE DATOS")
        print("="*80)
        print(f"{'ID':<5} {'Username':<20} {'Tipo':<15} {'Nombre':<25} {'Empresa':<10}")
        print("-"*80)
        
        for usuario in usuarios:
            user_id = usuario[0]
            username = usuario[1] or ""
            tipo = usuario[2] or "N/A"
            nombre = usuario[3] or "N/A"
            empresa_id = usuario[5] or "N/A"
            
            print(f"{user_id:<5} {username:<20} {tipo:<15} {nombre:<25} {empresa_id:<10}")
        
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n[X] Error al listar usuarios: {str(e)}")

def verificar_admin_existe(username):
    """Verifica si un usuario administrador existe"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT Id, username, tipo_usuario, nombre_completo
            FROM usuariosj
            WHERE username = ? AND tipo_usuario IN ('ADMIN', 'ADMINISTRADOR')
        """, (username,))
        
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return usuario is not None
        
    except Exception as e:
        print(f"[X] Error al verificar usuario: {str(e)}")
        return False

def crear_usuario_admin(username, password, nombre_completo, correo):
    """Crea un nuevo usuario administrador"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hashear la contraseña
        hashed_password = hash_password(password)
        
        # Insertar el usuario
        cursor.execute("""
            INSERT INTO usuariosj (username, password, tipo_usuario, nombre_completo, correo, EmpresaId)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (username, hashed_password, 'ADMIN', nombre_completo, correo))
        
        conn.commit()
        user_id = cursor.execute("SELECT @@IDENTITY").fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"\n[OK] Usuario administrador creado exitosamente!")
        print(f"   ID: {user_id}")
        print(f"   Username: {username}")
        print(f"   Nombre: {nombre_completo}")
        print(f"   Tipo: ADMIN\n")
        
        return True
        
    except Exception as e:
        print(f"\n[X] Error al crear usuario administrador: {str(e)}\n")
        return False

def actualizar_tipo_usuario(username, nuevo_tipo='ADMIN'):
    """Actualiza el tipo de usuario de un usuario existente"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuariosj
            SET tipo_usuario = ?
            WHERE username = ?
        """, (nuevo_tipo, username))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"\n[OK] Usuario '{username}' actualizado a tipo '{nuevo_tipo}'\n")
            result = True
        else:
            print(f"\n[X] Usuario '{username}' no encontrado\n")
            result = False
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"\n[X] Error al actualizar usuario: {str(e)}\n")
        return False

def menu_principal():
    """Menú principal del script"""
    while True:
        print("\n" + "="*60)
        print("GESTION DE USUARIOS ADMINISTRADORES")
        print("="*60)
        print("1. Listar todos los usuarios")
        print("2. Crear nuevo usuario administrador")
        print("3. Cambiar tipo de usuario existente a ADMIN")
        print("4. Verificar si un usuario admin existe")
        print("0. Salir")
        print("="*60)
        
        opcion = input("\nSeleccione una opcion: ").strip()
        
        if opcion == "1":
            listar_usuarios()
            
        elif opcion == "2":
            print("\n--- CREAR NUEVO USUARIO ADMINISTRADOR ---")
            username = input("Username: ").strip()
            
            if not username:
                print("[X] El username no puede estar vacio")
                continue
            
            password = input("Password: ").strip()
            
            if not password:
                print("[X] La contraseña no puede estar vacia")
                continue
                
            nombre_completo = input("Nombre completo: ").strip()
            correo = input("Correo electronico: ").strip()
            
            crear_usuario_admin(username, password, nombre_completo, correo)
            
        elif opcion == "3":
            print("\n--- ACTUALIZAR TIPO DE USUARIO ---")
            listar_usuarios()
            username = input("\nIngrese el username del usuario a actualizar: ").strip()
            
            if username:
                actualizar_tipo_usuario(username, 'ADMIN')
            else:
                print("[X] El username no puede estar vacio")
                
        elif opcion == "4":
            print("\n--- VERIFICAR USUARIO ADMIN ---")
            username = input("Username a verificar: ").strip()
            
            if username:
                if verificar_admin_existe(username):
                    print(f"\n[OK] El usuario '{username}' existe y es administrador\n")
                else:
                    print(f"\n[X] El usuario '{username}' NO existe como administrador\n")
            else:
                print("[X] El username no puede estar vacio")
                
        elif opcion == "0":
            print("\n[!] Hasta luego!\n")
            break
            
        else:
            print("\n[X] Opcion invalida. Intente nuevamente.\n")

if __name__ == "__main__":
    print("\n[+] HERRAMIENTA DE GESTION DE USUARIOS ADMINISTRADORES")
    print("   Este script te ayudara a crear y gestionar usuarios admin\n")
    
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n[!] Programa interrumpido. Hasta luego!\n")
    except Exception as e:
        print(f"\n[X] Error inesperado: {str(e)}\n")
