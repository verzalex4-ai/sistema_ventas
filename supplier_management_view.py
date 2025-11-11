# supplier_management_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import (
    obtener_proveedores,
    obtener_proveedor_por_id,
    agregar_proveedor,
    actualizar_proveedor,
    eliminar_proveedor,
)
from base_dialog import BaseDialog  # <-- IMPORTACIÓN AÑADIDA


class SupplierManagementView:
    def __init__(self, parent_frame, main_window, usuario_id):
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.usuario_id = usuario_id

        ttk.Label(
            self.parent_frame,
            text="Gestión de Proveedores",
            font=("Helvetica", 16, "bold"),
        ).pack(pady=10)

        control_frame = ttk.Frame(self.parent_frame)
        control_frame.pack(fill=X, padx=10, pady=5)

        ttk.Button(
            control_frame,
            text="Añadir Proveedor",
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

        columns = ("id", "nombre", "telefono", "email")
        self.tree = ttk.Treeview(
            self.parent_frame, columns=columns, show="headings", bootstyle="primary"
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("telefono", text="Teléfono")
        self.tree.heading("email", text="Email")

        self.tree.column("id", width=50, anchor=CENTER)
        self.tree.column("nombre", width=300)
        self.tree.column("telefono", width=150)
        self.tree.column("email", width=250)

        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.cargar_proveedores()

    def cargar_proveedores(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for supplier in obtener_proveedores():
            self.tree.insert("", END, values=supplier)

    def abrir_formulario(self, proveedor=None):
        SupplierForm(self.parent_frame, proveedor, self.cargar_proveedores)

    def editar_seleccionado(self):
        # 1. Obtener la referencia de la ventana principal para la Modalidad.
        # Usamos self.tree ya que es el widget de la tabla visible.
        root_window = self.tree.winfo_toplevel()

        seleccion = self.tree.focus()

        if not seleccion:
            # 2. Aplicamos la Modalidad al mensaje de "Sin Selección"
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un proveedor para editar.",
                parent=root_window,  # <-- ¡Modalidad aplicada!
            )
            return

        id_proveedor = self.tree.item(seleccion, "values")[0]
        proveedor_completo = obtener_proveedor_por_id(id_proveedor)

        if proveedor_completo:
            self.abrir_formulario(proveedor_completo)
        else:
            # 3. Aplicamos la Modalidad al mensaje de "Error"
            messagebox.showerror(
                "Error",
                "No se pudieron obtener los datos del proveedor.",
                parent=root_window,  # <-- ¡Modalidad aplicada!
            )

    def eliminar_seleccionado(self):
        root_window = self.tree.winfo_toplevel()
        seleccion = self.tree.focus()

        if not seleccion:
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un proveedor para eliminar.",
                parent=root_window,
            )
            return

        id_proveedor = self.tree.item(seleccion, "values")[0]
        nombre = self.tree.item(seleccion, "values")[1]

        # Mostrar el diálogo de confirmación antes de intentar cualquier eliminación
        if messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar al proveedor '{nombre}'? Esta acción es PERMANENTE si se procede.",
            parent=root_window,
        ):
            # La función de la BD (modificada) devuelve True o False
            if eliminar_proveedor(id_proveedor):
                # ÉXITO: El proveedor no tenía productos y se eliminó.
                messagebox.showinfo(
                    "Éxito",
                    f"El proveedor '{nombre}' ha sido eliminado.",
                    parent=root_window,
                )
                self.cargar_proveedores()
            else:
                # ERROR: Falló porque tenía productos.
                messagebox.showerror(
                    "Error de Eliminación",
                    f"No se pudo eliminar al proveedor '{nombre}'. Verifique que no tenga productos asociados.",
                    parent=root_window,
                )


# --- CLASE MODIFICADA: Ahora hereda de BaseDialog ---
class SupplierForm(BaseDialog):
    def __init__(self, parent, proveedor, callback):
        title = "Editar Proveedor" if proveedor else "Formulario de Proveedor"
        super().__init__(parent, title=title)

        self.proveedor = proveedor
        self.callback = callback

        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(expand=True, fill=BOTH)

        campos = ["Nombre:", "Teléfono:", "Email:", "Dirección:"]
        self.entries = {}
        for i, campo in enumerate(campos):
            ttk.Label(form_frame, text=campo).grid(row=i, column=0, sticky="w", pady=5)
            self.entries[campo] = ttk.Entry(form_frame, width=40)
            self.entries[campo].grid(row=i, column=1, sticky="ew", pady=5)

        if self.proveedor:
            # Estructura: (id, nombre, telefono, email, direccion, activo)
            self.entries["Nombre:"].insert(0, self.proveedor[1])
            self.entries["Teléfono:"].insert(0, self.proveedor[2])
            self.entries["Email:"].insert(0, self.proveedor[3])
            self.entries["Dirección:"].insert(0, self.proveedor[4])
            
        ttk.Button(
            form_frame, text="Guardar", command=self.guardar, bootstyle="success"
        ).grid(row=len(campos), column=0, columnspan=2, pady=15)
        # El centrado, transient y grab_set() ahora son automáticos

    def guardar(self):
        nombre = self.entries["Nombre:"].get()
        if not nombre:
            messagebox.showerror(
                "Campo Obligatorio", "El nombre es obligatorio.", parent=self
            )
            return

        telefono = self.entries["Teléfono:"].get()
        email = self.entries["Email:"].get()
        direccion = self.entries["Dirección:"].get()

        if self.proveedor:
            resultado = actualizar_proveedor(self.proveedor[0], nombre, telefono, email, direccion)
        else:
            resultado = agregar_proveedor(nombre, telefono, email, direccion)

        if resultado is True:
            messagebox.showinfo("Éxito", "Proveedor guardado.", parent=self)
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", str(resultado), parent=self)
