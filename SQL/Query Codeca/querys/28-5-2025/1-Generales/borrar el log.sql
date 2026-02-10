BACKUP DATABASE bsglp01
TO DISK = 'C:\test\bsglp01s.bak'
GO



Backup log bsglp01
to disk  ='C:\test\BackupLog.bak'



sp_helpdb bsglp01


ALTER DATABASE lucasFEQAS
SET RECOVERY SIMPLE;
GO
--Reducimos el log de transacciones a  1 MB.
DBCC SHRINKFILE(lucasFEQAS_log, 1);
GO
-- Cambiamos nuevamente el modelo de recuperación a Completo.
ALTER DATABASE lucasFEQAS
SET RECOVERY FULL;
GO