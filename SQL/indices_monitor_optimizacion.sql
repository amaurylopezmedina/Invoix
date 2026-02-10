-- ============================================================================
-- SCRIPT DE ÍNDICES RECOMENDADOS PARA OPTIMIZACIÓN DE ASESYS MONITOR
-- ============================================================================
-- Este script crea índices en las tablas de Facturación Electrónica para
-- mejorar el rendimiento de las consultas del módulo MONITOR.
--
-- IMPORTANTE: 
-- - Revisar si los índices ya existen antes de ejecutar
-- - Ejecutar en horarios de baja actividad si es un sistema en producción
-- - Monitorear el rendimiento después de crear los índices
-- ============================================================================

USE [NombreBaseDatos]  -- Reemplazar con el nombre de su base de datos
GO

-- ============================================================================
-- 1. ÍNDICE EN ESTADO FISCAL
-- ============================================================================
-- Este índice mejora las búsquedas por estado fiscal, que es el filtro
-- PRIORITARIO en el módulo MONITOR
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes 
               WHERE name = 'IX_FEEncabezado_EstadoFiscal' 
               AND object_id = OBJECT_ID('dbo.FEEncabezado'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_FEEncabezado_EstadoFiscal
    ON dbo.FEEncabezado (EstadoFiscal)
    INCLUDE (RNCEmisor, eNCF, FechaEmision, NumeroFacturaInterna, MontoTotal, TotalITBIS)
    WITH (ONLINE = OFF, FILLFACTOR = 90)
    
    PRINT 'Índice IX_FEEncabezado_EstadoFiscal creado exitosamente'
END
ELSE
BEGIN
    PRINT 'Índice IX_FEEncabezado_EstadoFiscal ya existe'
END
GO

-- ============================================================================
-- 2. ÍNDICE EN RNC EMISOR
-- ============================================================================
-- Mejora las búsquedas filtradas por RNC del emisor
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes 
               WHERE name = 'IX_FEEncabezado_RNCEmisor' 
               AND object_id = OBJECT_ID('dbo.FEEncabezado'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_FEEncabezado_RNCEmisor
    ON dbo.FEEncabezado (RNCEmisor)
    INCLUDE (eNCF, EstadoFiscal, FechaEmision, NumeroFacturaInterna)
    WITH (ONLINE = OFF, FILLFACTOR = 90)
    
    PRINT 'Índice IX_FEEncabezado_RNCEmisor creado exitosamente'
END
ELSE
BEGIN
    PRINT 'Índice IX_FEEncabezado_RNCEmisor ya existe'
END
GO

-- ============================================================================
-- 3. ÍNDICE EN FECHA EMISIÓN
-- ============================================================================
-- Mejora las búsquedas por rango de fechas
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes 
               WHERE name = 'IX_FEEncabezado_FechaEmision' 
               AND object_id = OBJECT_ID('dbo.FEEncabezado'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_FEEncabezado_FechaEmision
    ON dbo.FEEncabezado (FechaEmision)
    INCLUDE (RNCEmisor, eNCF, EstadoFiscal, NumeroFacturaInterna, MontoTotal, TotalITBIS)
    WITH (ONLINE = OFF, FILLFACTOR = 90)
    
    PRINT 'Índice IX_FEEncabezado_FechaEmision creado exitosamente'
END
ELSE
BEGIN
    PRINT 'Índice IX_FEEncabezado_FechaEmision ya existe'
END
GO

-- ============================================================================
-- 4. ÍNDICE COMPUESTO - RNC EMISOR + ENCF
-- ============================================================================
-- Optimiza las búsquedas específicas por RNC y eNCF (usado en todos los
-- endpoints de acciones: GenerarYFirmar, EnviarDGII, ConsultaDGII, etc.)
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes 
               WHERE name = 'IX_FEEncabezado_RNCEmisor_eNCF' 
               AND object_id = OBJECT_ID('dbo.FEEncabezado'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_FEEncabezado_RNCEmisor_eNCF
    ON dbo.FEEncabezado (RNCEmisor, eNCF)
    INCLUDE (EstadoFiscal, FechaEmision, FechaFirma, CodigoSeguridad, MontoTotal, TotalITBIS, MontoDGII, MontoITBISDGII, URLQR)
    WITH (ONLINE = OFF, FILLFACTOR = 90)
    
    PRINT 'Índice IX_FEEncabezado_RNCEmisor_eNCF creado exitosamente'
END
ELSE
BEGIN
    PRINT 'Índice IX_FEEncabezado_RNCEmisor_eNCF ya existe'
END
GO

-- ============================================================================
-- 5. ÍNDICE COMPUESTO - ESTADO FISCAL + FECHA EMISIÓN
-- ============================================================================
-- Optimiza las búsquedas combinadas más comunes en el MONITOR
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes 
               WHERE name = 'IX_FEEncabezado_EstadoFiscal_FechaEmision' 
               AND object_id = OBJECT_ID('dbo.FEEncabezado'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_FEEncabezado_EstadoFiscal_FechaEmision
    ON dbo.FEEncabezado (EstadoFiscal, FechaEmision DESC)
    INCLUDE (RNCEmisor, eNCF, NumeroFacturaInterna, MontoTotal, TotalITBIS, MontoDGII, MontoITBISDGII)
    WITH (ONLINE = OFF, FILLFACTOR = 90)
    
    PRINT 'Índice IX_FEEncabezado_EstadoFiscal_FechaEmision creado exitosamente'
END
ELSE
BEGIN
    PRINT 'Índice IX_FEEncabezado_EstadoFiscal_FechaEmision ya existe'
END
GO

-- ============================================================================
-- 6. ÍNDICE EN TIPO ECF
-- ============================================================================
-- Mejora las búsquedas filtradas por tipo de comprobante electrónico
-- ============================================================================

IF NOT EXISTS (SELECT * FROM sys.indexes 
               WHERE name = 'IX_FEEncabezado_TipoECF' 
               AND object_id = OBJECT_ID('dbo.FEEncabezado'))
BEGIN
    CREATE NONCLUSTERED INDEX IX_FEEncabezado_TipoECF
    ON dbo.FEEncabezado (TipoECF)
    INCLUDE (RNCEmisor, eNCF, EstadoFiscal, FechaEmision)
    WITH (ONLINE = OFF, FILLFACTOR = 90)
    
    PRINT 'Índice IX_FEEncabezado_TipoECF creado exitosamente'
END
ELSE
BEGIN
    PRINT 'Índice IX_FEEncabezado_TipoECF ya existe'
END
GO

-- ============================================================================
-- ESTADÍSTICAS Y MANTENIMIENTO
-- ============================================================================
-- Actualizar estadísticas después de crear los índices
-- ============================================================================

UPDATE STATISTICS dbo.FEEncabezado WITH FULLSCAN
GO

PRINT ''
PRINT '============================================================================'
PRINT 'RESUMEN DE ÍNDICES CREADOS PARA ASESYS MONITOR'
PRINT '============================================================================'
PRINT ''

-- Mostrar los índices creados
SELECT 
    i.name AS NombreIndice,
    i.type_desc AS TipoIndice,
    STATS_DATE(i.object_id, i.index_id) AS UltimaActualizacionEstadisticas,
    (SELECT SUM(s.used_page_count) * 8 / 1024.0 
     FROM sys.dm_db_partition_stats s 
     WHERE s.object_id = i.object_id AND s.index_id = i.index_id) AS TamanoMB
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID('dbo.FEEncabezado')
    AND i.name LIKE 'IX_FEEncabezado_%'
ORDER BY i.name
GO

PRINT ''
PRINT 'Script completado exitosamente'
PRINT 'Fecha: ' + CONVERT(VARCHAR(20), GETDATE(), 120)
GO

-- ============================================================================
-- NOTAS IMPORTANTES
-- ============================================================================
-- 
-- 1. IMPACTO EN RENDIMIENTO:
--    - Los índices mejoran las consultas SELECT
--    - Pueden ralentizar ligeramente las operaciones INSERT/UPDATE/DELETE
--    - El impacto es mínimo comparado con los beneficios en consultas
--
-- 2. MANTENIMIENTO:
--    - Ejecutar UPDATE STATISTICS periódicamente (semanal o mensual)
--    - Considerar reorganizar o reconstruir índices fragmentados
--    - Monitorear el uso de índices con DMVs
--
-- 3. MONITOREO:
--    Para verificar el uso de los índices, ejecutar:
--    
--    SELECT 
--        OBJECT_NAME(s.object_id) AS NombreTabla,
--        i.name AS NombreIndice,
--        s.user_seeks AS Busquedas,
--        s.user_scans AS Escaneos,
--        s.user_lookups AS Busquedas_Clave,
--        s.user_updates AS Actualizaciones
--    FROM sys.dm_db_index_usage_stats s
--    INNER JOIN sys.indexes i ON s.object_id = i.object_id AND s.index_id = i.index_id
--    WHERE OBJECT_NAME(s.object_id) = 'FEEncabezado'
--    ORDER BY s.user_seeks + s.user_scans + s.user_lookups DESC
--
-- 4. CONSIDERACIÓN DE CAJA:
--    El filtro por "caja" usa LEFT(NumeroFacturaInterna, 1)
--    Si las búsquedas por caja son muy frecuentes, considerar:
--    - Agregar una columna calculada persistida: Caja AS LEFT(NumeroFacturaInterna, 1) PERSISTED
--    - Crear un índice en esa columna calculada
--
-- 5. ROLLBACK:
--    Si necesita eliminar los índices creados:
--    
--    DROP INDEX IF EXISTS IX_FEEncabezado_EstadoFiscal ON dbo.FEEncabezado
--    DROP INDEX IF EXISTS IX_FEEncabezado_RNCEmisor ON dbo.FEEncabezado
--    DROP INDEX IF EXISTS IX_FEEncabezado_FechaEmision ON dbo.FEEncabezado
--    DROP INDEX IF EXISTS IX_FEEncabezado_RNCEmisor_eNCF ON dbo.FEEncabezado
--    DROP INDEX IF EXISTS IX_FEEncabezado_EstadoFiscal_FechaEmision ON dbo.FEEncabezado
--    DROP INDEX IF EXISTS IX_FEEncabezado_TipoECF ON dbo.FEEncabezado
--
-- ============================================================================
