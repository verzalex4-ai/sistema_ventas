# database.py
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
    nombre_db = "data.db"
    return os.path.join(ruta_base, nombre_db)


DB_PATH = obtener_ruta_db()


# --- DECORADOR PARA MANEJAR LA CONEXIÓN ---
def db_connection(func):
    """
    Decorador que gestiona la conexión a la base de datos,
    el commit, el rollback y el cierre de forma automática.
    """

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
            return None  # Retorna None en caso de error

    return wrapper


# Esta función NO lleva decorador porque es la configuración inicial.
def setup_database():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Asegúrate de incluir 'auditor' en los roles permitidos
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nombre_usuario TEXT UNIQUE NOT NULL, 
                contrasena_hash TEXT NOT NULL, 
                contrasena_salt TEXT NOT NULL,
                rol TEXT NOT NULL CHECK(rol IN ('admin', 'usuario', 'auditor'))
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE NOT NULL,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                costo REAL NOT NULL DEFAULT 0.0,
                precio REAL NOT NULL,
                stock INTEGER NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                proveedor_id INTEGER,
                categoria_id INTEGER, 
                FOREIGN KEY (proveedor_id) REFERENCES proveedores (id) ON DELETE SET NULL,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id) ON DELETE SET NULL
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                fecha_hora TEXT NOT NULL,
                total REAL NOT NULL,
                tipo_pago TEXT NOT NULL,
                deudor_id INTEGER,
                saldo_pendiente REAL NOT NULL DEFAULT 0.0,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (deudor_id) REFERENCES deudores (id)
            );
        """
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS detalles_venta (id INTEGER PRIMARY KEY AUTOINCREMENT, venta_id INTEGER NOT NULL, producto_id INTEGER NOT NULL, cantidad INTEGER NOT NULL, precio_unitario REAL NOT NULL, FOREIGN KEY (venta_id) REFERENCES ventas (id) ON DELETE CASCADE, FOREIGN KEY (producto_id) REFERENCES productos (id));"""
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nombre TEXT UNIQUE NOT NULL, 
                contacto TEXT, 
                telefono TEXT, 
                email TEXT, 
                direccion TEXT, 
                activo INTEGER NOT NULL DEFAULT 1 
            );
            """
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, proveedor_id INTEGER NOT NULL, fecha TEXT NOT NULL, total_costo REAL NOT NULL, FOREIGN KEY (proveedor_id) REFERENCES proveedores (id));"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS detalles_compra (id INTEGER PRIMARY KEY AUTOINCREMENT, compra_id INTEGER NOT NULL, producto_id INTEGER NOT NULL, cantidad INTEGER NOT NULL, costo_unitario REAL NOT NULL, FOREIGN KEY (compra_id) REFERENCES compras (id) ON DELETE CASCADE, FOREIGN KEY (producto_id) REFERENCES productos (id));"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS deudores (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL, telefono TEXT, direccion TEXT, notas TEXT, saldo REAL NOT NULL DEFAULT 0.0);"""
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pagos_deudores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deudor_id INTEGER NOT NULL,
                venta_id INTEGER,
                fecha TEXT NOT NULL,
                monto REAL NOT NULL,
                FOREIGN KEY (deudor_id) REFERENCES deudores (id),
                FOREIGN KEY (venta_id) REFERENCES ventas (id) ON DELETE SET NULL
            );
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS registro_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                fecha_hora TEXT NOT NULL,
                accion TEXT NOT NULL,
                descripcion TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            );
        """
        )

        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            usuarios_defecto = [
                ("admin", "admin", "admin"),
                ("cajero", "1234", "usuario"),
            ]
            for user, pwd, role in usuarios_defecto:
                salt = os.urandom(16)
                pwd_hash = hashlib.pbkdf2_hmac(
                    "sha256", pwd.encode("utf-8"), salt, 100000
                )
                cursor.execute(
                    "INSERT INTO usuarios (nombre_usuario, contrasena_hash, contrasena_salt, rol) VALUES (?, ?, ?, ?)",
                    (
                        user,
                        binascii.hexlify(pwd_hash).decode("utf-8"),
                        binascii.hexlify(salt).decode("utf-8"),
                        role,
                    ),
                )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error en la configuración de la base de datos: {e}")
    finally:
        if conn:
            conn.close()


# Esta función NO lleva decorador porque no usa la base de datos.
def crear_copia_de_seguridad(ruta_destino):
    try:
        shutil.copy(DB_PATH, ruta_destino)
        return True
    except Exception as e:
        print(f"Error al crear la copia de seguridad: {e}")
        return False


# Continúa en database.py...


# Esta función NO lleva decorador porque no usa la base de datos, ¡y debe asegurar que la conexión esté CERRADA!
def cerrar_db_temporalmente():
    """Cierra la conexión activa para permitir la manipulación del archivo de la DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        return True
    except sqlite3.Error as e:
        print(f"Error al intentar cerrar la conexión: {e}")
        return False


# Esta función NO lleva decorador porque no usa la base de datos.
def restaurar_copia_de_seguridad(ruta_origen):
    """
    Reemplaza la base de datos actual (data.db) con un archivo de backup.
    Retorna True si la restauración fue exitosa, False en caso contrario.
    """
    if not os.path.exists(ruta_origen):
        print("Error: El archivo de backup no existe.")
        return False

    # Es VITAL asegurar que la conexión está cerrada antes de reemplazar el archivo
    if not cerrar_db_temporalmente():
        # Si no se pudo cerrar, no procedemos
        return False

    try:
        # shutil.copy reemplaza el archivo destino si ya existe
        shutil.copy(ruta_origen, DB_PATH)
        return True
    except Exception as e:
        print(f"Error al restaurar la copia de seguridad: {e}")
        return False
    finally:
        # Opcionalmente, podrías intentar reabrir la conexión,
        # pero es más seguro indicar al usuario que reinicie la app.
        pass


# --- A PARTIR DE AQUÍ, TODAS LAS FUNCIONES LLEVAN EL DECORADOR ---


@db_connection
def verificar_credenciales(cursor, nombre_usuario, contrasena):
    cursor.execute(
        "SELECT id, rol, contrasena_hash, contrasena_salt FROM usuarios WHERE nombre_usuario = ?",
        (nombre_usuario,),
    )
    resultado = cursor.fetchone()
    if resultado is None:
        return None
    user_id, rol, stored_hash, stored_salt_hex = resultado
    salt = binascii.unhexlify(stored_salt_hex)
    new_hash = hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8"), salt, 100000)
    if binascii.hexlify(new_hash).decode("utf-8") == stored_hash:
        return user_id, rol
    else:
        return None


@db_connection
def obtener_productos(
    cursor, filtro="", incluir_id=False, categoria_id=None, proveedor_id=None
):
    """
    Devuelve productos activos (si existe la columna 'activo') o todos si la columna no existe.
    Soporta filtro (numérico -> prefijo en código, texto -> substring).
    """
    # Detectar si la columna 'activo' existe (para compatibilidad con DB que se haya modificado)
    cursor.execute("PRAGMA table_info(productos)")
    cols = [row[1] for row in cursor.fetchall()]
    activo_exists = "activo" in cols

    params = []
    if incluir_id:
        campos = (
            "p.id, p.codigo, p.nombre, p.costo, p.precio, p.stock, "
            "IFNULL(pr.nombre, 'N/A'), IFNULL(c.nombre, 'Sin Categoría')"
        )
    else:
        campos = "p.codigo, p.nombre, p.precio, p.stock"

    query = (
        f"SELECT {campos} FROM productos p "
        "LEFT JOIN proveedores pr ON p.proveedor_id = pr.id "
        "LEFT JOIN categorias c ON p.categoria_id = c.id"
    )

    # Si existe la columna activo, la usamos; si no, seleccionamos todo (compatibilidad)
    if activo_exists:
        query += " WHERE p.activo = 1"
    else:
        query += " WHERE 1=1"

    if proveedor_id:
        query += " AND p.proveedor_id = ?"
        params.append(proveedor_id)

    if filtro:
        filtro = filtro.strip()
        if filtro.isdigit():
            # búsqueda por prefijo en código y substring en nombre
            query += " AND (p.codigo LIKE ? OR LOWER(p.nombre) LIKE ?)"
            params.extend([f"{filtro}%", f"%{filtro.lower()}%"])
        else:
            # búsqueda por substring (nombre o código)
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
        (id_producto,),
    )
    return cursor.fetchone()


@db_connection
def agregar_producto(
    cursor,
    usuario_id,  # <--- NUEVO: ID de quien realiza la acción
    codigo,
    nombre,
    descripcion,
    costo,
    precio,
    stock,
    proveedor_id,
    categoria_id,
):
    """
    Inserta un producto y registra la auditoría.
    """
    try:
        cursor.execute(
            "INSERT INTO productos (codigo, nombre, descripcion, costo, precio, stock, activo, proveedor_id, categoria_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                codigo,
                nombre,
                descripcion,
                costo,
                precio,
                stock,
                1,
                proveedor_id,
                categoria_id,
            ),
        )
        # ---> REGISTRO DE AUDITORÍA <---
        # ---> REGISTRO DE AUDITORÍA <---
        registrar_auditoria(
            cursor,
            usuario_id,
            "PROD_CREADO",
            f"Producto '{nombre}' ({codigo}) agregado.",
        )
        return True
    except sqlite3.IntegrityError:
        return "Error: El código del producto ya existe."


@db_connection
def actualizar_producto(
    cursor,
    usuario_id,  # <--- NUEVO: ID de quien realiza la acción
    id_producto,
    codigo,
    nombre,
    descripcion,
    costo,
    precio,
    stock,
    proveedor_id,
    categoria_id,
):
    # Obtener el nombre actual para el registro de auditoría
    cursor.execute("SELECT nombre FROM productos WHERE id = ?", (id_producto,))
    nombre_antiguo = cursor.fetchone()
    if not nombre_antiguo:
        return "Error: Producto no encontrado."

    try:
        cursor.execute(
            "UPDATE productos SET codigo = ?, nombre = ?, descripcion = ?, costo = ?, precio = ?, stock = ?, proveedor_id = ?, categoria_id = ? WHERE id = ?",
            (
                codigo,
                nombre,
                descripcion,
                costo,
                precio,
                stock,
                proveedor_id,
                categoria_id,
                id_producto,
            ),
        )
        # ---> REGISTRO DE AUDITORÍA <---
        registrar_auditoria(
            cursor,
            usuario_id,
            "PROD_ACTUALIZADO",
            f"Producto ID {id_producto} ('{nombre_antiguo[0]}'). Nuevo nombre: '{nombre}'.",
        )
        return True
    except sqlite3.IntegrityError:
        return "Error: El código del producto ya existe."


@db_connection
def desactivar_producto(
    cursor, usuario_id, id_producto
):  # <--- NUEVO: ID de quien realiza la acción
    # Obtener el nombre del producto para el registro
    cursor.execute("SELECT nombre FROM productos WHERE id = ?", (id_producto,))
    nombre_producto = cursor.fetchone()
    if not nombre_producto:
        return False

    cursor.execute("UPDATE productos SET activo = 0 WHERE id = ?", (id_producto,))

    # ---> REGISTRO DE AUDITORÍA <---
    # ---> REGISTRO DE AUDITORÍA <---
    registrar_auditoria(
        cursor,
        usuario_id,
        "PROD_DESACTIVADO",
        f"Producto ID {id_producto} ('{nombre_producto[0]}') desactivado.",
    )
    return True


@db_connection
def registrar_venta(cursor, usuario_id, total, carrito, tipo_pago, deudor_id=None):
    try:
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        saldo_pendiente = total if tipo_pago == "Credito" else 0.0
        cursor.execute(
            "INSERT INTO ventas (usuario_id, fecha_hora, total, tipo_pago, deudor_id, saldo_pendiente) VALUES (?, ?, ?, ?, ?, ?)",
            (usuario_id, fecha_hora, total, tipo_pago, deudor_id, saldo_pendiente),
        )
        venta_id = cursor.lastrowid

        # Insertar detalles de la venta
        for codigo, item in carrito.items():
            cursor.execute("SELECT id FROM productos WHERE codigo = ?", (codigo,))
            producto_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO detalles_venta (venta_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                (venta_id, producto_id, item["cantidad"], item["precio"]),
            )
            # Actualizar stock
            cursor.execute(
                "UPDATE productos SET stock = stock - ? WHERE id = ?",
                (item["cantidad"], producto_id),
            )

        # Si es venta a crédito, actualizar saldo del deudor
        if tipo_pago == "Credito" and deudor_id is not None:
            cursor.execute(
                "UPDATE deudores SET saldo = saldo + ? WHERE id = ?", (total, deudor_id)
            )

        # Registro de auditoría
        tipo = "Crédito" if tipo_pago == "Credito" else "Contado"
        registrar_auditoria(
            cursor,
            usuario_id,
            "VENTA_REGISTRADA",
            f"Venta ID {venta_id}. Total: {total:.2f}. Tipo: {tipo}.",
        )

        return venta_id
    except sqlite3.Error as e:
        raise e


@db_connection
def obtener_info_venta(cursor, venta_id):
    cursor.execute("SELECT fecha_hora, total FROM ventas WHERE id = ?", (venta_id,))
    return cursor.fetchone()


@db_connection
def obtener_ventas_del_dia(cursor):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        SELECT v.id, v.fecha_hora, u.nombre_usuario, v.total
        FROM ventas v JOIN usuarios u ON v.usuario_id = u.id
        WHERE DATE(v.fecha_hora) = ? ORDER BY v.fecha_hora DESC
    """,
        (fecha_hoy,),
    )
    return cursor.fetchall()


@db_connection
def obtener_resumen_ventas_dia(cursor, usuario_id):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT SUM(total) FROM ventas WHERE usuario_id = ? AND DATE(fecha_hora) = ? AND tipo_pago = 'Contado'",
        (usuario_id, fecha_hoy),
    )
    resultado = cursor.fetchone()[0]
    return resultado if resultado is not None else 0.0


@db_connection
def obtener_usuarios(cursor):
    cursor.execute(
        "SELECT id, nombre_usuario, rol FROM usuarios ORDER BY nombre_usuario ASC"
    )
    return cursor.fetchall()


@db_connection
def agregar_usuario(cursor, nombre_usuario, contrasena, rol):
    try:
        salt = os.urandom(16)
        contrasena_hash = hashlib.pbkdf2_hmac(
            "sha256", contrasena.encode("utf-8"), salt, 100000
        )
        cursor.execute(
            "INSERT INTO usuarios (nombre_usuario, contrasena_hash, contrasena_salt, rol) VALUES (?, ?, ?, ?)",
            (
                nombre_usuario,
                binascii.hexlify(contrasena_hash).decode("utf-8"),
                binascii.hexlify(salt).decode("utf-8"),
                rol,
            ),
        )
        return True
    except sqlite3.IntegrityError:
        return "Error: El nombre de usuario ya existe."


@db_connection
def actualizar_contrasena(cursor, id_usuario, nueva_contrasena):
    nuevo_salt = os.urandom(16)
    nueva_contrasena_hash = hashlib.pbkdf2_hmac(
        "sha256", nueva_contrasena.encode("utf-8"), nuevo_salt, 100000
    )
    cursor.execute(
        "UPDATE usuarios SET contrasena_hash = ?, contrasena_salt = ? WHERE id = ?",
        (
            binascii.hexlify(nueva_contrasena_hash).decode("utf-8"),
            binascii.hexlify(nuevo_salt).decode("utf-8"),
            id_usuario,
        ),
    )
    return True


@db_connection
def eliminar_usuario(
    cursor, id_usuario_a_eliminar, usuario_admin_id
):  # <--- Nuevo parámetro para el Admin que elimina

    # 1. Obtener el nombre para el log antes de eliminar
    cursor.execute(
        "SELECT nombre_usuario FROM usuarios WHERE id = ?", (id_usuario_a_eliminar,)
    )
    nombre_usuario = cursor.fetchone()
    if not nombre_usuario:
        return False

    # 2. Eliminar el usuario
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario_a_eliminar,))

    # ---> REGISTRO DE AUDITORÍA <---
    # ---> REGISTRO DE AUDITORÍA <---
    registrar_auditoria(
        cursor,
        usuario_admin_id,
        "USUARIO_ELIMINADO",
        f"Usuario '{nombre_usuario[0]}' (ID: {id_usuario_a_eliminar}) fue eliminado.",
    )
    return True


@db_connection
def obtener_ventas_por_rango(cursor, fecha_inicio, fecha_fin):
    cursor.execute(
        "SELECT v.id, v.fecha_hora, u.nombre_usuario, v.total FROM ventas v JOIN usuarios u ON v.usuario_id = u.id WHERE DATE(v.fecha_hora) BETWEEN ? AND ? ORDER BY v.fecha_hora DESC",
        (fecha_inicio, fecha_fin),
    )
    return cursor.fetchall()


@db_connection
def obtener_productos_mas_vendidos(cursor, fecha_inicio, fecha_fin):
    cursor.execute(
        "SELECT p.nombre, SUM(dv.cantidad) as total_vendido FROM detalles_venta dv JOIN productos p ON dv.producto_id = p.id JOIN ventas v ON dv.venta_id = v.id WHERE DATE(v.fecha_hora) BETWEEN ? AND ? GROUP BY p.nombre ORDER BY total_vendido DESC",
        (fecha_inicio, fecha_fin),
    )
    return cursor.fetchall()


@db_connection
def obtener_detalle_de_venta(cursor, venta_id):
    cursor.execute(
        "SELECT p.nombre, dv.cantidad, (dv.cantidad * dv.precio_unitario) as subtotal FROM detalles_venta dv JOIN productos p ON dv.producto_id = p.id WHERE dv.venta_id = ?",
        (venta_id,),
    )
    return cursor.fetchall()


@db_connection
def obtener_proveedores(cursor, incluir_inactivos=False):
    """Obtiene la lista de proveedores (solo activos por defecto)."""
    
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
def agregar_proveedor(cursor, nombre, telefono, email, direccion):
    """Agrega un nuevo proveedor a la base de datos."""
    try:
        cursor.execute(
            "INSERT INTO proveedores (nombre, telefono, email, direccion, activo) VALUES (?, ?, ?, ?, 1)",
            (nombre, telefono, email, direccion),
        )
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe un proveedor con ese nombre."


@db_connection
def actualizar_proveedor(cursor, id_proveedor, nombre, telefono, email, direccion):
    """Actualiza los datos de un proveedor existente."""
    try:
        cursor.execute(
            "UPDATE proveedores SET nombre = ?, telefono = ?, email = ?, direccion = ? WHERE id = ?",
            (nombre, telefono, email, direccion, id_proveedor),
        )
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe otro proveedor con el mismo nombre."


@db_connection
def desactivar_proveedor(cursor, id_proveedor):
    """Realiza la eliminación lógica de un proveedor (activo = 0)."""
    
    cursor.execute("UPDATE proveedores SET activo = 0 WHERE id = ?", (id_proveedor,))
    
    if cursor.rowcount > 0:
        return True
    else:
        return "Error: No se encontró el proveedor."


@db_connection
def eliminar_proveedor(cursor, id_proveedor):
    cursor.execute(
        "SELECT COUNT(*) FROM productos WHERE proveedor_id = ?", (id_proveedor,)
    )
    num_productos = cursor.fetchone()[0]

    if num_productos > 0:
        return False

    try:
        cursor.execute("DELETE FROM proveedores WHERE id = ?", (id_proveedor,))
        return True
    except sqlite3.Error as e:
        print(f"Error al intentar eliminar proveedor: {e}")
        return False

@db_connection
def registrar_compra(cursor, proveedor_id, total_costo, carrito_compra):
    try:
        fecha = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO compras (proveedor_id, fecha, total_costo) VALUES (?, ?, ?)",
            (proveedor_id, fecha, total_costo),
        )
        compra_id = cursor.lastrowid
        for codigo, item in carrito_compra.items():
            cursor.execute(
                "SELECT id, stock FROM productos WHERE codigo = ?", (codigo,)
            )
            producto_id, stock_actual = cursor.fetchone()
            cursor.execute(
                "INSERT INTO detalles_compra (compra_id, producto_id, cantidad, costo_unitario) VALUES (?, ?, ?, ?)",
                (compra_id, producto_id, item["cantidad"], item["costo"]),
            )
            nuevo_stock = stock_actual + item["cantidad"]
            cursor.execute(
                "UPDATE productos SET stock = ? WHERE id = ?",
                (nuevo_stock, producto_id),
            )
        return True
    except sqlite3.Error as e:
        raise e


@db_connection
def obtener_deudores(cursor):
    cursor.execute(
        "SELECT id, nombre, telefono, saldo FROM deudores ORDER BY nombre ASC"
    )
    return cursor.fetchall()


@db_connection
def obtener_deudor_por_id(cursor, deudor_id):
    cursor.execute(
        "SELECT id, nombre, telefono, direccion, notas, saldo FROM deudores WHERE id = ?",
        (deudor_id,),
    )
    return cursor.fetchone()


@db_connection
def agregar_deudor(cursor, nombre, telefono, direccion, notas):
    try:
        cursor.execute(
            "INSERT INTO deudores (nombre, telefono, direccion, notas) VALUES (?, ?, ?, ?)",
            (nombre, telefono, direccion, notas),
        )
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe un deudor con ese nombre."


@db_connection
def actualizar_deudor(cursor, deudor_id, nombre, telefono, direccion, notas):
    try:
        cursor.execute(
            "UPDATE deudores SET nombre = ?, telefono = ?, direccion = ?, notas = ? WHERE id = ?",
            (nombre, telefono, direccion, notas, deudor_id),
        )
        return True
    except sqlite3.IntegrityError:
        return "Error: Ya existe un deudor con ese nombre."


@db_connection
def eliminar_deudor(cursor, deudor_id):
    cursor.execute("SELECT saldo FROM deudores WHERE id = ?", (deudor_id,))
    saldo = cursor.fetchone()
    if saldo and saldo[0] > 0.0:
        return "Error: No se puede eliminar un deudor con saldo pendiente."
    cursor.execute("DELETE FROM deudores WHERE id = ?", (deudor_id,))
    return True


@db_connection
def registrar_pago_deudor(cursor, deudor_id, venta_id, monto):
    try:
        cursor.execute("SELECT saldo_pendiente FROM ventas WHERE id = ?", (venta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return "Error: La venta especificada no existe."
        saldo_venta = resultado[0]
        if monto > saldo_venta:
            return "Error: El monto del pago no puede ser mayor al saldo pendiente de la deuda."

        fecha = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "INSERT INTO pagos_deudores (deudor_id, venta_id, fecha, monto) VALUES (?, ?, ?, ?)",
            (deudor_id, venta_id, fecha, monto),
        )
        cursor.execute(
            "UPDATE ventas SET saldo_pendiente = saldo_pendiente - ? WHERE id = ?",
            (monto, venta_id),
        )
        cursor.execute(
            "UPDATE deudores SET saldo = saldo - ? WHERE id = ?", (monto, deudor_id)
        )
        return True
    except sqlite3.Error as e:
        raise e


@db_connection
def obtener_ventas_deudor(cursor, deudor_id):
    cursor.execute(
        "SELECT id, fecha_hora, total FROM ventas WHERE deudor_id = ? AND tipo_pago = 'Credito' ORDER BY fecha_hora DESC",
        (deudor_id,),
    )
    return cursor.fetchall()


@db_connection
def obtener_deudas_pendientes_deudor(cursor, deudor_id):
    cursor.execute(
        "SELECT id, fecha_hora, total, saldo_pendiente FROM ventas WHERE deudor_id = ? AND saldo_pendiente > 0 ORDER BY fecha_hora ASC",
        (deudor_id,),
    )
    return cursor.fetchall()


@db_connection
def obtener_pagos_de_una_venta(cursor, venta_id):
    cursor.execute(
        "SELECT fecha, monto FROM pagos_deudores WHERE venta_id = ? ORDER BY fecha DESC",
        (venta_id,),
    )
    return cursor.fetchall()


@db_connection
def obtener_deudas_pagadas_deudor(cursor, deudor_id):
    cursor.execute(
        "SELECT id, fecha_hora, total FROM ventas WHERE deudor_id = ? AND tipo_pago = 'Credito' AND saldo_pendiente <= 0 ORDER BY fecha_hora DESC",
        (deudor_id,),
    )
    return cursor.fetchall()


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
def obtener_categorias(cursor):
    cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre ASC")
    return cursor.fetchall()


@db_connection
def agregar_categoria(cursor, nombre):
    try:
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        return True
    except sqlite3.IntegrityError:
        return "Error: Esa categoría ya existe."


@db_connection
def eliminar_categoria(cursor, id_categoria):
    try:
        cursor.execute("DELETE FROM categorias WHERE id = ?", (id_categoria,))
        return True
    except sqlite3.IntegrityError:
        # Esto ocurre si la restricción de clave foránea falla.
        return (
            "Error: No se puede eliminar la categoría porque tiene productos asignados."
        )


@db_connection
def obtener_compras_por_rango(cursor, fecha_inicio, fecha_fin):
    # --- CORRECCIÓN: Cambiamos a LEFT JOIN para más flexibilidad ---
    query = """
        SELECT c.id, c.fecha, IFNULL(p.nombre, 'PROVEEDOR ELIMINADO'), c.total_costo
        FROM compras c
        LEFT JOIN proveedores p ON c.proveedor_id = p.id
        WHERE DATE(c.fecha) BETWEEN ? AND ?
        ORDER BY c.fecha DESC
    """
    cursor.execute(query, (fecha_inicio, fecha_fin))
    return cursor.fetchall()


# Agrégala al final de tu archivo database.py


@db_connection
def obtener_ganancias_por_producto(cursor, fecha_inicio, fecha_fin):
    """
    Calcula los ingresos, costos y ganancia neta agrupados por cada producto
    en un rango de fechas, ordenado por la ganancia.
    """
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


# Agrégala al final de tu archivo database.py


@db_connection
def obtener_detalle_de_compra(cursor, compra_id):
    """
    Busca los productos, cantidades y costos de una compra específica.
    """
    query = """
        SELECT p.nombre, dc.cantidad, dc.costo_unitario, (dc.cantidad * dc.costo_unitario) as subtotal
        FROM detalles_compra dc
        JOIN productos p ON dc.producto_id = p.id
        WHERE dc.compra_id = ?
    """
    cursor.execute(query, (compra_id,))
    return cursor.fetchall()


def registrar_auditoria(cursor, usuario_id, accion, descripcion=""):
    """
    Registra una acción crítica en la tabla de auditoría.
    NOTA: Esta función NO lleva decorador porque se llama desde otras funciones decoradas.
    """
    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Obtener el rol del usuario
    cursor.execute("SELECT rol FROM usuarios WHERE id = ?", (usuario_id,))
    resultado = cursor.fetchone()
    rol = resultado[0] if resultado else "desconocido"
    
    cursor.execute(
        "INSERT INTO registro_auditoria (usuario_id, fecha_hora, accion, descripcion) VALUES (?, ?, ?, ?)",
        (usuario_id, fecha_hora, accion, descripcion),
    )



@db_connection
def obtener_registro_auditoria(cursor, limite=500):
    """
    Recupera los registros de auditoría más recientes.
    """
    query = """
        SELECT 
            ra.fecha_hora, 
            u.nombre_usuario, 
            ra.accion, 
            ra.descripcion
        FROM registro_auditoria ra
        JOIN usuarios u ON ra.usuario_id = u.id
        ORDER BY ra.fecha_hora DESC
        LIMIT ?
    """
    cursor.execute(query, (limite,))
    return cursor.fetchall()