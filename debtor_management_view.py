# debtor_management_view.py - CORREGIDO FASE 1
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from datetime import datetime
from database import (
    obtener_deudores,
    agregar_deudor,
    actualizar_deudor,
    eliminar_deudor,
    obtener_deudor_por_id,
    registrar_pago_deudor,
    obtener_ventas_deudor,
    obtener_pagos_de_una_venta,
    obtener_deudas_pendientes_deudor,
    obtener_deudas_pagadas_deudor,
)
from base_dialog import BaseDialog


class DebtorManagementView:
    def __init__(self, parent_frame, usuario_id):  # ✅ AGREGADO usuario_id
        self.parent_frame = parent_frame
        self.usuario_id = usuario_id  # ✅ AGREGADO

        ttk.Label(
            self.parent_frame,
            text="Gestión de Deudores",
            font=("Helvetica", 16, "bold"),
        ).pack(pady=10)

        control_frame = ttk.Frame(self.parent_frame)
        control_frame.pack(fill=X, padx=10, pady=5)

        ttk.Button(
            control_frame,
            text="Añadir Nuevo Deudor",
            command=self.abrir_formulario,
            bootstyle="success",
        ).pack(side=LEFT)
        ttk.Button(
            control_frame,
            text="Modificar Seleccionado",
            command=self.editar_seleccionado,
            bootstyle="info",
        ).pack(side=LEFT, padx=10)
        ttk.Button(
            control_frame,
            text="Eliminar Seleccionado",
            command=self.eliminar_seleccionado,
            bootstyle="danger",
        ).pack(side=LEFT)
        ttk.Button(
            control_frame,
            text="Ver Estado de Cuenta",
            command=self.ver_estado_de_cuenta,
            bootstyle="primary",
        ).pack(side=LEFT, padx=10)

        columns = ("id", "nombre", "telefono", "saldo")
        self.tree = ttk.Treeview(
            self.parent_frame, columns=columns, show="headings", bootstyle="primary"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre del Deudor")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("saldo", text="Saldo Pendiente")

        self.tree.column("id", width=50, anchor=CENTER)
        self.tree.column("nombre", width=300)
        self.tree.column("telefono", width=150)
        self.tree.column("saldo", width=150, anchor=E)

        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.tree.tag_configure("pagado", background="#dcf0d9")

        self.cargar_deudores()

    def cargar_deudores(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for debtor in obtener_deudores():
            saldo = debtor[3]
            saldo_formateado = f"${saldo:.2f}"
            tags = ("pagado",) if saldo <= 0 else ()
            self.tree.insert(
                "",
                END,
                values=(debtor[0], debtor[1], debtor[2], saldo_formateado),
                tags=tags,
            )

    def abrir_formulario(self, deudor_id=None):
        form = DebtorForm(self.parent_frame, deudor_id, self.cargar_deudores, self.usuario_id)  # ✅ AGREGADO usuario_id
        self.parent_frame.wait_window(form)

    def editar_seleccionado(self):
        root_window = self.tree.winfo_toplevel()
        seleccion = self.tree.focus()
        if not seleccion:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un deudor para editar.",
                parent=root_window,
            )
            return
        id_deudor = self.tree.item(seleccion, "values")[0]
        self.abrir_formulario(deudor_id=id_deudor)

    def eliminar_seleccionado(self):
        root_window = self.tree.winfo_toplevel()
        seleccion = self.tree.focus()

        if not seleccion:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un deudor para eliminar.",
                parent=root_window,
            )
            return

        id_deudor = self.tree.item(seleccion, "values")[0]
        nombre = self.tree.item(seleccion, "values")[1]

        if messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar a '{nombre}'? Solo se permitirá si su saldo es $0.00.",
            parent=root_window,
        ):
            resultado = eliminar_deudor(self.usuario_id, id_deudor)  # ✅ AGREGADO usuario_id

            if resultado is True:
                messagebox.showinfo("Éxito", "Deudor eliminado.", parent=root_window)
                self.cargar_deudores()
            else:
                messagebox.showerror("Error", str(resultado), parent=root_window)

    def ver_estado_de_cuenta(self):
        root_window = self.tree.winfo_toplevel()
        seleccion = self.tree.focus()
        if not seleccion:
            messagebox.showwarning(
                "Sin Selección", "Por favor, selecciona un deudor.", parent=root_window
            )
            return
        id_deudor = self.tree.item(seleccion, "values")[0]
        AccountStatusView(self.parent_frame, id_deudor, self.cargar_deudores, self.usuario_id)  # ✅ AGREGADO usuario_id


class DebtorForm(BaseDialog):
    def __init__(self, parent, deudor_id, callback, usuario_id):  # ✅ AGREGADO usuario_id
        title = "Editar Deudor" if deudor_id else "Formulario de Deudor"
        super().__init__(parent, title=title)

        self.deudor_id = deudor_id
        self.callback = callback
        self.usuario_id = usuario_id  # ✅ AGREGADO
        self.deudor_data = None

        if self.deudor_id:
            self.deudor_data = obtener_deudor_por_id(self.deudor_id)

        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(expand=True, fill=BOTH)

        campos = ["Nombre:", "Teléfono:", "Dirección:", "Notas:"]
        self.entries = {}
        for i, campo in enumerate(campos):
            ttk.Label(form_frame, text=campo).grid(row=i, column=0, sticky="w", pady=5)
            self.entries[campo] = ttk.Entry(form_frame, width=40)
            self.entries[campo].grid(row=i, column=1, sticky="ew", pady=5)

        if self.deudor_data:
            self.entries["Nombre:"].insert(0, self.deudor_data[1])
            self.entries["Teléfono:"].insert(0, self.deudor_data[2])
            self.entries["Dirección:"].insert(0, self.deudor_data[3])
            self.entries["Notas:"].insert(0, self.deudor_data[4])

        ttk.Button(
            form_frame, text="Guardar", command=self.guardar, bootstyle="success"
        ).grid(row=len(campos), column=0, columnspan=2, pady=15)

    def guardar(self):
        nombre = self.entries["Nombre:"].get()
        if not nombre:
            messagebox.showerror(
                "Campo Obligatorio", "El nombre es obligatorio.", parent=self
            )
            return
        datos = {
            "nombre": nombre,
            "telefono": self.entries["Teléfono:"].get(),
            "direccion": self.entries["Dirección:"].get(),
            "notas": self.entries["Notas:"].get(),
        }

        if self.deudor_id:
            resultado = actualizar_deudor(self.usuario_id, self.deudor_id, **datos)  # ✅ AGREGADO usuario_id
        else:
            resultado = agregar_deudor(self.usuario_id, **datos)  # ✅ AGREGADO usuario_id

        if resultado is True:
            try:
                self.callback(nombre_nuevo_deudor=nombre)
            except TypeError:
                self.callback()
            messagebox.showinfo("Éxito", "Deudor guardado.", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error", str(resultado), parent=self)


class AccountStatusView(ttk.Toplevel):
    def __init__(self, parent, deudor_id, callback_refrescar_lista, usuario_id):  # ✅ AGREGADO usuario_id
        super().__init__(title="Estado de Cuenta")
        self.deudor_id = deudor_id
        self.callback = callback_refrescar_lista
        self.usuario_id = usuario_id  # ✅ AGREGADO

        self.deudor_data = obtener_deudor_por_id(self.deudor_id)
        if not self.deudor_data:
            self.destroy()
            return

        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(expand=True, fill=BOTH)

        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=X, pady=(0, 10))
        ttk.Label(
            info_frame,
            text=f"Deudor: {self.deudor_data[1]}",
            font=("Helvetica", 14, "bold"),
        ).pack(side=LEFT)
        self.saldo_label = ttk.Label(info_frame, font=("Helvetica", 14, "bold"))
        self.saldo_label.pack(side=RIGHT)
        self.actualizar_label_saldo()

        self.btn_registrar_pago = ttk.Button(
            main_frame,
            text="Registrar Pago a la Deuda Seleccionada",
            command=self.registrar_pago,
            state="disabled",
        )
        self.btn_registrar_pago.pack(fill=X, ipady=5, pady=5)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=10)

        tab1 = ttk.Frame(notebook)
        tab2 = ttk.Frame(notebook)
        notebook.add(tab1, text=" Deudas y Pagos Actuales ")
        notebook.add(tab2, text=" Historial de Deudas Saldadas ")

        deudas_frame = ttk.Labelframe(
            tab1, text="Deudas Pendientes (Selecciona una para pagar)", padding=5
        )
        deudas_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        deudas_cols = ("id", "fecha", "total", "saldo_deuda")
        self.deudas_tree = ttk.Treeview(
            deudas_frame, columns=deudas_cols, show="headings"
        )
        self.deudas_tree.heading("id", text="ID Venta")
        self.deudas_tree.heading("fecha", text="Fecha")
        self.deudas_tree.heading("total", text="Monto Original")
        self.deudas_tree.heading("saldo_deuda", text="Saldo Pendiente")
        self.deudas_tree.column("id", width=60, anchor=CENTER)
        self.deudas_tree.column("fecha", width=120)
        self.deudas_tree.column("total", width=100, anchor=E)
        self.deudas_tree.column("saldo_deuda", width=110, anchor=E)
        self.deudas_tree.pack(fill=BOTH, expand=True)
        self.deudas_tree.bind("<<TreeviewSelect>>", self.seleccionar_deuda)

        pagos_frame = ttk.Labelframe(
            tab1, text="Pagos de la Deuda Seleccionada", padding=5
        )
        pagos_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=(5, 0))
        pagos_cols = ("fecha", "monto")
        self.pagos_tree = ttk.Treeview(pagos_frame, columns=pagos_cols, show="headings")
        self.pagos_tree.heading("fecha", text="Fecha")
        self.pagos_tree.heading("monto", text="Monto Pagado")
        self.pagos_tree.column("fecha", width=100, anchor=CENTER)
        self.pagos_tree.column("monto", width=80, anchor=E)
        self.pagos_tree.pack(fill=BOTH, expand=True)

        historial_frame = ttk.Labelframe(
            tab2, text="Deudas Completamente Pagadas", padding=5
        )
        historial_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        historial_cols = ("id", "fecha", "total")
        self.historial_tree = ttk.Treeview(
            historial_frame, columns=historial_cols, show="headings"
        )
        self.historial_tree.heading("id", text="ID Venta")
        self.historial_tree.heading("fecha", text="Fecha")
        self.historial_tree.heading("total", text="Monto Total")
        self.historial_tree.column("id", width=80, anchor=CENTER)
        self.historial_tree.column("fecha", width=150)
        self.historial_tree.column("total", width=120, anchor=E)
        self.historial_tree.pack(fill=BOTH, expand=True)

        self.cargar_deudas_pendientes()
        self.cargar_historial_saldado()
        self.transient(parent)
        self.grab_set()

    def actualizar_datos_deudor(self):
        self.deudor_data = obtener_deudor_por_id(self.deudor_id)

    def actualizar_label_saldo(self):
        saldo_actual = self.deudor_data[5]
        color = "danger" if saldo_actual > 0 else "success"
        self.saldo_label.config(
            text=f"Saldo Total: ${saldo_actual:.2f}", bootstyle=color
        )

    def cargar_deudas_pendientes(self):
        for i in self.deudas_tree.get_children():
            self.deudas_tree.delete(i)
        deudas = obtener_deudas_pendientes_deudor(self.deudor_id)
        for deuda in deudas:
            self.deudas_tree.insert(
                "",
                END,
                values=(deuda[0], deuda[1], f"${deuda[2]:.2f}", f"${deuda[3]:.2f}"),
            )

    def cargar_historial_saldado(self):
        for i in self.historial_tree.get_children():
            self.historial_tree.delete(i)
        deudas_pagadas = obtener_deudas_pagadas_deudor(self.deudor_id)
        for deuda in deudas_pagadas:
            self.historial_tree.insert(
                "", END, values=(deuda[0], deuda[1], f"${deuda[2]:.2f}")
            )

    def seleccionar_deuda(self, event=None):
        seleccion = self.deudas_tree.focus()
        if seleccion:
            self.btn_registrar_pago.config(state="normal")
            venta_id = self.deudas_tree.item(seleccion, "values")[0]
            self.cargar_historial_pagos(venta_id)
        else:
            self.btn_registrar_pago.config(state="disabled")
            self.limpiar_treeview(self.pagos_tree)

    def cargar_historial_pagos(self, venta_id):
        self.limpiar_treeview(self.pagos_tree)
        pagos = obtener_pagos_de_una_venta(venta_id)
        for pago in pagos:
            self.pagos_tree.insert("", END, values=(pago[0], f"${pago[1]:.2f}"))

    def registrar_pago(self):
        seleccion = self.deudas_tree.focus()
        if not seleccion:
            root_window = self.deudas_tree.winfo_toplevel()
            messagebox.showwarning(
                "Sin Selección",
                "Debes seleccionar una deuda de la lista.",
                parent=root_window,
            )
            return

        venta_id = self.deudas_tree.item(seleccion, "values")[0]
        saldo_pendiente_str = self.deudas_tree.item(seleccion, "values")[3]
        saldo_pendiente = float(saldo_pendiente_str.replace("$", ""))

        monto = simpledialog.askfloat(
            "Registrar Pago",
            f"El saldo de esta deuda es ${saldo_pendiente:.2f}.\n\nIngrese el monto del pago:",
            parent=self.deudas_tree.winfo_toplevel(),
            minvalue=0.01,
            maxvalue=saldo_pendiente,
        )

        if monto is None:
            return

        resultado = registrar_pago_deudor(self.usuario_id, self.deudor_id, venta_id, monto)  # ✅ AGREGADO usuario_id
        if resultado is True:
            messagebox.showinfo(
                "Éxito", "Pago registrado.", parent=self.deudas_tree.winfo_toplevel()
            )
            self.actualizar_datos_deudor()
            self.actualizar_label_saldo()
            self.cargar_deudas_pendientes()
            self.cargar_historial_saldado()
            self.limpiar_treeview(self.pagos_tree)
            self.btn_registrar_pago.config(state="disabled")
            self.callback()
        else:
            messagebox.showerror(
                "Error", str(resultado), parent=self.deudas_tree.winfo_toplevel()
            )

    def limpiar_treeview(self, tree):
        for item in tree.get_children():
            tree.delete(item)