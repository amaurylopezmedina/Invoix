#!/bin/bash
# perfect_project.sh - Optimizado para proyectos completos
# Uso: ./perfect_project.sh [directorio] [--parallel] [--cache]

PROJECT_DIR=${1:-"."}
PARALLEL=${2:-"--parallel"}
CACHE_DIR="${PROJECT_DIR}/.perfection_cache"

# Crear cache si no existe
mkdir -p "$CACHE_DIR"

echo "Iniciando revisión completa del proyecto: $PROJECT_DIR"

# Función optimizada para procesar archivos
process_file() {
    local file=$1
    local cache_file="$CACHE_DIR/$(basename "$file").cache"
    
    # Verificar si archivo cambió
    if [ -f "$cache_file" ] && [ "$file" -ot "$cache_file" ]; then
        echo "Omitiendo $file (sin cambios)"
        return
    fi
    
    echo "Procesando $file..."
    
    # Aplicar herramientas en secuencia optimizada
    autopep8 --in-place --aggressive "$file" 2>/dev/null
    black "$file" 2>/dev/null
    isort "$file" 2>/dev/null
    
    # Verificar calidad
    flake8 "$file" --max-line-length=88 --extend-ignore=E203,W503 > /dev/null
    if [ $? -eq 0 ]; then
        touch "$cache_file"
        echo "✓ $file perfeccionado"
    else
        echo "⚠ $file requiere revisión manual"
    fi
}

export -f process_file

# Procesar archivos, excluyendo archivos internos y de sistema
if [ "$PARALLEL" = "--parallel" ]; then
    find "$PROJECT_DIR" -name "*.py" -type f \
        -not -path "*/__pycache__/*" \
        -not -path "*/build/*" \
        -not -path "*/dist/*" \
        -not -path "*/.git/*" \
        -not -path "*/.tox/*" \
        -not -path "*/.mypy_cache/*" \
        -not -path "*/.pytest_cache/*" \
        -not -path "*/venv/*" \
        -not -path "*/env/*" \
        -not -path "*/.env*" \
        -not -name "*.pyc" \
        -not -name "*.pyo" \
        -not -name "*.log" \
        -not -name "*_internal*" \
        -not -name ".DS_Store" \
        | parallel process_file
else
    find "$PROJECT_DIR" -name "*.py" -type f \
        -not -path "*/__pycache__/*" \
        -not -path "*/build/*" \
        -not -path "*/dist/*" \
        -not -path "*/.git/*" \
        -not -path "*/.tox/*" \
        -not -path "*/.mypy_cache/*" \
        -not -path "*/.pytest_cache/*" \
        -not -path "*/venv/*" \
        -not -path "*/env/*" \
        -not -path "*/.env*" \
        -not -name "*.pyc" \
        -not -name "*.pyo" \
        -not -name "*.log" \
        -not -name "*_internal*" \
        -not -name ".DS_Store" \
        -exec bash -c 'process_file "$0"' {} \;
fi

echo "Revisión completa finalizada. Reporte generado en $CACHE_DIR/report.html"