import ttkbootstrap as ttk

class BaseDialog(ttk.Toplevel):
    """
    Una clase base para las ventanas de diálogo (Toplevel) que
    maneja automáticamente el centrado en la pantalla, la modalidad
    (grab_set) y la transitoriedad (transient).
    """
    def __init__(self, parent, title=""):
        super().__init__(parent)
        self.title(title)
        
        # Ocultamos la ventana temporalmente.
        self.withdraw()

        self.transient(parent)
        self.grab_set()
        
        # Centrado y visualización final
        self.center_window()

    def center_window(self):
        """
        Centra la ventana de diálogo en la pantalla y la muestra.
        """
        self.update_idletasks()  # Calcula tamaño real del contenido

        # Obtiene tamaño real ya ajustado al contenido
        width = self.winfo_width()
        height = self.winfo_height()

        # Coordenadas centradas
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)

        # Solo posiciona, sin forzar tamaño
        self.geometry(f'+{x}+{y}')

        # Muestra la ventana ya lista
        self.deiconify()
