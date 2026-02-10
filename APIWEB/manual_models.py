"""
Módulo para gestión de Manuales/Instructivos en PDF.
Almacena metadata en base de datos y archivos PDF en disco C:\\Manuales\\
"""
import os
import re
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from database import get_db_connection

logger = logging.getLogger(__name__)

# Configuración del directorio de manuales
MANUAL_DIRECTORY = r"C:\Manuales"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_NOMBRE_LENGTH = 150
ALLOWED_EXTENSIONS = {'.pdf'}

def ensure_manual_directory():
    """Crea el directorio de manuales si no existe."""
    try:
        Path(MANUAL_DIRECTORY).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio de manuales asegurado: {MANUAL_DIRECTORY}")
    except Exception as e:
        logger.error(f"Error al crear directorio de manuales: {e}")
        raise

def sanitize_filename(nombre: str) -> str:
    """
    Sanitiza el nombre para crear un filename seguro.
    Permite solo letras, números, guiones bajos, espacios y trunca a MAX_NOMBRE_LENGTH.
    Previene path traversal attacks.
    """
    # Remover cualquier carácter peligroso
    safe_name = re.sub(r'[^\w\s-]', '', nombre)
    # Reemplazar espacios con guiones bajos
    safe_name = re.sub(r'\s+', '_', safe_name)
    # Truncar a longitud máxima
    safe_name = safe_name[:MAX_NOMBRE_LENGTH]
    # Asegurar que no esté vacío
    if not safe_name:
        safe_name = "manual_sin_nombre"
    return safe_name

def validate_manual_data(nombre: str, categoria: str = None, descripcion: str = None) -> Tuple[bool, Optional[str]]:
    """
    Valida los datos del manual antes de guardar.
    Retorna (is_valid, error_message)
    """
    # Validar nombre
    if not nombre or len(nombre.strip()) < 3 or len(nombre.strip()) > MAX_NOMBRE_LENGTH:
        return False, f"El nombre debe tener entre 3 y {MAX_NOMBRE_LENGTH} caracteres"
    
    # Validar que no contenga caracteres peligrosos para path traversal
    if any(char in nombre for char in ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']):
        return False, "El nombre contiene caracteres no permitidos"
    
    # Validar categoría si se proporciona
    if categoria:
        valid_categorias = ['USUARIO', 'TECNICO', 'ADMINISTRADOR', 'CONFIGURACION', 'API', 'OTRO']
        if categoria.strip().upper() not in valid_categorias:
            return False, f"La categoría debe ser una de: {', '.join(valid_categorias)}"
    
    # Validar descripción
    if descripcion and len(descripcion) > 500:
        return False, "La descripción no puede exceder 500 caracteres"
    
    return True, None

def validate_pdf_file(file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """
    Valida que el archivo sea un PDF válido.
    Retorna (is_valid, error_message)
    """
    # Validar extensión
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Solo se permiten archivos PDF. Extensión recibida: {file_ext}"
    
    # Validar tamaño
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE // (1024*1024)} MB"
    
    # Validar que sea un PDF real (firma de archivo PDF)
    if not file_content.startswith(b'%PDF'):
        return False, "El archivo no es un PDF válido"
    
    # Validar tamaño mínimo (un PDF válido debe tener al menos algunos bytes)
    if len(file_content) < 100:
        return False, "El archivo es demasiado pequeño para ser un PDF válido"
    
    return True, None

def create_manual_table():
    """Crea la tabla de manuales en la base de datos si no existe."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='manuales' AND xtype='U')
        BEGIN
            CREATE TABLE manuales (
                id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
                nombre NVARCHAR(150) NOT NULL,
                categoria NVARCHAR(50),
                descripcion NVARCHAR(500),
                filename NVARCHAR(300) NOT NULL,
                file_size BIGINT NOT NULL,
                version NVARCHAR(20),
                created_at DATETIME NOT NULL DEFAULT GETDATE(),
                updated_at DATETIME NOT NULL DEFAULT GETDATE(),
                created_by NVARCHAR(100),
                download_count INT DEFAULT 0,
                INDEX idx_nombre (nombre),
                INDEX idx_categoria (categoria),
                INDEX idx_created_at (created_at)
            )
        END
        """
        cursor.execute(query)
        conn.commit()
        logger.info("Tabla manuales verificada/creada exitosamente")
        
    except Exception as e:
        logger.error(f"Error al crear tabla manuales: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_filename(manual_id: str, nombre: str) -> str:
    """Genera el nombre de archivo seguro con extensión .pdf"""
    safe_name = sanitize_filename(nombre)
    return f"{manual_id}_{safe_name}.pdf"

def save_manual_file(filename: str, content: bytes) -> bool:
    """
    Guarda el contenido del manual en un archivo PDF.
    Retorna True si es exitoso, False en caso contrario.
    """
    try:
        filepath = os.path.join(MANUAL_DIRECTORY, filename)
        
        # Prevenir path traversal verificando que el path final esté dentro del directorio
        real_path = os.path.realpath(filepath)
        real_manual_dir = os.path.realpath(MANUAL_DIRECTORY)
        
        if not real_path.startswith(real_manual_dir):
            logger.error(f"Intento de path traversal detectado: {filepath}")
            return False
        
        # Escribir archivo binario
        with open(filepath, 'wb') as f:
            f.write(content)
        
        logger.info(f"Archivo de manual guardado: {filename} ({len(content)} bytes)")
        return True
        
    except Exception as e:
        logger.error(f"Error al guardar archivo de manual {filename}: {e}")
        return False

def read_manual_file(filename: str) -> Optional[bytes]:
    """
    Lee el contenido de un archivo de manual.
    Retorna el contenido en bytes o None si hay error.
    """
    try:
        filepath = os.path.join(MANUAL_DIRECTORY, filename)
        
        # Prevenir path traversal
        real_path = os.path.realpath(filepath)
        real_manual_dir = os.path.realpath(MANUAL_DIRECTORY)
        
        if not real_path.startswith(real_manual_dir):
            logger.error(f"Intento de path traversal detectado: {filepath}")
            return None
        
        if not os.path.exists(filepath):
            logger.error(f"Archivo de manual no encontrado: {filename}")
            return None
        
        with open(filepath, 'rb') as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        logger.error(f"Error al leer archivo de manual {filename}: {e}")
        return None

def delete_manual_file(filename: str) -> bool:
    """
    Elimina un archivo de manual del disco.
    Retorna True si es exitoso, False en caso contrario.
    """
    try:
        filepath = os.path.join(MANUAL_DIRECTORY, filename)
        
        # Prevenir path traversal
        real_path = os.path.realpath(filepath)
        real_manual_dir = os.path.realpath(MANUAL_DIRECTORY)
        
        if not real_path.startswith(real_manual_dir):
            logger.error(f"Intento de path traversal detectado: {filepath}")
            return False
        
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Archivo de manual eliminado: {filename}")
            return True
        else:
            logger.warning(f"Archivo de manual no encontrado para eliminar: {filename}")
            return True  # No existe, objetivo cumplido
        
    except Exception as e:
        logger.error(f"Error al eliminar archivo de manual {filename}: {e}")
        return False

def create_manual(nombre: str, file_content: bytes, original_filename: str, 
                  categoria: str = None, descripcion: str = None, version: str = None,
                  username: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Crea un nuevo manual en la base de datos y guarda el archivo PDF.
    Retorna (manual_data, error_message)
    """
    conn = None
    cursor = None
    
    try:
        # Validar datos
        is_valid, error = validate_manual_data(nombre, categoria, descripcion)
        if not is_valid:
            return None, error
        
        # Validar archivo PDF
        is_valid_pdf, error = validate_pdf_file(file_content, original_filename)
        if not is_valid_pdf:
            return None, error
        
        # Generar ID único
        manual_id = str(uuid.uuid4())
        
        # Preparar datos
        nombre = nombre.strip()
        categoria = categoria.strip().upper() if categoria else None
        descripcion = descripcion.strip() if descripcion else None
        version = version.strip() if version else None
        file_size = len(file_content)
        
        # Generar filename
        filename = generate_filename(manual_id, nombre)
        
        # Guardar archivo primero
        if not save_manual_file(filename, file_content):
            return None, "Error al guardar el archivo PDF"
        
        # Guardar en base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO manuales (id, nombre, categoria, descripcion, filename, file_size, version, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (manual_id, nombre, categoria, descripcion, filename, file_size, version, username))
        conn.commit()
        
        # Obtener el registro creado
        cursor.execute("""
            SELECT id, nombre, categoria, descripcion, filename, file_size, version,
                   created_at, updated_at, created_by, download_count
            FROM manuales 
            WHERE id = ?
        """, (manual_id,))
        
        row = cursor.fetchone()
        
        result = {
            'id': str(row.id),
            'nombre': row.nombre,
            'categoria': row.categoria,
            'descripcion': row.descripcion,
            'filename': row.filename,
            'file_size': row.file_size,
            'version': row.version,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'updated_at': row.updated_at.isoformat() if row.updated_at else None,
            'created_by': row.created_by,
            'download_count': row.download_count
        }
        
        logger.info(f"Manual creado exitosamente: {manual_id} - {nombre}")
        return result, None
        
    except Exception as e:
        logger.error(f"Error al crear manual: {e}")
        if conn:
            conn.rollback()
        # Intentar eliminar archivo si falló la inserción en DB
        if 'filename' in locals():
            delete_manual_file(filename)
        return None, f"Error interno al crear manual: {str(e)}"
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_manuales(filters: Dict = None, limit: int = 20, offset: int = 0) -> Tuple[List[Dict], int]:
    """
    Obtiene lista de manuales con filtros y paginación.
    Retorna (lista_manuales, total_count)
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query base
        where_clauses = []
        params = []
        
        if filters:
            if filters.get('nombre'):
                where_clauses.append("nombre LIKE ?")
                params.append(f"%{filters['nombre']}%")
            
            if filters.get('categoria'):
                where_clauses.append("categoria = ?")
                params.append(filters['categoria'].upper())
            
            if filters.get('descripcion'):
                where_clauses.append("descripcion LIKE ?")
                params.append(f"%{filters['descripcion']}%")
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM manuales{where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone().total
        
        # Obtener registros paginados
        list_query = f"""
        SELECT id, nombre, categoria, descripcion, filename, file_size, version,
               created_at, updated_at, created_by, download_count
        FROM manuales
        {where_sql}
        ORDER BY created_at DESC
        OFFSET ? ROWS
        FETCH NEXT ? ROWS ONLY
        """
        
        cursor.execute(list_query, params + [offset, limit])
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': str(row.id),
                'nombre': row.nombre,
                'categoria': row.categoria,
                'descripcion': row.descripcion,
                'filename': row.filename,
                'file_size': row.file_size,
                'file_size_mb': round(row.file_size / (1024 * 1024), 2),
                'version': row.version,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                'created_by': row.created_by,
                'download_count': row.download_count
            })
        
        return results, total
        
    except Exception as e:
        logger.error(f"Error al obtener manuales: {e}")
        return [], 0
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_manual_by_id(manual_id: str) -> Optional[Dict]:
    """
    Obtiene un manual por su ID (solo metadata, no el archivo).
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre, categoria, descripcion, filename, file_size, version,
                   created_at, updated_at, created_by, download_count
            FROM manuales 
            WHERE id = ?
        """, (manual_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = {
            'id': str(row.id),
            'nombre': row.nombre,
            'categoria': row.categoria,
            'descripcion': row.descripcion,
            'filename': row.filename,
            'file_size': row.file_size,
            'file_size_mb': round(row.file_size / (1024 * 1024), 2),
            'version': row.version,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'updated_at': row.updated_at.isoformat() if row.updated_at else None,
            'created_by': row.created_by,
            'download_count': row.download_count
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error al obtener manual {manual_id}: {e}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def increment_download_count(manual_id: str) -> bool:
    """Incrementa el contador de descargas de un manual."""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE manuales
            SET download_count = download_count + 1
            WHERE id = ?
        """, (manual_id,))
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error al incrementar contador de descargas para manual {manual_id}: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_manual(manual_id: str) -> Tuple[bool, Optional[str]]:
    """
    Elimina un manual de la base de datos y su archivo.
    Retorna (success, error_message)
    """
    conn = None
    cursor = None
    
    try:
        # Obtener manual para saber el filename
        manual = get_manual_by_id(manual_id)
        if not manual:
            return False, "Manual no encontrado"
        
        # Eliminar de base de datos primero
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM manuales WHERE id = ?", (manual_id,))
        conn.commit()
        
        # Eliminar archivo
        if not delete_manual_file(manual['filename']):
            logger.warning(f"No se pudo eliminar archivo físico del manual {manual_id}")
        
        logger.info(f"Manual eliminado exitosamente: {manual_id}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error al eliminar manual {manual_id}: {e}")
        if conn:
            conn.rollback()
        return False, f"Error interno al eliminar manual: {str(e)}"
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
