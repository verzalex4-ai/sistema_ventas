# ticket_generator.py
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from database import obtener_info_venta, obtener_detalle_de_venta

def generar_ticket_pdf(venta_id):
    try:
        info_venta = obtener_info_venta(venta_id)
        detalles_venta = obtener_detalle_de_venta(venta_id)

        if not info_venta or not detalles_venta:
            print(f"No se encontraron datos para generar el ticket de la venta ID: {venta_id}")
            return False

        # --- MODIFICACIÓN: Ruta de guardado robusta ---
        # 1. Obtener la ruta a la carpeta 'Documentos' del usuario actual
        docs_path = os.path.join(os.path.expanduser('~'), 'Documents')
        
        # 2. Crear la carpeta si no existe
        os.makedirs(docs_path, exist_ok=True)
        
        # 3. Crear la ruta completa del archivo dentro de 'Documentos'
        nombre_archivo = os.path.join(docs_path, f"ticket_venta_{venta_id}.pdf")
        # ----------------------------------------------------
        
        c = canvas.Canvas(nombre_archivo, pagesize=(80 * mm, 150 * mm))
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(10 * mm, 140 * mm, "Mi Negocio POS")

        c.setFont("Helvetica", 8)
        c.drawString(10 * mm, 135 * mm, "--------------------------------------------------")
        
        fecha_hora, total_general = info_venta
        c.drawString(10 * mm, 130 * mm, f"Ticket de Venta N°: {venta_id}")
        c.drawString(10 * mm, 126 * mm, f"Fecha: {fecha_hora}")

        c.drawString(10 * mm, 121 * mm, "--------------------------------------------------")
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(10 * mm, 116 * mm, "Producto")
        c.drawString(45 * mm, 116 * mm, "Cant.")
        c.drawString(60 * mm, 116 * mm, "Subtotal")
        
        c.setFont("Helvetica", 8)
        y = 110 * mm
        for producto in detalles_venta:
            nombre, cantidad, subtotal = producto
            c.drawString(10 * mm, y, nombre[:25])
            c.drawString(47 * mm, y, str(cantidad))
            c.drawString(62 * mm, y, f"${subtotal:.2f}")
            y -= 4 * mm

        c.drawString(10 * mm, y - 2 * mm, "--------------------------------------------------")

        c.setFont("Helvetica-Bold", 11)
        c.drawString(10 * mm, y - 8 * mm, "TOTAL:")
        c.drawString(55 * mm, y - 8 * mm, f"${total_general:.2f}")

        c.save()
        
        # os.startfile funciona perfectamente con la ruta completa
        if os.name == 'nt': # Para Windows
            os.startfile(nombre_archivo)
            
        return True
    
    except Exception as e:
        print(f"Error al generar el ticket PDF: {e}")
        return False