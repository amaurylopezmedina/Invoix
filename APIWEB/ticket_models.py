"""
Modelos de datos para el sistema de Tickets de Incidencias
"""
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from database import get_db_connection
import logging

logger = logging.getLogger(__name__)


class PrioridadEnum(str, Enum):
    """Enum para prioridades de tickets"""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRÍTICA"
    
    @property
    def score(self) -> int:
        """Retorna el score numérico para ordenamiento"""
        return {
            "BAJA": 1,
            "MEDIA": 2,
            "ALTA": 3,
            "CRÍTICA": 4
        }[self.value]


class EstadoEnum(str, Enum):
    """Enum para estados de tickets"""
    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    RESUELTO = "RESUELTO"
    CERRADO = "CERRADO"


class TicketModel:
    """Modelo de datos para Ticket"""
    
    def __init__(self, 
                 id: str,
                 titulo: str,
                 prioridad: str,
                 categoria: str,
                 empresa: str,
                 descripcion: str,
                 estado: str,
                 creado_por: str,
                 asignado_a: Optional[str] = None,
                 prioridad_score: Optional[int] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 empresa_nombre: Optional[str] = None):
        self.id = id
        self.titulo = titulo
        self.prioridad = prioridad
        self.categoria = categoria
        self.empresa = empresa
        self.descripcion = descripcion
        self.estado = estado
        self.creado_por = creado_por
        self.asignado_a = asignado_a
        self.prioridad_score = prioridad_score or PrioridadEnum(prioridad).score
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.empresa_nombre = empresa_nombre
    
    def to_dict(self, include_description: bool = True, truncate_description: int = None) -> dict:
        """Convierte el ticket a diccionario"""
        descripcion = self.descripcion
        if truncate_description and descripcion:
            descripcion = descripcion[:truncate_description] + ('...' if len(descripcion) > truncate_description else '')
        
        data = {
            'id': self.id,
            'titulo': self.titulo,
            'prioridad': self.prioridad,
            'categoria': self.categoria,
            'empresa': self.empresa,
            'empresa_nombre': self.empresa_nombre,
            'estado': self.estado,
            'creado_por': self.creado_por,
            'asignado_a': self.asignado_a,
            'prioridad_score': self.prioridad_score,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        
        if include_description:
            data['descripcion'] = descripcion
            
        return data


class AttachmentModel:
    """Modelo de datos para Attachment"""
    
    def __init__(self,
                 id: str,
                 ticket_id: str,
                 filename: str,
                 original_name: str,
                 content_type: str,
                 size_bytes: int,
                 path: str,
                 uploaded_at: Optional[datetime] = None):
        self.id = id
        self.ticket_id = ticket_id
        self.filename = filename
        self.original_name = original_name
        self.content_type = content_type
        self.size_bytes = size_bytes
        self.path = path
        self.uploaded_at = uploaded_at or datetime.now()
    
    def to_dict(self) -> dict:
        """Convierte el attachment a diccionario"""
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'filename': self.filename,
            'original_name': self.original_name,
            'content_type': self.content_type,
            'size_bytes': self.size_bytes,
            'path': self.path,
            'uploaded_at': self.uploaded_at.isoformat() if isinstance(self.uploaded_at, datetime) else self.uploaded_at
        }


class TicketDatabase:
    """Clase para interactuar con la base de datos de tickets"""
    
    @staticmethod
    def create_tables():
        """Crea las tablas necesarias si no existen"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Tabla de tickets
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='tickets' AND xtype='U')
                BEGIN
                    CREATE TABLE tickets (
                        id NVARCHAR(50) PRIMARY KEY,
                        titulo NVARCHAR(200) NOT NULL,
                        prioridad NVARCHAR(20) NOT NULL CHECK (prioridad IN ('BAJA', 'MEDIA', 'ALTA', 'CRÍTICA')),
                        categoria NVARCHAR(100) NOT NULL,
                        empresa NVARCHAR(200) NULL,
                        descripcion NVARCHAR(MAX) NOT NULL,
                        estado NVARCHAR(20) NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'EN_PROGRESO', 'RESUELTO', 'CERRADO')),
                        creado_por NVARCHAR(200) NOT NULL,
                        asignado_a NVARCHAR(200) NULL,
                        prioridad_score INT NOT NULL,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        updated_at DATETIME2 DEFAULT GETDATE()
                    )
                END
            """)
            
            # Tabla de attachments
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ticket_attachments' AND xtype='U')
                BEGIN
                    CREATE TABLE ticket_attachments (
                        id NVARCHAR(50) PRIMARY KEY,
                        ticket_id NVARCHAR(50) NOT NULL,
                        filename NVARCHAR(255) NOT NULL,
                        original_name NVARCHAR(255) NOT NULL,
                        content_type NVARCHAR(100) NOT NULL,
                        size_bytes BIGINT NOT NULL,
                        path NVARCHAR(500) NOT NULL,
                        uploaded_at DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
                    )
                END
            """)
            
            # Índices para mejorar performance
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_tickets_estado' AND object_id = OBJECT_ID('tickets'))
                BEGIN
                    CREATE INDEX idx_tickets_estado ON tickets(estado)
                END
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_tickets_prioridad' AND object_id = OBJECT_ID('tickets'))
                BEGIN
                    CREATE INDEX idx_tickets_prioridad ON tickets(prioridad_score DESC)
                END
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_tickets_created_at' AND object_id = OBJECT_ID('tickets'))
                BEGIN
                    CREATE INDEX idx_tickets_created_at ON tickets(created_at DESC)
                END
            """)
            
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_ticket_attachments_ticket_id' AND object_id = OBJECT_ID('ticket_attachments'))
                BEGIN
                    CREATE INDEX idx_ticket_attachments_ticket_id ON ticket_attachments(ticket_id)
                END
            """)
            
            conn.commit()
            logger.info("Tablas de tickets creadas exitosamente")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear tablas de tickets: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def create_ticket(ticket: TicketModel) -> TicketModel:
        """Crea un nuevo ticket en la base de datos"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO tickets (id, titulo, prioridad, categoria, empresa, descripcion, 
                                   estado, creado_por, asignado_a, prioridad_score, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticket.id, ticket.titulo, ticket.prioridad, ticket.categoria, ticket.empresa,
                  ticket.descripcion, ticket.estado, ticket.creado_por, ticket.asignado_a,
                  ticket.prioridad_score, ticket.created_at, ticket.updated_at))
            conn.commit()
            logger.info(f"Ticket {ticket.id} creado exitosamente")
            return ticket
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear ticket: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_ticket_by_id(ticket_id: str) -> Optional[TicketModel]:
        """Obtiene un ticket por su ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT t.id, t.titulo, t.prioridad, t.categoria, t.empresa, t.descripcion, t.estado, 
                       t.creado_por, t.asignado_a, t.prioridad_score, t.created_at, t.updated_at,
                       COALESCE(e.NombreComercial, e.RazonSocial, t.empresa) as empresa_nombre
                FROM tickets t
                LEFT JOIN EmpresaFE e ON LTRIM(RTRIM(t.empresa)) = LTRIM(RTRIM(e.RNC))
                WHERE t.id = ?
            """, (ticket_id,))
            row = cursor.fetchone()
            if row:
                return TicketModel(*row)
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def list_tickets(estado: Optional[str] = None,
                    prioridad: Optional[str] = None,
                    categoria: Optional[str] = None,
                    empresa: Optional[str] = None,
                    creado_por: Optional[str] = None,
                    asignado_a: Optional[str] = None,
                    search: Optional[str] = None,
                    limit: int = 50,
                    offset: int = 0,
                    sort: str = "priority_score:desc,created_at:asc") -> tuple[List[TicketModel], int]:
        """Lista tickets con filtros y paginación"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Construir query base con alias 't' desde el inicio
            where_clauses = []
            params = []
            
            if estado and estado.upper() != "ALL":
                where_clauses.append("t.estado = ?")
                params.append(estado.upper())
            
            if prioridad:
                where_clauses.append("t.prioridad = ?")
                params.append(prioridad.upper())
            
            if categoria:
                where_clauses.append("t.categoria = ?")
                params.append(categoria)
            
            if empresa:
                where_clauses.append("t.empresa LIKE ?")
                params.append(f"%{empresa}%")
            
            if creado_por:
                where_clauses.append("t.creado_por = ?")
                params.append(creado_por)
            
            if asignado_a:
                where_clauses.append("t.asignado_a = ?")
                params.append(asignado_a)
            
            if search:
                where_clauses.append("(t.titulo LIKE ? OR t.descripcion LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])
            
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Parsear ordenamiento
            order_parts = []
            for sort_item in sort.split(","):
                parts = sort_item.strip().split(":")
                field = parts[0].strip()
                direction = parts[1].strip().upper() if len(parts) > 1 else "ASC"
                
                if field == "priority_score":
                    order_parts.append(f"t.prioridad_score {direction}")
                elif field == "created_at":
                    order_parts.append(f"t.created_at {direction}")
                elif field == "updated_at":
                    order_parts.append(f"t.updated_at {direction}")
            
            order_sql = "ORDER BY " + ", ".join(order_parts) if order_parts else "ORDER BY t.prioridad_score DESC, t.created_at ASC"
            
            # Contar total
            count_query = f"SELECT COUNT(*) FROM tickets t {where_sql}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Obtener registros con paginación
            query = f"""
                SELECT t.id, t.titulo, t.prioridad, t.categoria, t.empresa, t.descripcion, t.estado, 
                       t.creado_por, t.asignado_a, t.prioridad_score, t.created_at, t.updated_at,
                       COALESCE(e.NombreComercial, e.RazonSocial, t.empresa) as empresa_nombre
                FROM tickets t
                LEFT JOIN EmpresaFE e ON LTRIM(RTRIM(t.empresa)) = LTRIM(RTRIM(e.RNC))
                {where_sql}
                {order_sql}
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """
            params.extend([offset, limit])
            cursor.execute(query, params)
            
            tickets = []
            for row in cursor.fetchall():
                tickets.append(TicketModel(*row))
            
            return tickets, total_count
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update_ticket(ticket_id: str, **kwargs) -> Optional[TicketModel]:
        """Actualiza un ticket existente"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Construir UPDATE dinámico
            update_fields = []
            params = []
            
            allowed_fields = ['titulo', 'prioridad', 'categoria', 'empresa', 'descripcion', 
                            'estado', 'asignado_a']
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
                    
                    # Actualizar prioridad_score si se actualiza prioridad
                    if field == 'prioridad':
                        update_fields.append("prioridad_score = ?")
                        params.append(PrioridadEnum(value).score)
            
            if not update_fields:
                return TicketDatabase.get_ticket_by_id(ticket_id)
            
            # Siempre actualizar updated_at
            update_fields.append("updated_at = GETDATE()")
            
            query = f"""
                UPDATE tickets
                SET {', '.join(update_fields)}
                WHERE id = ?
            """
            params.append(ticket_id)
            
            cursor.execute(query, params)
            conn.commit()
            
            logger.info(f"Ticket {ticket_id} actualizado exitosamente")
            return TicketDatabase.get_ticket_by_id(ticket_id)
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al actualizar ticket: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete_ticket(ticket_id: str) -> bool:
        """Elimina un ticket"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            conn.commit()
            logger.info(f"Ticket {ticket_id} eliminado exitosamente")
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar ticket: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def create_attachment(attachment: AttachmentModel) -> AttachmentModel:
        """Crea un nuevo attachment"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO ticket_attachments (id, ticket_id, filename, original_name, 
                                               content_type, size_bytes, path, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (attachment.id, attachment.ticket_id, attachment.filename, attachment.original_name,
                  attachment.content_type, attachment.size_bytes, attachment.path, attachment.uploaded_at))
            conn.commit()
            logger.info(f"Attachment {attachment.id} creado exitosamente")
            return attachment
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al crear attachment: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_attachments_by_ticket(ticket_id: str) -> List[AttachmentModel]:
        """Obtiene todos los attachments de un ticket"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, ticket_id, filename, original_name, content_type, 
                       size_bytes, path, uploaded_at
                FROM ticket_attachments
                WHERE ticket_id = ?
                ORDER BY uploaded_at DESC
            """, (ticket_id,))
            
            attachments = []
            for row in cursor.fetchall():
                attachments.append(AttachmentModel(*row))
            return attachments
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_attachment_by_id(attachment_id: str) -> Optional[AttachmentModel]:
        """Obtiene un attachment por su ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, ticket_id, filename, original_name, content_type, 
                       size_bytes, path, uploaded_at
                FROM ticket_attachments
                WHERE id = ?
            """, (attachment_id,))
            row = cursor.fetchone()
            if row:
                return AttachmentModel(*row)
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete_attachment(attachment_id: str) -> bool:
        """Elimina un attachment"""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM ticket_attachments WHERE id = ?", (attachment_id,))
            conn.commit()
            logger.info(f"Attachment {attachment_id} eliminado exitosamente")
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al eliminar attachment: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
