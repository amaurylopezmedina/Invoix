"""
Módulo para gestión de Queries SQL de SQL Server.
Almacena metadata en base de datos y archivos .txt en disco C:\\Query\\
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

# Configuración del directorio de queries
QUERY_DIRECTORY = r"C:\Query"
MAX_QUERY_LENGTH = 20000
MAX_NAME_LENGTH = 100

def ensure_query_directory():
    """Crea el directorio de queries si no existe."""
    try:
        Path(QUERY_DIRECTORY).mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio de queries asegurado: {QUERY_DIRECTORY}")
    except Exception as e:
        logger.error(f"Error al crear directorio de queries: {e}")
        raise

def sanitize_filename(nombre: str) -> str:
    """
    Sanitiza el nombre para crear un filename seguro.
    Permite solo letras, números, guiones bajos y trunca a MAX_NAME_LENGTH.
    Previene path traversal attacks.
    """
    # Remover cualquier carácter peligroso
    safe_name = re.sub(r'[^\w\s-]', '', nombre)
    # Reemplazar espacios con guiones bajos
    safe_name = re.sub(r'\s+', '_', safe_name)
    # Truncar a longitud máxima
    safe_name = safe_name[:MAX_NAME_LENGTH]
    # Asegurar que no esté vacío
    if not safe_name:
        safe_name = "unnamed_query"
    return safe_name

def validate_query_data(data: Dict) -> Tuple[bool, Optional[str]]:
    """
    Valida los datos del query antes de guardar.
    Retorna (is_valid, error_message)
    """
    # Validar nombre
    nombre = data.get('nombre', '').strip()
    if not nombre or len(nombre) < 3 or len(nombre) > MAX_NAME_LENGTH:
        return False, f"El nombre debe tener entre 3 y {MAX_NAME_LENGTH} caracteres"
    
    # Validar tipo
    tipo = data.get('tipo', '').strip().upper()
    valid_tipos = ['SELECT', 'UPDATE', 'INSERT', 'DELETE', 'VIEW', 'PROCEDURE', 'FUNCTION', 'OTHER']
    if not tipo or tipo not in valid_tipos:
        return False, f"El tipo debe ser uno de: {', '.join(valid_tipos)}"
    
    # Validar query_text
    query_text = data.get('query_text', '').strip()
    if not query_text:
        return False, "El contenido del query (query_text) es obligatorio"
    
    if len(query_text) > MAX_QUERY_LENGTH:
        return False, f"El query no puede exceder {MAX_QUERY_LENGTH} caracteres"
    
    # Validar que no contenga caracteres peligrosos para path traversal
    if any(char in nombre for char in ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']):
        return False, "El nombre contiene caracteres no permitidos"
    
    return True, None

def create_query_table():
    """Crea la tabla de queries en la base de datos si no existe."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sql_queries' AND xtype='U')
        BEGIN
            CREATE TABLE sql_queries (
                id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
                nombre NVARCHAR(100) NOT NULL,
                tipo NVARCHAR(20) NOT NULL,
                finalidad NVARCHAR(500),
                empresa NVARCHAR(200),
                filename NVARCHAR(300) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT GETDATE(),
                updated_at DATETIME NOT NULL DEFAULT GETDATE(),
                created_by NVARCHAR(100),
                INDEX idx_nombre (nombre),
                INDEX idx_tipo (tipo),
                INDEX idx_empresa (empresa),
                INDEX idx_created_at (created_at)
            )
        END
        """
        cursor.execute(query)
        conn.commit()
        logger.info("Tabla sql_queries verificada/creada exitosamente")
        
    except Exception as e:
        logger.error(f"Error al crear tabla sql_queries: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def generate_filename(query_id: str, nombre: str) -> str:
    """Genera el nombre de archivo seguro."""
    safe_name = sanitize_filename(nombre)
    return f"{query_id}_{safe_name}.txt"

def save_query_file(filename: str, content: str) -> bool:
    """
    Guarda el contenido del query en un archivo .txt.
    Retorna True si es exitoso, False en caso contrario.
    """
    try:
        filepath = os.path.join(QUERY_DIRECTORY, filename)
        
        # Prevenir path traversal verificando que el path final esté dentro del directorio
        real_path = os.path.realpath(filepath)
        real_query_dir = os.path.realpath(QUERY_DIRECTORY)
        
        if not real_path.startswith(real_query_dir):
            logger.error(f"Intento de path traversal detectado: {filepath}")
            return False
        
        # Escribir archivo con encoding UTF-8
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Archivo de query guardado: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error al guardar archivo de query {filename}: {e}")
        return False

def read_query_file(filename: str) -> Optional[str]:
    """
    Lee el contenido de un archivo de query.
    Retorna el contenido o None si hay error.
    """
    try:
        filepath = os.path.join(QUERY_DIRECTORY, filename)
        
        # Prevenir path traversal
        real_path = os.path.realpath(filepath)
        real_query_dir = os.path.realpath(QUERY_DIRECTORY)
        
        if not real_path.startswith(real_query_dir):
            logger.error(f"Intento de path traversal detectado: {filepath}")
            return None
        
        if not os.path.exists(filepath):
            logger.error(f"Archivo de query no encontrado: {filename}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        logger.error(f"Error al leer archivo de query {filename}: {e}")
        return None

def delete_query_file(filename: str) -> bool:
    """
    Elimina un archivo de query del disco.
    Retorna True si es exitoso, False en caso contrario.
    """
    try:
        filepath = os.path.join(QUERY_DIRECTORY, filename)
        
        # Prevenir path traversal
        real_path = os.path.realpath(filepath)
        real_query_dir = os.path.realpath(QUERY_DIRECTORY)
        
        if not real_path.startswith(real_query_dir):
            logger.error(f"Intento de path traversal detectado: {filepath}")
            return False
        
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Archivo de query eliminado: {filename}")
            return True
        else:
            logger.warning(f"Archivo de query no encontrado para eliminar: {filename}")
            return True  # No existe, objetivo cumplido
        
    except Exception as e:
        logger.error(f"Error al eliminar archivo de query {filename}: {e}")
        return False

def create_backup(filename: str) -> bool:
    """
    Crea un backup del archivo antes de actualizarlo.
    Retorna True si es exitoso, False en caso contrario.
    """
    try:
        filepath = os.path.join(QUERY_DIRECTORY, filename)
        
        if not os.path.exists(filepath):
            return True  # No hay nada que respaldar
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(filename)[0]
        backup_filename = f"{base_name}_backup_{timestamp}.bak"
        backup_path = os.path.join(QUERY_DIRECTORY, backup_filename)
        
        # Prevenir path traversal
        real_backup = os.path.realpath(backup_path)
        real_query_dir = os.path.realpath(QUERY_DIRECTORY)
        
        if not real_backup.startswith(real_query_dir):
            logger.error(f"Intento de path traversal detectado en backup: {backup_path}")
            return False
        
        import shutil
        shutil.copy2(filepath, backup_path)
        logger.info(f"Backup creado: {backup_filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error al crear backup de {filename}: {e}")
        return False

def create_query(data: Dict, username: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Crea un nuevo query en la base de datos y guarda el archivo.
    Retorna (query_data, error_message)
    """
    conn = None
    cursor = None
    
    try:
        # Validar datos
        is_valid, error = validate_query_data(data)
        if not is_valid:
            return None, error
        
        # Generar ID único
        query_id = str(uuid.uuid4())
        
        # Extraer y preparar datos
        nombre = data['nombre'].strip()
        tipo = data['tipo'].strip().upper()
        finalidad = data.get('finalidad', '').strip() or None
        empresa = data.get('empresa', '').strip() or None
        query_text = data['query_text'].strip()
        
        # Generar filename
        filename = generate_filename(query_id, nombre)
        
        # Guardar archivo primero
        if not save_query_file(filename, query_text):
            return None, "Error al guardar el archivo de query"
        
        # Guardar en base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO sql_queries (id, nombre, tipo, finalidad, empresa, filename, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_query, (query_id, nombre, tipo, finalidad, empresa, filename, username))
        conn.commit()
        
        # Obtener el registro creado
        cursor.execute("""
            SELECT id, nombre, tipo, finalidad, empresa, filename, created_at, updated_at, created_by
            FROM sql_queries 
            WHERE id = ?
        """, (query_id,))
        
        row = cursor.fetchone()
        
        result = {
            'id': str(row.id),
            'nombre': row.nombre,
            'tipo': row.tipo,
            'finalidad': row.finalidad,
            'empresa': row.empresa,
            'filename': row.filename,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'updated_at': row.updated_at.isoformat() if row.updated_at else None,
            'created_by': row.created_by
        }
        
        logger.info(f"Query creado exitosamente: {query_id} - {nombre}")
        return result, None
        
    except Exception as e:
        logger.error(f"Error al crear query: {e}")
        if conn:
            conn.rollback()
        # Intentar eliminar archivo si falló la inserción en DB
        if 'filename' in locals():
            delete_query_file(filename)
        return None, f"Error interno al crear query: {str(e)}"
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_queries(filters: Dict = None, limit: int = 20, offset: int = 0) -> Tuple[List[Dict], int]:
    """
    Obtiene lista de queries con filtros y paginación.
    Retorna (lista_queries, total_count)
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
            
            if filters.get('tipo'):
                where_clauses.append("tipo = ?")
                params.append(filters['tipo'].upper())
            
            if filters.get('empresa'):
                where_clauses.append("empresa LIKE ?")
                params.append(f"%{filters['empresa']}%")
            
            if filters.get('finalidad'):
                where_clauses.append("finalidad LIKE ?")
                params.append(f"%{filters['finalidad']}%")
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM sql_queries{where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone().total
        
        # Obtener registros paginados
        list_query = f"""
        SELECT id, nombre, tipo, finalidad, empresa, filename, created_at, updated_at, created_by
        FROM sql_queries
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
                'tipo': row.tipo,
                'finalidad': row.finalidad,
                'empresa': row.empresa,
                'filename': row.filename,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'updated_at': row.updated_at.isoformat() if row.updated_at else None,
                'created_by': row.created_by
            })
        
        return results, total
        
    except Exception as e:
        logger.error(f"Error al obtener queries: {e}")
        return [], 0
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_query_by_id(query_id: str, include_text: bool = True) -> Optional[Dict]:
    """
    Obtiene un query por su ID.
    Si include_text=True, incluye el contenido del archivo.
    """
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, nombre, tipo, finalidad, empresa, filename, created_at, updated_at, created_by
            FROM sql_queries 
            WHERE id = ?
        """, (query_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        result = {
            'id': str(row.id),
            'nombre': row.nombre,
            'tipo': row.tipo,
            'finalidad': row.finalidad,
            'empresa': row.empresa,
            'filename': row.filename,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'updated_at': row.updated_at.isoformat() if row.updated_at else None,
            'created_by': row.created_by
        }
        
        # Leer contenido del archivo si se solicita
        if include_text:
            query_text = read_query_file(row.filename)
            if query_text is None:
                logger.warning(f"No se pudo leer el archivo del query {query_id}")
                result['query_text'] = ""
                result['file_error'] = True
            else:
                result['query_text'] = query_text
        
        return result
        
    except Exception as e:
        logger.error(f"Error al obtener query {query_id}: {e}")
        return None
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def update_query(query_id: str, data: Dict, username: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Actualiza un query existente.
    Retorna (query_data, error_message)
    """
    conn = None
    cursor = None
    
    try:
        # Validar datos
        is_valid, error = validate_query_data(data)
        if not is_valid:
            return None, error
        
        # Obtener query actual
        current_query = get_query_by_id(query_id, include_text=False)
        if not current_query:
            return None, "Query no encontrado"
        
        # Extraer datos nuevos
        nombre = data['nombre'].strip()
        tipo = data['tipo'].strip().upper()
        finalidad = data.get('finalidad', '').strip() or None
        empresa = data.get('empresa', '').strip() or None
        query_text = data['query_text'].strip()
        
        old_filename = current_query['filename']
        new_filename = old_filename
        
        # Si cambió el nombre, generar nuevo filename
        if nombre != current_query['nombre']:
            new_filename = generate_filename(query_id, nombre)
        
        # Crear backup del archivo actual
        create_backup(old_filename)
        
        # Guardar nuevo contenido
        if not save_query_file(new_filename, query_text):
            return None, "Error al guardar el archivo de query"
        
        # Si cambió el filename, eliminar archivo antiguo
        if new_filename != old_filename:
            delete_query_file(old_filename)
        
        # Actualizar base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_query_sql = """
        UPDATE sql_queries
        SET nombre = ?, tipo = ?, finalidad = ?, empresa = ?, 
            filename = ?, updated_at = GETDATE()
        WHERE id = ?
        """
        
        cursor.execute(update_query_sql, (nombre, tipo, finalidad, empresa, new_filename, query_id))
        conn.commit()
        
        # Obtener registro actualizado
        result = get_query_by_id(query_id, include_text=False)
        
        logger.info(f"Query actualizado exitosamente: {query_id} - {nombre}")
        return result, None
        
    except Exception as e:
        logger.error(f"Error al actualizar query {query_id}: {e}")
        if conn:
            conn.rollback()
        return None, f"Error interno al actualizar query: {str(e)}"
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def delete_query(query_id: str) -> Tuple[bool, Optional[str]]:
    """
    Elimina un query de la base de datos y su archivo.
    Retorna (success, error_message)
    """
    conn = None
    cursor = None
    
    try:
        # Obtener query para saber el filename
        query = get_query_by_id(query_id, include_text=False)
        if not query:
            return False, "Query no encontrado"
        
        # Eliminar de base de datos primero
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sql_queries WHERE id = ?", (query_id,))
        conn.commit()
        
        # Eliminar archivo
        if not delete_query_file(query['filename']):
            logger.warning(f"No se pudo eliminar archivo físico del query {query_id}")
        
        logger.info(f"Query eliminado exitosamente: {query_id}")
        return True, None
        
    except Exception as e:
        logger.error(f"Error al eliminar query {query_id}: {e}")
        if conn:
            conn.rollback()
        return False, f"Error interno al eliminar query: {str(e)}"
        
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
