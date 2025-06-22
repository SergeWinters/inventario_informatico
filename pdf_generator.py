# pdf_generator.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_pdf(filename, data):
    doc = SimpleDocTemplate(filename, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    styles.add(ParagraphStyle(name='TitlePage', fontSize=48, alignment=TA_LEFT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='SubTitle', fontSize=18, alignment=TA_LEFT, fontName="Helvetica"))
    styles.add(ParagraphStyle(name='Header', fontSize=14, alignment=TA_LEFT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name='Body', fontSize=10, alignment=TA_LEFT, fontName="Helvetica"))
    
    story = []
    
    # --- PÁGINA DE PORTADA ---
    try:
        logo = Image('logo.png', width=1.5*inch, height=0.75*inch)
        logo.hAlign = 'LEFT'
        story.append(logo)
    except Exception:
        story.append(Paragraph("WIK-IN", styles['Header'])) # Fallback si no hay logo

    story.append(Spacer(1, 4*inch))
    story.append(Paragraph("AUDITORÍA", styles['TitlePage']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(data['cliente'].upper(), styles['SubTitle']))
    story.append(Paragraph(data['fecha'].upper(), styles['Body']))
    story.append(PageBreak())

    # --- ÍNDICE ---
    story.append(Paragraph("1. RELACIÓN DE EQUIPOS", styles['Header']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("2. ESTRUCTURA INFORMÁTICA DEL CENTRO", styles['Header']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("3. UBICACIÓN FÍSICA / MANUALES", styles['Header']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("4. HISTÓRICO DE PROBLEMAS", styles['Header']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("5. MODO DE TRABAJO", styles['Header']))
    story.append(Spacer(1, 12))
    story.append(Paragraph("6. SOFTWARE Y EQUIPOS EXTRA", styles['Header']))
    story.append(PageBreak())

    # --- SECCIÓN 1: EQUIPOS ---
    story.append(Paragraph("1. RELACIÓN DE EQUIPOS", styles['TitlePage']))
    story.append(Spacer(1, 24))
    
    # PCs
    if data['pcs']:
        story.append(Paragraph("ORDENADORES", styles['Header']))
        pc_data = [['CÓDIGO', 'PLACA', 'RAM', 'CORE', 'DISCO', 'S.O', 'UBICACIÓN']]
        for pc in data['pcs']:
            pc_data.append([pc[2], pc[3], pc[4], pc[5], pc[6], pc[7], pc[9]])
        t = Table(pc_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 24))

    # Proyectores
    if data['proyectores']:
        story.append(Paragraph("PROYECTORES / PANTALLAS", styles['Header']))
        proy_data = [['CÓDIGO', 'MODELO', 'UBICACIÓN']]
        for p in data['proyectores']:
            proy_data.append([p[2], p[3], p[4]])
        t = Table(proy_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 24))

    # Impresoras
    if data['impresoras']:
        story.append(Paragraph("IMPRESORAS", styles['Header']))
        imp_data = [['CÓDIGO', 'MODELO', 'UBICACIÓN']]
        for i in data['impresoras']:
            imp_data.append([i[2], i[3], i[4]])
        t = Table(imp_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 24))
        
    # Servidores
    if data['servidores']:
        story.append(Paragraph("SERVIDORES", styles['Header']))
        srv_data = [['CÓDIGO', 'MODELO', 'USO', 'UBICACIÓN']]
        for s in data['servidores']:
            srv_data.append([s[2], s[3], s[4], s[5]])
        t = Table(srv_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 24))

    # Red
    if data['red']:
        story.append(Paragraph("ROUTERS / SWITCH / WIFI", styles['Header']))
        red_data = [['TIPO', 'MODELO', 'UBICACIÓN']]
        for r in data['red']:
            red_data.append([r[3], r[4], r[5]])
        t = Table(red_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
        story.append(PageBreak())

    # --- SECCIONES DE TEXTO ---
    story.append(Paragraph("2. ESTRUCTURA INFORMÁTICA DEL CENTRO", styles['Header']))
    story.append(Paragraph(data['estructura_info'].replace('\n', '<br/>'), styles['Body']))
    story.append(Spacer(1, 24))
    
    story.append(Paragraph("3. UBICACIÓN FÍSICA DE INTERÉS / MANUALES", styles['Header']))
    story.append(Paragraph(data['ubicacion_manuales'].replace('\n', '<br/>'), styles['Body']))
    story.append(Spacer(1, 24))

    story.append(Paragraph("4. HISTÓRICO DE PROBLEMAS GENERALES", styles['Header']))
    story.append(Paragraph(data['historico_problemas'].replace('\n', '<br/>'), styles['Body']))
    story.append(Spacer(1, 24))

    story.append(Paragraph("5. MODO DE TRABAJO DE LA ACADEMIA", styles['Header']))
    story.append(Paragraph(data['modo_trabajo'].replace('\n', '<br/>'), styles['Body']))
    story.append(PageBreak())

    # --- SOFTWARE Y EXTRAS ---
    story.append(Paragraph("6. SOFTWARE Y EQUIPOS EXTRA", styles['TitlePage']))
    story.append(Spacer(1, 24))
    
    if data['software']:
        story.append(Paragraph("SOFTWARE", styles['Header']))
        sw_data = [['SOFTWARE', 'LICENCIA']]
        for sw in data['software']:
            sw_data.append([sw[2], sw[3]])
        t = Table(sw_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.teal),
            ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 24))

    if data['equipos_extra']:
        story.append(Paragraph("EQUIPOS EXTRA (Videovigilancia, etc.)", styles['Header']))
        story.append(Paragraph(data['equipos_extra'].replace('\n', '<br/>'), styles['Body']))
        story.append(Spacer(1, 24))

    # Plano
    if data['plano_path']:
        story.append(PageBreak())
        story.append(Paragraph("PLANO DE UBICACIÓN", styles['TitlePage']))
        story.append(Spacer(1, 24))
        try:
            plano_img = Image(data['plano_path'], width=6*inch, height=8*inch, kind='proportional')
            story.append(plano_img)
        except Exception as e:
            story.append(Paragraph(f"No se pudo cargar la imagen del plano: {e}", styles['Body']))

    doc.build(story)