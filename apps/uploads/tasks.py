"""
Background tasks for processing uploads
Simple keyword-based DXF processing
"""

import logging
from apps.uploads.models import PlanUpload
from apps.projects.models import Project
from apps.retail_materials.dxf_processor import DXFProcessor

logger = logging.getLogger(__name__)


def process_dxf_upload(upload_id, file_path, project_id):
    """
    Process DXF upload using simple keyword matching
    
    Args:
        upload_id: ID of PlanUpload record
        file_path: Path to uploaded DXF file
        project_id: ID of associated project
    """
    
    logger.info(f"Starting DXF processing for upload {upload_id}")
    
    try:
        upload = PlanUpload.objects.get(id=upload_id)
        upload.processing_status = 'PROCESSING'
        upload.save()
        
        logger.info(f"Processing DXF file: {file_path}")
        
        # Get project
        project = Project.objects.get(id=project_id)
        
        # Use DXFProcessor - it creates the estimate internally
        processor = DXFProcessor(file_path, project)
        estimate = processor.process()
        
        if estimate:
            upload.processing_status = 'COMPLETED'
            upload.processing_result = {
                'estimate_id': estimate.id,
                'total': float(estimate.total)
            }
            upload.save()
            
            logger.info(f"✅ DXF processing completed successfully for upload {upload_id}")
            logger.info(f"   Estimate ID: {estimate.id}")
            logger.info(f"   Total: ₹{estimate.total:,.2f}")
            
            return {
                'success': True,
                'estimate_id': estimate.id,
                'total': float(estimate.total)
            }
        else:
            upload.processing_status = 'FAILED'
            upload.processing_result = {'error': 'Processing failed'}
            upload.save()
            
            logger.error(f"❌ DXF processing failed")
            return {
                'success': False,
                'error': 'Processing failed'
            }
            
    except Exception as e:
        logger.error(f"❌ Error in process_dxf_upload: {str(e)}")
        
        try:
            upload = PlanUpload.objects.get(id=upload_id)
            upload.processing_status = 'FAILED'
            upload.processing_result = {'error': str(e)}
            upload.save()
        except:
            pass
        
        return {
            'success': False,
            'error': str(e)
        }