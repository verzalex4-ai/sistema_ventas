# pos_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import (
    obtener_productos,
    registrar_venta,
    obtener_deudores,
    obtener_categorias,
)  # <-- Nueva importación
from debtor_management_view import DebtorForm
from ticket_generator import generar_ticket_pdf
from base_dialog import BaseDialog


class POSView:
    def __init__(self, parent_frame, usuario_id):
        self.parent_frame = parent_frame
        self.usuario_id = usuario_id
        self.carrito = {}
        self.stock_original_productos = (
            {}
        )  # Diccionario código_producto -> stock_original

        self.products_frame = ttk.Frame(self.parent_frame)
        self.products_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

        self.cart_frame = ttk.Frame(self.parent_frame, width=350)
        self.cart_frame.pack(side=RIGHT, fill=Y, padx=5, pady=5)
        self.cart_frame.pack_propagate(False)

        ttk.Label(
            self.products_frame, text="Punto de Venta", font=("Helvetica", 16, "bold")
        ).pack(pady=5)

        # --- NUEVO FRAME PARA FILTROS ---
        filter_frame = ttk.Frame(self.products_frame)
        filter_frame.pack(fill=X, pady=5)

        # Filtro por Categoría
        ttk.Label(filter_frame, text="Categoría:").pack(side=LEFT, padx=(0, 5))
        self.combo_categorias = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.combo_categorias.pack(side=LEFT)
        self.combo_categorias.bind("<<ComboboxSelected>>", self.filtrar_productos)

        # Búsqueda por Texto
        ttk.Label(filter_frame, text="Buscar:", style="padding-left:10px;").pack(
            side=LEFT, padx=(10, 5)
        )
        self.search_entry = ttk.Entry(filter_frame)
        self.search_entry.pack(side=LEFT, fill=X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.filtrar_productos)

        # Cargar categorías en el combobox
        self.cargar_categorias_combo()

        # --- FIN DE FILTROS ---

        columns = ("codigo", "nombre", "precio", "stock")
        self.products_tree = ttk.Treeview(
            self.products_frame, columns=columns, show="headings", bootstyle="primary"
        )
        self.products_tree.heading("codigo", text="Código")
        self.products_tree.heading("nombre", text="Nombre")
        self.products_tree.heading("precio", text="Precio")
        self.products_tree.heading("stock", text="Stock")
        self.products_tree.column("codigo", width=100, anchor=CENTER)
        self.products_tree.column("nombre", width=250)
        self.products_tree.column("precio", width=80, anchor=E)
        self.products_tree.column("stock", width=80, anchor=E)
        self.products_tree.pack(fill=BOTH, expand=True, pady=(5, 0))
        # ...
        self.products_tree.bind("<Double-1>", self.agregar_al_carrito)

        ttk.Label(self.cart_frame, text="Carrito", font=("Helvetica", 16, "bold")).pack(
            pady=5
        )

        cart_columns = ("nombre", "cantidad", "subtotal")
        self.cart_tree = ttk.Treeview(
            self.cart_frame, columns=cart_columns, show="headings", bootstyle="success"
        )
        self.cart_tree.heading("nombre", text="Producto")
        self.cart_tree.heading("cantidad", text="Cant.")
        self.cart_tree.heading("subtotal", text="Subtotal")
        self.cart_tree.column("nombre", width=150)
        self.cart_tree.column("cantidad", width=50, anchor=E)
        self.cart_tree.column("subtotal", width=80, anchor=E)
        self.cart_tree.pack(fill=BOTH, expand=True)
        self.cart_tree.bind("<Double-1>", self.remover_del_carrito)

        total_frame = ttk.Frame(self.cart_frame)
        total_frame.pack(side=BOTTOM, fill=X, pady=10)

        self.total_label = ttk.Label(
            total_frame, text="TOTAL: $0.00", font=("Helvetica", 14, "bold")
        )
        self.total_label.pack(pady=5)

        ttk.Button(
            total_frame,
            text="Finalizar Venta",
            command=self.finalizar_venta,
            bootstyle="success",
        ).pack(fill=X, ipady=5, pady=(5, 0))
        ttk.Button(
            total_frame,
            text="Cancelar",
            command=self.cancelar_venta,
            bootstyle="danger",
        ).pack(fill=X, ipady=5, pady=(5, 0))

        self.cargar_productos()

    # --- NUEVO MÉTODO ---
    def cargar_categorias_combo(self):
        self.categorias_map = {cat[1]: cat[0] for cat in obtener_categorias()}
        # Añadimos la opción para ver todos los productos
        opciones = ["Mostrar Todas"] + list(self.categorias_map.keys())
        self.combo_categorias["values"] = opciones
        self.combo_categorias.current(0)  # Seleccionamos "Mostrar Todas" por defecto

    # --- MÉTODO MODIFICADO ---
    def cargar_productos(self, filtro_texto="", categoria_id=None):
        # 1. Limpiamos la tabla
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        # 2. Obtenemos los productos de la BD
        productos = obtener_productos(filtro=filtro_texto, categoria_id=categoria_id)

        # 3. Iteramos y ajustamos el stock
        for producto in productos:
            # Los datos de la BD vienen así: (codigo, nombre, precio, stock)
            codigo, nombre, precio, stock_bd = (
                producto[0],
                producto[1],
                producto[2],
                producto[3],
            )

            # --- VERIFICACIÓN Y AJUSTE DEL STOCK ---

            # Chequeamos si este producto ya está en el carrito
            if codigo in self.carrito:
                # Si está, restamos la cantidad que hay en el carrito al stock de la BD
                cantidad_en_carrito = self.carrito[codigo]["cantidad"]
                stock_visual = stock_bd - cantidad_en_carrito

                # Opcional: Aseguramos que el stock visual no sea negativo
                if stock_visual < 0:
                    stock_visual = 0
            else:
                # Si no está en el carrito, el stock visual es el de la BD
                stock_visual = stock_bd

            # ---------------------------------------

            # 4. Insertamos en el Treeview con el stock ajustado
            # Usamos stock_visual en lugar de producto[3]
            self.products_tree.insert(
                "", END, values=(codigo, nombre, f"{precio:.2f}", stock_visual)
            )

    # --- MÉTODO MODIFICADO Y RENOMBRADO ---
    def filtrar_productos(self, event=None):
        filtro_texto = self.search_entry.get().strip()

        categoria_nombre = self.combo_categorias.get()
        categoria_id = None
        if categoria_nombre and categoria_nombre != "Mostrar Todas":
            categoria_id = self.categorias_map.get(categoria_nombre)

        self.cargar_productos(filtro_texto=filtro_texto, categoria_id=categoria_id)

    def finalizar_venta(self):
        root_window = self.parent_frame.winfo_toplevel()  # Obtener la ventana principal

        if not self.carrito:
            # --- CÓDIGO CORREGIDO: Añadir parent=root_window ---
            messagebox.showwarning(
                "Carrito Vacío",
                "No hay productos en el carrito para vender.",
                parent=root_window,
            )
            return

        total_str = self.total_label.cget("text").replace("TOTAL: $", "")
        total = float(total_str)

        # 1. El diálogo de pago ya es modal gracias a BaseDialog/wait_window
        dialogo_pago = PaymentDialog(self.parent_frame, f"${total:.2f}")
        self.parent_frame.wait_window(dialogo_pago)

        resultado = dialogo_pago.resultado
        if not resultado:
            return

        tipo_pago = resultado.get("tipo_pago")
        deudor_id = resultado.get("deudor_id")

        venta_id = registrar_venta(
            self.usuario_id, total, self.carrito, tipo_pago, deudor_id
        )

        # --- INICIO DEL BLOQUE DE CÓDIGO MODIFICADO ---

        # Obtenemos la ventana principal (el root de la aplicación)
        # Esto es importante para que el bloqueo afecte a toda la app.
        root_window = self.parent_frame.winfo_toplevel()

        if venta_id:
            # 2. Bloqueamos la ventana principal antes de mostrar los messageboxes
            root_window.grab_set()

            # Los messageboxes ahora bloquearán la interacción con la ventana POS
            messagebox.showinfo(
                "Venta Exitosa",
                f"La venta N°{venta_id} se ha registrado correctamente.",
                parent=root_window,
            )

            if messagebox.askyesno(
                "Imprimir Ticket",
                "¿Deseas generar el ticket de la venta?",
                parent=root_window,
            ):
                if not generar_ticket_pdf(venta_id):
                    messagebox.showerror(
                        "Error de Ticket",
                        "No se pudo generar el ticket en PDF.",
                        parent=root_window,
                    )

            # 3. Desbloqueamos la ventana principal después de que el usuario interactúa
            root_window.grab_release()

            self.cancelar_venta(confirmar=False)
            self.filtrar_productos()  # Usamos el nuevo método de filtro para recargar
        else:
            messagebox.showerror(
                "Error de Venta",
                "Ocurrió un error. El stock no ha sido modificado.",
                parent=root_window,
            )
        # --- FIN DEL BLOQUE DE CÓDIGO MODIFICADO ---

    def agregar_al_carrito(self, event=None):
        seleccion = self.products_tree.focus()
        if not seleccion:
            return

        datos = self.products_tree.item(seleccion, "values")
        codigo, nombre, precio_str, stock_visual_str = (
            datos[0],
            datos[1],
            datos[2],
            datos[3],
        )

        # Convertir a tipos numéricos
        precio = float(precio_str)
        stock_actual_visual = int(stock_visual_str)

        root_window = self.parent_frame.winfo_toplevel()

        # -------------------------------------------------------------------
        # 1. VALIDACIÓN DE STOCK
        # La validación se hace siempre contra el stock visible (disponible)
        if stock_actual_visual <= 0:
            messagebox.showwarning(
                "Sin Stock", f"'{nombre}' no tiene stock.", parent=root_window
            )
            return

        # -------------------------------------------------------------------
        # 2. PROCESO DE AGREGAR AL CARRITO

        if codigo in self.carrito:
            # Producto ya en carrito: Sólo incrementamos la cantidad

            # La validación debe ser contra el stock_original (el total de la BD)
            if (
                self.carrito[codigo]["cantidad"]
                < self.carrito[codigo]["stock_original"]
            ):
                self.carrito[codigo]["cantidad"] += 1
            else:
                messagebox.showwarning(
                    "Stock Insuficiente",
                    f"Stock máximo para '{nombre}' alcanzado.",
                    parent=root_window,
                )
                return
        else:
            # Producto nuevo en carrito: Inicializamos el carrito

            # --- CORRECCIÓN CLAVE ---
            # El stock_original DEBE ser la suma del stock_actual_visual + la cantidad que ya hay en el carrito (1)
            # para reflejar el stock real de la BD al momento de la carga.
            stock_original_calculado = (
                stock_actual_visual + 1
            )  # Si visible es 1, original era 2. Si visible es 0, original era 1.

            self.carrito[codigo] = {
                "nombre": nombre,
                "precio": precio,
                "cantidad": 1,
                "stock_original": stock_original_calculado,  # Usamos el stock total que debería tener
            }

        # -------------------------------------------------------------------
        # 3. ACTUALIZAR VISTA DE PRODUCTOS (Ahora solo restamos 1 al stock visual)

        # Simplemente restamos 1 al stock visible actual (porque ya validamos que hay al menos 1)
        nuevo_stock_visual = stock_actual_visual - 1

        # Obtener los valores actuales de la fila (Código, Nombre, Precio, Stock)
        valores_actuales = list(datos)

        # Sobrescribir solo el valor de Stock (índice 3) con el valor correcto
        valores_actuales[3] = nuevo_stock_visual

        # Aplicar los nuevos valores a la fila
        self.products_tree.item(seleccion, values=tuple(valores_actuales))

        # 4. ACTUALIZAR VISTA DEL CARRITO
        self.actualizar_vista_carrito()

    def actualizar_vista_carrito(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        total_venta = 0.0
        for codigo, item in self.carrito.items():
            subtotal = item["cantidad"] * item["precio"]
            total_venta += subtotal
            self.cart_tree.insert(
                "", END, values=(item["nombre"], item["cantidad"], f"{subtotal:.2f}")
            )
        self.total_label.config(text=f"TOTAL: ${total_venta:.2f}")

    def venta_en_curso(self):
        """Verifica si el carrito contiene productos."""
        return bool(self.carrito)

    def cancelar_venta(self, confirmar=True):
        # Asegúrate de que esta función acepte el parámetro 'confirmar=True'
        root_window = self.parent_frame.winfo_toplevel()

        if not self.carrito:
            messagebox.showinfo(
                "Carrito Vacío",
                "No hay productos en el carrito para cancelar.",
                parent=root_window,
            )
            return

        if confirmar:
            if not messagebox.askyesno(
                "Confirmar", "¿Cancelar la venta actual?", parent=root_window
            ):
                return

        self.carrito.clear()
        self.actualizar_vista_carrito()
        self.restaurar_productos()

    def remover_del_carrito(self, event=None):
        seleccion = self.cart_tree.focus()
        if not seleccion:
            return

        # 1. Obtener el nombre del producto seleccionado en el carrito
        nombre_sel = self.cart_tree.item(seleccion, "values")[0]
        codigo_a_modificar = None

        # Buscar el código del producto en el diccionario self.carrito
        for codigo, item in self.carrito.items():
            if item["nombre"] == nombre_sel:
                codigo_a_modificar = codigo
                break

        if not codigo_a_modificar:
            return  # Salir si no se encuentra el código

        # 2. Reducir la cantidad en el carrito (o eliminar si es 1)
        if self.carrito[codigo_a_modificar]["cantidad"] > 1:
            self.carrito[codigo_a_modificar]["cantidad"] -= 1
        else:
            # Si la cantidad es 1, lo eliminamos completamente del carrito
            del self.carrito[codigo_a_modificar]

        # 3. Calcular el nuevo stock visual que debe tener el producto

        # Obtenemos el stock original (del ítem en el carrito antes de la eliminación)
        # Si se eliminó (cantidad < 1), usamos el stock original guardado.
        # Si no se eliminó, usamos el stock original y restamos la nueva cantidad.
        stock_original_producto = self.carrito.get(codigo_a_modificar, {}).get(
            "stock_original", self.obtener_stock_actual_bd(codigo_a_modificar)
        )

        stock_en_carrito = self.carrito.get(codigo_a_modificar, {}).get("cantidad", 0)
        nuevo_stock_visual = stock_original_producto - stock_en_carrito

        # 4. Actualizar la fila en la tabla de productos (self.products_tree)

        # Necesitamos encontrar el identificador (iid) del producto en products_tree
        item_iid_a_modificar = None
        for iid in self.products_tree.get_children():
            # El código está en la posición 0 de los 'values' del products_tree
            if self.products_tree.item(iid, "values")[0] == codigo_a_modificar:
                item_iid_a_modificar = iid
                break

        if item_iid_a_modificar:
            # Obtener los valores actuales de la fila (Código, Nombre, Precio, Stock)
            valores_actuales = list(
                self.products_tree.item(item_iid_a_modificar, "values")
            )

            # Sobrescribir solo el valor de Stock (índice 3)
            valores_actuales[3] = nuevo_stock_visual

            # Aplicar los nuevos valores a la fila
            self.products_tree.item(
                item_iid_a_modificar, values=tuple(valores_actuales)
            )

        # 5. Actualizar la vista del carrito
        self.actualizar_vista_carrito()

    def restaurar_productos(self):
        """Limpia los filtros de búsqueda y recarga todos los productos desde la BD."""
        # Limpiar la caja de búsqueda de texto
        self.search_entry.delete(0, END)

        # Restaurar la categoría a "Mostrar Todas" (asumiendo que es la primera opción)
        self.combo_categorias.current(0)

        # Llamar a cargar_productos sin filtros para forzar la recarga completa
        # Esto usará los valores vacíos del search_entry y la categoría 0.
        self.cargar_productos(filtro_texto="", categoria_id=None)

    def cancelar_venta(self, confirmar=True):
        root_window = self.parent_frame.winfo_toplevel()  # Obtener la ventana principal

        if not self.carrito:
            # --- CÓDIGO CORREGIDO: Añadir parent=root_window ---
            messagebox.showinfo(
                "Carrito Vacío",
                "No hay productos en el carrito para cancelar.",
                parent=root_window,
            )
            return

        if confirmar:
            # Aquí ya usas parent=root_window si lo hiciste en la corrección anterior,
            # pero por si acaso, revisamos el askyesno
            if not messagebox.askyesno(
                "Confirmar", "¿Cancelar la venta actual?", parent=root_window
            ):
                return

        # 3. Limpia el carrito de datos y la vista del carrito
        self.carrito.clear()
        self.actualizar_vista_carrito()

        # 4. Llama al nuevo método para restaurar COMPLETAMENTE la vista de productos
        # Esto fuerza al Treeview a mostrar el stock original de la BD.
        self.restaurar_productos()


# (La clase PaymentDialog no sufre cambios en este paso)
class PaymentDialog(BaseDialog):
    def __init__(self, parent, total_str):
        super().__init__(parent, title="Finalizar Venta")
        self.resultado = None

        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill=BOTH)

        ttk.Label(main_frame, text="Total a Pagar:", font=("Helvetica", 12)).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(main_frame, text=total_str, font=("Helvetica", 14, "bold")).grid(
            row=0, column=1, columnspan=2, sticky="e", padx=10
        )

        ttk.Separator(main_frame, orient=HORIZONTAL).grid(
            row=1, column=0, columnspan=3, pady=10, sticky="ew"
        )

        self.tipo_pago_var = ttk.StringVar(value="Contado")
        ttk.Radiobutton(
            main_frame,
            text="Pago al Contado",
            variable=self.tipo_pago_var,
            value="Contado",
            command=self.toggle_deudores,
        ).grid(row=2, column=0, columnspan=3, sticky="w")
        ttk.Radiobutton(
            main_frame,
            text="Añadir a Deuda (Crédito)",
            variable=self.tipo_pago_var,
            value="Credito",
            command=self.toggle_deudores,
        ).grid(row=3, column=0, columnspan=3, sticky="w")

        self.deudores_label = ttk.Label(main_frame, text="Seleccionar Deudor:")
        self.combo_deudores = ttk.Combobox(main_frame, state="readonly")
        self.btn_nuevo_deudor = ttk.Button(
            main_frame,
            text="Nuevo Deudor",
            bootstyle="outline-success",
            command=self.crear_nuevo_deudor,
        )

        ttk.Button(
            main_frame,
            text="Confirmar Venta",
            command=self.confirmar,
            bootstyle="success",
        ).grid(row=6, column=0, columnspan=3, pady=(20, 0), sticky="ew")

        self.cargar_deudores()

    def cargar_deudores(self):
        deudores_data = obtener_deudores()
        self.deudores_map = {d[1]: d[0] for d in deudores_data}
        self.combo_deudores["values"] = list(self.deudores_map.keys())

    def toggle_deudores(self):
        if self.tipo_pago_var.get() == "Credito":
            self.deudores_label.grid(row=4, column=0, sticky="w", pady=(10, 0))
            self.combo_deudores.grid(row=4, column=1, sticky="ew", pady=(10, 0))
            self.btn_nuevo_deudor.grid(
                row=4, column=2, sticky="ew", padx=(5, 0), pady=(10, 0)
            )
        else:
            self.deudores_label.grid_forget()
            self.combo_deudores.grid_forget()
            self.btn_nuevo_deudor.grid_forget()
        self.center_window()

    def crear_nuevo_deudor(self):
        form_deudor = DebtorForm(self, None, self.refrescar_y_seleccionar_deudor)
        self.wait_window(form_deudor)

    def refrescar_y_seleccionar_deudor(self, nombre_nuevo_deudor=None):
        self.cargar_deudores()
        if nombre_nuevo_deudor:
            self.combo_deudores.set(nombre_nuevo_deudor)

    def confirmar(self):
        tipo_pago = self.tipo_pago_var.get()
        deudor_id = None

        if tipo_pago == "Credito":
            deudor_nombre = self.combo_deudores.get()
            if not deudor_nombre:
                messagebox.showwarning(
                    "Sin Selección",
                    "Debes seleccionar o crear un deudor para una venta a crédito.",
                    parent=self,
                )
                return
            deudor_id = self.deudores_map.get(deudor_nombre)

        self.resultado = {"tipo_pago": tipo_pago, "deudor_id": deudor_id}
        self.destroy()
