# devolucion_view.py - Sistema de Devoluciones
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import (
    buscar_ventas_para_devolucion,
    obtener_detalle_venta_para_devolucion,
    verificar_devolucion_previa,
    registrar_devolucion
)
from datetime import datetime


class DevolucionView:
    def __init__(self, parent_frame, usuario_id):
        self.parent_frame = parent_frame
        self.usuario_id = usuario_id
        
        self.venta_seleccionada = None
        self.info_venta = None
        self.detalles_venta = None
        self.productos_devolver = {}  # {producto_id: cantidad}
        
        self.crear_interfaz()

    def crear_interfaz(self):
        """Crea la interfaz principal de devoluciones."""
        
        # ============================================
        # ENCABEZADO
        # ============================================
        header_frame = ttk.Frame(self.parent_frame, padding=10)
        header_frame.pack(fill=X)
        
        ttk.Label(
            header_frame,
            text="🔄 Devoluciones",
            font=("Helvetica", 18, "bold")
        ).pack(side=LEFT)
        
        ttk.Label(
            header_frame,
            text="Busca la venta y selecciona los productos a devolver",
            font=("Helvetica", 10),
            bootstyle="info"
        ).pack(side=LEFT, padx=20)
        
        # ============================================
        # PANEL DE BÚSQUEDA
        # ============================================
        search_frame = ttk.Labelframe(
            self.parent_frame,
            text="🔍 Buscar Venta",
            padding=15
        )
        search_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        # Búsqueda por ID
        id_frame = ttk.Frame(search_frame)
        id_frame.pack(side=LEFT, padx=(0, 20))
        
        ttk.Label(id_frame, text="ID Venta:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 5))
        
        self.id_venta_var = ttk.StringVar()
        self.id_venta_entry = ttk.Entry(id_frame, textvariable=self.id_venta_var, width=10)
        self.id_venta_entry.pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            id_frame,
            text="Buscar",
            command=lambda: self.buscar_venta('id'),
            bootstyle="primary"
        ).pack(side=LEFT)
        
        # Búsqueda por fecha
        fecha_frame = ttk.Frame(search_frame)
        fecha_frame.pack(side=LEFT)
        
        ttk.Label(fecha_frame, text="Fecha:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 5))
        
        self.fecha_busqueda = ttk.DateEntry(
            fecha_frame,
            bootstyle="primary",
            dateformat="%Y-%m-%d",
            startdate=datetime.now()
        )
        self.fecha_busqueda.pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            fecha_frame,
            text="Buscar",
            command=lambda: self.buscar_venta('fecha'),
            bootstyle="primary"
        ).pack(side=LEFT)
        
        # ============================================
        # CONTENEDOR PRINCIPAL (2 COLUMNAS)
        # ============================================
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Columna izquierda - Resultados de búsqueda
        left_frame = ttk.Labelframe(
            main_container,
            text="📋 Resultados de Búsqueda",
            padding=10
        )
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        # Treeview resultados
        result_scroll = ttk.Scrollbar(left_frame, orient=VERTICAL)
        result_scroll.pack(side=RIGHT, fill=Y)
        
        result_columns = ("id", "fecha", "cajero", "total", "tipo_pago", "deudor")
        self.result_tree = ttk.Treeview(
            left_frame,
            columns=result_columns,
            show="headings",
            yscrollcommand=result_scroll.set,
            selectmode="browse"
        )
        result_scroll.config(command=self.result_tree.yview)
        
        self.result_tree.heading("id", text="ID", anchor=CENTER)
        self.result_tree.heading("fecha", text="Fecha", anchor=W)
        self.result_tree.heading("cajero", text="Cajero", anchor=W)
        self.result_tree.heading("total", text="Total", anchor=E)
        self.result_tree.heading("tipo_pago", text="Tipo", anchor=CENTER)
        self.result_tree.heading("deudor", text="Deudor", anchor=W)
        
        self.result_tree.column("id", width=50, anchor=CENTER)
        self.result_tree.column("fecha", width=130, anchor=W)
        self.result_tree.column("cajero", width=100, anchor=W)
        self.result_tree.column("total", width=80, anchor=E)
        self.result_tree.column("tipo_pago", width=70, anchor=CENTER)
        self.result_tree.column("deudor", width=120, anchor=W)
        
        self.result_tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.result_tree.bind("<<TreeviewSelect>>", self.cargar_detalle_venta)
        
        # Columna derecha - Detalle de la venta
        right_frame = ttk.Labelframe(
            main_container,
            text="📦 Detalle de la Venta",
            padding=10
        )
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        
        # Info de la venta
        self.info_label = ttk.Label(
            right_frame,
            text="Selecciona una venta para ver el detalle",
            font=("Helvetica", 10),
            foreground="gray"
        )
        self.info_label.pack(pady=10)
        
        # Treeview productos
        products_scroll = ttk.Scrollbar(right_frame, orient=VERTICAL)
        products_scroll.pack(side=RIGHT, fill=Y)
        
        product_columns = ("producto", "cantidad", "precio", "subtotal", "devolver")
        self.products_tree = ttk.Treeview(
            right_frame,
            columns=product_columns,
            show="headings",
            yscrollcommand=products_scroll.set,
            selectmode="browse"
        )
        products_scroll.config(command=self.products_tree.yview)
        
        self.products_tree.heading("producto", text="Producto", anchor=W)
        self.products_tree.heading("cantidad", text="Cant.", anchor=CENTER)
        self.products_tree.heading("precio", text="Precio", anchor=E)
        self.products_tree.heading("subtotal", text="Subtotal", anchor=E)
        self.products_tree.heading("devolver", text="A Devolver", anchor=CENTER)
        
        self.products_tree.column("producto", width=200, anchor=W)
        self.products_tree.column("cantidad", width=60, anchor=CENTER)
        self.products_tree.column("precio", width=70, anchor=E)
        self.products_tree.column("subtotal", width=80, anchor=E)
        self.products_tree.column("devolver", width=80, anchor=CENTER)
        
        self.products_tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.products_tree.bind("<Double-1>", self.seleccionar_cantidad_devolver)
        
        # ============================================
        # PANEL DE DEVOLUCIÓN
        # ============================================
        devolucion_frame = ttk.Labelframe(
            self.parent_frame,
            text="💰 Procesar Devolución",
            padding=15
        )
        devolucion_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        # Grid de información
        info_grid = ttk.Frame(devolucion_frame)
        info_grid.pack(fill=X, pady=(0, 10))
        
        ttk.Label(info_grid, text="Total de la Venta:", font=("Helvetica", 10, "bold")).grid(
            row=0, column=0, sticky=W, padx=(0, 10)
        )
        self.total_venta_label = ttk.Label(info_grid, text="$0.00", font=("Helvetica", 10))
        self.total_venta_label.grid(row=0, column=1, sticky=W)
        
        ttk.Label(info_grid, text="Total a Devolver:", font=("Helvetica", 11, "bold")).grid(
            row=0, column=2, sticky=W, padx=(20, 10)
        )
        self.total_devolucion_label = ttk.Label(
            info_grid, 
            text="$0.00", 
            font=("Helvetica", 12, "bold"),
            bootstyle="danger"
        )
        self.total_devolucion_label.grid(row=0, column=3, sticky=W)
        
        # Motivo
        ttk.Label(devolucion_frame, text="Motivo de la devolución:", font=("Helvetica", 10, "bold")).pack(
            anchor=W, pady=(5, 5)
        )
        
        self.motivo_text = ttk.Text(devolucion_frame, height=3, font=("Helvetica", 10), wrap=WORD)
        self.motivo_text.pack(fill=X, pady=(0, 10))
        
        # Botones
        btn_frame = ttk.Frame(devolucion_frame)
        btn_frame.pack(fill=X)
        
        self.btn_procesar = ttk.Button(
            btn_frame,
            text="✅ Procesar Devolución",
            command=self.procesar_devolucion,
            bootstyle="success",
            state="disabled"
        )
        self.btn_procesar.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="🔄 Limpiar",
            command=self.limpiar_formulario,
            bootstyle="secondary"
        ).pack(side=RIGHT, fill=X, expand=True, padx=(5, 0))
        
        # Bind Enter en búsqueda por ID
        self.id_venta_entry.bind("<Return>", lambda e: self.buscar_venta('id'))

    def buscar_venta(self, criterio):
        """Busca ventas según el criterio especificado."""
        # Limpiar resultados anteriores
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.limpiar_detalle()
        
        if criterio == 'id':
            valor = self.id_venta_var.get().strip()
            if not valor:
                messagebox.showwarning(
                    "Campo Vacío",
                    "Por favor, ingresa el ID de la venta.",
                    parent=self.parent_frame.winfo_toplevel()
                )
                return
            try:
                valor = int(valor)
            except ValueError:
                messagebox.showerror(
                    "Error",
                    "El ID debe ser un número.",
                    parent=self.parent_frame.winfo_toplevel()
                )
                return
        else:  # fecha
            valor = self.fecha_busqueda.entry.get()
        
        # Buscar en BD
        ventas = buscar_ventas_para_devolucion(criterio, valor)
        
        if not ventas:
            messagebox.showinfo(
                "Sin Resultados",
                "No se encontraron ventas con ese criterio.",
                parent=self.parent_frame.winfo_toplevel()
            )
            return
        
        # Mostrar resultados
        for venta in ventas:
            venta_id, fecha, cajero, total, tipo_pago, deudor = venta
            
            # Formatear fecha
            try:
                dt = datetime.strptime(fecha, "%Y-%m-%d %H:%M:%S")
                fecha_format = dt.strftime("%d/%m/%Y %H:%M")
            except:
                fecha_format = fecha
            
            self.result_tree.insert(
                "",
                END,
                values=(
                    venta_id,
                    fecha_format,
                    cajero,
                    f"${total:.2f}",
                    tipo_pago,
                    deudor
                )
            )

    def cargar_detalle_venta(self, event=None):
        """Carga el detalle de la venta seleccionada."""
        seleccion = self.result_tree.focus()
        if not seleccion:
            return
        
        venta_id = self.result_tree.item(seleccion, "values")[0]
        
        # Obtener detalle de la venta
        info_venta, detalles = obtener_detalle_venta_para_devolucion(venta_id)
        
        if not info_venta or not detalles:
            messagebox.showerror(
                "Error",
                "No se pudo obtener el detalle de la venta.",
                parent=self.parent_frame.winfo_toplevel()
            )
            return
        
        self.venta_seleccionada = venta_id
        self.info_venta = info_venta
        self.detalles_venta = detalles
        self.productos_devolver = {}
        
        # Verificar si tiene devoluciones previas
        tiene_devolucion, total_devuelto = verificar_devolucion_previa(venta_id)
        
        # Mostrar info de la venta
        venta_id, fecha, usuario_id, usuario, total, tipo_pago, deudor_id, deudor, saldo_pendiente = info_venta
        
        info_texto = f"Venta #{venta_id} | {fecha} | {tipo_pago}"
        if deudor_id:
            info_texto += f" | Deudor: {deudor}"
        if tiene_devolucion:
            info_texto += f"\n⚠️ Ya tiene devoluciones previas por ${total_devuelto:.2f}"
        
        self.info_label.config(text=info_texto, foreground="black")
        self.total_venta_label.config(text=f"${total:.2f}")
        
        # Cargar productos
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        for detalle in detalles:
            detalle_id, producto_id, codigo, nombre, cantidad, precio, subtotal = detalle
            
            self.products_tree.insert(
                "",
                END,
                values=(
                    nombre,
                    cantidad,
                    f"${precio:.2f}",
                    f"${subtotal:.2f}",
                    "0"
                ),
                tags=(str(producto_id),)
            )

    def seleccionar_cantidad_devolver(self, event=None):
        """Permite seleccionar la cantidad a devolver de un producto."""
        seleccion = self.products_tree.focus()
        if not seleccion:
            return
        
        valores = self.products_tree.item(seleccion, "values")
        tags = self.products_tree.item(seleccion, "tags")
        
        if not tags:
            return
        
        producto_id = int(tags[0])
        nombre_producto = valores[0]
        cantidad_original = int(valores[1])
        
        # Dialog para ingresar cantidad
        cantidad = ttk.dialogs.Querybox.get_integer(
            prompt=f"¿Cuántas unidades de '{nombre_producto}' devolver?\n(Máximo: {cantidad_original})",
            title="Cantidad a Devolver",
            initialvalue=0,
            minvalue=0,
            maxvalue=cantidad_original,
            parent=self.parent_frame.winfo_toplevel()
        )
        
        if cantidad is None:
            return
        
        # Actualizar cantidad a devolver
        if cantidad > 0:
            self.productos_devolver[producto_id] = cantidad
        elif producto_id in self.productos_devolver:
            del self.productos_devolver[producto_id]
        
        # Actualizar vista
        self.products_tree.item(seleccion, values=(
            valores[0], valores[1], valores[2], valores[3], str(cantidad)
        ))
        
        # Calcular total a devolver
        self.calcular_total_devolucion()

    def calcular_total_devolucion(self):
        """Calcula el total de la devolución."""
        total_devolucion = 0.0
        
        for detalle in self.detalles_venta:
            producto_id = detalle[1]
            precio_unitario = detalle[5]
            
            if producto_id in self.productos_devolver:
                cantidad_devolver = self.productos_devolver[producto_id]
                total_devolucion += cantidad_devolver * precio_unitario
        
        self.total_devolucion_label.config(text=f"${total_devolucion:.2f}")
        
        # Habilitar botón si hay productos a devolver
        if self.productos_devolver:
            self.btn_procesar.config(state="normal")
        else:
            self.btn_procesar.config(state="disabled")

    def procesar_devolucion(self):
        """Procesa la devolución."""
        root_window = self.parent_frame.winfo_toplevel()
        
        if not self.productos_devolver:
            messagebox.showwarning(
                "Sin Productos",
                "Debes seleccionar al menos un producto para devolver.",
                parent=root_window
            )
            return
        
        motivo = self.motivo_text.get("1.0", "end-1c").strip()
        
        if not motivo:
            if not messagebox.askyesno(
                "Sin Motivo",
                "No has ingresado un motivo para la devolución.\n¿Deseas continuar sin motivo?",
                parent=root_window
            ):
                return
        
        # Confirmación final
        total_str = self.total_devolucion_label.cget("text")
        tipo_pago = self.info_venta[5]
        
        mensaje = f"¿Confirmar devolución?\n\n"
        mensaje += f"Venta: #{self.venta_seleccionada}\n"
        mensaje += f"Total a devolver: {total_str}\n"
        mensaje += f"Productos: {len(self.productos_devolver)}\n"
        
        if tipo_pago == "Credito":
            mensaje += f"\n💡 Se ajustará la deuda del cliente."
        else:
            mensaje += f"\n💡 Se debe reintegrar el efectivo."
        
        if not messagebox.askyesno("Confirmar Devolución", mensaje, parent=root_window):
            return
        
        # Registrar en BD
        devolucion_id = registrar_devolucion(
            self.usuario_id,
            self.venta_seleccionada,
            self.productos_devolver,
            motivo
        )
        
        if devolucion_id:
            messagebox.showinfo(
                "Éxito",
                f"✅ Devolución registrada exitosamente.\n\nID: {devolucion_id}\n"
                f"Total devuelto: {total_str}",
                parent=root_window
            )
            self.limpiar_formulario()
        else:
            messagebox.showerror(
                "Error",
                "No se pudo registrar la devolución.",
                parent=root_window
            )

    def limpiar_detalle(self):
        """Limpia el detalle de la venta."""
        self.venta_seleccionada = None
        self.info_venta = None
        self.detalles_venta = None
        self.productos_devolver = {}
        
        self.info_label.config(
            text="Selecciona una venta para ver el detalle",
            foreground="gray"
        )
        self.total_venta_label.config(text="$0.00")
        self.total_devolucion_label.config(text="$0.00")
        
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        self.btn_procesar.config(state="disabled")

    def limpiar_formulario(self):
        """Limpia todo el formulario."""
        self.id_venta_var.set("")
        self.motivo_text.delete("1.0", "end")
        
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.limpiar_detalle()