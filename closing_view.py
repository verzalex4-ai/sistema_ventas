# closing_view.py - FASE 2: Diseño Corregido y Optimizado
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import (
    obtener_resumen_ventas_dia,
    registrar_cierre_caja,
    obtener_cierres_por_usuario,
    verificar_cierre_hoy,
    obtener_detalle_cierre
)
from datetime import datetime


class ClosingView:
    def __init__(self, parent_frame, usuario_id):
        self.parent_frame = parent_frame
        self.usuario_id = usuario_id
        
        # Obtener datos del sistema
        self.total_sistema = obtener_resumen_ventas_dia(self.usuario_id)
        self.total_efectivo_sistema = self.total_sistema
        
        # Verificar si ya cerró hoy
        self.ya_cerro_hoy = verificar_cierre_hoy(self.usuario_id)
        
        self.crear_interfaz()

    def crear_interfaz(self):
        """Crea la interfaz completa de cierre de caja."""
        
        # ============================================
        # CONTENEDOR PRINCIPAL
        # ============================================
        main_frame = ttk.Frame(self.parent_frame)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Frame izquierdo (formulario) con padding derecho
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(10, 5), pady=10)
        
        # Frame derecho (historial) con padding izquierdo
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 10), pady=10)
        
        # ============================================
        # LADO IZQUIERDO - FORMULARIO DE CIERRE
        # ============================================
        
        # Encabezado
        header_frame = ttk.Frame(left_frame)
        header_frame.pack(fill=X, pady=(0, 15))
        
        ttk.Label(
            header_frame,
            text="💰 Cierre de Caja",
            font=("Helvetica", 18, "bold")
        ).pack(anchor=W)
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        ttk.Label(
            header_frame,
            text=f"📅 {fecha_actual}",
            font=("Helvetica", 11),
            bootstyle="info"
        ).pack(anchor=W, pady=(5, 0))
        
        # Advertencia si ya cerró hoy
        if self.ya_cerro_hoy:
            warning_frame = ttk.Frame(left_frame)
            warning_frame.pack(fill=X, pady=(0, 10))
            
            ttk.Label(
                warning_frame,
                text="⚠️ Ya realizaste un cierre hoy",
                font=("Helvetica", 10, "bold"),
                bootstyle="warning"
            ).pack(anchor=W)
        
        # Resumen del Sistema
        summary_frame = ttk.Labelframe(
            left_frame,
            text="📊 Resumen del Sistema",
            padding=15
        )
        summary_frame.pack(fill=X, pady=(0, 15))
        
        summary_grid = ttk.Frame(summary_frame)
        summary_grid.pack(fill=X)
        
        ttk.Label(
            summary_grid,
            text="Total Vendido Hoy:",
            font=("Helvetica", 11, "bold")
        ).grid(row=0, column=0, sticky=W, pady=5)
        
        ttk.Label(
            summary_grid,
            text=f"${self.total_sistema:.2f}",
            font=("Helvetica", 11),
            bootstyle="success"
        ).grid(row=0, column=1, sticky=E, padx=20, pady=5)
        
        ttk.Label(
            summary_grid,
            text="Efectivo (Sistema):",
            font=("Helvetica", 11, "bold")
        ).grid(row=1, column=0, sticky=W, pady=5)
        
        ttk.Label(
            summary_grid,
            text=f"${self.total_efectivo_sistema:.2f}",
            font=("Helvetica", 11),
            bootstyle="info"
        ).grid(row=1, column=1, sticky=E, padx=20, pady=5)
        
        summary_grid.columnconfigure(1, weight=1)
        
        # Conteo de Caja
        count_frame = ttk.Labelframe(
            left_frame,
            text="🧮 Conteo de Efectivo",
            padding=15
        )
        count_frame.pack(fill=X, pady=(0, 15))
        
        count_grid = ttk.Frame(count_frame)
        count_grid.pack(fill=X)
        
        ttk.Label(
            count_grid,
            text="Efectivo Contado:",
            font=("Helvetica", 11, "bold")
        ).grid(row=0, column=0, sticky=W, pady=5)
        
        self.efectivo_contado_var = ttk.StringVar()
        self.efectivo_contado_entry = ttk.Entry(
            count_grid,
            textvariable=self.efectivo_contado_var,
            width=15,
            font=("Helvetica", 12),
            justify=RIGHT
        )
        self.efectivo_contado_entry.grid(row=0, column=1, sticky=E, pady=5)
        self.efectivo_contado_entry.focus()
        
        count_grid.columnconfigure(1, weight=1)
        
        ttk.Button(
            count_frame,
            text="🧮 Calcular Diferencia",
            command=self.calcular_diferencia,
            bootstyle="primary",
            width=25
        ).pack(pady=(10, 0))
        
        # Resultado de la Diferencia
        result_frame = ttk.Labelframe(
            left_frame,
            text="📊 Resultado",
            padding=15
        )
        result_frame.pack(fill=X, pady=(0, 15))
        
        result_grid = ttk.Frame(result_frame)
        result_grid.pack()
        
        ttk.Label(
            result_grid,
            text="Diferencia:",
            font=("Helvetica", 12, "bold")
        ).grid(row=0, column=0, padx=5)
        
        self.diferencia_label = ttk.Label(
            result_grid,
            text="$0.00",
            font=("Helvetica", 16, "bold"),
            bootstyle="secondary"
        )
        self.diferencia_label.grid(row=0, column=1, padx=5)
        
        self.estado_label = ttk.Label(
            result_grid,
            text="",
            font=("Helvetica", 12)
        )
        self.estado_label.grid(row=0, column=2, padx=5)
        
        # Observaciones
        obs_frame = ttk.Labelframe(
            left_frame,
            text="📝 Observaciones (opcional)",
            padding=10
        )
        obs_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
        
        self.observaciones_text = ttk.Text(
            obs_frame,
            height=4,
            font=("Helvetica", 10),
            wrap=WORD
        )
        self.observaciones_text.pack(fill=BOTH, expand=True)
        
        # Botón Registrar
        self.btn_registrar = ttk.Button(
            left_frame,
            text="✅ Registrar Cierre de Caja",
            command=self.registrar_cierre,
            bootstyle="success",
            state="disabled"
        )
        self.btn_registrar.pack(fill=X, ipady=8)
        
        # ============================================
        # LADO DERECHO - HISTORIAL DE CIERRES
        # ============================================
        
        history_header = ttk.Frame(right_frame)
        history_header.pack(fill=X, pady=(0, 10))
        
        ttk.Label(
            history_header,
            text="📜 Historial de Cierres",
            font=("Helvetica", 14, "bold")
        ).pack(side=LEFT)
        
        ttk.Button(
            history_header,
            text="🔄",
            command=self.cargar_historial,
            bootstyle="info-outline",
            width=3
        ).pack(side=RIGHT)
        
        # Frame para Treeview con scrollbar
        tree_container = ttk.Frame(right_frame)
        tree_container.pack(fill=BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Treeview
        columns = ("id", "fecha", "efectivo_sistema", "efectivo_contado", "diferencia", "estado")
        self.history_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        scrollbar.config(command=self.history_tree.yview)
        
        self.history_tree.heading("id", text="ID", anchor=CENTER)
        self.history_tree.heading("fecha", text="Fecha y Hora", anchor=W)
        self.history_tree.heading("efectivo_sistema", text="Sistema", anchor=E)
        self.history_tree.heading("efectivo_contado", text="Contado", anchor=E)
        self.history_tree.heading("diferencia", text="Diferencia", anchor=E)
        self.history_tree.heading("estado", text="Estado", anchor=CENTER)
        
        self.history_tree.column("id", width=40, anchor=CENTER)
        self.history_tree.column("fecha", width=140, anchor=W)
        self.history_tree.column("efectivo_sistema", width=80, anchor=E)
        self.history_tree.column("efectivo_contado", width=80, anchor=E)
        self.history_tree.column("diferencia", width=80, anchor=E)
        self.history_tree.column("estado", width=90, anchor=CENTER)
        
        # Colores por estado
        self.history_tree.tag_configure("cuadrada", background="#d4edda", foreground="#155724")
        self.history_tree.tag_configure("sobrante", background="#fff3cd", foreground="#856404")
        self.history_tree.tag_configure("faltante", background="#f8d7da", foreground="#721c24")
        
        self.history_tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Botón Ver Detalle
        ttk.Button(
            right_frame,
            text="👁️ Ver Detalle del Cierre Seleccionado",
            command=self.ver_detalle_cierre,
            bootstyle="info-outline"
        ).pack(fill=X, pady=(10, 0))
        
        # Cargar historial
        self.cargar_historial()
        
        # Bind Enter para calcular
        self.efectivo_contado_entry.bind("<Return>", lambda e: self.calcular_diferencia())
        
        # Bind doble click en historial
        self.history_tree.bind("<Double-1>", lambda e: self.ver_detalle_cierre())

    def calcular_diferencia(self):
        """Calcula la diferencia entre el efectivo contado y el del sistema."""
        root_window = self.parent_frame.winfo_toplevel()
        
        try:
            contado_str = self.efectivo_contado_var.get().strip()
            if not contado_str:
                messagebox.showwarning(
                    "Campo Vacío",
                    "Por favor, ingresa el efectivo contado.",
                    parent=root_window
                )
                return
            
            contado = float(contado_str)
        except (ValueError, TypeError):
            messagebox.showerror(
                "Error de Entrada",
                "Por favor, ingresa un número válido.",
                parent=root_window
            )
            return
        
        if contado < 0:
            messagebox.showerror(
                "Error",
                "El monto no puede ser negativo.",
                parent=root_window
            )
            return
        
        diferencia = contado - self.total_efectivo_sistema
        
        if diferencia == 0:
            resultado_texto = f"$0.00"
            estado_texto = "✅ Cuadrada"
            estilo = "success"
        elif diferencia > 0:
            resultado_texto = f"+${diferencia:.2f}"
            estado_texto = "⚠️ Sobrante"
            estilo = "warning"
        else:
            resultado_texto = f"-${abs(diferencia):.2f}"
            estado_texto = "❌ Faltante"
            estilo = "danger"
        
        self.diferencia_label.config(text=resultado_texto, bootstyle=estilo)
        self.estado_label.config(text=estado_texto, bootstyle=estilo)
        
        # Habilitar botón de registro
        self.btn_registrar.config(state="normal")

    def registrar_cierre(self):
        """Registra el cierre de caja en la base de datos."""
        root_window = self.parent_frame.winfo_toplevel()
        
        try:
            contado = float(self.efectivo_contado_var.get())
        except (ValueError, TypeError):
            messagebox.showerror(
                "Error",
                "Debes calcular la diferencia primero.",
                parent=root_window
            )
            return
        
        observaciones = self.observaciones_text.get("1.0", "end-1c").strip()
        diferencia = contado - self.total_efectivo_sistema
        
        # Confirmación
        mensaje = f"¿Confirmar cierre de caja?\n\n"
        mensaje += f"Efectivo Sistema: ${self.total_efectivo_sistema:.2f}\n"
        mensaje += f"Efectivo Contado: ${contado:.2f}\n"
        mensaje += f"Diferencia: ${diferencia:.2f}\n"
        
        if diferencia != 0:
            estado = "SOBRANTE" if diferencia > 0 else "FALTANTE"
            mensaje += f"\n⚠️ Hay un {estado} de ${abs(diferencia):.2f}"
        
        if not messagebox.askyesno("Confirmar Cierre", mensaje, parent=root_window):
            return
        
        # Registrar en BD
        cierre_id = registrar_cierre_caja(
            self.usuario_id,
            self.total_sistema,
            self.total_efectivo_sistema,
            contado,
            observaciones
        )
        
        if cierre_id:
            messagebox.showinfo(
                "Éxito",
                f"✅ Cierre registrado exitosamente.\n\nID del Cierre: {cierre_id}",
                parent=root_window
            )
            
            # Limpiar formulario
            self.efectivo_contado_var.set("")
            self.observaciones_text.delete("1.0", "end")
            self.diferencia_label.config(text="$0.00", bootstyle="secondary")
            self.estado_label.config(text="")
            self.btn_registrar.config(state="disabled")
            
            # Recargar historial
            self.cargar_historial()
            self.ya_cerro_hoy = True
        else:
            messagebox.showerror(
                "Error",
                "No se pudo registrar el cierre de caja.",
                parent=root_window
            )

    def cargar_historial(self):
        """Carga el historial de cierres del usuario."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        cierres = obtener_cierres_por_usuario(self.usuario_id, limite=20)
        
        if not cierres:
            return
        
        for cierre in cierres:
            cierre_id, fecha_hora, total_ventas, efectivo_sistema, efectivo_contado, diferencia, obs = cierre
            
            # Formatear fecha (solo fecha y hora, sin segundos)
            try:
                dt = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
                fecha_format = dt.strftime("%d/%m/%Y %H:%M")
            except:
                fecha_format = fecha_hora
            
            if diferencia == 0:
                estado = "✅ Cuadrada"
                tag = "cuadrada"
            elif diferencia > 0:
                estado = f"⚠️ +${diferencia:.2f}"
                tag = "sobrante"
            else:
                estado = f"❌ -${abs(diferencia):.2f}"
                tag = "faltante"
            
            self.history_tree.insert(
                "",
                END,
                values=(
                    cierre_id,
                    fecha_format,
                    f"${efectivo_sistema:.2f}",
                    f"${efectivo_contado:.2f}",
                    f"${diferencia:.2f}",
                    estado
                ),
                tags=(tag,)
            )

    def ver_detalle_cierre(self):
        """Muestra el detalle completo de un cierre seleccionado."""
        root_window = self.parent_frame.winfo_toplevel()
        seleccion = self.history_tree.focus()
        
        if not seleccion:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un cierre del historial.",
                parent=root_window
            )
            return
        
        cierre_id = self.history_tree.item(seleccion, "values")[0]
        detalle = obtener_detalle_cierre(cierre_id)
        
        if not detalle:
            messagebox.showerror(
                "Error",
                "No se pudo obtener el detalle del cierre.",
                parent=root_window
            )
            return
        
        # Mostrar ventana con el detalle
        DetalleClosingDialog(root_window, detalle)


class DetalleClosingDialog(ttk.Toplevel):
    """Ventana modal para mostrar el detalle de un cierre."""
    
    def __init__(self, parent, detalle):
        super().__init__(parent)
        self.title("Detalle del Cierre de Caja")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        
        cierre_id, fecha_hora, usuario, rol, total_ventas, efectivo_sistema, efectivo_contado, diferencia, observaciones = detalle
        
        main_frame = ttk.Frame(self, padding=25)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Encabezado
        ttk.Label(
            main_frame,
            text=f"Cierre de Caja #{cierre_id}",
            font=("Helvetica", 16, "bold"),
            bootstyle="primary"
        ).pack(pady=(0, 20))
        
        # Grid de información
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=X, pady=10)
        
        datos = [
            ("📅 Fecha y Hora:", fecha_hora),
            ("👤 Usuario:", f"{usuario} ({rol})"),
            ("💰 Total Ventas:", f"${total_ventas:.2f}"),
            ("💵 Efectivo Sistema:", f"${efectivo_sistema:.2f}"),
            ("🧮 Efectivo Contado:", f"${efectivo_contado:.2f}"),
            ("📊 Diferencia:", f"${diferencia:.2f}")
        ]
        
        for i, (label, value) in enumerate(datos):
            ttk.Label(
                info_frame,
                text=label,
                font=("Helvetica", 11, "bold")
            ).grid(row=i, column=0, sticky=W, pady=5, padx=(0, 15))
            
            # Color especial para la diferencia
            if "Diferencia" in label:
                if diferencia == 0:
                    style = "success"
                elif diferencia > 0:
                    style = "warning"
                else:
                    style = "danger"
                
                ttk.Label(
                    info_frame,
                    text=value,
                    font=("Helvetica", 11, "bold"),
                    bootstyle=style
                ).grid(row=i, column=1, sticky=W, pady=5)
            else:
                ttk.Label(
                    info_frame,
                    text=value,
                    font=("Helvetica", 11)
                ).grid(row=i, column=1, sticky=W, pady=5)
        
        # Observaciones
        if observaciones:
            ttk.Separator(main_frame, orient=HORIZONTAL).pack(fill=X, pady=15)
            
            ttk.Label(
                main_frame,
                text="📝 Observaciones:",
                font=("Helvetica", 11, "bold")
            ).pack(anchor=W, pady=(0, 5))
            
            obs_frame = ttk.Frame(main_frame)
            obs_frame.pack(fill=BOTH, expand=True, pady=(0, 15))
            
            obs_text = ttk.Text(
                obs_frame,
                height=4,
                font=("Helvetica", 10),
                wrap=WORD,
                state="normal"
            )
            obs_text.insert("1.0", observaciones)
            obs_text.config(state="disabled")
            obs_text.pack(fill=BOTH, expand=True)
        
        # Botón cerrar
        ttk.Button(
            main_frame,
            text="Cerrar",
            command=self.destroy,
            bootstyle="secondary",
            width=15
        ).pack(pady=(15, 0))
        
        # Centrar
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")