from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.projects.models import Project
from apps.estimates.models import Estimate, RoomEstimate


@api_view(["GET"])
def project_estimate_summary(request, project_id):
    project = Project.objects.get(id=project_id)
    estimate = Estimate.objects.filter(project=project).first()
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
