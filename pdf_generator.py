# pdf_generator.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, PageTemplate, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
import sys, os

def resource_path(relative_path):
    # CORRECCIÓN: Usamos la nueva estructura de rutas para compatibilidad con EXE
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- NUEVO: Función para el pie de página ---
def footer(canvas, doc):
    canvas.saveState()
    try:
        # Cargar el logo desde una ruta compatible
        logo_path = resource_path('logo.png')
        if os.path.exists(logo_path):
            # Posicionar el logo en la esquina inferior izquierda
            canvas.drawImage(logo_path, doc.leftMargin, 0.5 * inch, width=1.2*inch, height=0.6*inch, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print(f"Error al dibujar el logo en el pie de página: {e}")
        # Fallback por si el logo no carga
        canvas.setFont('Helvetica', 9)
        canvas.drawString(doc.leftMargin, 0.75 * inch, "ForgeNEX")

    canvas.setFont('Helvetica', 9)
    # Número de página en la esquina inferior derecha
    canvas.drawRightString(doc.width + doc.leftMargin, 0.75 * inch, f"Página {doc.page}")
    canvas.restoreState()

def generate_pdf(filename, data):
    # Aumentar el margen inferior para dar espacio al pie de página
    doc = SimpleDocTemplate(filename, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=1.2 * inch)
    
    # Crear una plantilla de página que llame a nuestra función de pie de página
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='main_template', frames=[frame], onPage=footer)
    doc.addPageTemplates([template])

    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(name='AppMainTitle', fontSize=36, alignment=TA_LEFT, fontName="Helvetica-Bold", leading=42))
    styles.add(ParagraphStyle(name='AppPageHeader', fontSize=18, alignment=TA_LEFT, fontName="Helvetica-Bold", spaceBefore=20, spaceAfter=15)) # Más espacio después
    styles.add(ParagraphStyle(name='AppClientSubtitle', fontSize=16, alignment=TA_LEFT, fontName="Helvetica", spaceBefore=10))
    styles.add(ParagraphStyle(name='AppTableTitle', fontSize=12, alignment=TA_LEFT, fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=8)) # Más espacio
    styles.add(ParagraphStyle(name='AppBodyText', fontSize=10, alignment=TA_LEFT, fontName="Helvetica"))

    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#008080")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7), # Fuente más pequeña para que quepa más
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F0F0F0")),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    
    story = []
    
    # --- PÁGINA DE PORTADA ---
    # CORRECCIÓN: Estructura para evitar solapamiento
    story.append(Spacer(1, 4 * inch))
    story.append(Paragraph("AUDITORÍA TECNOLÓGICA", styles['AppMainTitle']))
    story.append(Paragraph(data['cliente'].upper(), styles['AppClientSubtitle']))
    story.append(Paragraph(data['fecha'].upper(), styles['AppBodyText']))
    story.append(PageBreak())

    def add_section(title, data_list, headers):
        if not data_list: return
        story.append(Paragraph(title, styles['AppTableTitle']))
        table_data = [headers]
        for item in data_list:
            table_data.append([str(col) if col is not None else "" for col in item[2:]])
        
        t = Table(table_data, repeatRows=1)
        t.setStyle(table_style)
        story.append(t)
        story.append(Spacer(1, 18)) # Espacio después de cada tabla

    # --- SECCIÓN 1: EQUIPOS ---
    if any([data['pcs'], data['proyectores'], data['impresoras'], data['servidores'], data['red']]):
        story.append(Paragraph("1. RELACIÓN DE EQUIPOS", styles['AppPageHeader']))
        add_section("ORDENADORES", data['pcs'], ['Cód.', 'Placa', 'RAM', 'Core', 'Disco', 'S.O', 'Fuente', 'Antivirus', 'Ubic.', 'Obs.'])
        add_section("PROYECTORES / PANTALLAS", data['proyectores'], ['Cód.', 'Modelo', 'Táctil', 'Ubic.', 'Obs.'])
        add_section("IMPRESORAS", data['impresoras'], ['Cód.', 'Modelo', 'Conexión', 'Ubic.', 'Obs.'])
        add_section("SERVIDORES", data['servidores'], ['Cód.', 'Modelo', 'Uso', 'Ubic.', 'Obs.'])
        add_section("ROUTERS / SWITCH / WIFI / NAS", data['red'], ['Cód.', 'Tipo', 'Modelo', 'Ubic.', 'Obs.'])
        story.append(PageBreak())
    
    # --- SECCIÓN 2: SEGURIDAD ---
    if any([data['cctv_recorders'], data['cctv_cameras'], data['accesos'], data['credenciales']]):
        story.append(Paragraph("2. SEGURIDAD FÍSICA Y LÓGICA", styles['AppPageHeader']))
        add_section("GRABADORES CCTV (DVR/NVR)", data['cctv_recorders'], ['Marca', 'Modelo', 'Canales', 'Ubic.', 'Obs.'])
        add_section("CÁMARAS CCTV", data['cctv_cameras'], ['Marca', 'Modelo', 'Lente', 'Ubic.', 'Obs.'])
        add_section("CONTROL DE ACCESO", data['accesos'], ['Marca', 'Modelo', 'Tipo', 'Ubic.', 'Obs.'])
        add_section("CREDENCIALES (CONFIDENCIAL)", data['credenciales'], ['Elemento', 'Usuario', 'Contraseña', 'Notas'])
        story.append(PageBreak())
    
    # --- SECCIONES DE TEXTO Y SOFTWARE ---
    if any([data['software'], data['estructura_info'], data['ubicacion_manuales'], data['historico_problemas'], data['modo_trabajo'], data['equipos_extra']]):
        story.append(Paragraph("3. SOFTWARE, NOTAS Y PLANO", styles['AppPageHeader']))

        if data['software']:
            add_section("SOFTWARE Y LICENCIAS", data['software'], ['Software', 'Licencia'])
    
    def add_text_section(title, content):
        if not content.strip(): return
        story.append(Paragraph(title, styles['AppTableTitle']))
        story.append(Paragraph(content.replace('\n', '<br/>'), styles['AppBodyText']))
        story.append(Spacer(1, 18))

    add_text_section("ESTRUCTURA INFORMÁTICA", data['estructura_info'])
    add_text_section("UBICACIÓN MANUALES", data['ubicacion_manuales'])
    add_text_section("HISTÓRICO DE PROBLEMAS", data['historico_problemas'])
    add_text_section("MODO DE TRABAJO", data['modo_trabajo'])
    add_text_section("EQUIPOS EXTRA", data['equipos_extra'])

    if data['plano_path'] and os.path.exists(data['plano_path']):
        story.append(PageBreak())
        story.append(Paragraph("PLANO DE UBICACIÓN", styles['AppPageHeader']))
        try:
            plano_img = Image(data['plano_path'], width=7*inch, height=9*inch, kind='proportional')
            story.append(plano_img)
        except Exception as e:
            story.append(Paragraph(f"No se pudo cargar la imagen del plano: {e}", styles['AppBodyText']))

    doc.build(story)