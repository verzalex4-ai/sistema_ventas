# database.py - FASE 1: CORRECCIONES CRÍTICAS
import sqlite3
import hashlib
import os
import sys
from datetime import datetime
import shutil
import binascii


def obtener_ruta_db():
    if getattr(sys, "frozen", False):
        ruta_base = os.path.dirname(sys.executable)
    else:
        ruta_base = os.path.abspath(".")
    return os.path.join(ruta_base, "data.db")


DB_PATH = obtener_ruta_db()


# --- DECORADOR PARA MANEJAR LA CONEXIÓN ---
def db_connection(func):
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            result = func(cursor, *args, **kwargs)
            conn.commit()
            return result
        except sqlite3.Error as e:
            print(f"Error de base de datos en '{func.__name__}': {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()
    return wrapper


# ============================================================================
# CONFIGURACIÓN INICIAL DE LA BASE DE DATOS
# ============================================================================
def setup_database():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # --- TABLA USUARIOS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nombre_usuario TEXT UNIQUE NOT NULL, 
                contrasena_hash TEXT NOT NULL, 
                contrasena_salt TEXT NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('admin', 'usuario', 'auditor')),
                debe_cambiar_contrasena INTEGER NOT NULL DEFAULT 1
            );
        """)

        # --- TABLA CATEGORÍAS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            );
        """)

        # --- TABLA PROVEEDORES ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nombre TEXT UNIQUE NOT NULL, 
                contacto TEXT, 
                telefono TEXT, 
                email TEXT, 
                direccion TEXT, 
                activo INTEGER NOT NULL DEFAULT 1 
            );
        """)

        # --- TABLA PRODUCTOS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                costo REAL NOT NULL CHECK(costo >= 0),
                precio REAL NOT NULL CHECK(precio >= 0),
                stock INTEGER NOT NULL CHECK(stock >= 0),
                activo INTEGER NOT NULL DEFAULT 1,
                proveedor_id INTEGER,
                categoria_id INTEGER, 
                FOREIGN KEY (proveedor_id) REFERENCES proveedores (id) ON DELETE SET NULL,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE SET NULL
            );
        """)

        # --- TABLA DEUDORES ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deudores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nombre TEXT UNIQUE NOT NULL, 
                telefono TEXT, 
                direccion TEXT, 
                notas TEXT, 
                saldo REAL NOT NULL DEFAULT 0.0 CHECK(saldo >= 0)
            );
        """)

        # --- TABLA VENTAS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                fecha_hora TEXT NOT NULL,
                total REAL NOT NULL CHECK(total >= 0),
                tipo_pago TEXT NOT NULL CHECK(tipo_pago IN ('Contado', 'Credito')),
                deudor_id INTEGER,
                saldo_pendiente REAL NOT NULL DEFAULT 0.0 CHECK(saldo_pendiente >= 0),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (deudor_id) REFERENCES deudores (id)
            );
        """)

        # --- TABLA DETALLES VENTA ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalles_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                venta_id INTEGER NOT NULL, 
                producto_id INTEGER NOT NULL, 
                cantidad INTEGER NOT NULL CHECK(cantidad > 0), 
                precio_unitario REAL NOT NULL CHECK(precio_unitario >= 0), 
                FOREIGN KEY (venta_id) REFERENCES ventas (id) ON DELETE CASCADE, 
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            );
        """)

        # --- TABLA COMPRAS ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                proveedor_id INTEGER NOT NULL, 
                fecha TEXT NOT NULL, 
                total_costo REAL NOT NULL CHECK(total_costo >= 0), 
                FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
            );
        """)

        # --- TABLA DETALLES COMPRA ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalles_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                compra_id INTEGER NOT NULL, 
                producto_id INTEGER NOT NULL, 
                cantidad INTEGER NOT NULL CHECK(cantidad > 0), 
                costo_unitario REAL NOT NULL CHECK(costo_unitario >= 0), 
                FOREIGN KEY (compra_id) REFERENCES compras (id) ON DELETE CASCADE, 
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            );
        """)

        # --- TABLA PAGOS DEUDORES ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagos_deudores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deudor_id INTEGER NOT NULL,
                venta_id INTEGER,
                fecha TEXT NOT NULL,
                monto REAL NOT NULL CHECK(monto > 0),
                FOREIGN KEY (deudor_id) REFERENCES deudores (id),
                FOREIGN KEY (venta_id) REFERENCES ventas (id) ON DELETE SET NULL
            );
        """)

        # --- TABLA AUDITORÍA (CORREGIDA) ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registro_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                fecha_hora TEXT NOT NULL,
                accion TEXT NOT NULL,
                descripcion TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
            );
        """)

                # --- TABLA CIERRES DE CAJA ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cierres_caja (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                fecha_hora TEXT NOT NULL,
                total_ventas_sistema REAL NOT NULL CHECK(total_ventas_sistema >= 0),
                total_efectivo_sistema REAL NOT NULL CHECK(total_efectivo_sistema >= 0),
                efectivo_contado REAL NOT NULL CHECK(efectivo_contado >= 0),
                diferencia REAL NOT NULL,
                observaciones TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            );
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cierres_usuario ON cierres_caja(usuario_id);")

        # --- CREAR ÍNDICES PARA OPTIMIZAR BÚSQUEDAS ---
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_hora);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON registro_auditoria(fecha_hora);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON registro_auditoria(usuario_id);")

        # --- MIGRAR TABLA AUDITORÍA SI YA EXISTE SIN ROL ---
        try:
            cursor.execute("SELECT rol FROM registro_auditoria LIMIT 1")
        except sqlite3.OperationalError:
            # La columna 'rol' no existe, necesitamos migrar (silencioso)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registro_auditoria_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    fecha_hora TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    descripcion TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
                );
            """)
            cursor.execute("""
                INSERT INTO registro_auditoria_new (id, usuario_id, fecha_hora, accion, descripcion)
                SELECT id, usuario_id, fecha_hora, accion, descripcion FROM registro_auditoria;
            """)
            cursor.execute("DROP TABLE registro_auditoria;")
            cursor.execute("ALTER TABLE registro_auditoria_new RENAME TO registro_auditoria;")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON registro_auditoria(fecha_hora);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON registro_auditoria(usuario_id);")

        # --- MIGRAR COLUMNA debe_cambiar_contrasena SI NO EXISTE ---
        cursor.execute("PRAGMA table_info(usuarios)")
        columnas = [col[1] for col in cursor.fetchall()]
        if 'debe_cambiar_contrasena' not in columnas:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN debe_cambiar_contrasena INTEGER NOT NULL DEFAULT 0")
            # Marcar solo usuarios con contraseñas débiles
            cursor.execute("""
                UPDATE usuarios 
                SET debe_cambiar_contrasena = 1 
                WHERE nombre_usuario IN ('admin', 'cajero')
            """)

        # --- CREAR USUARIOS POR DEFECTO (SI NO EXISTEN) ---
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            usuarios_defecto = [
                ("admin", "Admin2024!", "admin"),
                ("cajero", "Cajero2024!", "usuario"),
            ]
            for user, pwd, role in usuarios_defecto:
                salt = os.urandom(16)
                pwd_hash = hashlib.pbkdf2_hmac('sha256', pwd.encode('utf-8'), salt, 100000)
                cursor.execute(
                    "INSERT INTO usuarios (nombre_usuario, contrasena_hash, contrasena_salt, rol, debe_cambiar_contrasena) VALUES (?, ?, ?, ?, 1)",
                    (user, binascii.hexlify(pwd_hash).decode('utf-8'), binascii.hexlify(salt).decode('utf-8'), role)
                )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Error en la configuración de la base de datos: {e}")
    finally:
        if conn:
            conn.close()


# ============================================================================
# FUNCIONES DE AUDITORÍA (CENTRALIZADAS)
# ============================================================================
def registrar_auditoria(cursor, usuario_id, accion, descripcion=""):
    """Registra una acción en la tabla de auditoría."""
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO registro_auditoria (usuario_id, fecha_hora, accion, descripcion) VALUES (?, ?, ?, ?)",
        (usuario_id, fecha_hora, accion, descripcion)
    )


@db_connection
def obtener_registro_auditoria(cursor, limite=500):
    """Recupera los registros de auditoría con el rol del usuario."""
    query = """
        SELECT 
            ra.fecha_hora, 
            u.nombre_usuario,
            u.rol,
            ra.accion, 
            ra.descripcion
        FROM registro_auditoria ra
        JOIN usuarios u ON ra.usuario_id = u.id
        ORDER BY ra.fecha_hora DESC
        LIMIT ?
    """
    cursor.execute(query, (limite,))
    return cursor.fetchall()


# ============================================================================
# FUNCIONES DE USUARIOS
# ============================================================================
@db_connection
def verificar_credenciales(cursor, nombre_usuario, contrasena):
    cursor.execute(
        "SELECT id, rol, contrasena_hash, contrasena_salt, debe_cambiar_contrasena FROM usuarios WHERE nombre_usuario = ?",
        (nombre_usuario,)
    )
    resultado = cursor.fetchone()
    if resultado is None:
        return None
    
    user_id, rol, stored_hash, stored_salt_hex, debe_cambiar = resultado
    salt = binascii.unhexlify(stored_salt_hex)
    new_hash = hashlib.pbkdf2_hmac('sha256', contrasena.encode('utf-8'), salt, 100000)
    
    if binascii.hexlify(new_hash).decode('utf-8') == stored_hash:
        return user_id, rol, bool(debe_cambiar)
    else:
        return None


@db_connection
def obtener_usuarios(cursor):
    cursor.execute("SELECT id, nombre_usuario, rol FROM usuarios ORDER BY nombre_usuario ASC")
    return cursor.fetchall()


@db_connection
def agregar_usuario(cursor, usuario_admin_id, nombre_usuario, contrasena, rol):
    """✅ MEJORADO: Valida contraseña y audita la creación."""
    if len(contrasena) < 6:
        return "Error: La contraseña debe tener al menos 6 caracteres."
    
    try:
        salt = os.urandom(16)
        contrasena_hash = hashlib.pbkdf2_hmac('sha256', contrasena.encode('utf-8'), salt, 100000)
        cursor.execute(
            "INSERT INTO usuarios (nombre_usuario, contrasena_hash, contrasena_salt, rol, debe_cambiar_contrasena) VALUES (?, ?, ?, ?, 0)",
            (nombre_usuario, binascii.hexlify(contrasena_hash).decode('utf-8'), 
             binascii.hexlify(salt).decode('utf-8'), rol)
        )
        registrar_auditoria(cursor, usuario_admin_id, "USUARIO_CREADO", 
                          f"Usuario '{nombre_usuario}' con rol '{rol}' fue creado.")
        return True
    except sqlite3.IntegrityError:
        return "Error: El nombre de usuario ya existe."


@db_connection
def actualizar_contrasena(cursor, id_usuario, nueva_contrasena, usuario_admin_id=None):
    """✅ MEJORADO: Valida contraseña, audita y quita flag de cambio."""
    if len(nueva_contrasena) < 6:
        return "Error: La contraseña debe tener al menos 6 caracteres."
    
    nuevo_salt = os.urandom(16)
    nueva_contrasena_hash = hashlib.pbkdf2_hmac('sha256', nueva_contrasena.encode('utf-8'), nuevo_salt, 100000)
    cursor.execute(
        "UPDATE usuarios SET contrasena_hash = ?, contrasena_salt = ?, debe_cambiar_contrasena = 0 WHERE id = ?",
        (binascii.hexlify(nueva_contrasena_hash).decode('utf-8'), 
         binascii.hexlify(nuevo_salt).decode('utf-8'), id_usuario)
    )
    
    # Auditar solo si lo hace un administrador sobre otro usuario
    if usuario_admin_id and usuario_admin_id != id_usuario:
        cursor.execute("SELECT nombre_usuario FROM usuarios WHERE id = ?", (id_usuario,))
        nombre = cursor.fetchone()[0]
        registrar_auditoria(cursor, usuario_admin_id, "CONTRASENA_CAMBIADA", 
                          f"Contraseña del usuario '{nombre}' fue modificada.")
    return True


@db_connection
def eliminar_usuario(cursor, id_usuario_a_eliminar, usuario_admin_id):
    cursor.execute("SELECT nombre_usuario FROM usuarios WHERE id = ?", (id_usuario_a_eliminar,))
    nombre_usuario = cursor.fetchone()
    if not nombre_usuario:
        return False
    
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario_a_eliminar,))
    registrar_auditoria(cursor, usuario_admin_id, "USUARIO_ELIMINADO", 
                       f"Usuario '{nombre_usuario[0]}' (ID: {id_usuario_a_eliminar}) fue eliminado.")
    return True


# ============================================================================
# FUNCIONES DE PRODUCTOS
# ============================================================================
@db_connection
def obtener_productos(cursor, filtro="", incluir_id=False, categoria_id=None, proveedor_id=None):
    params = []
    if incluir_id:
        campos = "p.id, p.codigo, p.nombre, p.costo, p.precio, p.stock, IFNULL(pr.nombre, 'N/A'), IFNULL(c.nombre, 'Sin Categoría')"
    else:
        campos = "p.codigo, p.nombre, p.precio, p.stock"

    query = f"SELECT {campos} FROM productos p LEFT JOIN proveedores pr ON p.proveedor_id = pr.id LEFT JOIN categorias c ON p.categoria_id = c.id WHERE p.activo = 1"

    if proveedor_id:
        query += " AND p.proveedor_id = ?"
        params.append(proveedor_id)

    if filtro:
        filtro = filtro.strip()
        if filtro.isdigit():
            query += " AND (p.codigo LIKE ? OR LOWER(p.nombre) LIKE ?)"
            params.extend([f"{filtro}%", f"%{filtro.lower()}%"])
        else:
            query += " AND (LOWER(p.nombre) LIKE ? OR p.codigo LIKE ?)"
            params.extend([f"%{filtro.lower()}%", f"%{filtro}%"])

    if categoria_id:
        query += " AND p.categoria_id = ?"
        params.append(categoria_id)

    query += " ORDER BY p.nombre ASC"
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


@db_connection
def obtener_producto_por_id(cursor, id_producto):
    cursor.execute(
        "SELECT id, codigo, nombre, descripcion, costo, precio, stock, proveedor_id, categoria_id FROM productos WHERE id = ?",
        (id_producto,)
    )
    return cursor.fetchone()


@db_connection
def agregar_producto(cursor, usuario_id, codigo, nombre, descripcion, costo, precio, stock, proveedor_id, categoria_id):
    """✅ MEJORADO: Valida que costo > 0 y audita."""
    if costo <= 0:
        return "Error: El costo debe ser mayor a 0 para calcular ganancias correctamente."
    
    if precio < costo:
        return "Advertencia: El precio de venta es menor al costo. Verificar."
    
    try:
        cursor.execute(
            "INSERT INTO productos (codigo, nombre, descripcion, costo, precio, stock, activo, proveedor_id, categoria_id) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (codigo, nombre, descripcion, costo, precio, stock, proveedor_id, categoria_id)
        )
        registrar_auditoria(cursor, usuario_id, "PROD_CREADO", 
                          f"Producto '{nombre}' ({codigo}) con costo ${costo:.2f} agregado.")
        return True
    except sqlite3.IntegrityError:
        return "Error: El código del producto ya existe."


@db_connection
def actualizar_producto(cursor, usuario_id, id_producto, codigo, nombre, descripcion, costo, precio, stock, proveedor_id, categoria_id):
    """✅ MEJORADO: Valida costo y audita cambios."""
    if costo <= 0:
        return "Error: El costo debe ser mayor a 0."
    
    if precio < costo:
        return "Advertencia: El precio de venta es menor al costo."
    
    cursor.execute("SELECT nombre, costo FROM productos WHERE id = ?", (id_producto,))
    resultado = cursor.fetchone()
    if not resultado:
        return "Error: Producto no encontrado."
    
    nombre_antiguo, costo_antiguo = resultado
    
    try:
        cursor.execute(
            "UPDATE productos SET codigo = ?, nombre = ?, descripcion = ?, costo = ?, precio = ?, stock = ?, proveedor_id = ?, categoria_id = ? WHERE id = ?",
            (codigo, nombre, descripcion, costo, precio, stock, proveedor_id, categoria_id, id_producto)
        )
        
        cambios = []
        if nombre != nombre_antiguo:
            cambios.append(f"nombre: '{nombre_antiguo}' → '{nombre}'")
        if costo != costo_antiguo:
            cambios.append(f"costo: ${costo_antiguo:.2f} → ${costo:.2f}")
        
        desc = f"Producto ID {id_producto}. Cambios: {', '.join(cambios)}" if cambios else f"Producto ID {id_producto} actualizado."
        registrar_auditoria(cursor, usuario_id, "PROD_ACTUALIZADO", desc)
        return True
    except sqlite3.IntegrityError:
        return "Error: El código del producto ya existe."


@db_connection
def desactivar_producto(cursor, usuario_id, id_producto):
    cursor.execute("SELECT nombre FROM productos WHERE id = ?", (id_producto,))
    nombre_producto = cursor.fetchone()
    if not nombre_producto:
        return False

    cursor.execute("UPDATE productos SET activo = 0 WHERE id = ?", (id_producto,))
    registrar_auditoria(cursor, usuario_id, "PROD_DESACTIVADO", 
                       f"Producto ID {id_producto} ('{nombre_producto[0]}') desactivado.")
    return True


# ============================================================================
# FUNCIONES DE VENTAS
# ============================================================================
@db_connection
def registrar_venta(cursor, usuario_id, total, carrito, tipo_pago, deudor_id=None):
    try:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        saldo_pendiente = total if tipo_pago == "Credito" else 0.0
        
        cursor.execute(
            "INSERT INTO ventas (usuario_id, fecha_hora, total, tipo_pago, deudor_id, saldo_pendiente) VALUES (?, ?, ?, ?, ?, ?)",
            (usuario_id, fecha_hora, total, tipo_pago, deudor_id, saldo_pendiente)
        )
        venta_id = cursor.lastrowid

        for codigo, item in carrito.items():
            cursor.execute("SELECT id FROM productos WHERE codigo = ?", (codigo,))
            producto_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO detalles_venta (venta_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                (venta_id, producto_id, item["cantidad"], item["precio"])
            )
            cursor.execute("UPDATE productos SET stock = stock - ? WHERE id = ?", (item["cantidad"], producto_id))

        if tipo_pago == "Credito" and deudor_id is not None:
            cursor.execute("UPDATE deudores SET saldo = saldo + ? WHERE id = ?", (total, deudor_id))

        tipo = "Crédito" if tipo_pago == "Credito" else "Contado"
        registrar_auditoria(cursor, usuario_id, "VENTA_REGISTRADA", 
                          f"Venta ID {venta_id}. Total: ${total:.2f}. Tipo: {tipo}.")
        return venta_id
    except sqlite3.Error as e:
        raise e


@db_connection
def obtener_ventas_del_dia(cursor):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT v.id, v.fecha_hora, u.nombre_usuario, v.total FROM ventas v "
        "JOIN usuarios u ON v.usuario_id = u.id WHERE DATE(v.fecha_hora) = ? ORDER BY v.fecha_hora DESC",
        (fecha_hoy,)
    )
    return cursor.fetchall()


@db_connection
def obtener_resumen_ventas_dia(cursor, usuario_id):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT SUM(total) FROM ventas WHERE usuario_id = ? AND DATE(fecha_hora) = ? AND tipo_pago = 'Contado'",
        (usuario_id, fecha_hoy)
    )
    resultado = cursor.fetchone()[0]
    return resultado if resultado is not None else 0.0


@db_connection
def obtener_info_venta(cursor, venta_id):
    cursor.execute("SELECT fecha_hora, total FROM ventas WHERE id = ?", (venta_id,))
    return cursor.fetchone()


@db_connection
def obtener_detalle_de_venta(cursor, venta_id):
    cursor.execute(
        "SELECT p.nombre, dv.cantidad, (dv.cantidad * dv.precio_unitario) as subtotal FROM detalles_venta dv "
        "JOIN productos p ON dv.producto_id = p.id WHERE dv.venta_id = ?",
        (venta_id,)
    )
    return cursor.fetchall()


@db_connection
def obtener_ventas_por_rango(cursor, fecha_inicio, fecha_fin):
    cursor.execute(
        "SELECT v.id, v.fecha_hora, u.nombre_usuario, v.total FROM ventas v "
        "JOIN usuarios u ON v.usuario_id = u.id WHERE DATE(v.fecha_hora) BETWEEN ? AND ? ORDER BY v.fecha_hora DESC",
        (fecha_inicio, fecha_fin)
    )
    return cursor.fetchall()


@db_connection
def obtener_productos_mas_vendidos(cursor, fecha_inicio, fecha_fin):
    cursor.execute(
        "SELECT p.nombre, SUM(dv.cantidad) as total_vendido FROM detalles_venta dv "
        "JOIN productos p ON dv.producto_id = p.id JOIN ventas v ON dv.venta_id = v.id "
        "WHERE DATE(v.fecha_hora) BETWEEN ? AND ? GROUP BY p.nombre ORDER BY total_vendido DESC",
        (fecha_inicio, fecha_fin)
    )
    return cursor.fetchall()


# ============================================================================
# FUNCIONES DE COMPRAS
# ============================================================================
@db_connection
def registrar_compra(cursor, usuario_id, proveedor_id, total_costo, carrito_compra):
    """✅ MEJORADO: Audita las compras."""
    try:
        fecha = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO compras (proveedor_id, fecha, total_costo) VALUES (?, ?, ?)",
            (proveedor_id, fecha, total_costo)
        )
        compra_id = cursor.lastrowid
        
        for codigo, item in carrito_compra.items():
            cursor.execute("SELECT id, stock FROM productos WHERE codigo = ?", (codigo,))
            producto_id, stock_actual = cursor.fetchone()
            cursor.execute(
                "INSERT INTO detalles_compra (compra_id, producto_id, cantidad, costo_unitario) VALUES (?, ?, ?, ?)",
                (compra_id, producto_id, item["cantidad"], item["costo"])
            )
            nuevo_stock = stock_actual + item["cantidad"]
            cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (nuevo_stock, producto_id))
        
        cursor.execute("SELECT nombre FROM proveedores WHERE id = ?", (proveedor_id,))
        nombre_prov = cursor.fetchone()[0]
        registrar_auditoria(cursor, usuario_id, "COMPRA_REGISTRADA", 
                          f"Compra ID {compra_id} a '{nombre_prov}'. Total: ${total_costo:.2f}.")
        return True
    except sqlite3.Error as e:
        raise e


@db_connection
def obtener_compras_por_rango(cursor, fecha_inicio, fecha_fin):
    query = """
        SELECT c.id, c.fecha, IFNULL(p.nombre, 'PROVEEDOR ELIMINADO'), c.total_costo
        FROM compras c LEFT JOIN proveedores p ON c.proveedor_id = p.id
        WHERE DATE(c.fecha) BETWEEN ? AND ? ORDER BY c.fecha DESC
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    return cursor.fetchall()


@db_connection
def obtener_detalle_de_compra(cursor, compra_id):
    query = """
        SELECT p.nombre, dc.cantidad, dc.costo_unitario, (dc.cantidad * dc.costo_unitario) as subtotal
        FROM detalles_compra dc JOIN productos p ON dc.producto_id = p.id WHERE dc.compra_id = ?
    """
    cursor.execute(query, (compra_id,))
    return cursor.fetchall()


# ============================================================================
# FUNCIONES DE PROVEEDORES
# ============================================================================
@db_connection
def obtener_proveedores(cursor, incluir_inactivos=False):
    query = "SELECT id, nombre, telefono, email FROM proveedores"
    if not incluir_inactivos:
        query += " WHERE activo = 1"
    query += " ORDER BY nombre ASC"
    cursor.execute(query)
    return cursor.fetchall()


@db_connection
def obtener_proveedor_por_id(cursor, id_proveedor):
    cursor.execute("SELECT id, nombre, telefono, email, direccion, activo FROM proveedores WHERE id = ?", (id_proveedor,))
    return cursor.fetchone()


@db_connection
def agregar_proveedor(cursor, usuario_id, nombre, telefono, email, direccion):
    """✅ MEJORADO: Audita la creación."""
    try:
        cursor.execute(
            "INSERT INTO proveedores (nombre, telefono, email, direccion, activo) VALUES (?, ?, ?, ?, 1)",
            (nombre, telefono, email, direccion)
        )
        registrar_auditoria(cursor, usuario_id, "PROVEEDOR_CREADO", 
                          f"Proveedor '{nombre}' agregado.")
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe un proveedor con ese nombre."


@db_connection
def actualizar_proveedor(cursor, usuario_id, id_proveedor, nombre, telefono, email, direccion):
    """✅ MEJORADO: Audita la actualización."""
    cursor.execute("SELECT nombre FROM proveedores WHERE id = ?", (id_proveedor,))
    nombre_antiguo = cursor.fetchone()
    if not nombre_antiguo:
        return "Error: Proveedor no encontrado."
    
    try:
        cursor.execute(
            "UPDATE proveedores SET nombre = ?, telefono = ?, email = ?, direccion = ? WHERE id = ?",
            (nombre, telefono, email, direccion, id_proveedor)
        )
        if nombre != nombre_antiguo[0]:
            registrar_auditoria(cursor, usuario_id, "PROVEEDOR_ACTUALIZADO", 
                              f"Proveedor '{nombre_antiguo[0]}' → '{nombre}'.")
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe otro proveedor con el mismo nombre."


@db_connection
def desactivar_proveedor(cursor, usuario_id, id_proveedor):
    """✅ MEJORADO: Eliminación lógica con auditoría."""
    cursor.execute("SELECT nombre FROM proveedores WHERE id = ?", (id_proveedor,))
    nombre = cursor.fetchone()
    if not nombre:
        return "Error: No se encontró el proveedor."
    
    cursor.execute("UPDATE proveedores SET activo = 0 WHERE id = ?", (id_proveedor,))
    registrar_auditoria(cursor, usuario_id, "PROVEEDOR_DESACTIVADO", 
                       f"Proveedor '{nombre[0]}' desactivado.")
    return True


# ============================================================================
# FUNCIONES DE DEUDORES
# ============================================================================
@db_connection
def obtener_deudores(cursor):
    cursor.execute("SELECT id, nombre, telefono, saldo FROM deudores ORDER BY nombre ASC")
    return cursor.fetchall()


@db_connection
def obtener_deudor_por_id(cursor, deudor_id):
    cursor.execute(
        "SELECT id, nombre, telefono, direccion, notas, saldo FROM deudores WHERE id = ?",
        (deudor_id,)
    )
    return cursor.fetchone()


@db_connection
def agregar_deudor(cursor, usuario_id, nombre, telefono, direccion, notas):
    """✅ MEJORADO: Audita la creación."""
    try:
        cursor.execute(
            "INSERT INTO deudores (nombre, telefono, direccion, notas) VALUES (?, ?, ?, ?)",
            (nombre, telefono, direccion, notas)
        )
        registrar_auditoria(cursor, usuario_id, "DEUDOR_CREADO", 
                          f"Deudor '{nombre}' agregado.")
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe un deudor con ese nombre."


@db_connection
def actualizar_deudor(cursor, usuario_id, deudor_id, nombre, telefono, direccion, notas):
    """✅ MEJORADO: Audita la actualización."""
    cursor.execute("SELECT nombre FROM deudores WHERE id = ?", (deudor_id,))
    nombre_antiguo = cursor.fetchone()
    if not nombre_antiguo:
        return "Error: Deudor no encontrado."
    
    try:
        cursor.execute(
            "UPDATE deudores SET nombre = ?, telefono = ?, direccion = ?, notas = ? WHERE id = ?",
            (nombre, telefono, direccion, notas, deudor_id)
        )
        if nombre != nombre_antiguo[0]:
            registrar_auditoria(cursor, usuario_id, "DEUDOR_ACTUALIZADO", 
                              f"Deudor '{nombre_antiguo[0]}' → '{nombre}'.")
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe un deudor con ese nombre."


@db_connection
def eliminar_deudor(cursor, usuario_id, deudor_id):
    """✅ MEJORADO: Audita la eliminación."""
    cursor.execute("SELECT nombre, saldo FROM deudores WHERE id = ?", (deudor_id,))
    resultado = cursor.fetchone()
    if not resultado:
        return "Error: Deudor no encontrado."
    
    nombre, saldo = resultado
    if saldo > 0.0:
        return "Error: No se puede eliminar un deudor con saldo pendiente."
    
    cursor.execute("DELETE FROM deudores WHERE id = ?", (deudor_id,))
    registrar_auditoria(cursor, usuario_id, "DEUDOR_ELIMINADO", 
                       f"Deudor '{nombre}' eliminado.")
    return True


@db_connection
def registrar_pago_deudor(cursor, usuario_id, deudor_id, venta_id, monto):
    """✅ MEJORADO: Audita los pagos."""
    try:
        cursor.execute("SELECT saldo_pendiente FROM ventas WHERE id = ?", (venta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return "Error: La venta especificada no existe."
        
        saldo_venta = resultado[0]
        if monto > saldo_venta:
            return "Error: El monto del pago no puede ser mayor al saldo pendiente."

        fecha = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO pagos_deudores (deudor_id, venta_id, fecha, monto) VALUES (?, ?, ?, ?)",
            (deudor_id, venta_id, fecha, monto)
        )
        cursor.execute(
            "UPDATE ventas SET saldo_pendiente = saldo_pendiente - ? WHERE id = ?",
            (monto, venta_id)
        )
        cursor.execute(
            "UPDATE deudores SET saldo = saldo - ? WHERE id = ?", 
            (monto, deudor_id)
        )
        
        cursor.execute("SELECT nombre FROM deudores WHERE id = ?", (deudor_id,))
        nombre_deudor = cursor.fetchone()[0]
        registrar_auditoria(cursor, usuario_id, "PAGO_REGISTRADO", 
                          f"Pago de ${monto:.2f} de '{nombre_deudor}' a venta ID {venta_id}.")
        return True
    except sqlite3.Error as e:
        raise e


@db_connection
def obtener_ventas_deudor(cursor, deudor_id):
    cursor.execute(
        "SELECT id, fecha_hora, total FROM ventas WHERE deudor_id = ? AND tipo_pago = 'Credito' ORDER BY fecha_hora DESC",
        (deudor_id,)
    )
    return cursor.fetchall()


@db_connection
def obtener_deudas_pendientes_deudor(cursor, deudor_id):
    cursor.execute(
        "SELECT id, fecha_hora, total, saldo_pendiente FROM ventas "
        "WHERE deudor_id = ? AND saldo_pendiente > 0 ORDER BY fecha_hora ASC",
        (deudor_id,)
    )
    return cursor.fetchall()


@db_connection
def obtener_pagos_de_una_venta(cursor, venta_id):
    cursor.execute(
        "SELECT fecha, monto FROM pagos_deudores WHERE venta_id = ? ORDER BY fecha DESC",
        (venta_id,)
    )
    return cursor.fetchall()


@db_connection
def obtener_deudas_pagadas_deudor(cursor, deudor_id):
    cursor.execute(
        "SELECT id, fecha_hora, total FROM ventas "
        "WHERE deudor_id = ? AND tipo_pago = 'Credito' AND saldo_pendiente <= 0 ORDER BY fecha_hora DESC",
        (deudor_id,)
    )
    return cursor.fetchall()


# ============================================================================
# FUNCIONES DE CATEGORÍAS
# ============================================================================
@db_connection
def obtener_categorias(cursor):
    cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    return cursor.fetchall()


@db_connection
def agregar_categoria(cursor, usuario_id, nombre):
    """✅ MEJORADO: Audita la creación."""
    try:
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        registrar_auditoria(cursor, usuario_id, "CATEGORIA_CREADA", 
                          f"Categoría '{nombre}' creada.")
        return True
    except sqlite3.IntegrityError:
        return "Error: Esa categoría ya existe."


@db_connection
def eliminar_categoria(cursor, usuario_id, id_categoria):
    """✅ MEJORADO: Audita la eliminación."""
    cursor.execute("SELECT nombre FROM categorias WHERE id = ?", (id_categoria,))
    nombre = cursor.fetchone()
    if not nombre:
        return "Error: Categoría no encontrada."
    
    try:
        cursor.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
        registrar_auditoria(cursor, usuario_id, "CATEGORIA_ELIMINADA", 
                          f"Categoría '{nombre[0]}' eliminada.")
        return True
    except sqlite3.IntegrityError:
        return "Error: No se puede eliminar la categoría porque tiene productos asignados."


# ============================================================================
# FUNCIONES DE REPORTES
# ============================================================================
@db_connection
def obtener_reporte_ganancias(cursor, fecha_inicio, fecha_fin):
    query = """
        SELECT
            SUM(dv.cantidad * dv.precio_unitario) as total_ventas,
            SUM(dv.cantidad * p.costo) as total_costo
        FROM detalles_venta dv
        JOIN productos p ON dv.producto_id = p.id
        JOIN ventas v ON dv.venta_id = v.id
        WHERE DATE(v.fecha_hora) BETWEEN ? AND ?
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    resultado = cursor.fetchone()
    total_ventas = resultado[0] if resultado and resultado[0] is not None else 0.0
    total_costo = resultado[1] if resultado and resultado[1] is not None else 0.0
    ganancia_neta = total_ventas - total_costo
    return {
        "total_ventas": total_ventas,
        "total_costo": total_costo,
        "ganancia_neta": ganancia_neta,
    }


@db_connection
def obtener_ganancias_por_producto(cursor, fecha_inicio, fecha_fin):
    query = """
        SELECT
            p.nombre,
            SUM(dv.cantidad) AS cantidad_total,
            SUM(dv.cantidad * dv.precio_unitario) AS ingresos_totales,
            SUM(dv.cantidad * p.costo) AS costo_total,
            (SUM(dv.cantidad * dv.precio_unitario) - SUM(dv.cantidad * p.costo)) AS ganancia_neta
        FROM detalles_venta dv
        JOIN productos p ON dv.producto_id = p.id
        JOIN ventas v ON dv.venta_id = v.id
        WHERE DATE(v.fecha_hora) BETWEEN ? AND ?
        GROUP BY p.id, p.nombre
        ORDER BY ganancia_neta DESC
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    return cursor.fetchall()


# ============================================================================
# FUNCIONES DE BACKUP
# ============================================================================
def crear_copia_de_seguridad(ruta_destino):
    try:
        shutil.copy(DB_PATH, ruta_destino)
        return True
    except Exception as e:
        print(f"Error al crear la copia de seguridad: {e}")
        return False


def restaurar_copia_de_seguridad(ruta_origen):
    if not os.path.exists(ruta_origen):
        print("Error: El archivo de backup no existe.")
        return False

    try:
        shutil.copy(ruta_origen, DB_PATH)
        return True
    except Exception as e:
        print(f"Error al restaurar la copia de seguridad: {e}")
        return False

# ============================================================================
# FUNCIONES DE CIERRE DE CAJA
# ============================================================================

@db_connection
def registrar_cierre_caja(cursor, usuario_id, total_ventas_sistema, total_efectivo_sistema, efectivo_contado, observaciones=""):
    """
    Registra un cierre de caja y audita la acción.
    """
    try:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        diferencia = efectivo_contado - total_efectivo_sistema
        
        cursor.execute(
            """INSERT INTO cierres_caja 
               (usuario_id, fecha_hora, total_ventas_sistema, total_efectivo_sistema, 
                efectivo_contado, diferencia, observaciones) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (usuario_id, fecha_hora, total_ventas_sistema, total_efectivo_sistema, 
             efectivo_contado, diferencia, observaciones)
        )
        cierre_id = cursor.lastrowid
        
        # Auditar el cierre
        estado = "CUADRADA" if diferencia == 0 else ("SOBRANTE" if diferencia > 0 else "FALTANTE")
        registrar_auditoria(
            cursor, 
            usuario_id, 
            "CIERRE_CAJA",
            f"Cierre ID {cierre_id}. Efectivo sistema: ${total_efectivo_sistema:.2f}, "
            f"Contado: ${efectivo_contado:.2f}, Diferencia: ${diferencia:.2f} ({estado})"
        )
        
        return cierre_id
    except sqlite3.Error as e:
        print(f"Error al registrar cierre de caja: {e}")
        return None


@db_connection
def obtener_cierres_por_usuario(cursor, usuario_id, limite=30):
    """Obtiene el historial de cierres de un usuario específico."""
    query = """
        SELECT 
            id,
            fecha_hora,
            total_ventas_sistema,
            total_efectivo_sistema,
            efectivo_contado,
            diferencia,
            observaciones
        FROM cierres_caja
        WHERE usuario_id = ?
        ORDER BY fecha_hora DESC
        LIMIT ?
    """
    cursor.execute(query, (usuario_id, limite))
    return cursor.fetchall()


@db_connection
def obtener_cierres_por_rango(cursor, fecha_inicio, fecha_fin):
    """Obtiene todos los cierres en un rango de fechas."""
    query = """
        SELECT 
            c.id,
            c.fecha_hora,
            u.nombre_usuario,
            c.total_ventas_sistema,
            c.total_efectivo_sistema,
            c.efectivo_contado,
            c.diferencia,
            c.observaciones
        FROM cierres_caja c
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE DATE(c.fecha_hora) BETWEEN ? AND ?
        ORDER BY c.fecha_hora DESC
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    return cursor.fetchall()


@db_connection
def obtener_detalle_cierre(cursor, cierre_id):
    """Obtiene el detalle completo de un cierre específico."""
    query = """
        SELECT 
            c.id,
            c.fecha_hora,
            u.nombre_usuario,
            u.rol,
            c.total_ventas_sistema,
            c.total_efectivo_sistema,
            c.efectivo_contado,
            c.diferencia,
            c.observaciones
        FROM cierres_caja c
        JOIN usuarios u ON c.usuario_id = u.id
        WHERE c.id = ?
    """
    cursor.execute(query, (cierre_id,))
    return cursor.fetchone()


@db_connection
def verificar_cierre_hoy(cursor, usuario_id):
    """Verifica si ya existe un cierre para el usuario en el día actual."""
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """SELECT COUNT(*) FROM cierres_caja 
           WHERE usuario_id = ? AND DATE(fecha_hora) = ?""",
        (usuario_id, fecha_hoy)
    )
    count = cursor.fetchone()[0]
    return count > 0


@db_connection
def obtener_resumen_cierres(cursor, fecha_inicio, fecha_fin):
    """Obtiene un resumen estadístico de los cierres en un rango de fechas."""
    query = """
        SELECT 
            COUNT(*) as total_cierres,
            SUM(total_efectivo_sistema) as total_efectivo,
            SUM(efectivo_contado) as total_contado,
            SUM(diferencia) as total_diferencia,
            AVG(diferencia) as promedio_diferencia,
            SUM(CASE WHEN diferencia > 0 THEN diferencia ELSE 0 END) as total_sobrantes,
            SUM(CASE WHEN diferencia < 0 THEN diferencia ELSE 0 END) as total_faltantes,
            SUM(CASE WHEN diferencia = 0 THEN 1 ELSE 0 END) as cierres_cuadrados
        FROM cierres_caja
        WHERE DATE(fecha_hora) BETWEEN ? AND ?
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    resultado = cursor.fetchone()
    
    if not resultado or resultado[0] == 0:
        return {
            "total_cierres": 0,
            "total_efectivo": 0.0,
            "total_contado": 0.0,
            "total_diferencia": 0.0,
            "promedio_diferencia": 0.0,
            "total_sobrantes": 0.0,
            "total_faltantes": 0.0,
            "cierres_cuadrados": 0
        }
    
    return {
        "total_cierres": resultado[0],
        "total_efectivo": resultado[1] or 0.0,
        "total_contado": resultado[2] or 0.0,
        "total_diferencia": resultado[3] or 0.0,
        "promedio_diferencia": resultado[4] or 0.0,
        "total_sobrantes": resultado[5] or 0.0,
        "total_faltantes": resultado[6] or 0.0,
        "cierres_cuadrados": resultado[7] or 0
    }

@db_connection
def buscar_ventas_para_devolucion(cursor, criterio, valor):
    """
    Busca ventas que puedan ser devueltas.
    
    Args:
        criterio: 'id', 'fecha', 'deudor'
        valor: El valor a buscar
    
    Returns:
        Lista de ventas encontradas
    """
    if criterio == 'id':
        query = """
            SELECT 
                v.id,
                v.fecha_hora,
                u.nombre_usuario,
                v.total,
                v.tipo_pago,
                IFNULL(d.nombre, 'N/A') as deudor
            FROM ventas v
            JOIN usuarios u ON v.usuario_id = u.id
            LEFT JOIN deudores d ON v.deudor_id = d.id
            WHERE v.id = ?
        """
        cursor.execute(query, (valor,))
    elif criterio == 'fecha':
        query = """
            SELECT 
                v.id,
                v.fecha_hora,
                u.nombre_usuario,
                v.total,
                v.tipo_pago,
                IFNULL(d.nombre, 'N/A') as deudor
            FROM ventas v
            JOIN usuarios u ON v.usuario_id = u.id
            LEFT JOIN deudores d ON v.deudor_id = d.id
            WHERE DATE(v.fecha_hora) = ?
            ORDER BY v.fecha_hora DESC
        """
        cursor.execute(query, (valor,))
    else:
        return []
    
    return cursor.fetchall()


@db_connection
def obtener_detalle_venta_para_devolucion(cursor, venta_id):
    """
    Obtiene el detalle completo de una venta para procesarla.
    
    Returns:
        Tupla con (info_venta, detalles_productos)
    """
    # Info general de la venta
    cursor.execute("""
        SELECT 
            v.id,
            v.fecha_hora,
            v.usuario_id,
            u.nombre_usuario,
            v.total,
            v.tipo_pago,
            v.deudor_id,
            IFNULL(d.nombre, 'N/A') as deudor_nombre,
            v.saldo_pendiente
        FROM ventas v
        JOIN usuarios u ON v.usuario_id = u.id
        LEFT JOIN deudores d ON v.deudor_id = d.id
        WHERE v.id = ?
    """, (venta_id,))
    
    info_venta = cursor.fetchone()
    if not info_venta:
        return None, None
    
    # Detalles de productos
    cursor.execute("""
        SELECT 
            dv.id,
            dv.producto_id,
            p.codigo,
            p.nombre,
            dv.cantidad,
            dv.precio_unitario,
            (dv.cantidad * dv.precio_unitario) as subtotal
        FROM detalles_venta dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
    """, (venta_id,))
    
    detalles = cursor.fetchall()
    
    return info_venta, detalles


@db_connection
def verificar_devolucion_previa(cursor, venta_id):
    """
    Verifica si una venta ya tiene devoluciones registradas.
    
    Returns:
        Tupla (tiene_devolucion, total_devuelto)
    """
    cursor.execute("""
        SELECT 
            COUNT(*),
            IFNULL(SUM(total_devolucion), 0)
        FROM devoluciones
        WHERE venta_id = ?
    """, (venta_id,))
    
    resultado = cursor.fetchone()
    tiene_devolucion = resultado[0] > 0
    total_devuelto = resultado[1]
    
    return tiene_devolucion, total_devuelto


@db_connection
def registrar_devolucion(cursor, usuario_id, venta_id, productos_devolver, motivo=""):
    """
    Registra una devolución completa o parcial.
    
    Args:
        usuario_id: Usuario que procesa la devolución
        venta_id: ID de la venta original
        productos_devolver: Dict {producto_id: cantidad_a_devolver}
        motivo: Razón de la devolución
    
    Returns:
        ID de la devolución o None si falla
    """
    try:
        # 1. Obtener info de la venta
        cursor.execute("""
            SELECT tipo_pago, deudor_id, total
            FROM ventas
            WHERE id = ?
        """, (venta_id,))
        
        venta_info = cursor.fetchone()
        if not venta_info:
            return None
        
        tipo_pago, deudor_id, total_venta = venta_info
        
        # 2. Calcular total de la devolución
        total_devolucion = 0.0
        detalles_devolucion = []
        
        for producto_id, cantidad_devolver in productos_devolver.items():
            # Obtener precio unitario de la venta original
            cursor.execute("""
                SELECT precio_unitario
                FROM detalles_venta
                WHERE venta_id = ? AND producto_id = ?
            """, (venta_id, producto_id))
            
            precio_unitario = cursor.fetchone()[0]
            subtotal = cantidad_devolver * precio_unitario
            total_devolucion += subtotal
            
            detalles_devolucion.append((producto_id, cantidad_devolver, precio_unitario))
        
        # 3. Determinar si es devolución completa o parcial
        es_completa = (total_devolucion >= total_venta)
        tipo_devolucion = "COMPLETA" if es_completa else "PARCIAL"
        
        # 4. Registrar la devolución
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO devoluciones 
            (venta_id, usuario_id, fecha_hora, total_devolucion, tipo_devolucion, motivo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (venta_id, usuario_id, fecha_hora, total_devolucion, tipo_devolucion, motivo))
        
        devolucion_id = cursor.lastrowid
        
        # 5. Registrar detalles de la devolución
        for producto_id, cantidad, precio_unitario in detalles_devolucion:
            cursor.execute("""
                INSERT INTO detalles_devolucion
                (devolucion_id, producto_id, cantidad_devuelta, precio_unitario)
                VALUES (?, ?, ?, ?)
            """, (devolucion_id, producto_id, cantidad, precio_unitario))
            
            # 6. Restaurar stock
            cursor.execute("""
                UPDATE productos
                SET stock = stock + ?
                WHERE id = ?
            """, (cantidad, producto_id))
        
        # 7. Procesar reintegro según tipo de pago
        if tipo_pago == "Credito" and deudor_id:
            # Reducir deuda del deudor
            cursor.execute("""
                UPDATE deudores
                SET saldo = saldo - ?
                WHERE id = ?
            """, (total_devolucion, deudor_id))
            
            # Actualizar saldo pendiente de la venta
            cursor.execute("""
                UPDATE ventas
                SET saldo_pendiente = saldo_pendiente - ?
                WHERE id = ?
            """, (total_devolucion, venta_id))
        
        # 8. Auditar
        cursor.execute("SELECT nombre FROM deudores WHERE id = ?", (deudor_id,)) if deudor_id else None
        nombre_deudor = cursor.fetchone()[0] if deudor_id and cursor.rowcount > 0 else "N/A"
        
        registrar_auditoria(
            cursor,
            usuario_id,
            "DEVOLUCION_REGISTRADA",
            f"Devolución ID {devolucion_id} de venta #{venta_id}. "
            f"Total: ${total_devolucion:.2f}. Tipo: {tipo_devolucion}. "
            f"Pago: {tipo_pago}{f' (Deudor: {nombre_deudor})' if deudor_id else ''}."
        )
        
        return devolucion_id
        
    except sqlite3.Error as e:
        print(f"Error al registrar devolución: {e}")
        return None


@db_connection
def obtener_devoluciones_por_rango(cursor, fecha_inicio, fecha_fin):
    """
    Obtiene todas las devoluciones en un rango de fechas.
    """
    query = """
        SELECT 
            d.id,
            d.fecha_hora,
            d.venta_id,
            u.nombre_usuario,
            d.total_devolucion,
            d.tipo_devolucion,
            d.motivo
        FROM devoluciones d
        JOIN usuarios u ON d.usuario_id = u.id
        WHERE DATE(d.fecha_hora) BETWEEN ? AND ?
        ORDER BY d.fecha_hora DESC
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    return cursor.fetchall()


@db_connection
def obtener_detalle_devolucion(cursor, devolucion_id):
    """
    Obtiene el detalle completo de una devolución.
    """
    # Info general
    cursor.execute("""
        SELECT 
            d.id,
            d.venta_id,
            d.fecha_hora,
            u.nombre_usuario,
            d.total_devolucion,
            d.tipo_devolucion,
            d.motivo
        FROM devoluciones d
        JOIN usuarios u ON d.usuario_id = u.id
        WHERE d.id = ?
    """, (devolucion_id,))
    
    info_devolucion = cursor.fetchone()
    if not info_devolucion:
        return None, None
    
    # Productos devueltos
    cursor.execute("""
        SELECT 
            p.nombre,
            dd.cantidad_devuelta,
            dd.precio_unitario,
            (dd.cantidad_devuelta * dd.precio_unitario) as subtotal
        FROM detalles_devolucion dd
        JOIN productos p ON dd.producto_id = p.id
        WHERE dd.devolucion_id = ?
    """, (devolucion_id,))
    
    detalles = cursor.fetchall()
    
    return info_devolucion, detalles


@db_connection
def obtener_estadisticas_devoluciones(cursor, fecha_inicio, fecha_fin):
    """
    Obtiene estadísticas de devoluciones en un período.
    """
    query = """
        SELECT 
            COUNT(*) as total_devoluciones,
            SUM(total_devolucion) as monto_total_devuelto,
            SUM(CASE WHEN tipo_devolucion = 'COMPLETA' THEN 1 ELSE 0 END) as completas,
            SUM(CASE WHEN tipo_devolucion = 'PARCIAL' THEN 1 ELSE 0 END) as parciales,
            AVG(total_devolucion) as promedio_devolucion
        FROM devoluciones
        WHERE DATE(fecha_hora) BETWEEN ? AND ?
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    resultado = cursor.fetchone()
    
    if not resultado or resultado[0] == 0:
        return {
            "total_devoluciones": 0,
            "monto_total_devuelto": 0.0,
            "completas": 0,
            "parciales": 0,
            "promedio_devolucion": 0.0
        }
    
    return {
        "total_devoluciones": resultado[0],
        "monto_total_devuelto": resultado[1] or 0.0,
        "completas": resultado[2] or 0,
        "parciales": resultado[3] or 0,
        "promedio_devolucion": resultado[4] or 0.0
    }