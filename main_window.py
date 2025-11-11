# main_window.py
import ttkbootstrap as ttk
from user_management_view import UserManagementView
from auditoria_view import AuditoriaView # <--- USAR ESTE NOMBRE
from supplier_management_view import SupplierManagementView
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from datetime import datetime
from database import (
    crear_copia_de_seguridad,
    restaurar_copia_de_seguridad,
    registrar_auditoria,
)
from pos_view import POSView
from sales_history_view import SalesHistoryView
from closing_view import ClosingView
from product_management_view import ProductManagementView
from user_management_view import UserManagementView
from reports_view import ReportsView
from supplier_management_view import SupplierManagementView
from purchase_entry_view import PurchaseEntryView
from debtor_management_view import DebtorManagementView
from auditoria_view import AuditoriaView


class MainWindow:
    def __init__(self, root, rol, usuario_id):
        self.root = root
        self.rol = rol
        self.usuario_id = usuario_id
        self.root.withdraw()

        self.main_win = ttk.Toplevel(self.root)
        self.main_win.title("Panel Principal del Sistema")
        self.main_win.geometry("1024x600")

        self.main_win.update_idletasks()
        width = self.main_win.winfo_width()
        height = self.main_win.winfo_height()
        x = (self.main_win.winfo_screenwidth() // 2) - (width // 2)
        y = (self.main_win.winfo_screenheight() // 2) - (height // 2)
        self.main_win.geometry(f"{width}x{height}+{x}+{y}")

        self.main_win.protocol("WM_DELETE_WINDOW", self.cerrar_app)

        self.sidebar_frame = ttk.Frame(self.main_win, bootstyle="secondary")
        self.sidebar_frame.pack(side=LEFT, fill=Y, padx=(0, 5), pady=0)

        self.content_frame = ttk.Frame(self.main_win, padding=10)
        self.content_frame.pack(side=RIGHT, fill=BOTH, expand=True)

        # ----------------------------------------------------
        # CLAVE: Inicializa la referencia a la vista POS
        self.pos_view = None
        # ----------------------------------------------------

        ttk.Label(
            self.sidebar_frame,
            text=f"Usuario: {rol.upper()}",
            font=("Helvetica", 12, "bold"),
            bootstyle="inverse-secondary",
        ).pack(pady=10, padx=10)

        # ----------------------------------------------------
        # CLAVE: Modificamos las llamadas de los botones para usar la función de verificación
        # ----------------------------------------------------
        # main_window.py (dentro de la función __init__)

        # Botones de uso general (visibles para todos los roles)
        ttk.Button(
            self.sidebar_frame, text="Punto de Venta", command=self.abrir_punto_venta
        ).pack(fill=X, padx=10, pady=5)
        ttk.Button(
            self.sidebar_frame,
            text="Historial de Ventas",
            command=lambda: self.verificar_y_cambiar_seccion(
                self._abrir_historial_ventas_interno
            ),
        ).pack(fill=X, padx=10, pady=5)
        ttk.Button(
            self.sidebar_frame,
            text="Cierre de Caja",
            command=lambda: self.verificar_y_cambiar_seccion(
                self._abrir_cierre_caja_interno
            ),
        ).pack(fill=X, padx=10, pady=5)

        # ----------------------------------------------------------------------
        # BLOQUE 1: AUDITORÍA (Acceso para 'admin' o 'auditor') 🕵️
        # ----------------------------------------------------------------------
        if self.rol in ["admin", "auditor"]:
            ttk.Separator(self.sidebar_frame).pack(fill=X, pady=10, padx=5)
            ttk.Label(
                self.sidebar_frame,
                text="Auditoría",
                font=("Helvetica", 12, "bold"),
                bootstyle="inverse-secondary",
            ).pack(pady=(0, 5))

            # Botón de acceso al registro de auditoría (llama al nuevo método _abrir_auditoria_interno)
            ttk.Button(
                self.sidebar_frame,
                text="Ver Registro de Actividad",
                command=lambda: self.verificar_y_cambiar_seccion(
                    self._abrir_auditoria_interno
                ),
            ).pack(fill=X, padx=10, pady=5)

        # ----------------------------------------------------------------------
        # BLOQUE 2: ADMINISTRACIÓN Y GESTIÓN (Exclusivo para 'admin') 🔧
        # ----------------------------------------------------------------------
        if self.rol == "admin":
            ttk.Separator(self.sidebar_frame).pack(fill=X, pady=10, padx=5)
            ttk.Label(
                self.sidebar_frame,
                text="Admin",
                font=("Helvetica", 12, "bold"),
                bootstyle="inverse-secondary",
            ).pack(pady=(0, 5))

            # Botones de Gestión (Admin)
            ttk.Button(
                self.sidebar_frame,
                text="Gestionar Deudores",
                command=lambda: self.verificar_y_cambiar_seccion(
                    self._abrir_gestion_deudores_interno
                ),
            ).pack(fill=X, padx=10, pady=5)
            ttk.Button(
                self.sidebar_frame,
                text="Gestionar Productos",
                command=lambda: self.verificar_y_cambiar_seccion(
                    self._abrir_gestion_productos_interno
                ),
            ).pack(fill=X, padx=10, pady=5)
            ttk.Button(
                self.sidebar_frame,
                text="Gestionar Usuarios",
                command=lambda: self.verificar_y_cambiar_seccion(
                    self._abrir_gestion_usuarios_interno
                ),
            ).pack(fill=X, padx=10, pady=5)
            ttk.Button(
                self.sidebar_frame,
                text="Gestionar Proveedores",
                command=lambda: self.verificar_y_cambiar_seccion(
                    self._abrir_gestion_proveedores_interno
                ),
            ).pack(fill=X, padx=10, pady=5)
            ttk.Button(
                self.sidebar_frame,
                text="Registrar Compra",
                command=lambda: self.verificar_y_cambiar_seccion(
                    self._abrir_registro_compra_interno
                ),
            ).pack(fill=X, padx=10, pady=5)
            ttk.Button(
                self.sidebar_frame,
                text="Ver Reportes",
                command=lambda: self.verificar_y_cambiar_seccion(
                    self._abrir_reportes_interno
                ),
            ).pack(fill=X, padx=10, pady=5)

            # Botones de Backup/Restauración
            ttk.Separator(self.sidebar_frame).pack(fill=X, pady=10, padx=5)
            ttk.Button(
                self.sidebar_frame,
                text="Crear Copia de Seguridad",
                command=self.realizar_copia_de_seguridad,
                bootstyle="warning",
            ).pack(fill=X, padx=10, pady=5)
            ttk.Button(
                self.sidebar_frame,
                text="Restaurar DB",
                command=self.restaurar_base_de_datos,
                bootstyle="danger",
            ).pack(fill=X, padx=10, pady=5)

        ttk.Button(
            self.sidebar_frame,
            text="Cerrar Sesión",
            command=self.cerrar_sesion,
            bootstyle="danger",
        ).pack(side=BOTTOM, fill=X, padx=10, pady=10)

        self.abrir_punto_venta()  # Inicia en la vista POS

    def limpiar_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # --- MÉTODO CENTRAL DE VERIFICACIÓN (APLICA LA MODALIDAD) ---
    # ------------------------------------------------------------------
    def verificar_y_cambiar_seccion(self, nueva_vista_func):
        """
        Verifica si hay una venta en curso en el POS antes de cambiar de sección.

        :param nueva_vista_func: La función (método) para abrir la nueva vista.
        """
        # Verificamos si la vista POS está inicializada y si hay una venta activa
        if self.pos_view and self.pos_view.venta_en_curso():

            root_window = self.main_win

            respuesta = messagebox.askyesno(
                "Venta en Curso",
                "Hay productos en el carrito. ¿Desea CANCELAR la venta y cambiar de sección?",
                parent=root_window,
            )

            if not respuesta:
                # Si el usuario dice NO, detenemos la acción.
                return

            # Si el usuario dice SÍ, cancelamos la venta (sin pedir confirmación doble)
            self.pos_view.cancelar_venta(confirmar=False)

        # Ejecutamos la función de la nueva vista (la lambda que le pasamos)
        self.limpiar_content_frame()
        nueva_vista_func()

    # ------------------------------------------------------------------
    # --- MÉTODOS PÚBLICOS DE NAVEGACIÓN (CREA y GUARDA self.pos_view) ---
    # ------------------------------------------------------------------
    def abrir_punto_venta(self):
        self.limpiar_content_frame()
        # CLAVE: Creamos la instancia y la guardamos en self.pos_view
        self.pos_view = POSView(self.content_frame, self.usuario_id)

    # ------------------------------------------------------------------
    # --- MÉTODOS INTERNOS DE NAVEGACIÓN (Ejecutados después de la verificación) ---
    # ------------------------------------------------------------------
    # Renombramos los antiguos métodos "abrir_..." a "_abrir_..._interno"
    # y eliminamos self.limpiar_content_frame() ya que se hace en verificar_y_cambiar_seccion

    def _abrir_historial_ventas_interno(self):
        SalesHistoryView(self.content_frame, self.usuario_id)

    def _abrir_cierre_caja_interno(self):
        ClosingView(self.content_frame, self.usuario_id)

    def _abrir_gestion_deudores_interno(self):
        DebtorManagementView(self.content_frame)

    def _abrir_gestion_productos_interno(self):
        self.limpiar_content_frame()  # ✅ MÉTODO CORRECTO
        ProductManagementView(self.content_frame, self, self.usuario_id)

    def _abrir_gestion_usuarios_interno(self):
        self.limpiar_content_frame()  # ✅ MÉTODO CORRECTO
        UserManagementView(self.content_frame, self, self.usuario_id)

    def _abrir_gestion_proveedores_interno(self):
        self.limpiar_content_frame()  # ✅ MÉTODO CORRECTO
        # Pasamos los parámetros estándar (frame, ventana, id_usuario)
        SupplierManagementView(self.content_frame, self, self.usuario_id)
        
    def _abrir_registro_compra_interno(self):
        PurchaseEntryView(self.content_frame)

    def _abrir_reportes_interno(self):
        ReportsView(self.content_frame)

    def _abrir_auditoria_interno(self):
        AuditoriaView(self.content_frame)

    def realizar_copia_de_seguridad(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_archivo_backup = f"backup_data_{timestamp}.db"
        ruta_destino = filedialog.asksaveasfilename(
            initialfile=nombre_archivo_backup,
            defaultextension=".db",
            filetypes=[
                ("Archivos de Base de Datos", "*.db"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if ruta_destino:
            if crear_copia_de_seguridad(ruta_destino):
                messagebox.showinfo(
                    "Éxito",
                    f"Copia de seguridad creada exitosamente en:\n{ruta_destino}",
                )
            else:
                messagebox.showerror("Error", "No se pudo crear la copia de seguridad.")

    def restaurar_base_de_datos(self):
        """
        Pide confirmación y selecciona un archivo de backup para restaurar la DB.
        """
        root_window = self.main_win

        # 1. Advertencia y Confirmación
        confirm = messagebox.askyesno(
            "ADVERTENCIA CRÍTICA: Restaurar DB",
            "¡ATENCIÓN! La restauración de la base de datos SOBREESCRIBIRÁ todos los datos actuales.\n\n"
            "¿Está completamente seguro de que desea continuar?",
            parent=root_window,
        )

        if not confirm:
            messagebox.showinfo(
                "Cancelado", "La restauración ha sido cancelada.", parent=root_window
            )
            return

        # 2. Selección del archivo de origen
        ruta_origen = filedialog.askopenfilename(
            title="Seleccionar Archivo de Base de Datos para Restaurar",
            defaultextension=".db",
            filetypes=[
                ("Archivos de Base de Datos", "*.db"),
                ("Todos los archivos", "*.*"),
            ],
        )

        if ruta_origen:
            # 3. Proceso de Restauración
            if restaurar_copia_de_seguridad(ruta_origen):
                messagebox.showwarning(
                    "Éxito y Aviso",
                    "Base de datos restaurada exitosamente.\n\n"
                    "¡ATENCIÓN! La aplicación DEBE REINICIARSE para cargar los nuevos datos. Cerrando la sesión...",
                    parent=root_window,
                )
                self.cerrar_sesion()  # Cerrar la ventana principal
            else:
                messagebox.showerror(
                    "Error de Restauración",
                    "No se pudo restaurar la base de datos.\n"
                    "Asegúrese de que la aplicación no esté bloqueando el archivo de la DB.",
                    parent=root_window,
                )
        else:
            messagebox.showinfo(
                "Cancelado",
                "No se seleccionó ningún archivo de restauración.",
                parent=root_window,
            )

    def cerrar_app(self):
        # Opcional: Podrías añadir una verificación aquí también si quieres.
        self.root.quit()

    def cerrar_sesion(self):
        # Opcional: Podrías añadir una verificación aquí también si quieres.
        self.main_win.destroy()
        self.root.deiconify()
