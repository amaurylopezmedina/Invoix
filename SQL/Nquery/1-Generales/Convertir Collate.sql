/*==============================================================================
🏢 ASESYS, SRL
Autor: Amaury López
Propósito: Cambiar la colación de toda la base de datos "josecamacho"
Fecha: 2025-10-23
Compatibilidad: SQL Server 2017+
Notas:
 - Cambia la colación de la base y de todas las columnas tipo texto (char/varchar/nchar/nvarchar/text/ntext)
 - Elimina temporalmente claves foráneas e índices y luego los recrea
 - Genera log detallado del proceso
==============================================================================*/

USE master;
GO

-- ================================================================
-- 1️⃣  Cambiar colación de la base de datos
-- ================================================================
PRINT 'Cambiando colación de la base de datos...';
ALTER DATABASE josecamacho SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO

ALTER DATABASE josecamacho COLLATE SQL_Latin1_General_CP1_CI_AS;
GO

ALTER DATABASE josecamacho SET MULTI_USER;
GO

PRINT '✅ Colación de la base de datos cambiada correctamente.';
GO


-- ================================================================
-- 2️⃣  Cambiar colación de TODAS las tablas seleccionadas
-- ================================================================
USE josecamacho;
GO

DECLARE @TablasAProcesar TABLE (ID INT IDENTITY(1,1), TableName NVARCHAR(128));

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
('impuesto');

DECLARE @TargetCollation NVARCHAR(128) = 'SQL_Latin1_General_CP1_CI_AS';
DECLARE @CurrentTable NVARCHAR(128);
DECLARE @CurrentID INT = 1;
DECLARE @MaxID INT = (SELECT MAX(ID) FROM @TablasAProcesar);
DECLARE @CompleteSQL NVARCHAR(MAX);
DECLARE @LogMessage NVARCHAR(1000);

IF OBJECT_ID('tempdb..#ColacionLog') IS NOT NULL
    DROP TABLE #ColacionLog;

CREATE TABLE #ColacionLog (
    ID INT IDENTITY(1,1),
    TableName NVARCHAR(128),
    ExecutionTime DATETIME DEFAULT GETDATE(),
    Status NVARCHAR(10),
    ErrorMessage NVARCHAR(MAX)
);

WHILE @CurrentID <= @MaxID
BEGIN
    SELECT @CurrentTable = TableName FROM @TablasAProcesar WHERE ID = @CurrentID;
    SET @LogMessage = '🔹 Procesando tabla: ' + @CurrentTable;
    PRINT @LogMessage;

    BEGIN TRY
        DECLARE @DropIndexSQL NVARCHAR(MAX) = N'';
        DECLARE @CreateIndexSQL NVARCHAR(MAX) = N'';
        DECLARE @DropFKSQL NVARCHAR(MAX) = N'';
        DECLARE @CreateFKSQL NVARCHAR(MAX) = N'';
        DECLARE @AlterSQL NVARCHAR(MAX) = N'';

        -- ======================================================
        -- 1️⃣ Manejo de claves foráneas
        -- ======================================================
        IF OBJECT_ID('tempdb..#FKTemp') IS NOT NULL DROP TABLE #FKTemp;

        SELECT 
            fk.name AS FKName,
            OBJECT_NAME(fk.parent_object_id) AS ParentTable,
            OBJECT_NAME(fk.referenced_object_id) AS RefTable,
            COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS ParentCol,
            COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS RefCol
        INTO #FKTemp
        FROM sys.foreign_keys fk
        JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        WHERE OBJECT_NAME(fk.parent_object_id) = @CurrentTable;

        SELECT 
            @DropFKSQL = STRING_AGG('ALTER TABLE ' + QUOTENAME(ParentTable) + ' DROP CONSTRAINT ' + QUOTENAME(FKName) + ';', CHAR(13) + CHAR(10))
        FROM #FKTemp;

        SELECT 
            @CreateFKSQL = STRING_AGG(
                'ALTER TABLE ' + QUOTENAME(ParentTable) + 
                ' ADD CONSTRAINT ' + QUOTENAME(FKName) + 
                ' FOREIGN KEY (' + QUOTENAME(ParentCol) + ') REFERENCES ' +
                QUOTENAME(RefTable) + '(' + QUOTENAME(RefCol) + ');',
                CHAR(13) + CHAR(10))
        FROM #FKTemp;

        DROP TABLE #FKTemp;

        -- ======================================================
        -- 2️⃣ Manejo de índices
        -- ======================================================
        IF OBJECT_ID('tempdb..#IndexColumns') IS NOT NULL DROP TABLE #IndexColumns;

        SELECT 
            i.name AS IndexName,
            OBJECT_NAME(i.object_id) AS TableName,
            STRING_AGG(QUOTENAME(c.name), ', ') AS ColumnList,
            i.is_unique
        INTO #IndexColumns
        FROM sys.indexes i
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE OBJECT_NAME(i.object_id) = @CurrentTable
          AND i.type > 0
          AND i.is_primary_key = 0
        GROUP BY i.name, i.object_id, i.is_unique;

        SELECT 
            @DropIndexSQL = STRING_AGG('DROP INDEX ' + QUOTENAME(IndexName) + ' ON ' + QUOTENAME(@CurrentTable) + ';', CHAR(13) + CHAR(10))
        FROM #IndexColumns;

        SELECT 
            @CreateIndexSQL = STRING_AGG(
                'CREATE ' + CASE WHEN is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
                'INDEX ' + QUOTENAME(IndexName) + ' ON ' + QUOTENAME(@CurrentTable) + 
                ' (' + ColumnList + ');', CHAR(13) + CHAR(10))
        FROM #IndexColumns;

        DROP TABLE #IndexColumns;

        -- ======================================================
        -- 3️⃣ Alterar colaciones de columnas
        -- ======================================================
        SELECT 
            @AlterSQL = STRING_AGG(
                'ALTER TABLE ' + QUOTENAME(@CurrentTable) + ' ALTER COLUMN ' + QUOTENAME(COLUMN_NAME) + ' ' +
                DATA_TYPE +
                CASE 
                    WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN '(MAX)' 
                    WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL THEN '(' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR(10)) + ')' 
                    ELSE '' 
                END +
                ' COLLATE ' + @TargetCollation + ';',
                CHAR(13) + CHAR(10))
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = @CurrentTable
          AND DATA_TYPE IN ('char', 'varchar', 'nchar', 'nvarchar', 'text', 'ntext');

        -- ======================================================
        -- 4️⃣ Combinar scripts y ejecutar
        -- ======================================================
        SET @CompleteSQL = ISNULL(@DropFKSQL, '') + ISNULL(@DropIndexSQL, '') + ISNULL(@AlterSQL, '') + ISNULL(@CreateIndexSQL, '') + ISNULL(@CreateFKSQL, '');

        IF @AlterSQL IS NOT NULL AND LEN(@AlterSQL) > 0
        BEGIN
            PRINT '--- Ejecutando cambios en ' + @CurrentTable + ' ---';
            EXEC sp_executesql @CompleteSQL;
            INSERT INTO #ColacionLog (TableName, Status) VALUES (@CurrentTable, 'SUCCESS');
            PRINT '✅ Tabla ' + @CurrentTable + ' procesada correctamente.';
        END
        ELSE
        BEGIN
            INSERT INTO #ColacionLog (TableName, Status) VALUES (@CurrentTable, 'SKIPPED');
            PRINT '⚪ Tabla ' + @CurrentTable + ' no requiere cambios.';
        END
    END TRY
    BEGIN CATCH
        INSERT INTO #ColacionLog (TableName, Status, ErrorMessage)
        VALUES (@CurrentTable, 'ERROR', ERROR_MESSAGE());
        PRINT '❌ Error en tabla ' + @CurrentTable + ': ' + ERROR_MESSAGE();
    END CATCH;

    SET @CurrentID += 1;
END;

-- ======================================================
-- 5️⃣ Resumen final
-- ======================================================
PRINT '--- RESULTADO FINAL ---';
SELECT TableName, Status, ErrorMessage, ExecutionTime
FROM #ColacionLog
ORDER BY ID;

DROP TABLE #ColacionLog;
GO
