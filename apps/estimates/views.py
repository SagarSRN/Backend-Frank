from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import os

from apps.estimates.services_enhanced import generate_detailed_estimate
from apps.estimates.models import Estimate, RoomEstimate
from apps.projects.models import Project
from apps.estimates.pdf_generator import generate_estimate_pdf


class GenerateEstimateAPIView(APIView):
    """
    Generate estimate for a project
    POST /api/projects/{id}/generate-estimate/
    """
    def post(self, request, project_id):
        estimate = generate_detailed_estimate(project_id)

        if not estimate:
            return Response(
                {"error": "No rooms found for this project"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "project_id": project_id,
                "total_tiles_sqm": estimate.total_tiles_sqm,
                "total_paint_sqm": estimate.total_paint_sqm,
                "cement_bags": estimate.cement_bags,
                "sand_tons": estimate.sand_tons,
                "total_cost": estimate.total_cost,
            },
            status=status.HTTP_201_CREATED
        )


@api_view(["GET"])
def project_estimate_summary(request, project_id):
    """
    Get estimate summary for a project
    GET /api/projects/{id}/estimate/
    """
    project = get_object_or_404(Project, id=project_id)
    estimate = getattr(project, "estimate", None)
    room_estimates = RoomEstimate.objects.filter(project=project)

    return Response({
        "project": {
            "id": project.id,
            "name": project.name,
            "builtup_area": project.builtup_area,
        },
        "summary": {
            "total_tiles_sqm": estimate.total_tiles_sqm if estimate else 0,
            "total_paint_sqm": estimate.total_paint_sqm if estimate else 0,
            "cement_bags": estimate.cement_bags if estimate else 0,
            "sand_tons": estimate.sand_tons if estimate else 0,
            "total_cost": estimate.total_cost if estimate else 0,
        },
        "rooms": [
            {
                "room": r.room.name,
                "tiles_sqm": r.tiles_sqm,
                "paint_sqm": r.paint_sqm,
                "cement_bags": r.cement_bags,
                "sand_tons": r.sand_tons,
                "cost": r.cost,
            }
            for r in room_estimates
        ]
    })


@api_view(["GET"])
def download_estimate_pdf(request, project_id):
    """
    Generate and download PDF estimate for a project
    GET /api/projects/{id}/estimate/download-pdf/
    """
    project = get_object_or_404(Project, id=project_id)
    estimate = getattr(project, "estimate", None)
    
    if not estimate:
        return Response(
            {'error': 'No estimate found for this project'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    room_estimates = RoomEstimate.objects.filter(project=project)
    
    # Generate PDF
    try:
        pdf_path = generate_estimate_pdf(project, estimate, room_estimates)
        
        # Return the file
        pdf_file = open(pdf_path, 'rb')
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="estimate_{project.name.replace(" ", "_")}.pdf"'
        
        return response
    
    except Exception as e:
        return Response(
            {'error': f'Error generating PDF: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )