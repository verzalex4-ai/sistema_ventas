# reports_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from datetime import date
from tkinter import messagebox
from database import (obtener_ventas_por_rango, obtener_productos_mas_vendidos, 
                      obtener_detalle_de_venta, obtener_reporte_ganancias, 
                      obtener_compras_por_rango, obtener_ganancias_por_producto,
                      obtener_detalle_de_compra)

class ReportsView:
    def __init__(self, parent_frame):
        self.parent_frame = parent_frame
        self.active_report_method = None

        ttk.Label(self.parent_frame, text="Reportes", font=("Helvetica", 16, "bold")).pack(pady=10)

        # --- Frame de filtros y botones ---
        filter_frame = ttk.Frame(self.parent_frame)
        filter_frame.pack(fill=X, padx=10, pady=5)
        hoy = date.today()
        primer_dia_mes = hoy.replace(day=1)
        ttk.Label(filter_frame, text="Desde:").pack(side=LEFT, padx=(0,5))
        self.fecha_inicio_entry = ttk.DateEntry(filter_frame, bootstyle="primary", dateformat="%Y-%m-%d", startdate=primer_dia_mes)
        self.fecha_inicio_entry.pack(side=LEFT)
        ttk.Label(filter_frame, text="Hasta:").pack(side=LEFT, padx=(20,5))
        self.fecha_fin_entry = ttk.DateEntry(filter_frame, bootstyle="primary", dateformat="%Y-%m-%d")
        self.fecha_fin_entry.pack(side=LEFT)
        self.fecha_inicio_entry.bind("<<DateEntrySelected>>", self.actualizar_reporte_automatico)
        self.fecha_fin_entry.bind("<<DateEntrySelected>>", self.actualizar_reporte_automatico)
        
        button_frame = ttk.Frame(self.parent_frame)
        button_frame.pack(fill=X, padx=10, pady=10)
        ttk.Button(button_frame, text="Ver Ventas", command=self.mostrar_reporte_ventas, bootstyle="primary").pack(side=LEFT)
        ttk.Button(button_frame, text="Ver Compras", command=self.mostrar_reporte_compras, bootstyle="warning").pack(side=LEFT, padx=10)
        ttk.Button(button_frame, text="Top Productos", command=self.mostrar_reporte_top_productos, bootstyle="info").pack(side=LEFT)
        ttk.Button(button_frame, text="Calcular Ganancias", command=self.mostrar_reporte_ganancias, bootstyle="success").pack(side=LEFT, padx=10)

        # --- Frame principal de resultados ---
        results_frame = ttk.Frame(self.parent_frame)
        results_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        main_tree_frame = ttk.Frame(results_frame)
        main_tree_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        self.main_tree = ttk.Treeview(main_tree_frame, show='headings')
        self.main_tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.main_tree.bind("<<TreeviewSelect>>", self.mostrar_detalle_seleccion)
        main_scrollbar = ttk.Scrollbar(main_tree_frame, orient=VERTICAL, command=self.main_tree.yview)
        main_scrollbar.pack(side=RIGHT, fill=Y)
        self.main_tree.configure(yscrollcommand=main_scrollbar.set)
        
        detail_tree_frame = ttk.Frame(results_frame)
        detail_tree_frame.pack(fill=BOTH, expand=True)
        self.detail_label = ttk.Label(detail_tree_frame, text="Detalles", font=("Helvetica", 11, "bold"))
        self.detail_label.pack(pady=(0,5), anchor="w")
        detail_tree_inner_frame = ttk.Frame(detail_tree_frame)
        detail_tree_inner_frame.pack(fill=BOTH, expand=True)
        self.detail_tree = ttk.Treeview(detail_tree_inner_frame, show='headings', bootstyle="info")
        self.detail_tree.pack(side=LEFT, fill=BOTH, expand=True)
        detail_scrollbar = ttk.Scrollbar(detail_tree_inner_frame, orient=VERTICAL, command=self.detail_tree.yview)
        detail_scrollbar.pack(side=RIGHT, fill=Y)
        self.detail_tree.configure(yscrollcommand=detail_scrollbar.set)

        # --- Frame de resumen ---
        summary_frame = ttk.Labelframe(self.parent_frame, text="Resumen de Ganancias", padding=(10,10))
        summary_frame.pack(fill=X, padx=10, pady=5)
        self.label_total_ventas = ttk.Label(summary_frame, text="Ingresos Totales: $0.00", font=("Helvetica", 11, "bold"))
        self.label_total_ventas.pack(side=LEFT, expand=True)
        self.label_total_costo = ttk.Label(summary_frame, text="Costo de Mercadería: $0.00", font=("Helvetica", 11, "bold"))
        self.label_total_costo.pack(side=LEFT, expand=True)
        self.label_ganancia_neta = ttk.Label(summary_frame, text="Ganancia Neta: $0.00", font=("Helvetica", 11, "bold"))
        self.label_ganancia_neta.pack(side=LEFT, expand=True)
        self.label_margen = ttk.Label(summary_frame, text="Margen: 0.00%", font=("Helvetica", 11, "bold"), bootstyle="success")
        self.label_margen.pack(side=LEFT, expand=True)

    def _configurar_treeview(self, tree, columnas_config):
        """Función central para configurar las columnas de cualquier tabla."""
        # Limpiar cualquier configuración de columnas anterior (importante para evitar residuos)
        tree.delete(*tree.get_children())
        tree.config(columns=list(columnas_config.keys()))

        for col_id, props in columnas_config.items():
            tree.heading(col_id, text=props['text'], anchor=props.get('head_anchor', props.get('anchor', 'w'))) # Alinea el texto del encabezado

            tree.column(
                col_id, 
                width=props.get('width', 100),       # Ancho inicial
                minwidth=props.get('minwidth', 50),  # Ancho mínimo para que no se contraiga demasiado
                anchor=props.get('anchor', 'w'),     # Alineación del contenido de la celda
                stretch=props.get('stretch', False)  # Si la columna se estira o no
            )
    
    def actualizar_reporte_automatico(self, event=None):
        if self.active_report_method:
            self.active_report_method()

    def limpiar_vistas(self):
        """Limpia ambas tablas y las etiquetas de resumen, y resetea las columnas."""
        self.main_tree.delete(*self.main_tree.get_children())
        self.detail_tree.delete(*self.detail_tree.get_children())
        
        # Es crucial resetear las columnas para que _configurar_treeview las cree desde cero
        self.main_tree.config(columns=[]) 
        self.detail_tree.config(columns=[])
        
        self.detail_label.config(text="Detalles")
        self.label_total_ventas.config(text="Ingresos Totales: $0.00")
        self.label_total_costo.config(text="Costo de Mercadería: $0.00")
        self.label_ganancia_neta.config(text="Ganancia Neta: $0.00")
        self.label_margen.config(text="Margen: 0.00%")

    def mostrar_reporte_ventas(self):
        self.active_report_method = self.mostrar_reporte_ventas
        self.limpiar_vistas()
        
        columnas = {
            'id':      {'text': 'ID Venta',     'width': 80, 'anchor': CENTER, 'head_anchor': CENTER},
            'fecha':   {'text': 'Fecha y Hora', 'width': 160, 'anchor': 'w', 'head_anchor': 'w'},
            'cajero':  {'text': 'Cajero',       'width': 200, 'anchor': 'w', 'head_anchor': 'w', 'stretch': True},
            'total':   {'text': 'Total',        'width': 120, 'anchor': 'e', 'head_anchor': 'e'} # 'e' para derecha
        }
        self._configurar_treeview(self.main_tree, columnas)
        
        ventas = obtener_ventas_por_rango(self.fecha_inicio_entry.entry.get(), self.fecha_fin_entry.entry.get())
        if not ventas:
            messagebox.showinfo("Sin Resultados", "No se encontraron ventas en el período.", parent=self.parent_frame)
            return
        for venta in ventas:
            self.main_tree.insert('', END, values=(venta[0], venta[1], venta[2], f"${venta[3]:.2f}"))
    
    def mostrar_reporte_compras(self):
        self.active_report_method = self.mostrar_reporte_compras
        self.limpiar_vistas()

        columnas = {
            'id':        {'text': 'ID Compra',   'width': 80, 'anchor': CENTER, 'head_anchor': CENTER},
            'fecha':     {'text': 'Fecha',       'width': 150, 'anchor': 'w', 'head_anchor': 'w'},
            'proveedor': {'text': 'Proveedor',   'width': 250, 'anchor': 'w', 'head_anchor': 'w', 'stretch': True},
            'total':     {'text': 'Total Costo', 'width': 120, 'anchor': 'e', 'head_anchor': 'e'}
        }
        self._configurar_treeview(self.main_tree, columnas)

        compras = obtener_compras_por_rango(self.fecha_inicio_entry.entry.get(), self.fecha_fin_entry.entry.get())
        if not compras:
            messagebox.showinfo("Sin Resultados", "No se encontraron compras en el período.", parent=self.parent_frame)
            return
        for compra in compras:
            self.main_tree.insert('', END, values=(compra[0], compra[1], compra[2], f"${compra[3]:.2f}"))

    def mostrar_reporte_top_productos(self):
        self.active_report_method = self.mostrar_reporte_top_productos
        self.limpiar_vistas()

        columnas = {
            'producto': {'text': 'Producto',         'width': 400, 'anchor': 'w', 'head_anchor': 'w', 'stretch': True},
            'cantidad': {'text': 'Cantidad Vendida', 'width': 150, 'anchor': CENTER, 'head_anchor': CENTER}
        }
        self._configurar_treeview(self.main_tree, columnas)
        
        productos = obtener_productos_mas_vendidos(self.fecha_inicio_entry.entry.get(), self.fecha_fin_entry.entry.get())
        if not productos:
            messagebox.showinfo("Sin Resultados", "No se vendieron productos en el período.", parent=self.parent_frame)
            return
        for producto in productos:
            self.main_tree.insert('', END, values=producto)
    
    def mostrar_detalle_seleccion(self, event=None):
        self.detail_tree.delete(*self.detail_tree.get_children())
        seleccion = self.main_tree.focus()
        if not seleccion: return
        
        try:
            columnas_actuales = self.main_tree['columns']
            valores_item = self.main_tree.item(seleccion, 'values')
            if not valores_item: return
            id_seleccionado = valores_item[0]
        except (IndexError, KeyError):
            return

        if columnas_actuales == ('id', 'fecha', 'cajero', 'total'):
            self.detail_label.config(text=f"Detalle de Venta #{id_seleccionado}")
            columnas = {
                'producto': {'text': 'Producto', 'width': 300, 'anchor': 'w', 'head_anchor': 'w', 'stretch': True},
                'cantidad': {'text': 'Cant.',    'width': 80,  'anchor': CENTER, 'head_anchor': CENTER},
                'subtotal': {'text': 'Subtotal', 'width': 120, 'anchor': 'e', 'head_anchor': 'e'}
            }
            self._configurar_treeview(self.detail_tree, columnas)
            
            detalles = obtener_detalle_de_venta(id_seleccionado)
            for d in detalles: self.detail_tree.insert('', END, values=(d[0], d[1], f"${d[2]:.2f}"))
        
        elif columnas_actuales == ('id', 'fecha', 'proveedor', 'total'):
            self.detail_label.config(text=f"Detalle de Compra #{id_seleccionado}")
            columnas = {
                'producto': {'text': 'Producto',    'width': 300, 'anchor': 'w', 'head_anchor': 'w', 'stretch': True},
                'cantidad': {'text': 'Cant.',       'width': 80,  'anchor': CENTER, 'head_anchor': CENTER},
                'costo_u':  {'text': 'Costo Unit.', 'width': 120, 'anchor': 'e', 'head_anchor': 'e'},
                'subtotal': {'text': 'Subtotal',    'width': 120, 'anchor': 'e', 'head_anchor': 'e'}
            }
            self._configurar_treeview(self.detail_tree, columnas)
            
            detalles = obtener_detalle_de_compra(id_seleccionado)
            for d in detalles: self.detail_tree.insert('', END, values=(d[0], d[1], f"${d[2]:.2f}", f"${d[3]:.2f}"))

    def mostrar_reporte_ganancias(self):
        self.active_report_method = self.mostrar_reporte_ganancias
        self.limpiar_vistas()
        
        fecha_inicio, fecha_fin = self.fecha_inicio_entry.entry.get(), self.fecha_fin_entry.entry.get()
        reporte_general = obtener_reporte_ganancias(fecha_inicio, fecha_fin)
        
        if not reporte_general or reporte_general.get('total_ventas', 0) == 0:
            messagebox.showinfo("Sin Resultados", "No hay datos para calcular ganancias.", parent=self.parent_frame)
            return
            
        total_ventas, ganancia_neta = reporte_general['total_ventas'], reporte_general['ganancia_neta']
        margen = (ganancia_neta / total_ventas) * 100 if total_ventas > 0 else 0
        self.label_total_ventas.config(text=f"Ingresos Totales: ${total_ventas:.2f}")
        self.label_total_costo.config(text=f"Costo de Mercadería: ${reporte_general['total_costo']:.2f}")
        self.label_ganancia_neta.config(text=f"Ganancia Neta: ${ganancia_neta:.2f}")
        self.label_margen.config(text=f"Margen: {margen:.2f}%")

        columnas = {
            'producto': {'text': 'Producto',       'width': 250, 'anchor': 'w', 'head_anchor': 'w', 'stretch': True},
            'cantidad': {'text': 'Cant. Vendida',  'width': 100, 'anchor': CENTER, 'head_anchor': CENTER},
            'ingresos': {'text': 'Ingresos',       'width': 120, 'anchor': 'e', 'head_anchor': 'e'},
            'costo':    {'text': 'Costo',          'width': 120, 'anchor': 'e', 'head_anchor': 'e'},
            'ganancia': {'text': 'Ganancia Neta',  'width': 120, 'anchor': 'e', 'head_anchor': 'e'}
        }
        self._configurar_treeview(self.main_tree, columnas)

        reporte_productos = obtener_ganancias_por_producto(fecha_inicio, fecha_fin)
        for prod in reporte_productos:
            self.main_tree.insert('', END, values=(prod[0], prod[1], f"${prod[2]:.2f}", f"${prod[3]:.2f}", f"${prod[4]:.2f}"))