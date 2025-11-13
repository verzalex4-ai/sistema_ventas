# auditoria_view.py - CORREGIDO FASE 1

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Querybox
from tkinter import messagebox, filedialog
from database import obtener_registro_auditoria
from datetime import datetime, timedelta
import csv

class AuditoriaView:
    def __init__(self, master):
        self.master = master
        self.frame = ttk.Frame(master, padding=15)
        self.frame.pack(fill=BOTH, expand=True)

        self.datos_completos = []
        
        self.categorias_acciones = {
            "TODAS": "Todas las Acciones",
            "PROD": "Productos",
            "VENTA": "Ventas",
            "USUARIO": "Usuarios",
            "DEUDOR": "Deudores",
            "PROVEEDOR": "Proveedores",
            "COMPRA": "Compras",
            "CATEGORIA": "Categorías",
            "PAGO": "Pagos"
        }

        self.crear_interfaz()
        self.cargar_datos_auditoria()

    def crear_interfaz(self):
        """Crea toda la interfaz de usuario."""
        
        # ENCABEZADO
        header_frame = ttk.Frame(self.frame)
        header_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            header_frame, 
            text="🕵️ REGISTRO DE AUDITORÍA Y ACTIVIDAD", 
            font=("Helvetica", 18, "bold"), 
            bootstyle="primary"
        ).pack(side=LEFT)
        
        ttk.Button(
            header_frame,
            text="📊 Exportar a CSV",
            command=self.exportar_csv,
            bootstyle="success-outline"
        ).pack(side=RIGHT, padx=5)
        
        ttk.Button(
            header_frame,
            text="🔄 Refrescar",
            command=self.cargar_datos_auditoria,
            bootstyle="info-outline"
        ).pack(side=RIGHT)

        # PANEL DE FILTROS
        filtros_frame = ttk.LabelFrame(self.frame, text="🔍 Filtros de Búsqueda", padding=15)
        filtros_frame.pack(fill=X, pady=(0, 10))

        # FILA 1: Búsqueda y Categoría
        row1 = ttk.Frame(filtros_frame)
        row1.pack(fill=X, pady=(0, 10))

        ttk.Label(row1, text="Buscar:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 5))
        self.search_var = ttk.StringVar()
        search_entry = ttk.Entry(row1, textvariable=self.search_var, width=40)
        search_entry.pack(side=LEFT, padx=(0, 20))
        search_entry.bind("<KeyRelease>", lambda e: self.aplicar_filtros())
        
        ttk.Label(row1, text="Categoría:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 5))
        self.categoria_var = ttk.StringVar(value="TODAS")
        categoria_combo = ttk.Combobox(
            row1, 
            textvariable=self.categoria_var,
            values=list(self.categorias_acciones.values()),
            state="readonly",
            width=20
        )
        categoria_combo.pack(side=LEFT)
        categoria_combo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        # FILA 2: Usuario y Rol
        row2 = ttk.Frame(filtros_frame)
        row2.pack(fill=X, pady=(0, 10))

        ttk.Label(row2, text="Usuario:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 5))
        self.usuario_var = ttk.StringVar(value="Todos")
        self.usuario_combo = ttk.Combobox(
            row2,
            textvariable=self.usuario_var,
            values=["Todos"],
            state="readonly",
            width=15
        )
        self.usuario_combo.pack(side=LEFT, padx=(0, 20))
        self.usuario_combo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        ttk.Label(row2, text="Rol:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 5))
        self.rol_var = ttk.StringVar(value="Todos")
        rol_combo = ttk.Combobox(
            row2,
            textvariable=self.rol_var,
            values=["Todos", "admin", "usuario", "auditor"],
            state="readonly",
            width=12
        )
        rol_combo.pack(side=LEFT, padx=(0, 20))
        rol_combo.bind("<<ComboboxSelected>>", lambda e: self.aplicar_filtros())

        # FILA 3: Rango de Fechas
        row3 = ttk.Frame(filtros_frame)
        row3.pack(fill=X)

        ttk.Label(row3, text="Rango de Fechas:", font=("Helvetica", 10, "bold")).pack(side=LEFT, padx=(0, 10))

        ttk.Label(row3, text="Desde:").pack(side=LEFT, padx=(0, 5))
        self.fecha_desde_entry = ttk.DateEntry(
            row3,
            bootstyle="primary",
            dateformat="%Y-%m-%d",
            firstweekday=0,
            startdate=datetime.now()
        )
        self.fecha_desde_entry.pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            row3,
            text="✖",
            command=self.limpiar_fecha_desde,
            bootstyle="danger-outline",
            width=3
        ).pack(side=LEFT, padx=(0, 15))
        
        ttk.Label(row3, text="Hasta:").pack(side=LEFT, padx=(0, 5))
        self.fecha_hasta_entry = ttk.DateEntry(
            row3,
            bootstyle="primary",
            dateformat="%Y-%m-%d",
            firstweekday=0,
            startdate=datetime.now()
        )
        self.fecha_hasta_entry.pack(side=LEFT, padx=(0, 5))
        
        ttk.Button(
            row3,
            text="✖",
            command=self.limpiar_fecha_hasta,
            bootstyle="danger-outline",
            width=3
        ).pack(side=LEFT, padx=(0, 15))

        ttk.Label(row3, text="(Formato: YYYY-MM-DD)", font=("Helvetica", 8)).pack(side=LEFT, padx=(0, 10))

        ttk.Button(row3, text="Hoy", command=lambda: self.filtro_rapido("hoy"), bootstyle="info", width=8).pack(side=LEFT, padx=2)
        ttk.Button(row3, text="7 días", command=lambda: self.filtro_rapido("7dias"), bootstyle="info", width=8).pack(side=LEFT, padx=2)
        ttk.Button(row3, text="30 días", command=lambda: self.filtro_rapido("30dias"), bootstyle="info", width=8).pack(side=LEFT, padx=2)
        ttk.Button(row3, text="Limpiar", command=self.limpiar_filtros, bootstyle="warning", width=8).pack(side=LEFT, padx=2)
        
        # ESTADÍSTICAS
        stats_frame = ttk.Frame(self.frame)
        stats_frame.pack(fill=X, pady=(0, 10))

        self.stats_label = ttk.Label(
            stats_frame,
            text="📊 Total de registros: 0 | Mostrando: 0",
            font=("Helvetica", 10, "bold"),
            bootstyle="info"
        )
        self.stats_label.pack(side=LEFT)

        # TABLA DE REGISTROS
        table_frame = ttk.Frame(self.frame)
        table_frame.pack(fill=BOTH, expand=True)

        scrollbar_y = ttk.Scrollbar(table_frame, orient=VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=HORIZONTAL)

        self.columns = ("fecha_hora", "usuario", "rol", "accion", "descripcion")
        self.tree = ttk.Treeview(
            table_frame,
            columns=self.columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            bootstyle="primary"
        )

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        self.tree.heading("fecha_hora", text="📅 Fecha y Hora", anchor=W)
        self.tree.heading("usuario", text="👤 Usuario", anchor=W)
        self.tree.heading("rol", text="🎭 Rol", anchor=CENTER)
        self.tree.heading("accion", text="⚡ Acción", anchor=W)
        self.tree.heading("descripcion", text="📝 Descripción", anchor=W)

        self.tree.column("fecha_hora", width=150, anchor=W)
        self.tree.column("usuario", width=120, anchor=W)
        self.tree.column("rol", width=80, anchor=CENTER)
        self.tree.column("accion", width=150, anchor=W)
        self.tree.column("descripcion", width=500, anchor=W)

        self.tree.tag_configure("oddrow", background="#161d80")
        self.tree.tag_configure("evenrow", background="#161d80")

        self.tree.tag_configure("CREADO", foreground="#28a745")
        self.tree.tag_configure("ACTUALIZADO", foreground="#007bff")
        self.tree.tag_configure("ELIMINADO", foreground="#dc3545")
        self.tree.tag_configure("DESACTIVADO", foreground="#ffc107")

        self.tree.tag_configure('selected', foreground='black')
        self.tree.tag_bind('<<TreeviewSelect>>', lambda e: None)
        
        scrollbar_y.pack(side=RIGHT, fill=Y)
        scrollbar_x.pack(side=BOTTOM, fill=X)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

    def cargar_datos_auditoria(self):
        """Carga todos los registros de auditoría desde la base de datos."""
        try:
            registros = obtener_registro_auditoria(limite=1000)
            
            if not registros:
                self.datos_completos = []
                self.mostrar_en_tabla([])
                messagebox.showinfo("Sin Registros", "No hay registros de auditoría disponibles.", parent=self.frame.winfo_toplevel())
                return

            self.datos_completos = []
            usuarios_unicos = set()
            roles_unicos = set()

            # ✅ CORRECCIÓN CRÍTICA: Ahora desempaquetamos 5 valores (con rol)
            for registro in registros:
                fecha_hora, usuario, rol, accion, descripcion = registro
                
                usuarios_unicos.add(usuario)
                roles_unicos.add(rol)
                
                self.datos_completos.append((fecha_hora, usuario, rol, accion, descripcion))

            usuarios_lista = ["Todos"] + sorted(list(usuarios_unicos))
            self.usuario_combo.config(values=usuarios_lista)

            self.limpiar_fecha_desde()
            self.limpiar_fecha_hasta()
            
            self.aplicar_filtros()

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar los registros de auditoría:\n{e}", parent=self.frame.winfo_toplevel())

    def aplicar_filtros(self):
        """Aplica todos los filtros activos a los datos."""
        if not self.datos_completos:
            self.mostrar_en_tabla([])
            return

        busqueda = self.search_var.get().lower().strip()
        categoria_seleccionada = self.categoria_var.get()
        usuario_seleccionado = self.usuario_var.get()
        rol_seleccionado = self.rol_var.get()
        fecha_desde = self.fecha_desde_entry.entry.get().strip()
        fecha_hasta = self.fecha_hasta_entry.entry.get().strip()

        categoria_clave = next(
            (k for k, v in self.categorias_acciones.items() if v == categoria_seleccionada),
            "TODAS"
        )

        datos_filtrados = []
        for fecha_hora, usuario, rol, accion, descripcion in self.datos_completos:
            
            if busqueda:
                texto_completo = f"{fecha_hora} {usuario} {accion} {descripcion}".lower()
                if busqueda not in texto_completo:
                    continue

            if categoria_clave != "TODAS":
                if not accion.startswith(categoria_clave):
                    continue

            if usuario_seleccionado != "Todos":
                if usuario != usuario_seleccionado:
                    continue

            if rol_seleccionado != "Todos":
                if rol != rol_seleccionado:
                    continue

            if fecha_desde:
                try:
                    fecha_registro = datetime.strptime(fecha_hora.split()[0], "%Y-%m-%d")
                    fecha_filtro_desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
                    if fecha_registro < fecha_filtro_desde:
                        continue
                except ValueError:
                    pass

            if fecha_hasta:
                try:
                    fecha_registro = datetime.strptime(fecha_hora.split()[0], "%Y-%m-%d")
                    fecha_filtro_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")
                    if fecha_registro > fecha_filtro_hasta:
                        continue
                except ValueError:
                    pass

            datos_filtrados.append((fecha_hora, usuario, rol, accion, descripcion))

        self.mostrar_en_tabla(datos_filtrados)

    def mostrar_en_tabla(self, datos):
        """Muestra los datos en el Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, (fecha_hora, usuario, rol, accion, descripcion) in enumerate(datos):
            tags = ["oddrow" if idx % 2 == 0 else "evenrow"]
            
            if "CREADO" in accion or "AGREGADO" in accion:
                tags.append("CREADO")
            elif "ACTUALIZADO" in accion or "MODIFICADO" in accion:
                tags.append("ACTUALIZADO")
            elif "ELIMINADO" in accion:
                tags.append("ELIMINADO")
            elif "DESACTIVADO" in accion:
                tags.append("DESACTIVADO")

            self.tree.insert("", END, values=(fecha_hora, usuario, rol, accion, descripcion), tags=tags)

        total = len(self.datos_completos)
        mostrados = len(datos)
        self.stats_label.config(text=f"📊 Total de registros: {total} | Mostrando: {mostrados}")

    def filtro_rapido(self, tipo):
        """Aplica filtros de fecha rápidos."""
        hoy = datetime.now()
        
        if tipo == "hoy":
            self.fecha_desde_entry.entry.delete(0, 'end')
            self.fecha_desde_entry.entry.insert(0, hoy.strftime("%Y-%m-%d"))
            self.fecha_hasta_entry.entry.delete(0, 'end')
            self.fecha_hasta_entry.entry.insert(0, hoy.strftime("%Y-%m-%d"))
        elif tipo == "7dias":
            hace_7_dias = hoy - timedelta(days=7)
            self.fecha_desde_entry.entry.delete(0, 'end')
            self.fecha_desde_entry.entry.insert(0, hace_7_dias.strftime("%Y-%m-%d"))
            self.fecha_hasta_entry.entry.delete(0, 'end')
            self.fecha_hasta_entry.entry.insert(0, hoy.strftime("%Y-%m-%d"))
        elif tipo == "30dias":
            hace_30_dias = hoy - timedelta(days=30)
            self.fecha_desde_entry.entry.delete(0, 'end')
            self.fecha_desde_entry.entry.insert(0, hace_30_dias.strftime("%Y-%m-%d"))
            self.fecha_hasta_entry.entry.delete(0, 'end')
            self.fecha_hasta_entry.entry.insert(0, hoy.strftime("%Y-%m-%d"))
        
        self.aplicar_filtros()

    def limpiar_filtros(self):
        """Limpia todos los filtros activos."""
        self.search_var.set("")
        self.categoria_var.set("TODAS")
        self.usuario_var.set("Todos")
        self.rol_var.set("Todos")
        self.limpiar_fecha_desde()
        self.limpiar_fecha_hasta()
        self.aplicar_filtros()
    
    def limpiar_fecha_desde(self):
        """Limpia solo la fecha desde."""
        self.fecha_desde_entry.entry.delete(0, 'end')
        self.aplicar_filtros()
    
    def limpiar_fecha_hasta(self):
        """Limpia solo la fecha hasta."""
        self.fecha_hasta_entry.entry.delete(0, 'end')
        self.aplicar_filtros()

    def exportar_csv(self):
        """Exporta los registros visibles a un archivo CSV."""
        datos_visibles = []
        for item in self.tree.get_children():
            valores = self.tree.item(item, "values")
            datos_visibles.append(valores)

        if not datos_visibles:
            messagebox.showwarning("Sin Datos", "No hay registros para exportar.", parent=self.frame.winfo_toplevel())
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"auditoria_{timestamp}.csv"
        
        ruta_archivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            initialfile=nombre_archivo,
            parent=self.frame.winfo_toplevel()
        )

        if not ruta_archivo:
            return

        try:
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Fecha y Hora", "Usuario", "Rol", "Acción", "Descripción"])
                writer.writerows(datos_visibles)
            
            messagebox.showinfo("Éxito", f"Registros exportados exitosamente a:\n{ruta_archivo}", parent=self.frame.winfo_toplevel())
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar:\n{e}", parent=self.frame.winfo_toplevel())