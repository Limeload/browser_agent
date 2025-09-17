"""
Archive Service
Handles export and archival of session data, transcripts, and results
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog
import boto3
from google.cloud import storage
from models.schemas import (
    TranscriptResponse, IntentResponse, ExecutionResponse, 
    ExportData, SessionData
)
from services.monitoring import MonitoringService

logger = structlog.get_logger()

class ArchiveService:
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
        self.s3_client = None
        self.gcs_client = None
        self.local_storage_path = os.getenv("LOCAL_STORAGE_PATH", "./archive")
        
    async def initialize(self):
        """Initialize archive service"""
        logger.info("Initializing Archive service")
        
        try:
            # Initialize cloud storage clients
            if os.getenv("AWS_ACCESS_KEY_ID"):
                self.s3_client = boto3.client('s3')
                logger.info("S3 client initialized")
            
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                self.gcs_client = storage.Client()
                logger.info("GCS client initialized")
            
            # Create local storage directory
            os.makedirs(self.local_storage_path, exist_ok=True)
            
            logger.info("Archive service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Archive service", error=str(e))
            raise
    
    async def archive_session_data(
        self,
        session_id: str,
        transcript: TranscriptResponse,
        intent: IntentResponse,
        execution: ExecutionResponse
    ):
        """Archive session data"""
        try:
            logger.info("Archiving session data", session_id=session_id)
            
            # Create archive data structure
            archive_data = {
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "transcript": transcript.dict(),
                "intent": intent.dict(),
                "execution": execution.dict(),
                "metadata": {
                    "archive_version": "1.0",
                    "total_processing_time": (
                        transcript.processing_time + 
                        intent.processing_time + 
                        execution.execution_time
                    )
                }
            }
            
            # Save locally
            await self._save_locally(session_id, archive_data)
            
            # Upload to cloud storage
            await self._upload_to_cloud(session_id, archive_data)
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "archive_sessions_total",
                1,
                {"session_id": session_id}
            )
            
            logger.info("Session data archived successfully", session_id=session_id)
            
        except Exception as e:
            logger.error("Failed to archive session data", 
                        error=str(e), 
                        session_id=session_id)
            raise
    
    async def _save_locally(self, session_id: str, data: Dict[str, Any]):
        """Save data to local storage"""
        try:
            # Create session directory
            session_dir = os.path.join(self.local_storage_path, session_id)
            os.makedirs(session_dir, exist_ok=True)
            
            # Save JSON data
            json_path = os.path.join(session_dir, f"{session_id}_archive.json")
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Save screenshots if any
            if "execution" in data and "screenshots" in data["execution"]:
                screenshots_dir = os.path.join(session_dir, "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                for i, screenshot_data in enumerate(data["execution"]["screenshots"]):
                    screenshot_path = os.path.join(screenshots_dir, f"screenshot_{i}.png")
                    # Assuming screenshot_data is base64 encoded
                    import base64
                    with open(screenshot_path, 'wb') as f:
                        f.write(base64.b64decode(screenshot_data))
            
            logger.debug("Data saved locally", session_id=session_id, path=json_path)
            
        except Exception as e:
            logger.error("Failed to save locally", error=str(e), session_id=session_id)
            raise
    
    async def _upload_to_cloud(self, session_id: str, data: Dict[str, Any]):
        """Upload data to cloud storage"""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            # Upload to S3
            if self.s3_client:
                bucket_name = os.getenv("S3_BUCKET_NAME", "voice-agent-archive")
                key = f"sessions/{session_id}/{timestamp}_archive.json"
                
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.s3_client.put_object(
                        Bucket=bucket_name,
                        Key=key,
                        Body=json.dumps(data, indent=2),
                        ContentType='application/json'
                    )
                )
                
                logger.debug("Data uploaded to S3", session_id=session_id, key=key)
            
            # Upload to GCS
            if self.gcs_client:
                bucket_name = os.getenv("GCS_BUCKET_NAME", "voice-agent-archive")
                bucket = self.gcs_client.bucket(bucket_name)
                blob_name = f"sessions/{session_id}/{timestamp}_archive.json"
                blob = bucket.blob(blob_name)
                
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: blob.upload_from_string(
                        json.dumps(data, indent=2),
                        content_type='application/json'
                    )
                )
                
                logger.debug("Data uploaded to GCS", session_id=session_id, blob=blob_name)
            
        except Exception as e:
            logger.error("Failed to upload to cloud", error=str(e), session_id=session_id)
            # Don't raise - cloud upload failure shouldn't break the flow
    
    async def export_session(self, session_id: str, format: str = "json") -> Dict[str, Any]:
        """Export session data in specified format"""
        try:
            logger.info("Exporting session", session_id=session_id, format=format)
            
            # Load session data
            session_data = await self._load_session_data(session_id)
            
            if not session_data:
                raise ValueError(f"Session {session_id} not found")
            
            # Create export data
            export_data = ExportData(
                session_id=session_id,
                transcripts=[session_data["transcript"]],
                intents=[session_data["intent"]],
                executions=[session_data["execution"]],
                screenshots=session_data["execution"].get("screenshots", []),
                metadata=session_data.get("metadata", {})
            )
            
            if format == "json":
                return export_data.dict()
            
            elif format == "csv":
                return await self._export_to_csv(export_data)
            
            elif format == "html":
                return await self._export_to_html(export_data)
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error("Failed to export session", 
                        error=str(e), 
                        session_id=session_id)
            raise
    
    async def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from storage"""
        try:
            # Try local storage first
            session_dir = os.path.join(self.local_storage_path, session_id)
            json_path = os.path.join(session_dir, f"{session_id}_archive.json")
            
            if os.path.exists(json_path):
                with open(json_path, 'r') as f:
                    return json.load(f)
            
            # Try cloud storage
            if self.s3_client:
                bucket_name = os.getenv("S3_BUCKET_NAME", "voice-agent-archive")
                # List objects with session prefix
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.s3_client.list_objects_v2(
                        Bucket=bucket_name,
                        Prefix=f"sessions/{session_id}/"
                    )
                )
                
                if "Contents" in response:
                    # Get the most recent file
                    latest_file = max(response["Contents"], key=lambda x: x["LastModified"])
                    
                    # Download and return data
                    obj_response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.s3_client.get_object(
                            Bucket=bucket_name,
                            Key=latest_file["Key"]
                        )
                    )
                    
                    return json.loads(obj_response["Body"].read().decode('utf-8'))
            
            return None
            
        except Exception as e:
            logger.error("Failed to load session data", error=str(e), session_id=session_id)
            return None
    
    async def _export_to_csv(self, export_data: ExportData) -> Dict[str, Any]:
        """Export data to CSV format"""
        csv_data = {
            "session_id": export_data.session_id,
            "export_timestamp": export_data.export_timestamp.isoformat(),
            "format": "csv",
            "data": []
        }
        
        # Convert transcripts to CSV rows
        for transcript in export_data.transcripts:
            csv_data["data"].append({
                "type": "transcript",
                "timestamp": transcript.timestamp.isoformat(),
                "text": transcript.transcript,
                "confidence": transcript.confidence,
                "processing_time": transcript.processing_time
            })
        
        # Convert intents to CSV rows
        for intent in export_data.intents:
            csv_data["data"].append({
                "type": "intent",
                "timestamp": intent.timestamp.isoformat(),
                "intent_type": intent.intent_type,
                "confidence": intent.confidence,
                "raw_text": intent.raw_text,
                "processing_time": intent.processing_time
            })
        
        # Convert executions to CSV rows
        for execution in export_data.executions:
            csv_data["data"].append({
                "type": "execution",
                "timestamp": execution.timestamp.isoformat(),
                "success": execution.success,
                "execution_time": execution.execution_time,
                "final_url": execution.final_url,
                "error_message": execution.error_message
            })
        
        return csv_data
    
    async def _export_to_html(self, export_data: ExportData) -> Dict[str, Any]:
        """Export data to HTML format"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Voice Agent Session Report - {export_data.session_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .transcript {{ background-color: #e8f4fd; }}
                .intent {{ background-color: #fff2e8; }}
                .execution {{ background-color: #e8f8e8; }}
                .metadata {{ font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Voice Agent Session Report</h1>
                <p><strong>Session ID:</strong> {export_data.session_id}</p>
                <p><strong>Export Time:</strong> {export_data.export_timestamp}</p>
            </div>
        """
        
        # Add transcripts
        for transcript in export_data.transcripts:
            html_content += f"""
            <div class="section transcript">
                <h3>Transcript</h3>
                <p>{transcript.transcript}</p>
                <div class="metadata">
                    Confidence: {transcript.confidence:.2f} | 
                    Processing Time: {transcript.processing_time:.2f}s
                </div>
            </div>
            """
        
        # Add intents
        for intent in export_data.intents:
            html_content += f"""
            <div class="section intent">
                <h3>Intent</h3>
                <p><strong>Type:</strong> {intent.intent_type}</p>
                <p><strong>Text:</strong> {intent.raw_text}</p>
                <p><strong>Confidence:</strong> {intent.confidence:.2f}</p>
                <div class="metadata">
                    Processing Time: {intent.processing_time:.2f}s
                </div>
            </div>
            """
        
        # Add executions
        for execution in export_data.executions:
            html_content += f"""
            <div class="section execution">
                <h3>Execution</h3>
                <p><strong>Success:</strong> {execution.success}</p>
                <p><strong>Final URL:</strong> {execution.final_url or 'N/A'}</p>
                <p><strong>Execution Time:</strong> {execution.execution_time:.2f}s</p>
                {f'<p><strong>Error:</strong> {execution.error_message}</p>' if execution.error_message else ''}
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        return {
            "session_id": export_data.session_id,
            "export_timestamp": export_data.export_timestamp.isoformat(),
            "format": "html",
            "content": html_content
        }
    
    async def list_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List available sessions"""
        try:
            sessions = []
            
            # List local sessions
            if os.path.exists(self.local_storage_path):
                for session_dir in os.listdir(self.local_storage_path):
                    if os.path.isdir(os.path.join(self.local_storage_path, session_dir)):
                        json_path = os.path.join(self.local_storage_path, session_dir, f"{session_dir}_archive.json")
                        if os.path.exists(json_path):
                            with open(json_path, 'r') as f:
                                data = json.load(f)
                                sessions.append({
                                    "session_id": session_dir,
                                    "timestamp": data.get("timestamp"),
                                    "storage": "local"
                                })
            
            # Sort by timestamp (newest first)
            sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return sessions[:limit]
            
        except Exception as e:
            logger.error("Failed to list sessions", error=str(e))
            return []
    
    def is_healthy(self) -> bool:
        """Check if archive service is healthy"""
        try:
            return (
                self.s3_client is not None or 
                self.gcs_client is not None or
                os.path.exists(self.local_storage_path)
            )
        except Exception:
            return False
