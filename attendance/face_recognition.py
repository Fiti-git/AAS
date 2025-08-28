# in your_app/face_recognition.py

import boto3
import logging

logger = logging.getLogger(__name__)

def compare_faces(source_bytes, target_bytes, aws_access_key, aws_secret_key, aws_region='us-east-2', similarity_threshold=95):
    """
    Compares two faces using AWS Rekognition.
    Accepts image bytes directly.
    """
    try:
        rekognition = boto3.client(
            'rekognition',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

        response = rekognition.compare_faces(
            SourceImage={'Bytes': source_bytes},
            TargetImage={'Bytes': target_bytes},
            SimilarityThreshold=similarity_threshold
        )
        return response
    except Exception as e:
        logger.error(f"AWS Rekognition error: {str(e)}")
        # Re-raise the exception to be handled by the view
        raise e