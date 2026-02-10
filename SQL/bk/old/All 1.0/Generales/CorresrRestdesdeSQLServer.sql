EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;

EXEC sp_configure 'Ole Automation Procedures', 1;
RECONFIGURE;

EXEC sp_configure 'Ole Automation Procedures';

-- Primero, habilita OLE Automation en SQL Server (requiere permisos de administrador)
-- EXEC sp_configure 'show advanced options', 1;
-- RECONFIGURE;
-- EXEC sp_configure 'Ole Automation Procedures', 1;
-- RECONFIGURE;

-- Crear un procedimiento almacenado para llamar al servicio REST
CREATE or alter PROCEDURE dbo.EnviarDatosAlServicioREST
    @RNCEmisor VARCHAR(20),
    @eNCF VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ObjectToken INT
    DECLARE @ResponseText VARCHAR(8000)
    DECLARE @URL VARCHAR(255) = 'http://localhost:5000/procesar'
    DECLARE @JSON NVARCHAR(MAX)
    
    -- Crear el objeto para la solicitud HTTP
    EXEC sp_OACreate 'MSXML2.XMLHTTP', @ObjectToken OUT
    
    IF @ObjectToken IS NULL
    BEGIN
        RAISERROR('No se pudo crear el objeto HTTP', 16, 1)
        RETURN
    END
    
    -- Preparar JSON para el cuerpo de la solicitud
    SET @JSON = N'{"RNCEmisor": "' + @RNCEmisor + '", "eNCF": "' + @eNCF + '"}'
    
    BEGIN TRY
        -- Iniciar la conexión (POST)
        EXEC sp_OAMethod @ObjectToken, 'open', NULL, 'POST', @URL, 'false'
        
        -- Establecer encabezados
        EXEC sp_OAMethod @ObjectToken, 'setRequestHeader', NULL, 'Content-Type', 'application/json'
        
        -- Enviar la solicitud con los datos
        EXEC sp_OAMethod @ObjectToken, 'send', NULL, @JSON
        
        -- Obtener la respuesta
        EXEC sp_OAGetProperty @ObjectToken, 'responseText', @ResponseText OUTPUT
        
        -- Registrar la respuesta (opcional)
        INSERT INTO dbo.LogServicioREST (RNCEmisor, eNCF, FechaEnvio, Respuesta)
        VALUES (@RNCEmisor, @eNCF, GETDATE(), @ResponseText)
        
    END TRY
    BEGIN CATCH
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
        
        -- Registrar el error
        INSERT INTO dbo.LogServicioREST (RNCEmisor, eNCF, FechaEnvio, Respuesta)
        VALUES (@RNCEmisor, @eNCF, GETDATE(), 'ERROR: ' + @ErrorMessage)
        
        -- Propagar el error
        RAISERROR('Error al llamar al servicio REST: %s', 16, 1, @ErrorMessage)
    END CATCH
    
    -- Liberar el objeto
    EXEC sp_OADestroy @ObjectToken
END
GO

-- Crear tabla de log para registrar las respuestas (opcional pero recomendado)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'LogServicioREST')
BEGIN
    CREATE TABLE dbo.LogServicioREST (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        RNCEmisor VARCHAR(20),
        eNCF VARCHAR(50),
        FechaEnvio DATETIME,
        Respuesta VARCHAR(8000)
    )
END
GO


Select * from LogServicioREST

-- Crear el trigger que llamará al servicio REST después de insertar
CREATE OR ALTER TRIGGER trg_EnviarDatosServicioREST
ON dbo.TuTabla -- Reemplaza con el nombre de tu tabla
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Variables para almacenar los datos del registro insertado
    DECLARE @RNCEmisor VARCHAR(20)
    DECLARE @eNCF VARCHAR(50)
    
    -- Obtener los datos del registro insertado
    SELECT @RNCEmisor = RNCEmisor, @eNCF = eNCF
    FROM INSERTED
    
    -- Llamar al procedimiento que envía los datos al servicio REST
    EXEC dbo.EnviarDatosAlServicioREST @RNCEmisor, @eNCF
END
GO