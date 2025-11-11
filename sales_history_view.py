# sales_history_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from database import obtener_ventas_del_dia, obtener_detalle_de_venta
from datetime import datetime

class SalesHistoryView:
    def __init__(self, parent_frame, usuario_id):
        # El usuario_id ya no es necesario para la consulta, pero lo mantenemos por consistencia
        self.parent_frame = parent_frame
        
        ttk.Label(self.parent_frame, text="Historial de Ventas de Hoy (Todos los Usuarios)", font=("Helvetica", 16, "bold")).pack(pady=10)

        # --- Frame para las dos tablas ---
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # --- Tabla Principal de Ventas ---
        sales_frame = ttk.Frame(main_frame)
        sales_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        # Añadimos la columna 'usuario'
        columns = ('id', 'hora', 'usuario', 'total')
        self.history_tree = ttk.Treeview(sales_frame, columns=columns, show='headings', bootstyle="primary")
        
        self.history_tree.heading('id', text='ID Venta')
        self.history_tree.heading('hora', text='Hora')
        self.history_tree.heading('usuario', text='Vendido por')
        self.history_tree.heading('total', text='Total Vendido')
        
        self.history_tree.column('id', width=80, anchor=CENTER)
        self.history_tree.column('hora', width=120, anchor=CENTER)
        self.history_tree.column('usuario', width=150)
        self.history_tree.column('total', width=120, anchor=E)

        self.history_tree.pack(fill=BOTH, expand=True)
        # Evento para cuando se selecciona una fila
        self.history_tree.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        # --- Tabla de Detalles de la Venta ---
        details_frame = ttk.Labelframe(main_frame, text="Detalle de la Venta Seleccionada", padding=5)
        details_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        details_columns = ('producto', 'cantidad', 'subtotal')
        self.details_tree = ttk.Treeview(details_frame, columns=details_columns, show='headings', bootstyle="info")

        self.details_tree.heading('producto', text='Producto')
        self.details_tree.heading('cantidad', text='Cantidad')
        self.details_tree.heading('subtotal', text='Subtotal')

        self.details_tree.column('producto', width=200)
        self.details_tree.column('cantidad', width=80, anchor=CENTER)
        self.details_tree.column('subtotal', width=100, anchor=E)

        self.details_tree.pack(fill=BOTH, expand=True)
        
        self.cargar_historial()

    def cargar_historial(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
            
        # La función ahora trae todas las ventas del día
        ventas = obtener_ventas_del_dia()
        
        for venta in ventas:
            # venta = (id, fecha_hora, nombre_usuario, total)
            id_venta = venta[0]
            fecha_hora_obj = datetime.strptime(venta[1], "%Y-%m-%d %H:%M:%S")
            hora_formateada = fecha_hora_obj.strftime("%H:%M:%S")
            usuario = venta[2]
            total_formateado = f"${venta[3]:.2f}"
            
            self.history_tree.insert('', END, values=(id_venta, hora_formateada, usuario, total_formateado))

    def mostrar_detalle(self, event=None):
        # Limpiar la tabla de detalles
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)

        # Obtener la venta seleccionada
        seleccion = self.history_tree.focus()
        if not seleccion:
            return
            
        id_venta_seleccionada = self.history_tree.item(seleccion, 'values')[0]
        
        # Obtener y mostrar los detalles de esa venta
        detalles = obtener_detalle_de_venta(id_venta_seleccionada)
        for detalle in detalles:
            # detalle = (nombre, cantidad, subtotal)
            subtotal_formateado = f"${detalle[2]:.2f}"
            self.details_tree.insert('', END, values=(detalle[0], detalle[1], subtotal_formateado))