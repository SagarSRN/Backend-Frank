"""
PDF Generator for Construction Estimates
Generates professional PDF estimates from project data
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.conf import settings
import os
from datetime import datetime


def generate_estimate_pdf(project, estimate, room_estimates):
    """
    Generate a professional estimate PDF
    
    Args:
        project: Project object
        estimate: Estimate object  
        room_estimates: QuerySet of RoomEstimate objects
    
    Returns:
        str: Path to generated PDF file
    """
    # Create output directory if it doesn't exist
    output_dir = os.path.join(settings.MEDIA_ROOT, 'estimates')
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"estimate_{project.id}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Create PDF document
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Title
    title = Paragraph("PROJECT ESTIMATE", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Project Information Section
    project_info_data = [
        ['Project Name:', project.name],
        ['Project Type:', project.project_type],
        ['Scope:', project.scope],
        ['Location:', project.location],
        ['Built-up Area:', f"{project.builtup_area} sqft"],
        ['Date:', datetime.now().strftime('%B %d, %Y')],
    ]
    
    project_table = Table(project_info_data, colWidths=[2*inch, 4*inch])
    project_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(project_table)
    elements.append(Spacer(1, 20))
    
    # Room-wise Breakdown Section
    if room_estimates:
        room_heading = Paragraph("Room-wise Breakdown", heading_style)
        elements.append(room_heading)
        elements.append(Spacer(1, 12))
        
        # Room table headers
        room_data = [['Room Name', 'Tiles (sqm)', 'Paint (sqm)', 'Cement (bags)', 'Sand (tons)', 'Cost (₹)']]
        
        # Add room data
        for r in room_estimates:
            room_data.append([
                r.room.name,
                f"{r.tiles_sqm:.2f}",
                f"{r.paint_sqm:.2f}",
                str(r.cement_bags),
                f"{r.sand_tons:.2f}",
                f"₹ {r.cost:,.2f}"
            ])
        
        room_table = Table(room_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
        room_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Body styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(room_table)
        elements.append(Spacer(1, 20))
    
    # Materials Summary Section
    materials_heading = Paragraph("Materials Summary", heading_style)
    elements.append(materials_heading)
    elements.append(Spacer(1, 12))
    
    materials_data = [
        ['Material', 'Quantity', 'Unit'],
        ['Floor Tiles', f"{estimate.total_tiles_sqm:.2f}", 'sqm'],
        ['Wall Paint', f"{estimate.total_paint_sqm:.2f}", 'sqm'],
        ['Cement', str(estimate.cement_bags), 'bags'],
        ['Sand', f"{estimate.sand_tons:.2f}", 'tons'],
    ]
    
    materials_table = Table(materials_data, colWidths=[3*inch, 2*inch, 1.5*inch])
    materials_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(materials_table)
    elements.append(Spacer(1, 30))
    
    # Total Cost Section
    total_data = [
        ['TOTAL PROJECT COST', f"₹ {estimate.total_cost:,.2f}"]
    ]
    
    total_table = Table(total_data, colWidths=[4*inch, 2.5*inch])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(total_table)
    elements.append(Spacer(1, 30))
    
    # Footer note
    note_style = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    note = Paragraph(
        "This estimate is based on the uploaded floor plan analysis and standard material rates. "
        "Actual costs may vary based on market conditions and specific requirements.",
        note_style
    )
    elements.append(note)
    
    # Build PDF
    doc.build(elements)
    
    return filepath
