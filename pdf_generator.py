# pdf_generator.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch
import sys, os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def generate_pdf(filename, data):
    doc = SimpleDocTemplate(filename, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    # --- CORRECCIÓN DEFINITIVA: Nombres de estilo únicos con prefijo "App" ---
    styles.add(ParagraphStyle(name='AppMainTitle', fontSize=36, alignment=TA_LEFT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='AppPageHeader', fontSize=18, alignment=TA_LEFT, fontName="Helvetica-Bold", spaceBefore=20, spaceAfter=10))
    styles.add(ParagraphStyle(name='AppClientSubtitle', fontSize=16, alignment=TA_LEFT, fontName="Helvetica"))
    styles.add(ParagraphStyle(name='AppTableTitle', fontSize=12, alignment=TA_LEFT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='AppBodyText', fontSize=10, alignment=TA_LEFT, fontName="Helvetica")) # Este era el que fallaba

    table_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#008080")),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F0F0F0")),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    
    story = []
    
    # --- PÁGINA DE PORTADA ---
    try:
        logo = Image(resource_path('logo.png'), width=1.5*inch, height=0.75*inch)
        logo.hAlign = 'LEFT'
        story.append(logo)
    except Exception:
        story.append(Paragraph("Inventario Tecnológico", styles['AppTableTitle']))

    story.append(Spacer(1, 4*inch))
    story.append(Paragraph("AUDITORÍA TECNOLÓGICA", styles['AppMainTitle']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(data['cliente'].upper(), styles['AppClientSubtitle']))
    story.append(Paragraph(data['fecha'].upper(), styles['AppBodyText']))
    story.append(PageBreak())

    def add_section(title, data_list, headers):
        if not data_list: return
        story.append(Paragraph(title, styles['AppTableTitle']))
        table_data = [headers]
        for item in data_list:
            # Slicing item[2:] to skip id and inventario_id
            table_data.append([str(col) for col in item[2:]])
        
        t = Table(table_data, repeatRows=1)
        t.setStyle(table_style)
        story.append(t)
        story.append(Spacer(1, 24))

    # --- SECCIÓN 1: EQUIPOS ---
    story.append(Paragraph("1. RELACIÓN DE EQUIPOS", styles['AppPageHeader']))
    add_section("ORDENADORES", data['pcs'], ['Cód.', 'Placa', 'RAM', 'Core', 'Disco', 'S.O', 'Fuente', 'Antivirus', 'Ubic.', 'Obs.'])
    add_section("PROYECTORES / PANTALLAS", data['proyectores'], ['Cód.', 'Modelo', 'Táctil', 'Ubic.', 'Obs.'])
    add_section("IMPRESORAS", data['impresoras'], ['Cód.', 'Modelo', 'Conexión', 'Ubic.', 'Obs.'])
    add_section("SERVIDORES", data['servidores'], ['Cód.', 'Modelo', 'Uso', 'Ubic.', 'Obs.'])
    add_section("ROUTERS / SWITCH / WIFI / NAS", data['red'], ['Cód.', 'Tipo', 'Modelo', 'Ubic.', 'Obs.'])
    story.append(PageBreak())
    
    # --- SECCIÓN 2: SEGURIDAD ---
    story.append(Paragraph("2. SEGURIDAD FÍSICA Y LÓGICA", styles['AppPageHeader']))
    add_section("GRABADORES CCTV (DVR/NVR)", data['cctv_recorders'], ['Marca', 'Modelo', 'Canales', 'Ubic.', 'Obs.'])
    add_section("CÁMARAS CCTV", data['cctv_cameras'], ['Marca', 'Modelo', 'Lente', 'Ubic.', 'Obs.'])
    add_section("CONTROL DE ACCESO", data['accesos'], ['Marca', 'Modelo', 'Tipo', 'Ubic.', 'Obs.'])
    add_section("CREDENCIALES (CONFIDENCIAL)", data['credenciales'], ['Elemento', 'Usuario', 'Contraseña', 'Notas'])
    story.append(PageBreak())
    
    # --- SECCIONES DE TEXTO Y SOFTWARE ---
    story.append(Paragraph("3. SOFTWARE, NOTAS Y PLANO", styles['AppPageHeader']))

    if data['software']:
        story.append(Paragraph("SOFTWARE Y LICENCIAS", styles['AppTableTitle']))
        sw_data = [['SOFTWARE', 'LICENCIA']]
        for sw in data['software']:
            sw_data.append(sw[2:])
        t = Table(sw_data, repeatRows=1)
        t.setStyle(table_style)
        story.append(t)
        story.append(Spacer(1, 24))
    
    def add_text_section(title, content):
        if not content.strip(): return
        story.append(Paragraph(title, styles['AppTableTitle']))
        story.append(Paragraph(content.replace('\n', '<br/>'), styles['AppBodyText']))
        story.append(Spacer(1, 12))

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