from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.estimates.services import generate_estimate


class GenerateEstimateAPIView(APIView):
    def post(self, request, project_id):
        estimate = generate_estimate(project_id)

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
