from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import PlanUpload
from .serializers import PlanUploadSerializer
from apps.projects.models import Project
from .tasks import process_dxf_upload


class PlanUploadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for uploading and managing plan files (DXF)
    AUTO-CREATES PROJECT IF MISSING
    """
    queryset = PlanUpload.objects.all()
    serializer_class = PlanUploadSerializer

    def create(self, request, *args, **kwargs):
        """
        Handle file upload - AUTO-CREATE PROJECT IF NEEDED
        """
        print("\n" + "="*80)
        print("📤 UPLOAD REQUEST RECEIVED")
        print("="*80)
        print(f"Files in request: {list(request.FILES.keys())}")
        print(f"Data in request: {dict(request.data)}")
        
        # Check if file is present
        if 'file' not in request.FILES:
            print("❌ ERROR: No file in request!")
            return Response(
                {'error': 'No file provided. Please upload a DXF file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        print(f"📄 File received: {uploaded_file.name}")
        print(f"   Size: {uploaded_file.size} bytes")
        
        # Validate file extension
        if not uploaded_file.name.lower().endswith('.dxf'):
            print(f"❌ ERROR: Invalid file type!")
            return Response(
                {'error': 'Invalid file type. Please upload a .dxf file.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get project_id from request data
        project_id = request.data.get('project_id')
        if not project_id:
            print("❌ ERROR: No project_id provided!")
            return Response(
                {'error': 'project_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"📦 Project ID: {project_id}")
        
        # Get or create project
        try:
            project = Project.objects.get(id=project_id)
            print(f"✅ Project found: {project.name}")
        except Project.DoesNotExist:
            print(f"⚠️ Project {project_id} not found! Creating it...")
            
            # AUTO-CREATE PROJECT
            project = Project.objects.create(
                id=project_id,
                name=f"Auto-Created Project {project_id}",
                location="Not Specified",
                builtup_area=1000  # Default value
            )
            print(f"✅ Auto-created project: {project.name}")
        
        # Get scale (default to 'mm')
        scale = request.data.get('scale', 'mm')
        print(f"📏 Scale: {scale}")
        
        # Create upload record
        try:
            upload = PlanUpload.objects.create(
                project=project,
                file=uploaded_file,
                file_type='dxf',
                scale=scale,
                processed=False
            )
            print(f"✅ Upload record created with ID: {upload.id}")
            
            # Process DXF file
            print(f"🔄 Starting DXF processing...")
            process_dxf_upload(upload.id)
            
            # Serialize and return
            serializer = self.get_serializer(upload)
            print(f"✅ Upload successful!")
            print("="*80 + "\n")
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            print(f"❌ ERROR during upload: {str(e)}")
            import traceback
            print(traceback.format_exc())
            print("="*80 + "\n")
            
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def project_upload_status(request, project_id):
    """
    Get upload status for a project
    """
    try:
        project = get_object_or_404(Project, id=project_id)
        uploads = PlanUpload.objects.filter(project=project).order_by('-uploaded_at')
        
        if not uploads.exists():
            return Response({
                'has_upload': False,
                'message': 'No uploads found for this project'
            })
        
        latest_upload = uploads.first()
        serializer = PlanUploadSerializer(latest_upload)
        
        return Response({
            'has_upload': True,
            'upload': serializer.data,
            'processed': latest_upload.processed
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )