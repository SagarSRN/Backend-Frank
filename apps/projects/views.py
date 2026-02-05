from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectSerializer

from apps.rooms.models import Room
from apps.estimates.models import Estimate


# ✅ CRUD APIs → /api/projects/
class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


# ✅ Summary API → /api/projects/<id>/summary/
@api_view(["GET"])
def project_summary(request, project_id):
    project = Project.objects.get(id=project_id)

    rooms = Room.objects.filter(project=project)
    estimate = Estimate.objects.filter(project=project).first()

    return Response({
        "project": {
            "id": project.id,
            "name": project.name,
            "builtup_area": project.builtup_area
        },
        "rooms": [
            {
                "name": r.name,
                "area": r.area
            }
            for r in rooms
        ],
        "estimate": {
            "total_tiles_sqm": estimate.total_tiles_sqm if estimate else 0,
            "total_paint_sqm": estimate.total_paint_sqm if estimate else 0,
            "cement_bags": estimate.cement_bags if estimate else 0,
            "sand_tons": estimate.sand_tons if estimate else 0,
            "total_cost": estimate.total_cost if estimate else 0
        }
    })
