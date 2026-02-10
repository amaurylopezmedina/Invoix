import win32print
import platform

def listar_impresoras():
    """
    Función que lista todas las impresoras locales y remotas
    disponibles en el sistema.
    """
    print(f"Sistema operativo detectado: {platform.system()}")
    
    try:
        impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | 
                                             win32print.PRINTER_ENUM_CONNECTIONS)
        
        print("\nLista de todas las impresoras:")
        print("-" * 50)
        
        impresoras_locales = []
        impresoras_remotas = []
        
        for i, impresora in enumerate(impresoras, 1):
            nombre = impresora[2]
            # El índice 2 contiene el nombre de la impresora
            
            # Determinamos si la impresora es local o remota
            if '\\\\' in nombre:  # Las impresoras remotas suelen tener formato \\servidor\impresora
                impresoras_remotas.append(nombre)
            else:
                impresoras_locales.append(nombre)
        
        # Mostrar impresoras locales
        print("Impresoras Locales:")
        if impresoras_locales:
            for i, impresora in enumerate(impresoras_locales, 1):
                print(f"  {i}. {impresora}")
        else:
            print("  No se encontraron impresoras locales.")
        
        # Mostrar impresoras remotas
        print("\nImpresoras Remotas:")
        if impresoras_remotas:
            for i, impresora in enumerate(impresoras_remotas, 1):
                print(f"  {i}. {impresora}")
        else:
            print("  No se encontraron impresoras remotas.")
            
        print(f"\nTotal: {len(impresoras)} impresora(s) encontrada(s)")
        
    except Exception as e:
        print(f"Error al enumerar las impresoras: {e}")
        
        # Si estamos en un sistema que no es Windows, sugerimos alternativas
        if platform.system() != "Windows":
            print("\nEste script usa la biblioteca win32print, que solo funciona en Windows.")
            print("Para sistemas Linux, prueba con:")
            print("  import os")
            print("  os.system('lpstat -a') # Lista impresoras CUPS")
            print("\nPara sistemas macOS, prueba con:")
            print("  import os")
            print("  os.system('lpstat -p') # Lista impresoras")

if __name__ == "__main__":
    listar_impresoras()