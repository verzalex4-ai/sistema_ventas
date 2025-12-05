# main.py - FASE 1: LOGIN CON LOGO Y CAMBIO DE CONTRASEÑA OBLIGATORIO
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from PIL import Image, ImageTk
import os
from database import setup_database, verificar_credenciales, actualizar_contrasena
from main_window import MainWindow


class PasswordChangeDialog(ttk.Toplevel):
    """Diálogo modal para cambio obligatorio de contraseña."""
    def __init__(self, parent, usuario_id, nombre_usuario):
        super().__init__(parent)
        self.title("Cambio de Contraseña Obligatorio")
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.nueva_contrasena = None
        
        # Modal
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        
        # Contenido
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(
            main_frame, 
            text="⚠️ Cambio de Contraseña Requerido",
            font=("Helvetica", 14, "bold"),
            bootstyle="warning"
        ).pack(pady=(0, 10))
        
        ttk.Label(
            main_frame,
            text=f"Hola {nombre_usuario}, por seguridad debes cambiar\ntu contraseña antes de continuar.",
            font=("Helvetica", 10),
            justify=CENTER
        ).pack(pady=(0, 20))
        
        # Campo nueva contraseña
        ttk.Label(main_frame, text="Nueva Contraseña (mínimo 6 caracteres):").pack(anchor="w")
        self.entry_password = ttk.Entry(main_frame, show="●", width=30)
        self.entry_password.pack(fill=X, pady=(5, 10))
        self.entry_password.focus_set()
        
        # Campo confirmar contraseña
        ttk.Label(main_frame, text="Confirmar Contraseña:").pack(anchor="w")
        self.entry_confirm = ttk.Entry(main_frame, show="●", width=30)
        self.entry_confirm.pack(fill=X, pady=(5, 20))
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X)
        
        ttk.Button(
            btn_frame,
            text="Cambiar Contraseña",
            command=self.cambiar_contrasena,
            bootstyle="success"
        ).pack(side=LEFT, expand=True, fill=X, padx=(0, 5))
        
        ttk.Button(
            btn_frame,
            text="Cerrar Sesión",
            command=self.destroy,
            bootstyle="secondary"
        ).pack(side=RIGHT, expand=True, fill=X, padx=(5, 0))
        
        self.bind("<Return>", lambda e: self.cambiar_contrasena())
        
        # Centrar
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")
    
    def cambiar_contrasena(self):
        nueva = self.entry_password.get()
        confirmar = self.entry_confirm.get()
        
        if not nueva or not confirmar:
            messagebox.showerror("Error", "Ambos campos son obligatorios.", parent=self)
            return
        
        if len(nueva) < 6:
            messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres.", parent=self)
            return
        
        if nueva != confirmar:
            messagebox.showerror("Error", "Las contraseñas no coinciden.", parent=self)
            return
        
        # Actualizar en la BD (el propio usuario se cambia su contraseña)
        resultado = actualizar_contrasena(self.usuario_id, nueva)
        
        if resultado is True:
            self.nueva_contrasena = nueva
            messagebox.showinfo(
                "Éxito", 
                "Contraseña actualizada correctamente.\nAhora puedes acceder al sistema.",
                parent=self
            )
            self.destroy()
        else:
            messagebox.showerror("Error", str(resultado), parent=self)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ClickVenta")
        
        # Frame principal
        self.main_container = ttk.Frame(self.root, padding=(20, 20))
        self.main_container.pack(expand=True, fill=BOTH)
        
        # ============================================
        # LADO IZQUIERDO - LOGO
        # ============================================
        left_frame = ttk.Frame(self.main_container)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 20))
        
        # Intentar cargar el logo
        self.logo_label = ttk.Label(left_frame)
        self.logo_label.pack(expand=True)
        self.cargar_logo()
        
        # ============================================
        # LADO DERECHO - FORMULARIO DE LOGIN
        # ============================================
        right_frame = ttk.Frame(self.main_container)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # Contenedor del formulario
        self.frame = ttk.Frame(right_frame, padding=(20, 20))
        self.frame.pack(expand=True)
        
        ttk.Label(
            self.frame, 
            text="Inicio de Sesión", 
            font=("Helvetica", 16, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        ttk.Label(self.frame, text="Usuario:").grid(row=1, column=0, pady=5, sticky="w")
        self.entry_usuario = ttk.Entry(self.frame, width=30)
        self.entry_usuario.grid(row=1, column=1, pady=5, padx=(5, 0))
        self.entry_usuario.focus()
        
        ttk.Label(self.frame, text="Contraseña:").grid(row=2, column=0, pady=5, sticky="w")
        self.entry_contra = ttk.Entry(self.frame, show="●", width=30)
        self.entry_contra.grid(row=2, column=1, pady=5, padx=(5, 0))
        
        self.btn_login = ttk.Button(
            self.frame,
            text="Ingresar",
            command=self.intentar_login,
            bootstyle="primary",
        )
        self.btn_login.grid(row=3, column=0, columnspan=2, pady=(20, 0), ipady=5, sticky="ew")
        
        self.root.bind("<Return>", lambda event=None: self.btn_login.invoke())
        self.root.eval("tk::PlaceWindow . center")

    def cargar_logo(self):
        """Intenta cargar el logo desde varios posibles ubicaciones."""
        posibles_rutas = [
            "logo.png",                    # En la carpeta raíz del proyecto
            os.path.join("assets", "logo.png"),  # En una carpeta 'assets'
            os.path.join("images", "logo.png"),  # En una carpeta 'images'
        ]
        
        logo_cargado = False
        
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                try:
                    # Cargar y redimensionar la imagen
                    imagen = Image.open(ruta)
                    
                    # Redimensionar manteniendo la proporción (máximo 300x300)
                    imagen.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    
                    # Convertir para tkinter
                    self.logo_image = ImageTk.PhotoImage(imagen)
                    self.logo_label.config(image=self.logo_image)
                    
                    logo_cargado = True
                    print(f"✅ Logo cargado desde: {ruta}")
                    break
                    
                except Exception as e:
                    print(f"❌ Error al cargar logo desde {ruta}: {e}")
        
        if not logo_cargado:
            # Si no se encuentra el logo, mostrar un texto alternativo
            self.logo_label.config(
                text="🏪\nSISTEMA POS\nVentas",
                font=("Helvetica", 32, "bold"),
                bootstyle="primary"
            )
            print("ℹ️ No se encontró logo.png - Se muestra texto alternativo")
            print(f"   Busca el logo en las siguientes rutas:")
            for ruta in posibles_rutas:
                print(f"   - {os.path.abspath(ruta)}")

    def intentar_login(self):
        usuario = self.entry_usuario.get()
        contrasena = self.entry_contra.get()
        resultado = verificar_credenciales(usuario, contrasena)
        
        if resultado:
            usuario_id, rol, debe_cambiar = resultado
            
            # ✅ NUEVA LÓGICA: Verificar si debe cambiar contraseña
            if debe_cambiar:
                dialog = PasswordChangeDialog(self.root, usuario_id, usuario)
                self.root.wait_window(dialog)
                
                # Si cerró el diálogo sin cambiar la contraseña, no continuar
                if dialog.nueva_contrasena is None:
                    messagebox.showinfo(
                        "Acceso Denegado",
                        "Debes cambiar tu contraseña para acceder al sistema.",
                        parent=self.root
                    )
                    return
            
            # Continuar con el login normal
            MainWindow(self.root, rol, usuario_id)
        else:
            messagebox.showerror(
                "Login Fallido", 
                "Usuario o contraseña incorrectos.", 
                parent=self.root
            )


if __name__ == "__main__":
    setup_database()
    root = ttk.Window(themename="superhero")
    app = App(root)
    root.mainloop()