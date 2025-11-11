# closing_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import obtener_resumen_ventas_dia


class ClosingView:
    def __init__(self, parent_frame, usuario_id):
        self.parent_frame = parent_frame
        self.usuario_id = usuario_id

        self.total_sistema = obtener_resumen_ventas_dia(self.usuario_id)
        self.total_efectivo_sistema = self.total_sistema

        container = ttk.Frame(self.parent_frame)
        container.pack(expand=True, fill=BOTH, padx=20, pady=20)

        ttk.Label(
            container, text="Cierre de Caja", font=("Helvetica", 16, "bold")
        ).pack(pady=(0, 20))

        summary_frame = ttk.Labelframe(
            container, text="Resumen del Sistema", padding=15
        )
        summary_frame.pack(fill=X)

        ttk.Label(
            summary_frame,
            text="Total Vendido (Sistema):",
            font=("Helvetica", 11, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(
            summary_frame, text=f"${self.total_sistema:.2f}", font=("Helvetica", 11)
        ).grid(row=0, column=1, sticky="e", padx=5, pady=5)

        ttk.Label(
            summary_frame,
            text="Total en Efectivo (Sistema):",
            font=("Helvetica", 11, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(
            summary_frame,
            text=f"${self.total_efectivo_sistema:.2f}",
            font=("Helvetica", 11),
        ).grid(row=1, column=1, sticky="e", padx=5, pady=5)

        count_frame = ttk.Labelframe(container, text="Conteo de Caja", padding=15)
        count_frame.pack(fill=X, pady=20)

        ttk.Label(
            count_frame,
            text="Efectivo Contado en Caja:",
            font=("Helvetica", 11, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=5, pady=10)
        self.efectivo_contado_entry = ttk.Entry(
            count_frame, width=15, font=("Helvetica", 11)
        )
        self.efectivo_contado_entry.grid(row=0, column=1, sticky="e", padx=5, pady=10)

        ttk.Button(
            count_frame,
            text="Calcular Diferencia",
            command=self.calcular_diferencia,
            bootstyle="primary",
        ).grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)

        result_frame = ttk.Frame(container)
        result_frame.pack(fill=X)

        ttk.Label(
            result_frame, text="Diferencia:", font=("Helvetica", 12, "bold")
        ).pack(side=LEFT, padx=5)
        self.diferencia_label = ttk.Label(
            result_frame, text="$0.00", font=("Helvetica", 12, "bold")
        )
        self.diferencia_label.pack(side=LEFT, padx=5)

    def calcular_diferencia(self):
        # -------------------------------------------------------------------
        # 1. Obtener la referencia de la ventana principal para la Modalidad
        # Asumiendo que esta función está en una clase de Vista (ej. ClosingView)
        # y tienes acceso a un frame padre (self.parent_frame o self.main_frame)
        try:
            root_window = (
                self.main_frame.winfo_toplevel()
            )  # Ajusta self.main_frame si usas otro nombre
        except AttributeError:
            # Si no tienes un self.main_frame, usa self.efectivo_contado_entry.winfo_toplevel()
            root_window = self.efectivo_contado_entry.winfo_toplevel()
        # -------------------------------------------------------------------

        try:
            contado = float(self.efectivo_contado_entry.get())
        except (ValueError, TypeError):
            # 2. Aplicamos la Modalidad con el parámetro 'parent'
            messagebox.showerror(
                "Error de Entrada",
                "Por favor, ingresa un número válido.",
                parent=root_window,
            )
            return

        diferencia = contado - self.total_efectivo_sistema

        if diferencia == 0:
            resultado_texto, estilo = f"$0.00 (Caja Cuadrada)", "success"
        elif diferencia > 0:
            resultado_texto, estilo = f"${diferencia:.2f} (Sobrante)", "warning"
        else:
            resultado_texto, estilo = f"${diferencia:.2f} (Faltante)", "danger"

        self.diferencia_label.config(text=resultado_texto, bootstyle=estilo)
