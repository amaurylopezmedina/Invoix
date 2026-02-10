-- =============================================
-- Script de Optimización de Indices
-- Para FEEnvioASESYS - Facturación Electrónica
-- Fecha: 5 de febrero de 2026
-- =============================================

USE [bscodeca01]; -- Cambiar por tu base de datos
GO

SET NOCOUNT ON;
GO

PRINT '========================================';
PRINT 'Iniciando creación de índices optimizados';
PRINT 'Fecha: ' + CONVERT(VARCHAR, GETDATE(), 120);
PRINT '========================================';
PRINT '';

-- =============================================
-- 1. ÍNDICE PRINCIPAL PARA CONSULTA DE PENDIENTES
-- =============================================
PRINT '1. Creando índice IX_FEEncabezado_EstadoFiscal_Envio...';

IF EXISTS (SELECT 1 FROM sys.indexes 
           WHERE name = 'IX_FEEncabezado_EstadoFiscal_Envio' 
           AND object_id = OBJECT_ID('vFEEncabezado'))
BEGIN
    PRINT '   → Ya existe, eliminando versión anterior...';
    DROP INDEX IX_FEEncabezado_EstadoFiscal_Envio ON vFEEncabezado;
END

CREATE NONCLUSTERED INDEX IX_FEEncabezado_EstadoFiscal_Envio
ON [dbo].[vFEEncabezado] (EstadoFiscal, TipoECFL, FechaEmision)
INCLUDE (
    RNCEmisor, eNCF, Tabla, campo1, campo2, TipoECF, 
    MontoTotal, CodigoSeguridad, RazonSocialEmisor, 
    RazonSocialComprador, FechaCreacion
)
WITH (
    FILLFACTOR = 90,
    PAD_INDEX = ON,
    ONLINE = ON,
    SORT_IN_TEMPDB = ON,
    DATA_COMPRESSION = PAGE  -- Compresión para ahorrar espacio
);

PRINT '   ✓ Índice IX_FEEncabezado_EstadoFiscal_Envio creado exitosamente';
PRINT '';

-- =============================================
-- 2. ÍNDICE PARA VERIFICACIÓN DE ENVIADOS
-- =============================================
PRINT '2. Creando índice IX_FEEncabezado_Enviado...';

IF EXISTS (SELECT 1 FROM sys.indexes 
           WHERE name = 'IX_FEEncabezado_Enviado' 
           AND object_id = OBJECT_ID('vFEEncabezado'))
BEGIN
    PRINT '   → Ya existe, eliminando versión anterior...';
    DROP INDEX IX_FEEncabezado_Enviado ON vFEEncabezado;
END

CREATE NONCLUSTERED INDEX IX_FEEncabezado_Enviado
ON [dbo].[vFEEncabezado] (RNCEmisor, eNCF)
INCLUDE (enviado)
WHERE enviado = 1  -- Filtered index: solo facturas enviadas
WITH (
    FILLFACTOR = 95,
    PAD_INDEX = ON,
    ONLINE = ON,
    SORT_IN_TEMPDB = ON,
    DATA_COMPRESSION = PAGE
);

PRINT '   ✓ Índice IX_FEEncabezado_Enviado creado exitosamente';
PRINT '';

-- =============================================
-- 3. ÍNDICE PARA TABLA DE TOKENS
-- =============================================
PRINT '3. Creando índice IX_FEToken_RNC_Ambiente...';

IF EXISTS (SELECT 1 FROM sys.indexes 
           WHERE name = 'IX_FEToken_RNC_Ambiente' 
           AND object_id = OBJECT_ID('FEToken'))
BEGIN
    PRINT '   → Ya existe, eliminando versión anterior...';
    DROP INDEX IX_FEToken_RNC_Ambiente ON FEToken;
END

CREATE NONCLUSTERED INDEX IX_FEToken_RNC_Ambiente
ON [dbo].[FEToken] (rnc, ambiente, expedido DESC)
INCLUDE (token, expira)
WITH (
    FILLFACTOR = 90,
    PAD_INDEX = ON,
    ONLINE = ON,
    SORT_IN_TEMPDB = ON,
    DATA_COMPRESSION = ROW
);

PRINT '   ✓ Índice IX_FEToken_RNC_Ambiente creado exitosamente';
PRINT '';

-- =============================================
-- 4. ACTUALIZAR ESTADÍSTICAS
-- =============================================
PRINT '4. Actualizando estadísticas...';

UPDATE STATISTICS vFEEncabezado WITH FULLSCAN;
UPDATE STATISTICS FEToken WITH FULLSCAN;

PRINT '   ✓ Estadísticas actualizadas';
PRINT '';

-- =============================================
-- 5. VERIFICACIÓN Y REPORTE
-- =============================================
PRINT '========================================';
PRINT 'VERIFICACIÓN DE ÍNDICES CREADOS';
PRINT '========================================';

SELECT 
    OBJECT_NAME(i.object_id) AS Tabla,
    i.name AS NombreIndice,
    i.type_desc AS TipoIndice,
    ps.used_page_count * 8 / 1024.0 AS SizeMB,
    ps.row_count AS FilasIndexadas,
    CASE 
        WHEN i.fill_factor = 0 THEN 100 
        ELSE i.fill_factor 
    END AS FillFactor
FROM sys.indexes i
INNER JOIN sys.dm_db_partition_stats ps 
    ON i.object_id = ps.object_id 
    AND i.index_id = ps.index_id
WHERE i.name IN (
    'IX_FEEncabezado_EstadoFiscal_Envio',
    'IX_FEEncabezado_Enviado',
    'IX_FEToken_RNC_Ambiente'
)
ORDER BY Tabla, NombreIndice;

PRINT '';
PRINT '========================================';
PRINT 'ÍNDICES CREADOS EXITOSAMENTE';
PRINT '========================================';
PRINT '';
PRINT 'Próximos pasos:';
PRINT '1. Monitorear el uso de índices durante 24-48 horas';
PRINT '2. Verificar mejora en tiempo de respuesta';
PRINT '3. Programar mantenimiento semanal de índices';
PRINT '';
PRINT 'Query de monitoreo:';
PRINT 'SELECT * FROM sys.dm_db_index_usage_stats';
PRINT 'WHERE database_id = DB_ID() AND object_id = OBJECT_ID(''vFEEncabezado'')';
PRINT '';

-- =============================================
-- 6. CONFIGURACIÓN ADICIONAL RECOMENDADA
-- =============================================
PRINT '========================================';
PRINT 'CONFIGURACIÓN ADICIONAL RECOMENDADA';
PRINT '========================================';
PRINT '';
PRINT 'Ejecutar los siguientes comandos si es posible:';
PRINT '';
PRINT '-- Habilitar Read Committed Snapshot';
PRINT 'ALTER DATABASE [' + DB_NAME() + '] SET READ_COMMITTED_SNAPSHOT ON;';
PRINT '';
PRINT '-- Optimizar para queries ad-hoc';
PRINT 'EXEC sp_configure ''optimize for ad hoc workloads'', 1;';
PRINT 'RECONFIGURE;';
PRINT '';
PRINT '-- Configurar max server memory (ajustar según RAM)';
PRINT 'EXEC sp_configure ''max server memory'', 8192; -- 8GB';
PRINT 'RECONFIGURE;';
PRINT '';

GO

-- =============================================
-- SCRIPT DE MANTENIMIENTO SEMANAL
-- (Guardar como job de SQL Agent)
-- =============================================
/*
USE [bscodeca01];
GO

-- Rebuild índices fragmentados
ALTER INDEX IX_FEEncabezado_EstadoFiscal_Envio 
ON vFEEncabezado 
REBUILD WITH (FILLFACTOR = 90, ONLINE = ON);

ALTER INDEX IX_FEEncabezado_Enviado 
ON vFEEncabezado 
REBUILD WITH (FILLFACTOR = 95, ONLINE = ON);

ALTER INDEX IX_FEToken_RNC_Ambiente 
ON FEToken 
REBUILD WITH (FILLFACTOR = 90, ONLINE = ON);

-- Actualizar estadísticas
UPDATE STATISTICS vFEEncabezado WITH FULLSCAN;
UPDATE STATISTICS FEToken WITH FULLSCAN;
*/
