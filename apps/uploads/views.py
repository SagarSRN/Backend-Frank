
import os
import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.http import JsonResponse

from .models import PlanUpload
from .serializers import PlanUploadSerializer
from apps.projects.models import Project
from .tasks import process_dxf_upload

logger = logging.getLogger(__name__)


class PlanUploadViewSet(viewsets.ModelViewSet):
    """API endpoint for plan uploads"""
    
    queryset = PlanUpload.objects.all()
    serializer_class = PlanUploadSerializer
    
    def create(self, request, *args, **kwargs):
        """Handle file upload"""
        
        logger.info("=" * 80)
        logger.info("📤 UPLOAD REQUEST RECEIVED")
        logger.info("=" * 80)
        logger.info(f"Files in request: {list(request.FILES.keys())}")
        logger.info(f"Data in request: {dict(request.data)}")
        
        try:
            # Get uploaded file
            uploaded_file = request.FILES.get('file')
            
            if not uploaded_file:
                logger.error("❌ No file in request")
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"📄 File received: {uploaded_file.name}")
            logger.info(f"   Size: {uploaded_file.size} bytes")
            
            # Get project
            project_id = request.data.get('project_id')
            
            if not project_id:
                logger.error("❌ No project_id provided")
                return Response(
                    {'error': 'project_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"📦 Project ID: {project_id}")
            
            try:
                project = Project.objects.get(id=project_id)
                logger.info(f"✅ Project found: {project.name}")
            except Project.DoesNotExist:
                logger.error(f"❌ Project {project_id} not found")
                return Response(
                    {'error': f'Project {project_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get scale and file type
            scale = request.data.get('scale', 'mm')
            file_type = request.data.get('file_type', 'dxf')
            
            logger.info(f"📏 Scale: {scale}")
            
            # Create upload record
            upload = PlanUpload.objects.create(
                project=project,
                file=uploaded_file,
                file_type=file_type,
                scale=scale,
                processing_status='PENDING'
            )
            
            logger.info(f"✅ Upload record created with ID: {upload.id}")
            
            # Get file path
            file_path = upload.file.path
            logger.info(f"📁 File saved to: {file_path}")
            
            # Process DXF file
            logger.info("🔄 Starting DXF processing...")
            
            try:
                # Pass all 3 required arguments
                result = process_dxf_upload(upload.id, file_path, project.id)
                
                logger.info(f"✅ DXF processing completed: {result}")
                
                # Refresh upload to get updated status
                upload.refresh_from_db()
                
                # Return response
                serializer = self.get_serializer(upload)
                
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                logger.error(f"❌ DXF processing error: {str(e)}")
                logger.exception("Full traceback:")
                
                # Update upload status
                upload.processing_status = 'FAILED'
                upload.processing_result = {'error': str(e)}
                upload.save()
                
                return Response(
                    {
                        'error': f'DXF processing failed: {str(e)}',
                        'upload_id': upload.id
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"❌ ERROR during upload: {str(e)}")
            logger.exception("Full traceback:")
            logger.info("=" * 80)
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get upload processing status"""
        
        upload = self.get_object()
        
        return Response({
            'id': upload.id,
            'status': upload.processing_status,
            'result': upload.processing_result,
            'created_at': upload.created_at,
            'updated_at': upload.updated_at
        })


# Standalone function for project upload status
def project_upload_status(request, pk):
    """Get all uploads for a project - standalone view"""
    
    try:
        project = Project.objects.get(id=pk)
        uploads = PlanUpload.objects.filter(project=project).order_by('-created_at')
        
        serializer = PlanUploadSerializer(uploads, many=True)
        
        return JsonResponse({
            'project_id': pk,
            'project_name': project.name,
            'uploads': serializer.data
        })
    except Project.DoesNotExist:
        return JsonResponse(
            {'error': f'Project {pk} not found'},
            status=404
        )