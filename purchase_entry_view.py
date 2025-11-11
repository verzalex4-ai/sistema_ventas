# purchase_entry_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk  # Necesario para StringVar
from tkinter import messagebox
from database import obtener_proveedores, obtener_productos, registrar_compra


# =============================================================================
# 1. CLASE DE DIÁLOGO MODAL PERSONALIZADO (REEMPLAZA a simpledialog)
# =============================================================================
class InputAmountDialog(ttk.Toplevel):
    """Diálogo modal personalizado para ingresar cantidad o costo unitario con validación de campo vacío."""

    def __init__(self, parent, title, prompt, value_type):
        super().__init__(parent)
        self.title(title)

        # Configuraciones de Modalidad
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.result = None
        self.value_type = value_type  # 'int' o 'float'

        # Contenido
        ttk.Label(self, text=prompt).pack(pady=10, padx=20)

        self.value_var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.value_var, justify=RIGHT)
        self.entry.pack(pady=5, padx=20, fill=X)
        self.entry.focus_set()

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame, text="OK", command=self.on_ok, bootstyle="success"
        ).pack(side=LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(
            side=LEFT, padx=5
        )

        # Centrar el diálogo (Mejora de UX)
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = parent.winfo_x() + parent.winfo_width() // 2 - width // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - height // 2
        self.geometry(f"+{x}+{y}")

        # Esperar hasta que se cierre (implementa la modalidad)
        self.wait_window(self)

    def on_ok(self):
        value_str = self.value_var.get().strip()
        root_window = self.winfo_toplevel()

        if not value_str:
            # Validación: Campo Vacío
            messagebox.showerror(
                "Error de Campo",
                "¡No puedes dejar este campo vacío!",
                parent=root_window,
            )
            return

        try:
            value = None
            if self.value_type == "int":
                value = int(value_str)
                if value < 1:
                    messagebox.showerror(
                        "Error de Valor",
                        "La cantidad debe ser 1 o superior.",
                        parent=root_window,
                    )
                    return

            elif self.value_type == "float":
                value = float(value_str)
                if value < 0.0:
                    messagebox.showerror(
                        "Error de Valor",
                        "El costo unitario no puede ser negativo.",
                        parent=root_window,
                    )
                    return

            self.result = value
            self.destroy()  # Cierra el diálogo y retorna el valor

        except ValueError:
            # Validación: Formato Incorrecto
            messagebox.showerror(
                "Error de Formato",
                "Por favor, ingresa un número válido.",
                parent=root_window,
            )


# =============================================================================
# 2. VISTA PRINCIPAL
# =============================================================================
class PurchaseEntryView:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.carrito_compra = {}

        top_frame = ttk.Frame(self.parent_frame)
        top_frame.pack(fill=X, padx=10, pady=5)

        ttk.Label(top_frame, text="Proveedor:", font=("Helvetica", 11, "bold")).pack(
            side=LEFT, padx=(0, 5)
        )

        # --- INICIO DE CORRECCIÓN: INCLUIR OPCIÓN "Mostrar Todos" ---
        proveedores = {p[1]: p[0] for p in obtener_proveedores()}
        self.proveedores_map = proveedores

        nombres_proveedores = list(proveedores.keys())
        nombres_proveedores.insert(0, "Mostrar Todos")

        self.combo_proveedor = ttk.Combobox(
            top_frame, values=nombres_proveedores, state="readonly"
        )
        self.combo_proveedor.set("Mostrar Todos")  # Valor inicial
        # --- FIN DE CORRECCIÓN ---

        self.combo_proveedor.pack(side=LEFT, padx=5)

        self.combo_proveedor.bind("<<ComboboxSelected>>", self.filtrar_por_proveedor)

        ttk.Label(
            top_frame, text="Buscar Producto:", font=("Helvetica", 11, "bold")
        ).pack(side=LEFT, padx=(20, 5))
        self.search_entry = ttk.Entry(top_frame, width=40)
        self.search_entry.pack(side=LEFT, fill=X, expand=True)
        self.search_entry.bind("<KeyRelease>", self.buscar_producto)

        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        products_list_frame = ttk.Frame(main_frame)
        products_list_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        ttk.Label(
            products_list_frame,
            text="Doble clic para agregar producto a la compra",
            font=("Helvetica", 10),
        ).pack()

        columns_prod = ("codigo", "nombre", "stock")
        self.products_tree = ttk.Treeview(
            products_list_frame,
            columns=columns_prod,
            show="headings",
            bootstyle="primary",
        )
        self.products_tree.heading("codigo", text="Código")
        self.products_tree.heading("nombre", text="Nombre")
        self.products_tree.heading("stock", text="Stock Actual")
        self.products_tree.column("codigo", width=100)
        self.products_tree.column("nombre", width=300)
        self.products_tree.column("stock", width=100, anchor=CENTER)
        self.products_tree.pack(fill=BOTH, expand=True)
        self.products_tree.bind("<Double-1>", self.agregar_a_compra)

        purchase_cart_frame = ttk.Frame(main_frame, width=400)
        purchase_cart_frame.pack(side=RIGHT, fill=Y)
        purchase_cart_frame.pack_propagate(False)

        ttk.Label(
            purchase_cart_frame,
            text="Mercadería a Ingresar",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=5)
        columns_cart = ("nombre", "cantidad", "costo_u", "subtotal")
        self.cart_tree = ttk.Treeview(
            purchase_cart_frame,
            columns=columns_cart,
            show="headings",
            bootstyle="success",
        )
        self.cart_tree.heading("nombre", text="Producto")
        self.cart_tree.heading("cantidad", text="Cant.")
        self.cart_tree.heading("costo_u", text="Costo Unit.")
        self.cart_tree.heading("subtotal", text="Subtotal")
        self.cart_tree.column("nombre", width=150)
        self.cart_tree.column("cantidad", width=60, anchor=CENTER)
        self.cart_tree.column("costo_u", width=80, anchor=E)
        self.cart_tree.column("subtotal", width=80, anchor=E)
        self.cart_tree.pack(fill=BOTH, expand=True)

        total_frame = ttk.Frame(purchase_cart_frame)
        total_frame.pack(side=BOTTOM, fill=X, pady=10)
        self.total_label = ttk.Label(
            total_frame, text="COSTO TOTAL: $0.00", font=("Helvetica", 14, "bold")
        )
        self.total_label.pack(pady=5)
        ttk.Button(
            total_frame,
            text="Registrar Compra",
            command=self.confirmar_registro_compra,
            bootstyle="success",
        ).pack(fill=X, ipady=5)

        self.cargar_productos()

    # --- FILTRAR Y CARGAR PRODUCTOS ---
    def filtrar_por_proveedor(self, event=None):
        proveedor_nombre = self.combo_proveedor.get()

        if proveedor_nombre == "Mostrar Todos":
            proveedor_id = None
        else:
            proveedor_id = self.proveedores_map.get(proveedor_nombre)

        self.search_entry.delete(0, END)
        self.cargar_productos(proveedor_id=proveedor_id)

    def cargar_productos(self, filtro="", proveedor_id=None):
        for i in self.products_tree.get_children():
            self.products_tree.delete(i)
        for p in obtener_productos(filtro=filtro, proveedor_id=proveedor_id):
            self.products_tree.insert("", END, values=(p[0], p[1], p[3]))

    def buscar_producto(self, event=None):
        proveedor_nombre = self.combo_proveedor.get()

        if proveedor_nombre == "Mostrar Todos":
            proveedor_id = None
        else:
            proveedor_id = self.proveedores_map.get(proveedor_nombre)

        self.cargar_productos(self.search_entry.get(), proveedor_id)

    # --- MÉTODO AGREGAR A COMPRA (USANDO EL NUEVO DIÁLOGO MODAL) ---
    # --- MÉTODO AGREGAR A COMPRA (AÑADIDA VALIDACIÓN DE PROVEEDOR) ---
    def agregar_a_compra(self, event=None):
        seleccion = self.products_tree.focus()
        if not seleccion:
            return

        # 1. Obtener la referencia de la ventana principal para la Modalidad
        root_window = self.products_tree.winfo_toplevel()
        proveedor_nombre = self.combo_proveedor.get()

        # **CORRECCIÓN:** Validar si hay un proveedor específico seleccionado
        if not proveedor_nombre or proveedor_nombre == "Mostrar Todos":
            messagebox.showwarning(
                "Falta Proveedor",
                "Para añadir productos a la compra, primero debes seleccionar un proveedor específico.",
                parent=root_window,
            )
            return

        # Continúa solo si hay un proveedor válido seleccionado
        datos = self.products_tree.item(seleccion, "values")
        codigo, nombre = datos[0], datos[1]

        # 2. Cantidad: Usa el diálogo personalizado
        dialog_cantidad = InputAmountDialog(
            parent=root_window,
            title="Ingreso de Cantidad",
            prompt=f"Ingrese la cantidad de '{nombre}' que ingresó:",
            value_type="int",
        )
        cantidad = dialog_cantidad.result

        if cantidad is None:
            return

        # 3. Costo Unitario: Usa el diálogo personalizado
        dialog_costo = InputAmountDialog(
            parent=root_window,
            title="Costo Unitario",
            prompt=f"Ingrese el costo por unidad de '{nombre}':",
            value_type="float",
        )
        costo = dialog_costo.result

        if costo is None:
            return

        # Si llegamos aquí, ambos valores son válidos y hay un proveedor
        self.carrito_compra[codigo] = {
            "nombre": nombre,
            "cantidad": cantidad,
            "costo": costo,
        }
        self.actualizar_vista_compra()

    def actualizar_vista_compra(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        costo_total = 0.0
        for item in self.carrito_compra.values():
            subtotal = item["cantidad"] * item["costo"]
            costo_total += subtotal
            self.cart_tree.insert(
                "",
                END,
                values=(
                    item["nombre"],
                    item["cantidad"],
                    f"${item['costo']:.2f}",
                    f"${subtotal:.2f}",
                ),
            )
        self.total_label.config(text=f"COSTO TOTAL: ${costo_total:.2f}")

    # --- CONFIRMAR REGISTRO COMPRA ---
    def confirmar_registro_compra(self):
        try:
            root_window = self.combo_proveedor.winfo_toplevel()
        except AttributeError:
            root_window = None

        proveedor_nombre = self.combo_proveedor.get()

        if not proveedor_nombre or proveedor_nombre == "Mostrar Todos":
            messagebox.showwarning(
                "Falta Proveedor",
                "Por favor, selecciona un proveedor específico para registrar la compra.",
                parent=root_window,
            )
            return

        if not self.carrito_compra:
            messagebox.showwarning(
                "Carrito Vacío",
                "No hay productos en la lista de compra.",
                parent=root_window,
            )
            return

        # Extracción de datos
        proveedor_id = self.proveedores_map[proveedor_nombre]

        try:
            total_costo = float(
                self.total_label.cget("text").replace("COSTO TOTAL: $", "")
            )
        except ValueError:
            messagebox.showerror(
                "Error de Cálculo",
                "El costo total no es un número válido. Por favor, revisa la compra.",
                parent=root_window,
            )
            return

        if messagebox.askyesno(
            "Confirmar Compra",
            f"Se registrará una compra al proveedor '{proveedor_nombre}' por un total de ${total_costo:.2f}. El stock de los productos se actualizará.\n\n¿Deseas continuar?",
            parent=root_window,
        ):
            if registrar_compra(proveedor_id, total_costo, self.carrito_compra):
                messagebox.showinfo(
                    "Éxito",
                    "La compra ha sido registrada y el stock actualizado.",
                    parent=root_window,
                )
                self.carrito_compra.clear()
                self.actualizar_vista_compra()
                self.cargar_productos()
            else:
                messagebox.showerror(
                    "Error",
                    "Ocurrió un error al registrar la compra.",
                    parent=root_window,
                )
