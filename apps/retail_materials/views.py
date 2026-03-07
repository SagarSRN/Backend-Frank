"""
Complete Retail Materials API Views with Export
Location: backend/apps/retail_materials/views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from .models import MaterialCategory, Material, Component, RetailEstimate
from .serializers import (
    MaterialCategorySerializer, MaterialSerializer,
    ComponentSerializer, RetailEstimateSerializer,
    RetailEstimateDetailSerializer
)
from apps.projects.models import Project

# For PDF/Excel export
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime


class MaterialCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for material categories
    """
    queryset = MaterialCategory.objects.filter(is_active=True)
    serializer_class = MaterialCategorySerializer
    
    @action(detail=True, methods=['get'])
    def materials(self, request, pk=None):
        """Get all materials in a category"""
        category = self.get_object()
        materials = category.materials.filter(is_active=True)
        serializer = MaterialSerializer(materials, many=True)
        return Response(serializer.data)


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for materials
    """
    queryset = Material.objects.filter(is_active=True)
    serializer_class = MaterialSerializer
    filterset_fields = ['category', 'category__category_type', 'unit']
    search_fields = ['name', 'specification']


class ComponentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for components
    """
    queryset = Component.objects.all()
    serializer_class = ComponentSerializer
    filterset_fields = ['project', 'component_type', 'auto_detected']
    
    def get_queryset(self):
        queryset = Component.objects.all()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('project', 'material', 'material__category')


class RetailEstimateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for retail estimates
    """
    queryset = RetailEstimate.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RetailEstimateDetailSerializer
        return RetailEstimateSerializer
    
    def get_queryset(self):
        queryset = RetailEstimate.objects.all()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.select_related('project')
    
    @action(detail=True, methods=['post'])
    def recalculate(self, request, pk=None):
        """Recalculate estimate totals"""
        estimate = self.get_object()
        total = estimate.calculate_totals()
        serializer = self.get_serializer(estimate)
        return Response({
            'message': 'Estimate recalculated successfully',
            'total': total,
            'estimate': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def by_category(self, request, pk=None):
        """Get estimate grouped by category"""
        estimate = self.get_object()
        grouped = estimate.get_components_by_category()
        
        # Calculate category totals
        result = []
        for category_name, components in grouped.items():
            category_total = sum(c['amount'] for c in components)
            result.append({
                'category': category_name,
                'components': components,
                'total': category_total
            })
        
        return Response({
            'project': estimate.project.name,
            'categories': result,
            'subtotal': float(estimate.subtotal),
            'gst_percentage': float(estimate.gst_percentage),
            'gst_amount': float(estimate.gst_amount),
            'total': float(estimate.total)
        })
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Download retail estimate as PDF"""
        estimate = self.get_object()
        project = estimate.project
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Retail_Estimate_{project.name}_{datetime.now().strftime("%Y%m%d")}.pdf"'
        
        # Create PDF
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#7C3AED'),
            alignment=TA_CENTER,
            spaceAfter=30,
        )
        
        # Title
        elements.append(Paragraph(f"<b>{project.name}</b>", title_style))
        elements.append(Paragraph(f"Retail Display Estimate", styles['Heading2']))
        elements.append(Paragraph(f"Location: {project.location}", styles['Normal']))
        elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Get components by category
        grouped = estimate.get_components_by_category()
        
        # Create table for each category
        for category_name, components in grouped.items():
            # Category header
            elements.append(Paragraph(f"<b>{category_name}</b>", styles['Heading3']))
            
            # Table data
            data = [['Description', 'Quantity', 'Unit', 'Rate (₹)', 'Amount (₹)']]
            category_total = 0
            
            for comp in components:
                data.append([
                    comp['description'],
                    f"{comp['quantity']:.2f}",
                    comp['unit'],
                    f"{comp['rate']:,.2f}",
                    f"{comp['amount']:,.2f}"
                ])
                category_total += comp['amount']
            
            # Category subtotal
            data.append(['', '', '', 'Subtotal:', f"₹{category_total:,.2f}"])
            
            # Create table
            table = Table(data, colWidths=[3*inch, 1*inch, 0.8*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Grand total table
        total_data = [
            ['Subtotal', f"₹{estimate.subtotal:,.2f}"],
            [f'GST @ {estimate.gst_percentage}%', f"₹{estimate.gst_amount:,.2f}"],
            ['Grand Total', f"₹{estimate.total:,.2f}"]
        ]
        
        total_table = Table(total_data, colWidths=[4*inch, 2*inch])
        total_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#7C3AED')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
        ]))
        
        elements.append(Spacer(1, 0.5*inch))
        elements.append(total_table)
        
        # Build PDF
        doc.build(elements)
        
        return response
    
    @action(detail=True, methods=['get'])
    def download_excel(self, request, pk=None):
        """Download retail estimate as Excel"""
        estimate = self.get_object()
        project = estimate.project
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Estimate"
        
        # Styles
        title_font = Font(size=18, bold=True, color="7C3AED")
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="7C3AED", end_color="7C3AED", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Title
        ws['A1'] = project.name
        ws['A1'].font = title_font
        ws['A2'] = f"Retail Display Estimate"
        ws['A3'] = f"Location: {project.location}"
        ws['A4'] = f"Date: {datetime.now().strftime('%B %d, %Y')}"
        
        row = 6
        
        # Get components by category
        grouped = estimate.get_components_by_category()
        
        for category_name, components in grouped.items():
            # Category header
            ws[f'A{row}'] = category_name
            ws[f'A{row}'].font = Font(size=14, bold=True)
            row += 1
            
            # Table headers
            headers = ['Description', 'Quantity', 'Unit', 'Rate (₹)', 'Amount (₹)']
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=row, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')
                cell.border = border
            row += 1
            
            # Components
            category_total = 0
            for comp in components:
                ws.cell(row=row, column=1, value=comp['description']).border = border
                ws.cell(row=row, column=2, value=comp['quantity']).border = border
                ws.cell(row=row, column=3, value=comp['unit']).border = border
                ws.cell(row=row, column=4, value=comp['rate']).border = border
                ws.cell(row=row, column=5, value=comp['amount']).border = border
                category_total += comp['amount']
                row += 1
            
            # Category subtotal
            ws.cell(row=row, column=4, value="Subtotal:").font = Font(bold=True)
            ws.cell(row=row, column=5, value=category_total).font = Font(bold=True)
            row += 2
        
        # Grand total
        ws.cell(row=row, column=4, value="Subtotal:")
        ws.cell(row=row, column=5, value=float(estimate.subtotal))
        row += 1
        
        ws.cell(row=row, column=4, value=f"GST @ {estimate.gst_percentage}%:")
        ws.cell(row=row, column=5, value=float(estimate.gst_amount))
        row += 1
        
        ws.cell(row=row, column=4, value="Grand Total:").font = Font(bold=True, size=14)
        ws.cell(row=row, column=5, value=float(estimate.total)).font = Font(bold=True, size=14, color="7C3AED")
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 40
        ws.column_dimensions['B'].width = 12
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 15
        ws.column_dimensions['E'].width = 15
        
        # Save to response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Retail_Estimate_{project.name}_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        wb.save(response)
        
        return response