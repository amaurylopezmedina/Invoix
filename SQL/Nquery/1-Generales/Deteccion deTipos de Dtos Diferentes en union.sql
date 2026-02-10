-- === Configura aquí tus vistas en el mismo orden del UNION ===
DECLARE@src TABLE (src INT IDENTITY (1, 1), view_name SYSNAME);

INSERT INTO
@src (view_name)
VALUES
    ('dbo.vFEVentaRD'),
    ('dbo.vFEVentaUS'),
    ('dbo.vFEDevCORD'),
    ('dbo.vFEDevCRRD'),
    ('dbo.vFEGASMENCC'),
    ('dbo.vFEGASMENCXP'),
    ('dbo.vFEEncPI');

-- === Catálogo de tipos numéricos vs texto ===
;

WITH
    types AS (
        SELECT
            t.user_type_id,
            t.name AS type_name,
            CASE
                WHEN t.name IN (
                    'tinyint',
                    'smallint',
                    'int',
                    'bigint',
                    'decimal',
                    'numeric',
                    'money',
                    'smallmoney',
                    'float',
                    'real'
                ) THEN 1
                ELSE 0
            END AS is_numeric,
            CASE
                WHEN t.name IN (
                    'char',
                    'nchar',
                    'varchar',
                    'nvarchar',
                    'text',
                    'ntext'
                ) THEN 1
                ELSE 0
            END AS is_text
        FROM
            sys.types t
    ),
    cols AS (
        SELECT
            s.src,
            s.view_name,
            c.column_id,
            c.name AS col_name,
            ty.type_name,
            ty.is_numeric,
            ty.is_text
        FROM
@src s
            JOIN sys.objects o ON o.object_id = OBJECT_ID (s.view_name)
            AND o.type IN ('V', 'U') -- vista o tabla
            JOIN sys.columns c ON c.object_id = o.object_id
            JOIN sys.types t ON t.user_type_id = c.user_type_id
            JOIN types ty ON ty.user_type_id = t.user_type_id
    ),
    base AS ( -- toma la 1ra vista como "molde" del UNION
        SELECT
            column_id,
            col_name,
            type_name,
            is_numeric,
            is_text
        FROM
            cols
        WHERE
            src = 1
    )
SELECT
    b.column_id AS pos,
    b.col_name AS col_en_union, -- nombre que hereda el UNION
    'src1:' + (
        SELECT
            view_name
        FROM
@src
        WHERE
            src = 1
    ) AS vista_base,
    b.type_name AS tipo_base,
    'src' + CAST(c.src AS varchar(10)) + ':' + c.view_name AS vista_comparada,
    c.type_name AS tipo_comparada,
    CASE
        WHEN b.is_numeric <> c.is_numeric
        OR b.type_name <> c.type_name THEN '⚠️ POSIBLE CONFLICTO'
        ELSE ''
    END AS observacion
FROM
    base b
    JOIN cols c ON c.column_id = b.column_id
ORDER BY
    b.column_id,
    c.src;
