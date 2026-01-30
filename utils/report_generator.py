"""
Módulo para generación de informes
"""

import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from datetime import datetime
import io
from config.settings import CONFIGURACION_INFORME, CONFIGURACION

def generar_informe_word(datos: dict, analisis: dict) -> bytes:
    """
    Genera un informe completo en formato Word
    """
    doc = Document()
    
    # Configurar estilos
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    
    # Título
    titulo = doc.add_heading(CONFIGURACION_INFORME['titulo'], 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Subtítulo
    subtitulo = doc.add_heading(CONFIGURACION_INFORME['subtitulo'], 1)
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Información general
    doc.add_paragraph()
    info = doc.add_paragraph()
    info.add_run('Entidad: ').bold = True
    info.add_run(CONFIGURACION['nombre_entidad'] + '\n')
    info.add_run('Ejercicio auditado: ').bold = True
    info.add_run(CONFIGURACION['ejercicio_auditado'] + '\n')
    info.add_run('Fecha del informe: ').bold = True
    info.add_run(datetime.now().strftime('%d/%m/%Y'))
    
    doc.add_page_break()
    
    # 1. RESUMEN EJECUTIVO
    doc.add_heading('1. RESUMEN EJECUTIVO', 1)
    
    doc.add_paragraph(f"""
    El presente informe recoge los resultados de la auditoría del Registro Contable de Facturas (RCF)
    de {CONFIGURACION['nombre_entidad']} correspondiente al ejercicio {CONFIGURACION['ejercicio_auditado']},
    en cumplimiento del artículo 12.3 de la Ley 25/2013, de 27 de diciembre.
    """)
    
    # Métricas principales
    doc.add_heading('1.1. Cifras Principales', 2)
    
    tabla_datos = [
        ['Concepto', 'Valor'],
        ['Total de facturas recibidas', f"{len(datos['rcf']):,}"],
        ['Facturas electrónicas', f"{len(datos['rcf'][datos['rcf']['es_papel']==False]):,}"],
        ['Facturas en papel', f"{len(datos['rcf'][datos['rcf']['es_papel']==True]):,}"],
        ['Solicitudes de anulación', f"{len(datos['anulaciones']):,}"],
    ]
    
    tabla = doc.add_table(rows=len(tabla_datos), cols=2)
    tabla.style = 'Light Grid Accent 1'
    
    for i, fila in enumerate(tabla_datos):
        for j, valor in enumerate(fila):
            tabla.rows[i].cells[j].text = str(valor)
    
    doc.add_page_break()
    
    # 2. FACTURAS EN PAPEL
    doc.add_heading('2. ANÁLISIS DE FACTURAS EN PAPEL', 1)
    
    if 'facturas_papel' in analisis:
        papel = analisis['facturas_papel']
        
        doc.add_paragraph(f"""
        Se han identificado {papel['total_sospechosas']:,} facturas en papel susceptibles de incumplir
        la normativa de obligatoriedad de factura electrónica (Ley 25/2013 y Circular 1/2015 IGAE).
        """)
        
        doc.add_heading('2.1. Evolución Mensual', 2)
        doc.add_paragraph("Ver gráfico adjunto en Dashboard.")
        
        doc.add_heading('2.2. Top 10 por Importe', 2)
        if 'top_10_importe' in papel and len(papel['top_10_importe']) > 0:
            tabla_top = [['Nº Factura', 'NIF', 'Razón Social', 'Importe']]
            for _, row in papel['top_10_importe'].head(10).iterrows():
                tabla_top.append([
                    str(row.get('numero_factura', '')),
                    str(row.get('nif_emisor', ''))[:10] + '...',
                    str(row.get('razon_social', ''))[:30],
                    f"{row.get('importe_total', 0):,.2f} €"
                ])
            
            tabla = doc.add_table(rows=len(tabla_top), cols=4)
            tabla.style = 'Light Grid Accent 1'
            for i, fila in enumerate(tabla_top):
                for j, valor in enumerate(fila):
                    tabla.rows[i].cells[j].text = str(valor)
    
    doc.add_page_break()
    
    # 3. TIEMPOS DE ANOTACIÓN
    doc.add_heading('3. TIEMPOS DE ANOTACIÓN EN RCF', 1)
    
    if 'anotacion' in analisis:
        anot = analisis['anotacion']
        
        doc.add_paragraph(f"""
        El tiempo medio de anotación de facturas en el RCF ha sido de {anot.get('tiempo_medio_min', 0):.2f} minutos.
        """)
        
        if anot.get('facturas_retenidas', 0) > 0:
            doc.add_paragraph(f"""
            ⚠️ ALERTA: Se han detectado {anot['facturas_retenidas']} facturas retenidas en FACe
            pendientes de descarga por el RCF.
            """)
    
    doc.add_page_break()
    
    # 4. VALIDACIONES
    doc.add_heading('4. VALIDACIONES ORDEN HAP/1650/2015', 1)
    
    if 'validaciones' in analisis:
        val = analisis['validaciones']
        
        doc.add_paragraph(f"""
        Se han aplicado las 8 validaciones establecidas en la Orden HAP/1650/2015 sobre
        {val.get('total_facturas_validadas', 0):,} facturas electrónicas.
        """)
        
        doc.add_heading('4.1. Resumen de Validaciones', 2)
        
        tabla_val = [['Validación', 'Incumplimientos', '%']]
        for codigo, resultado in val.get('validaciones', {}).items():
            tabla_val.append([
                resultado['nombre'],
                str(resultado['num_incumplimientos']),
                f"{resultado['porcentaje']:.2f}%"
            ])
        
        tabla = doc.add_table(rows=len(tabla_val), cols=3)
        tabla.style = 'Light Grid Accent 1'
        for i, fila in enumerate(tabla_val):
            for j, valor in enumerate(fila):
                tabla.rows[i].cells[j].text = str(valor)
    
    doc.add_page_break()
    
    # 5. TRAMITACIÓN
    doc.add_heading('5. TRAMITACIÓN DE FACTURAS', 1)
    
    if 'tramitacion' in analisis:
        tram = analisis['tramitacion']
        
        doc.add_paragraph(f"""
        Se han tramitado {tram.get('total_anulaciones', 0)} solicitudes de anulación,
        de las cuales {tram.get('anulaciones_aceptadas', 0)} fueron aceptadas.
        """)
    
    doc.add_page_break()
    
    # 6. OBLIGACIONES Y MOROSIDAD
    doc.add_heading('6. FACTURAS PENDIENTES Y MOROSIDAD', 1)
    
    if 'obligaciones' in analisis:
        oblig = analisis['obligaciones']
        
        doc.add_paragraph(f"""
        Se han identificado {oblig.get('facturas_3_meses', 0)} facturas con más de 3 meses
        desde su anotación sin haberse reconocido la obligación.
        """)
        
        if oblig.get('facturas_3_meses', 0) > 0:
            doc.add_paragraph("""
            Estas facturas requieren un seguimiento especial por parte de los órganos gestores
            competentes para evitar incumplimientos de la normativa de morosidad.
            """)
    
    doc.add_page_break()
    
    # 7. CONCLUSIONES
    doc.add_heading('7. CONCLUSIONES Y RECOMENDACIONES', 1)
    
    doc.add_paragraph("""
    De los análisis realizados se desprenden las siguientes conclusiones:
    """)
    
    conclusiones = doc.add_paragraph(style='List Number')
    conclusiones.add_run("""El Registro Contable de Facturas cumple en general con los requisitos
    establecidos en la Ley 25/2013 y su normativa de desarrollo.""")
    
    if 'facturas_papel' in analisis and analisis['facturas_papel'].get('total_sospechosas', 0) > 0:
        conclusiones = doc.add_paragraph(style='List Number')
        conclusiones.add_run(f"""Se recomienda revisar las {analisis['facturas_papel']['total_sospechosas']}
        facturas en papel identificadas que podrían incumplir la obligatoriedad de factura electrónica.""")
    
    if 'anotacion' in analisis and analisis['anotacion'].get('facturas_retenidas', 0) > 0:
        conclusiones = doc.add_paragraph(style='List Number')
        conclusiones.add_run(f"""Es necesario investigar las causas de retención de
        {analisis['anotacion']['facturas_retenidas']} facturas en el PGEFe.""")
    
    # Footer
    doc.add_page_break()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run(CONFIGURACION_INFORME['footer']).italic = True
    
    # Guardar en bytes
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    return buffer.getvalue()

def generar_informe_pdf(datos: dict, analisis: dict) -> bytes:
    """
    Genera un informe ejecutivo en formato PDF
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0066CC'),
        spaceAfter=30,
        alignment=1  # Centro
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#FF6B35'),
        spaceAfter=12
    )
    
    # Título
    story.append(Paragraph(CONFIGURACION_INFORME['titulo'], titulo_style))
    story.append(Paragraph(CONFIGURACION_INFORME['subtitulo'], styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Información
    info_text = f"""
    <b>Entidad:</b> {CONFIGURACION['nombre_entidad']}<br/>
    <b>Ejercicio:</b> {CONFIGURACION['ejercicio_auditado']}<br/>
    <b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Resumen ejecutivo
    story.append(Paragraph("RESUMEN EJECUTIVO", subtitulo_style))
    
    # Tabla de cifras
    datos_tabla = [
        ['Concepto', 'Valor'],
        ['Total facturas', f"{len(datos['rcf']):,}"],
        ['Facturas electrónicas', f"{len(datos['rcf'][datos['rcf']['es_papel']==False]):,}"],
        ['Facturas papel', f"{len(datos['rcf'][datos['rcf']['es_papel']==True]):,}"],
        ['Anulaciones', f"{len(datos['anulaciones']):,}"],
    ]
    
    tabla = Table(datos_tabla, colWidths=[3*inch, 2*inch])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(tabla)
    story.append(PageBreak())
    
    # Hallazgos principales
    story.append(Paragraph("PRINCIPALES HALLAZGOS", subtitulo_style))
    
    hallazgos = []
    
    if 'facturas_papel' in analisis:
        hallazgos.append(f"• {analisis['facturas_papel'].get('total_sospechosas', 0):,} facturas en papel susceptibles de incumplimiento")
    
    if 'anotacion' in analisis:
        hallazgos.append(f"• Tiempo medio de anotación: {analisis['anotacion'].get('tiempo_medio_min', 0):.2f} minutos")
        if analisis['anotacion'].get('facturas_retenidas', 0) > 0:
            hallazgos.append(f"• ⚠️ {analisis['anotacion']['facturas_retenidas']} facturas retenidas en FACe")
    
    if 'validaciones' in analisis:
        hallazgos.append(f"• Cumplimiento validaciones: {analisis['validaciones'].get('porcentaje_cumplimiento', 100):.2f}%")
    
    if 'obligaciones' in analisis:
        hallazgos.append(f"• {analisis['obligaciones'].get('facturas_3_meses', 0)} facturas >3 meses sin reconocimiento")
    
    for hallazgo in hallazgos:
        story.append(Paragraph(hallazgo, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    # Footer
    story.append(Spacer(1, 1*inch))
    footer_text = f"<i>{CONFIGURACION_INFORME['footer']}</i>"
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Construir PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer.getvalue()