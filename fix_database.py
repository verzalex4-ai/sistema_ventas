# fix_database.py
import sqlite3
import os

def agregar_columna_activo():
    """Agrega la columna 'activo' a la tabla proveedores si no existe."""
    
    # Obtener la ruta de la base de datos
    if getattr(sys, "frozen", False):
        ruta_base = os.path.dirname(sys.executable)
    else:
        ruta_base = os.path.abspath(".")
    
    db_path = os.path.join(ruta_base, "data.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(proveedores)")
        columnas = [columna[1] for columna in cursor.fetchall()]
        
        if 'activo' not in columnas:
            print("❌ Columna 'activo' no existe. Agregando...")
            
            # Agregar la columna con valor por defecto 1 (activo)
            cursor.execute("ALTER TABLE proveedores ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
            conn.commit()
            
            print("✅ Columna 'activo' agregada exitosamente.")
        else:
            print("✅ La columna 'activo' ya existe.")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error al modificar la base de datos: {e}")
        return False

if __name__ == "__main__":
    import sys
    agregar_columna_activo()