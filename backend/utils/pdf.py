from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

BRAND_BLUE = colors.HexColor('#2563EB')
LIGHT_BG = colors.HexColor('#F5F7FA')
TEXT_DARK = colors.HexColor('#212121')


def get_styles():
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        'TitleWhite', parent=styles['Title'], textColor=colors.white, alignment=TA_LEFT,
    )
    subtitle = ParagraphStyle(
        'SubtitleWhite', parent=styles['Heading3'], textColor=colors.white, alignment=TA_LEFT,
    )
    info = ParagraphStyle(
        'Info', parent=styles['Normal'], textColor=TEXT_DARK, alignment=TA_LEFT,
    )
    return {
        'title': title,
        'subtitle': subtitle,
        'info': info,
    }


def build_header(titulo: str, subtitulo: str, logo_url: str = None):
    """Construye un encabezado con barra azul y texto blanco, con logo opcional a la derecha."""
    styles = get_styles()
    # Preparar contenido de texto (título + subtítulo)
    text_cell = [Paragraph(titulo, styles['title']), Spacer(1, 2), Paragraph(subtitulo, styles['subtitle'])]
    # Intentar cargar logo desde URL si está disponible
    logo_flowable = ""
    if logo_url:
        try:
            import urllib.request
            import io as _io
            with urllib.request.urlopen(logo_url) as resp:
                img_bytes = resp.read()
            logo_flowable = Image(_io.BytesIO(img_bytes), width=120, height=60)
        except Exception:
            logo_flowable = ""
    # Construir tabla del encabezado con dos columnas (texto, logo)
    data = [[text_cell, logo_flowable]]
    header = Table(data, colWidths=[440, 120])
    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    header.hAlign = 'LEFT'
    return header


def build_separator():
    sep = Table([[" "]], colWidths=[460])
    sep.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    sep.hAlign = 'LEFT'
    return sep


def apply_table_style(table):
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [LIGHT_BG, colors.white]),
    ]))
    table.hAlign = 'CENTER'
    return table