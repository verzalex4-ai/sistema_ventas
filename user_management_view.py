# user_management_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import obtener_usuarios, agregar_usuario, actualizar_contrasena, eliminar_usuario
from base_dialog import BaseDialog

class UserManagementView:
    # MODIFICADO: Ahora acepta 'main_window' y 'usuario_id'
    def __init__(self, parent_frame, main_window, usuario_id):
        self.parent_frame = parent_frame
        self.main_window = main_window
        self.usuario_id = usuario_id  # <--- ID del usuario para auditoría
        
        ttk.Label(self.parent_frame, text="Gestión de Usuarios", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        control_frame = ttk.Frame(self.parent_frame)
        control_frame.pack(fill=X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Añadir Nuevo Usuario", command=self.abrir_formulario_usuario, bootstyle="success").pack(side=LEFT)
        ttk.Button(control_frame, text="Cambiar Contraseña", command=self.cambiar_contrasena_seleccionada, bootstyle="info").pack(side=LEFT, padx=10)
        ttk.Button(control_frame, text="Eliminar Seleccionado", command=self.eliminar_usuario_seleccionado, bootstyle="danger").pack(side=LEFT)

        columns = ('id', 'nombre_usuario', 'rol')
        self.users_tree = ttk.Treeview(self.parent_frame, columns=columns, show='headings', bootstyle="primary")
        
        self.users_tree.heading('id', text='ID')
        self.users_tree.heading('nombre_usuario', text='Nombre de Usuario')
        self.users_tree.heading('rol', text='Rol')
        
        self.users_tree.column('id', width=50, anchor=CENTER)
        self.users_tree.column('nombre_usuario', width=300)
        self.users_tree.column('rol', width=150, anchor=CENTER)

        self.users_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.cargar_usuarios()

    def cargar_usuarios(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for user in obtener_usuarios():
            self.users_tree.insert('', END, values=user)

    def abrir_formulario_usuario(self):
        # --- CORRECCIÓN: Se añade wait_window ---
        form = UserForm(parent=self.parent_frame, callback_actualizar=self.cargar_usuarios)
        self.parent_frame.wait_window(form)

    def cambiar_contrasena_seleccionada(self):
        # 1. Obtener la referencia de la ventana principal para la Modalidad
        root_window = self.users_tree.winfo_toplevel()

        seleccion = self.users_tree.focus()

        if not seleccion:
            # Aplicamos la Modalidad al mensaje de "Sin Selección"
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un usuario.",
                parent=root_window,  # <-- Modalidad para el mensaje
            )
            return

        id_usuario = self.users_tree.item(seleccion, "values")[0]
        nombre_usuario = self.users_tree.item(seleccion, "values")[1]

        # 2. Instanciamos el formulario, pasándole la ventana raíz como 'parent'
        form = PasswordForm(
            parent=root_window,  # <-- Hacemos el formulario hijo de la ventana principal
            user_id=id_usuario,
            username=nombre_usuario,
            callback_actualizar=self.cargar_usuarios,
        )

        # 3. Bloqueamos la ventana principal (root_window) hasta que el formulario (form) se cierre.
        root_window.wait_window(form)


    def eliminar_usuario_seleccionado(self):
        # 1. Obtener la referencia de la ventana principal para la Modalidad
        root_window = self.users_tree.winfo_toplevel()

        seleccion = self.users_tree.focus()

        if not seleccion:
            # Aplicamos la Modalidad al mensaje de "Sin Selección"
            messagebox.showwarning(
                "Sin Selección",
                "Por favor, selecciona un usuario para eliminar.",
                parent=root_window,  # <-- Modalidad aplicada
            )
            return

        id_usuario = self.users_tree.item(seleccion, "values")[0]
        nombre_usuario = self.users_tree.item(seleccion, "values")[1]

        if nombre_usuario == "admin":
            # Aplicamos la Modalidad al mensaje de error
            messagebox.showerror(
                "Acción no permitida",
                "No puedes eliminar al usuario 'admin' principal.",
                parent=root_window,  # <-- Modalidad aplicada
            )
            return

        # Aplicamos la Modalidad al cuadro de diálogo de confirmación 'askyesno'
        if messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar al usuario '{nombre_usuario}'? Esta acción es permanente.",
            parent=root_window,  # <-- Modalidad aplicada
        ):
            # MODIFICADO: Ahora pasamos self.usuario_id como primer argumento
            if eliminar_usuario(self.usuario_id, id_usuario):
                # Aplicamos la Modalidad al mensaje de éxito
                messagebox.showinfo(
                    "Éxito",
                    "El usuario ha sido eliminado.",
                    parent=root_window,  # <-- Modalidad aplicada
                )
                self.cargar_usuarios()
            else:
                # Aplicamos la Modalidad al mensaje de error
                messagebox.showerror(
                    "Error",
                    "No se pudo eliminar el usuario. Es posible que tenga transacciones asociadas.",
                    parent=root_window,  # <-- Modalidad aplicada
                )


class UserForm(BaseDialog):
    def __init__(self, parent, callback_actualizar):
        super().__init__(parent, title="Añadir Nuevo Usuario")
        self.callback = callback_actualizar
        
        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(expand=True, fill=BOTH)
        
        ttk.Label(form_frame, text="Nombre de Usuario:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_username = ttk.Entry(form_frame, width=30)
        self.entry_username.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=5)
        self.entry_password = ttk.Entry(form_frame, width=30, show="●")
        self.entry_password.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Rol:").grid(row=2, column=0, sticky="w", pady=5)
        self.combo_rol = ttk.Combobox(form_frame, values=["usuario", "admin"], state="readonly", width=28)
        self.combo_rol.grid(row=2, column=1, pady=5)
        self.combo_rol.set("usuario") 
        
        ttk.Button(form_frame, text="Guardar", command=self.guardar, bootstyle="success").grid(row=3, column=0, columnspan=2, pady=15)

    def guardar(self):
        username = self.entry_username.get()
        password = self.entry_password.get()
        rol = self.combo_rol.get()
        if not all([username, password, rol]):
            messagebox.showerror("Campos Vacíos", "Todos los campos son obligatorios.", parent=self)
            return
        # NOTA: La adición de un usuario podría auditarse, pero a menudo no es estrictamente necesario,
        # ya que la acción se refleja en la propia tabla de usuarios. Por ahora, mantenemos solo la eliminación auditada.
        resultado = agregar_usuario(username, password, rol)
        if resultado is True:
            messagebox.showinfo("Éxito", "Usuario creado.", parent=self)
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", str(resultado), parent=self)

class PasswordForm(BaseDialog):
    def __init__(self, parent, user_id, username, callback_actualizar):
        super().__init__(parent, title=f"Cambiar Contraseña para '{username}'")
        self.user_id = user_id
        self.callback = callback_actualizar
        
        form_frame = ttk.Frame(self, padding=20)
        form_frame.pack(expand=True, fill=BOTH)
        
        ttk.Label(form_frame, text="Nueva Contraseña:").grid(row=0, column=0, sticky="w", pady=5)
        self.entry_password = ttk.Entry(form_frame, width=30, show="●")
        self.entry_password.grid(row=0, column=1, pady=5)
        
        ttk.Button(form_frame, text="Actualizar", command=self.actualizar, bootstyle="success").grid(row=1, column=0, columnspan=2, pady=15)

    def actualizar(self):
        new_password = self.entry_password.get()
        if not new_password:
            messagebox.showerror("Campo Vacío", "La contraseña no puede estar vacía.", parent=self)
            return
        if len(new_password) < 4:
            messagebox.showwarning("Contraseña Corta", "Se recomienda al menos 4 caracteres.", parent=self)
        # NOTA: La actualización de contraseña no genera auditoría en el flujo actual de database.py,
        # pero si se necesitara, aquí sería el lugar para pasar el usuario_id (el del administrador
        # que realiza el cambio, que no está disponible directamente en esta clase).
        if actualizar_contrasena(self.user_id, new_password):
            messagebox.showinfo("Éxito", "Contraseña actualizada.", parent=self)
            self.callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo actualizar la contraseña.", parent=self)