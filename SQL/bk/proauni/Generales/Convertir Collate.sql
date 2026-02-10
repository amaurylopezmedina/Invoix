
/*
Lista de tablas a verificar

empresa
cliente
producto
suplidor
transa01
tradetalle
cxcmovi11
cxcmovi2
cxcdetalle1
cxcdetalle2
cxpmovi1
cxpdetalle
cajachica

ambiente
fetoken
sis_globalsec


*/






USE master;
GO
-- Paso 1: Poner la base de datos en modo de usuario único
ALTER DATABASE proauni SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO
-- Paso 2: Cambiar el cotejamiento
ALTER DATABASE proauni COLLATE SQL_Latin1_General_CP1_CI_AS;
GO
-- Paso 3: Volver al modo multiusuario
ALTER DATABASE proauni SET MULTI_USER;
GO



-- tabla Por tabla

DECLARE @TableName NVARCHAR(128) = 'sis_TipoNCF'
DECLARE @TargetCollation NVARCHAR(128) = 'SQL_Latin1_General_CP1_CI_AS'

-- Primero identificamos todos los índices que dependen de columnas de texto
DECLARE @DropIndexSQL NVARCHAR(MAX) = ''
DECLARE @CreateIndexSQL NVARCHAR(MAX) = ''

-- Obtener los índices a eliminar y sus definiciones para recrearlos después
SELECT @DropIndexSQL = @DropIndexSQL + 'DROP INDEX ' + i.name + ' ON ' + @TableName + ';' + CHAR(13) + CHAR(10),
       @CreateIndexSQL = @CreateIndexSQL + 'CREATE ' + 
                        CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
                        'INDEX ' + i.name + ' ON ' + @TableName + ' (' +
                        (SELECT STRING_AGG(c.name, ', ') FROM sys.index_columns ic
                         JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                         WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id) +
                        ');' + CHAR(13) + CHAR(10)
FROM sys.indexes i
WHERE i.object_id = OBJECT_ID(@TableName)
AND i.type > 0 -- Excluir el montón (heap)
AND i.is_primary_key = 0 -- Excluir la clave primaria, que requiere manejo especial
AND EXISTS (
    SELECT 1 FROM sys.index_columns ic
    JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    JOIN INFORMATION_SCHEMA.COLUMNS isc ON isc.TABLE_NAME = @TableName AND isc.COLUMN_NAME = c.name
    WHERE ic.object_id = i.object_id 
    AND ic.index_id = i.index_id
    AND isc.DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar', 'text', 'ntext')
);

-- Generar el script para alterar las columnas
DECLARE @AlterSQL NVARCHAR(MAX) = ''
SELECT @AlterSQL = @AlterSQL + 
    'ALTER TABLE ' + @TableName + ' ALTER COLUMN [' + COLUMN_NAME + '] ' + 
    DATA_TYPE + 
    CASE 
        WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN '(MAX)' 
        WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL THEN '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR(10)) + ')' 
        ELSE '' 
    END + 
    ' COLLATE ' + @TargetCollation + ';' + CHAR(13) + CHAR(10)
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = @TableName
AND DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar', 'text', 'ntext')

-- Crear un script completo que:
-- 1. Elimina los índices
-- 2. Altera las columnas
-- 3. Recrea los índices
DECLARE @CompleteSQL NVARCHAR(MAX) = @DropIndexSQL + @AlterSQL + @CreateIndexSQL

-- Imprimir el script para revisar
PRINT @CompleteSQL

-- Ejecutar el script (descomenta la siguiente línea después de revisar el script)
EXEC sp_executesql @CompleteSQL


--DECLARE @TableName NVARCHAR(128) = 'impuesto'
-- Verificar las columnas después del cambio
 SELECT COLUMN_NAME, DATA_TYPE, COLLATION_NAME
 FROM INFORMATION_SCHEMA.COLUMNS
 WHERE TABLE_NAME = @TableName AND DATA_TYPE LIKE '%char%'



 --Todas las tablas de la BD

 -- Script para cambiar la colación de múltiples tablas
-- Crea una tabla temporal para almacenar las tablas a procesar
DECLARE @TablasAProcesar TABLE (ID INT IDENTITY(1,1), TableName NVARCHAR(128))

-- Inserta las tablas que deseas procesar
INSERT INTO @TablasAProcesar (TableName)
VALUES 
('empresa'),
('cliente'),
('producto'),
('suplidor'),
('transa01'),
('tradetalle'),
('cxcmovi1'),
('cxcmovi2'),
('cxcdetalle1'),
('cxcdetalle2'),
('cxpmovi1'),
('cxpdetalle'),
('cajachica'),
('ambiente'),
('fetoken'),
('sis_globalsec'),
('sis_TipoNCF'),
('impuesto')


-- Configura la colación objetivo
DECLARE @TargetCollation NVARCHAR(128) = 'SQL_Latin1_General_CP1_CI_AS'

-- Variables para el ciclo
DECLARE @CurrentTable NVARCHAR(128)
DECLARE @CurrentID INT = 1
DECLARE @MaxID INT = (SELECT MAX(ID) FROM @TablasAProcesar)
DECLARE @CompleteSQL NVARCHAR(MAX)
DECLARE @LogMessage NVARCHAR(1000)

-- Crear una tabla para registrar el progreso y posibles errores
IF OBJECT_ID('tempdb..#ColacionLog') IS NOT NULL
    DROP TABLE #ColacionLog;
    
CREATE TABLE #ColacionLog (
    ID INT IDENTITY(1,1),
    TableName NVARCHAR(128),
    ExecutionTime DATETIME DEFAULT GETDATE(),
    Status NVARCHAR(10),
    ErrorMessage NVARCHAR(MAX)
)

-- Iniciar el ciclo
WHILE @CurrentID <= @MaxID
BEGIN
    -- Obtener la tabla actual
    SELECT @CurrentTable = TableName FROM @TablasAProcesar WHERE ID = @CurrentID
    
    -- Registrar inicio del procesamiento
    SET @LogMessage = 'Iniciando procesamiento de la tabla: ' + @CurrentTable
    PRINT @LogMessage
    
    BEGIN TRY
        -- Inicializar variables para este ciclo
        DECLARE @DropIndexSQL NVARCHAR(MAX) = ''
        DECLARE @CreateIndexSQL NVARCHAR(MAX) = ''
        DECLARE @AlterSQL NVARCHAR(MAX) = ''
        
        -- Obtener los índices a eliminar y sus definiciones para recrearlos después
        SELECT @DropIndexSQL = @DropIndexSQL + 'DROP INDEX ' + i.name + ' ON ' + @CurrentTable + ';' + CHAR(13) + CHAR(10),
               @CreateIndexSQL = @CreateIndexSQL + 'CREATE ' + 
                            CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
                            'INDEX ' + i.name + ' ON ' + @CurrentTable + ' (' +
                            (SELECT STRING_AGG(c.name, ', ') FROM sys.index_columns ic
                             JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                             WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id) +
                            ');' + CHAR(13) + CHAR(10)
        FROM sys.indexes i
        WHERE i.object_id = OBJECT_ID(@CurrentTable)
        AND i.type > 0 -- Excluir el montón (heap)
        AND i.is_primary_key = 0 -- Excluir la clave primaria
        AND EXISTS (
            SELECT 1 FROM sys.index_columns ic
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            JOIN INFORMATION_SCHEMA.COLUMNS isc ON isc.TABLE_NAME = @CurrentTable AND isc.COLUMN_NAME = c.name
            WHERE ic.object_id = i.object_id 
            AND ic.index_id = i.index_id
            AND isc.DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar', 'text', 'ntext')
        );
        
        -- Manejo de restricciones de clave foránea
        DECLARE @DropFKSQL NVARCHAR(MAX) = ''
        DECLARE @CreateFKSQL NVARCHAR(MAX) = ''
        
        SELECT @DropFKSQL = @DropFKSQL + 'ALTER TABLE ' + OBJECT_NAME(fk.parent_object_id) + 
                          ' DROP CONSTRAINT ' + fk.name + ';' + CHAR(13) + CHAR(10),
               @CreateFKSQL = @CreateFKSQL + 'ALTER TABLE ' + OBJECT_NAME(fk.parent_object_id) + 
                           ' ADD CONSTRAINT ' + fk.name + ' FOREIGN KEY (' + 
                           COL_NAME(fkc.parent_object_id, fkc.parent_column_id) + ') REFERENCES ' +
                           OBJECT_NAME(fk.referenced_object_id) + '(' + 
                           COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) + ');' + CHAR(13) + CHAR(10)
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        JOIN INFORMATION_SCHEMA.COLUMNS isc ON 
            (isc.TABLE_NAME = OBJECT_NAME(fkc.parent_object_id) AND 
             isc.COLUMN_NAME = COL_NAME(fkc.parent_object_id, fkc.parent_column_id)) OR
            (isc.TABLE_NAME = OBJECT_NAME(fkc.referenced_object_id) AND 
             isc.COLUMN_NAME = COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id))
        WHERE (OBJECT_NAME(fkc.parent_object_id) = @CurrentTable OR 
               OBJECT_NAME(fkc.referenced_object_id) = @CurrentTable) AND
              isc.DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar', 'text', 'ntext');
        
        -- Generar el script para alterar las columnas
        SELECT @AlterSQL = @AlterSQL + 
            'ALTER TABLE ' + @CurrentTable + ' ALTER COLUMN [' + COLUMN_NAME + '] ' + 
            DATA_TYPE + 
            CASE 
                WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN '(MAX)' 
                WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL THEN '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR(10)) + ')' 
                ELSE '' 
            END + 
            ' COLLATE ' + @TargetCollation + ';' + CHAR(13) + CHAR(10)
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = @CurrentTable
        AND DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar', 'text', 'ntext');
        
        -- Crear un script completo
        SET @CompleteSQL = 
            -- Primero eliminar las FKs
            CASE WHEN LEN(@DropFKSQL) > 0 THEN '-- Eliminar claves foráneas' + CHAR(13) + CHAR(10) + @DropFKSQL ELSE '' END +
            -- Luego eliminar índices
            CASE WHEN LEN(@DropIndexSQL) > 0 THEN '-- Eliminar índices' + CHAR(13) + CHAR(10) + @DropIndexSQL ELSE '' END +
            -- Alterar columnas
            CASE WHEN LEN(@AlterSQL) > 0 THEN '-- Cambiar colación de columnas' + CHAR(13) + CHAR(10) + @AlterSQL ELSE '' END +
            -- Recrear índices
            CASE WHEN LEN(@CreateIndexSQL) > 0 THEN '-- Recrear índices' + CHAR(13) + CHAR(10) + @CreateIndexSQL ELSE '' END +
            -- Recrear FKs
            CASE WHEN LEN(@CreateFKSQL) > 0 THEN '-- Recrear claves foráneas' + CHAR(13) + CHAR(10) + @CreateFKSQL ELSE '' END;
        
        -- Verificar si hay algo que cambiar
        IF LEN(@AlterSQL) > 0
        BEGIN
            -- Imprimir detalles para registro
            PRINT '-- Procesando tabla: ' + @CurrentTable
            PRINT @CompleteSQL
            
            -- Ejecutar el script
            EXEC sp_executesql @CompleteSQL
            
            -- Registrar éxito
            INSERT INTO #ColacionLog (TableName, Status)
            VALUES (@CurrentTable, 'SUCCESS')
            
            SET @LogMessage = 'Tabla ' + @CurrentTable + ' procesada correctamente.'
            PRINT @LogMessage
        END
        ELSE
        BEGIN
            -- No hay columnas para cambiar
            SET @LogMessage = 'Tabla ' + @CurrentTable + ' no tiene columnas que requieran cambio de colación.'
            PRINT @LogMessage
            
            INSERT INTO #ColacionLog (TableName, Status)
            VALUES (@CurrentTable, 'SKIPPED')
        END
    END TRY
    BEGIN CATCH
        -- Manejar errores
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY()
        DECLARE @ErrorState INT = ERROR_STATE()
        
        SET @LogMessage = 'Error procesando tabla ' + @CurrentTable + ': ' + @ErrorMessage
        PRINT @LogMessage
        
        INSERT INTO #ColacionLog (TableName, Status, ErrorMessage)
        VALUES (@CurrentTable, 'ERROR', @ErrorMessage)
        
        -- Continuar con la siguiente tabla a pesar del error
    END CATCH
    
    -- Incrementar contador para la siguiente tabla
    SET @CurrentID = @CurrentID + 1
END

-- Mostrar resumen final
SELECT TableName, Status, ErrorMessage, ExecutionTime
FROM #ColacionLog
ORDER BY ID;

-- Limpiar
DROP TABLE #ColacionLog;