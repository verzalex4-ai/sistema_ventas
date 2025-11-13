# product_management_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from database import (
    obtener_productos,
    obtener_producto_por_id,
    agregar_producto,
    actualizar_producto,
    desactivar_producto,
    obtener_proveedores,
    obtener_categorias,
    agregar_categoria,
    eliminar_categoria,
)
from base_dialog import BaseDialog


class ProductManagementView:
    # MODIFICADO: Ahora acepta 'main_window' y 'usuario_id'
    def __init__(self, parent_frame, main_window, usuario_id):
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.usuario_id = usuario_id  # <--- ID del usuario para auditoría

        ttk.Label(
            self.parent_frame,
            text="Gestión de Inventario",
            font=("Helvetica", 16, "bold"),
        ).pack(pady=10)

        control_frame = ttk.Frame(self.parent_frame)
        control_frame.pack(fill=X, padx=10, pady=5)

        ttk.Button(
            control_frame,
            text="Añadir Nuevo Producto",
            command=self.abrir_formulario_producto,
            bootstyle="success",
        ).pack(side=LEFT)
        ttk.Button(
            control_frame,
            text="Modificar Seleccionado",
            command=self.editar_producto_seleccionado,
            bootstyle="info",
        ).pack(side=LEFT, padx=10)
        ttk.Button(
            control_frame,
            text="Eliminar producto",
            command=self.desactivar_producto_seleccionado,
            bootstyle="danger",
        ).pack(side=LEFT)
        ttk.Button(
            control_frame,
            text="Gestionar Categorías",
            command=self.abrir_gestion_categorias,
            bootstyle="secondary",
        ).pack(side=LEFT, padx=10)

        columns = (
            "id",
            "codigo",
            "nombre",
            "costo",
            "precio",
            "stock",
            "proveedor",
            "categoria",
        )
        self.products_tree = ttk.Treeview(
            self.parent_frame, columns=columns, show="headings", bootstyle="primary"
        )

        self.products_tree.heading("id", text="ID")
        self.products_tree.heading("codigo", text="Código")
        self.products_tree.heading("nombre", text="Nombre")
        self.products_tree.heading("costo", text="Costo")
        self.products_tree.heading("precio", text="Precio Venta")
        self.products_tree.heading("stock", text="Stock")
        self.products_tree.heading("proveedor", text="Proveedor")
        self.products_tree.heading("categoria", text="Categoría")

        self.products_tree.column("id", width=40, anchor=CENTER)
        self.products_tree.column("codigo", width=100, anchor=W)
        self.products_tree.column("nombre", width=220, anchor=W)
        self.products_tree.column("costo", width=80, anchor=E)
        self.products_tree.column("precio", width=90, anchor=E)
        self.products_tree.column("stock", width=60, anchor=E)
        self.products_tree.column("proveedor", width=150, anchor=W)
        self.products_tree.column("categoria", width=150, anchor=W)

        self.products_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.cargar_productos()

    def cargar_productos(self):
        # Limpiar la tabla antes de cargar los productos
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        # Obtener los productos de la base de datos
        productos = obtener_productos(incluir_id=True)

        if not productos:
            return  # Si no hay productos, termina la función sin error

        # Insertar cada producto en el Treeview
        for producto in productos:
            try:
                # Manejo seguro de valores nulos y posibles índices faltantes
                id_val = (
                    producto[0] if len(producto) > 0 and producto[0] is not None else ""
                )
                codigo_val = (
                    producto[1] if len(producto) > 1 and producto[1] is not None else ""
                )
                nombre_val = (
                    producto[2] if len(producto) > 2 and producto[2] is not None else ""
                )
                costo_val = (
                    float(producto[3])
                    if len(producto) > 3 and producto[3] is not None
                    else 0.0
                )
                precio_val = (
                    float(producto[4])
                    if len(producto) > 4 and producto[4] is not None
                    else 0.0
                )
                stock_val = (
                    producto[5] if len(producto) > 5 and producto[5] is not None else 0
                )
                proveedor_val = (
                    producto[6] if len(producto) > 6 and producto[6] is not None else ""
                )
                categoria_val = (
                    producto[7] if len(producto) > 7 and producto[7] is not None else ""
                )

                # Formatear costo y precio
                costo_f = f"${costo_val:.2f}"
                precio_f = f"${precio_val:.2f}"

                # Insertar en el Treeview
                self.products_tree.insert(
                    "",
                    END,
                    values=(
                        id_val,
                        codigo_val,
                        nombre_val,
                        costo_f,
                        precio_f,
                        stock_val,
                        proveedor_val,
                        categoria_val,
                    ),
                )

            except Exception as e:
                print(f"Error al cargar producto: {e}")

    def abrir_formulario_producto(self, producto=None):
        # MODIFICADO: Pasamos self.usuario_id al formulario
        form = ProductForm(
            self.parent_frame, producto, self.cargar_productos, self.usuario_id
        )
        self.parent_frame.wait_window(form)

    def abrir_gestion_categorias(self):
        dialog = CategoryManagerDialog(self.parent_frame, self.cargar_productos, self.usuario_id)
        self.parent_frame.wait_window(dialog)

    def editar_producto_seleccionado(self):
        # 1. Obtener la referencia de la ventana principal para la Modalidad.
        # Usamos self.products_tree porque es el widget de la tabla visible.
        root_window = self.products_tree.winfo_toplevel()

        seleccion = self.products_tree.focus()

        if not seleccion:
            # 2. Aplicar la Modalidad al mensaje de "Sin Selección"
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un producto para modificar.",
                parent=root_window,
            )
            return

        id_producto = self.products_tree.item(seleccion, "values")[0]
        producto_completo = obtener_producto_por_id(id_producto)

        if producto_completo:
            self.abrir_formulario_producto(producto_completo)
        else:
            # 3. Aplicar la Modalidad al mensaje de "Error"
            messagebox.showerror(
                "Error",
                "No se pudieron obtener los datos del producto.",
                parent=root_window,
            )

    def desactivar_producto_seleccionado(self):
        # --- CORRECCIÓN CLAVE ---
        # 1. Obtener la referencia de la ventana principal para la Modalidad.
        try:
            root_window = self.products_tree.winfo_toplevel()
        except AttributeError:
            root_window = self.tree.winfo_toplevel()

        # ------------------------

        seleccion = self.products_tree.focus()

        if not seleccion:
            # 2. Aplicamos la Modalidad al mensaje de Sin Selección
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un producto.",
                parent=root_window,
            )
            return

        id_producto = self.products_tree.item(seleccion, "values")[0]
        # Nota: Asumiendo que el nombre del producto es el índice 2
        nombre_producto = self.products_tree.item(seleccion, "values")[2]

        # 3. Aplicamos la Modalidad al cuadro de confirmación
        if messagebox.askyesno(
            "Confirmar", f"¿Eliminar '{nombre_producto}'?", parent=root_window
        ):

            # MODIFICADO: Ahora pasamos self.usuario_id como primer argumento
            if desactivar_producto(self.usuario_id, id_producto):
                # 4. Aplicamos la Modalidad al mensaje de éxito
                messagebox.showinfo(
                    "Éxito", "Producto desactivado.", parent=root_window
                )
                self.cargar_productos()
            else:
                # 5. Aplicamos la Modalidad al mensaje de error
                messagebox.showerror(
                    "Error", "No se pudo desactivar el producto.", parent=root_window
                )


# --------------------------------------------
# FORMULARIO DE PRODUCTO
# --------------------------------------------
class ProductForm(BaseDialog):
    # MODIFICADO: Ahora acepta 'usuario_id'
    def __init__(self, parent, producto, callback_actualizar, usuario_id):
        title = "Editar Producto" if producto else "Formulario de Producto"
        super().__init__(parent, title=title)

        self.producto = producto
        self.callback = callback_actualizar
        self.usuario_id = usuario_id  # <--- ID del usuario para auditoría

        self.proveedores_map = {prov[1]: prov[0] for prov in obtener_proveedores()}
        self.categorias_map = {cat[1]: cat[0] for cat in obtener_categorias()}

        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(expand=True, fill=BOTH)

        campos = [
            "Código:",
            "Nombre:",
            "Descripción:",
            "Costo:",
            "Precio:",
            "Stock:",
            "Proveedor:",
            "Categoría:",
        ]
        self.entries = {}
        for i, campo in enumerate(campos):
            ttk.Label(form_frame, text=campo).grid(row=i, column=0, sticky="w", pady=5)
            if campo == "Proveedor:":
                self.entries[campo] = ttk.Combobox(
                    form_frame,
                    values=list(self.proveedores_map.keys()),
                    state="readonly",
                    width=38,
                )
            elif campo == "Categoría:":
                self.entries[campo] = ttk.Combobox(
                    form_frame,
                    values=list(self.categorias_map.keys()),
                    state="readonly",
                    width=38,
                )
            else:
                self.entries[campo] = ttk.Entry(form_frame, width=40)
            self.entries[campo].grid(row=i, column=1, sticky="ew", pady=5)

        if self.producto:
            self.entries["Código:"].insert(0, self.producto[1])
            self.entries["Nombre:"].insert(0, self.producto[2])
            self.entries["Descripción:"].insert(0, self.producto[3])
            self.entries["Costo:"].insert(0, self.producto[4])
            self.entries["Precio:"].insert(0, self.producto[5])
            self.entries["Stock:"].insert(0, self.producto[6])

            id_proveedor_actual = self.producto[7]
            nombre_proveedor_actual = next(
                (
                    nombre
                    for nombre, id_prov in self.proveedores_map.items()
                    if id_prov == id_proveedor_actual
                ),
                None,
            )
            if nombre_proveedor_actual:
                self.entries["Proveedor:"].set(nombre_proveedor_actual)

            id_categoria_actual = self.producto[8]
            nombre_categoria_actual = next(
                (
                    nombre
                    for nombre, id_cat in self.categorias_map.items()
                    if id_cat == id_categoria_actual
                ),
                None,
            )
            if nombre_categoria_actual:
                self.entries["Categoría:"].set(nombre_categoria_actual)

        ttk.Button(
            form_frame, text="Guardar", command=self.guardar, bootstyle="success"
        ).grid(row=len(campos), column=0, columnspan=2, pady=15)

    def guardar(self):
        try:
            codigo = self.entries["Código:"].get()
            nombre = self.entries["Nombre:"].get()
            descripcion = self.entries["Descripción:"].get()

            # Costo: Si está vacío, se asume 0.0. Si no está vacío, se convierte a float.
            costo_str = self.entries["Costo:"].get().strip()
            costo = float(costo_str) if costo_str else 0.0

            # Precio: Si está vacío, se asume 0.0. Si no está vacío, se convierte a float.
            precio_str = self.entries["Precio:"].get().strip()
            precio = float(precio_str) if precio_str else 0.0

            # Stock: Si está vacío, se asume 0. Si no está vacío, se convierte a int.
            stock_str = self.entries["Stock:"].get().strip()
            stock = int(stock_str) if stock_str else 0

            nombre_proveedor = self.entries["Proveedor:"].get()
            nombre_categoria = self.entries["Categoría:"].get()

        except (ValueError, TypeError):
            # Este bloque se activa si, por ejemplo, ingresan texto en Costo/Precio/Stock
            messagebox.showerror(
                "Error de Entrada",
                "Costo, Precio y Stock deben ser números válidos. Por favor, verifica el formato.",
                parent=self,
            )
            return

        # 2. Validación de campos obligatorios (Código y Nombre)
        if not all([codigo, nombre]):
            messagebox.showerror(
                "Campos Vacíos", "Código y Nombre son obligatorios.", parent=self
            )
            return

        # 3. Mapeo de IDs (permite que sean None si no se seleccionó nada)
        proveedor_id = self.proveedores_map.get(nombre_proveedor)
        categoria_id = self.categorias_map.get(nombre_categoria)

        # 4. Llamada a la base de datos
        if self.producto:
            id_producto = self.producto[0]
            # MODIFICADO: Añadido self.usuario_id como primer argumento
            resultado = actualizar_producto(
                self.usuario_id,
                id_producto,
                codigo,
                nombre,
                descripcion,
                costo,
                precio,
                stock,
                proveedor_id,
                categoria_id,
            )
        else:
            # MODIFICADO: Añadido self.usuario_id como primer argumento
            resultado = agregar_producto(
                self.usuario_id,
                codigo,
                nombre,
                descripcion,
                costo,
                precio,
                stock,
                proveedor_id,
                categoria_id,
            )

        # 5. Manejo del resultado
        if resultado is True:
            messagebox.showinfo("Éxito", "Producto guardado.", parent=self)
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", str(resultado), parent=self)


# --------------------------------------------
# GESTIÓN DE CATEGORÍAS
# --------------------------------------------
class CategoryManagerDialog(BaseDialog):
    def __init__(self, parent, callback_refrescar, usuario_id):
        super().__init__(parent, title="Gestionar Categorías")
        self.callback = callback_refrescar
        self.usuario_id = usuario_id

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=True)

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        columns = ("id", "nombre")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=10
        )
        # 1. Configurar la alineación de las cabeceras
        self.tree.heading("id", text="ID", anchor=CENTER)
        self.tree.heading("nombre", text="Nombre de la Categoría", anchor=W)

        # 2. Configurar la alineación del CONTENIDO
        self.tree.column("id", width=50, anchor=CENTER)
        self.tree.column("nombre", width=250, anchor=W)

        self.tree.pack(fill=BOTH, expand=True)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=LEFT, fill=Y)

        ttk.Button(
            button_frame,
            text="Añadir",
            command=self.anadir_categoria,
            bootstyle="success",
        ).pack(fill=X, pady=2)
        ttk.Button(
            button_frame,
            text="Eliminar",
            command=self.eliminar_seleccion,
            bootstyle="danger",
        ).pack(fill=X, pady=2)
        ttk.Button(
            button_frame, text="Cerrar", command=self.cerrar, bootstyle="secondary"
        ).pack(fill=X, side=BOTTOM)

        self.cargar_categorias()
        self.protocol("WM_DELETE_WINDOW", self.cerrar)

    def cargar_categorias(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for cat in obtener_categorias():
            self.tree.insert("", END, values=cat)

    def anadir_categoria(self):
        while True:
            nombre = simpledialog.askstring(
                "Nueva Categoría", "Nombre de la nueva categoría:", parent=self
            )
            if nombre is None:
                return
            if not nombre.strip():
                messagebox.showwarning(
                    "Campo Vacío",
                    "El nombre de la categoría no puede estar vacío. Por favor, inténtalo de nuevo.",
                    parent=self,
                )
                continue
            nombre_limpio = nombre.strip()
            resultado = agregar_categoria(self.usuario_id, nombre_limpio)
            if resultado is True:
                messagebox.showinfo(
                    "Éxito", f"Categoría '{nombre_limpio}' añadida.", parent=self
                )   
                self.cargar_categorias()
                break
            else:
                messagebox.showerror("Error", resultado, parent=self)

    def eliminar_seleccion(self):
        seleccion = self.tree.focus()
        if not seleccion:
            messagebox.showwarning(
                "Sin selección",
                "Por favor, selecciona una categoría para eliminar.",
                parent=self,
            )
            return

        cat_id = self.tree.item(seleccion, "values")[0]
        cat_nombre = self.tree.item(seleccion, "values")[1]

        if messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar la categoría '{cat_nombre}'?\nLos productos en esta categoría quedarán como 'Sin Categoría'.",
            parent=self,
        ):
            resultado = eliminar_categoria(self.usuario_id, cat_id)
            if resultado is True:
                self.cargar_categorias()
            else:
                messagebox.showerror("Error", resultado, parent=self)

    def cerrar(self):
        self.callback()
        self.destroy()