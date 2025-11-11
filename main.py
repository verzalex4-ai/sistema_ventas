#main.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from database import setup_database, verificar_credenciales
from main_window import MainWindow



class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Ventas - Login")
        self.frame = ttk.Frame(self.root, padding=(20, 20))
        self.frame.pack(expand=True, fill=BOTH)
        self.label_titulo = ttk.Label(
            self.frame, text="Inicio de Sesión", font=("Helvetica", 16, "bold")
        )
        self.label_titulo.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        self.label_usuario = ttk.Label(self.frame, text="Usuario:")
        self.label_usuario.grid(row=1, column=0, pady=5, sticky="w")
        self.entry_usuario = ttk.Entry(self.frame, width=30)
        self.entry_usuario.grid(row=1, column=1, pady=5, padx=(5, 0))
        self.entry_usuario.focus()
        self.label_contra = ttk.Label(self.frame, text="Contraseña:")
        self.label_contra.grid(row=2, column=0, pady=5, sticky="w")
        self.entry_contra = ttk.Entry(self.frame, show="●", width=30)
        self.entry_contra.grid(row=2, column=1, pady=5, padx=(5, 0))
        self.btn_login = ttk.Button(
            self.frame,
            text="Ingresar",
            command=self.intentar_login,
            bootstyle="primary",
        )
        self.btn_login.grid(
            row=3, column=0, columnspan=2, pady=(20, 0), ipady=5, sticky="ew"
        )
        self.root.bind("<Return>", lambda event=None: self.btn_login.invoke())
        self.root.eval("tk::PlaceWindow . center")

    def intentar_login(self):
        usuario = self.entry_usuario.get()
        contrasena = self.entry_contra.get()
        resultado = verificar_credenciales(usuario, contrasena)
        if resultado:
            usuario_id, rol = resultado
            MainWindow(self.root, rol, usuario_id)
        else:
            messagebox.showerror(
                "Login Fallido", "Usuario o contraseña incorrectos.", parent=self.root
            )


if __name__ == "__main__":
    setup_database()
    root = ttk.Window(themename="superhero")
    app = App(root)
    root.mainloop()
