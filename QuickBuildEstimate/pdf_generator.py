import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from openai_services import generate_proposal_summary
from cost_engine import get_cost_breakdown
import logging

def generate_proposal_pdf(estimate):
    """Generate a professional PDF proposal for the estimate"""
    
    try:
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Build content
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1C1C1E')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#1C1C1E')
        )
        
        # Header
        story.append(Paragraph("CONSTRUCTION ESTIMATE PROPOSAL", title_style))
        story.append(Spacer(1, 20))
        
        # Project info
        project_info = [
            ['Project Name:', estimate.name],
            ['Estimate Date:', estimate.created_at.strftime('%B %d, %Y')],
            ['Proposal Valid Until:', (estimate.created_at.replace(day=estimate.created_at.day + 30)).strftime('%B %d, %Y')]
        ]
        
        project_table = Table(project_info, colWidths=[2*inch, 4*inch])
        project_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 20))
        
        # Generate AI summary
        try:
            ai_summary = generate_proposal_summary(estimate)
            story.append(Paragraph("Project Overview", heading_style))
            story.append(Paragraph(ai_summary, styles['Normal']))
            story.append(Spacer(1, 20))
        except Exception as e:
            logging.warning(f"Could not generate AI summary: {e}")
            # Continue without AI summary
        
        # Cost breakdown
        story.append(Paragraph("Cost Breakdown", heading_style))
        
        breakdown = get_cost_breakdown(estimate)
        
        # Materials section
        if breakdown['materials']:
            story.append(Paragraph("Materials & Supplies", styles['Heading3']))
            
            for bundle, items in breakdown['materials'].items():
                story.append(Paragraph(f"<b>{bundle}</b>", styles['Normal']))
                
                material_data = [['Item', 'Qty', 'Unit', 'Unit Cost', 'Total']]
                for item in items:
                    material_data.append([
                        item['name'],
                        f"{item['quantity']:.1f}",
                        item['unit'] or 'ea',
                        f"${item['unit_cost']:.2f}",
                        f"${item['total_cost']:.2f}"
                    ])
                
                material_table = Table(material_data, colWidths=[2.5*inch, 0.6*inch, 0.6*inch, 0.8*inch, 0.8*inch])
                material_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                story.append(material_table)
                story.append(Spacer(1, 10))
        
        # Labor section
        if breakdown['labor']:
            story.append(Paragraph("Labor", styles['Heading3']))
            
            for category, tasks in breakdown['labor'].items():
                story.append(Paragraph(f"<b>{category}</b>", styles['Normal']))
                
                labor_data = [['Task', 'Hours', 'Rate/Hr', 'Total']]
                for task in tasks:
                    labor_data.append([
                        task['task'],
                        f"{task['hours']:.1f}",
                        f"${task['hourly_rate']:.2f}",
                        f"${task['total_cost']:.2f}"
                    ])
                
                labor_table = Table(labor_data, colWidths=[3*inch, 0.8*inch, 0.8*inch, 0.8*inch])
                labor_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                story.append(labor_table)
                story.append(Spacer(1, 10))
        
        # Area costs section
        if breakdown['area_costs']:
            story.append(Paragraph("Area-Based Costs", styles['Heading3']))
            
            area_data = [['Room/Area', 'Square Feet', 'Rate/SF', 'Total']]
            for room, data in breakdown['area_costs'].items():
                area_data.append([
                    f"{room} ({data['category']})",
                    f"{data['area_ft2']:.0f}",
                    f"${data['psf_rate']:.2f}",
                    f"${data['total_cost']:.2f}"
                ])
            
            area_table = Table(area_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
            area_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            story.append(area_table)
            story.append(Spacer(1, 20))
        
        # Total summary
        story.append(Paragraph("Cost Summary", heading_style))
        
        totals_data = [
            ['Materials & Supplies:', f"${breakdown['totals']['materials']:,.2f}"],
            ['Labor:', f"${breakdown['totals']['labor']:,.2f}"],
            ['Area-Based Costs:', f"${breakdown['totals']['area_costs']:,.2f}"],
            ['', ''],
            ['Subtotal:', f"${estimate.subtotal:,.2f}"],
            [f'Profit ({estimate.profit_percentage}%):', f"${estimate.profit_amount:,.2f}"],
            [f'Contingency ({estimate.contingency_percentage}%):', f"${estimate.contingency_amount:,.2f}"],
            ['', ''],
            ['GRAND TOTAL:', f"${estimate.grand_total:,.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#1C1C1E')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, -1), (-1, -1), 12),
            ('LINEBELOW', (0, 4), (-1, 4), 1, colors.black),
            ('LINEBELOW', (0, 7), (-1, 7), 1, colors.black),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        # Terms and conditions
        story.append(Paragraph("Terms & Conditions", heading_style))
        terms = """
        • This estimate is valid for 30 days from the date above.
        • All work will be performed in accordance with local building codes.
        • Change orders may affect the final cost and timeline.
        • Payment schedule: 10% down, progress payments as work is completed.
        • Final payment due upon substantial completion.
        • Warranty: 1 year on workmanship, manufacturer warranty on materials.
        """
        story.append(Paragraph(terms, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        logging.info(f"PDF proposal generated for estimate {estimate.id}")
        return buffer
        
    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        raise Exception(f"Failed to generate PDF proposal: {str(e)}")
