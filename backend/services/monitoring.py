"""
Monitoring Service
Handles structured logging, metrics collection, and observability
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import structlog
import redis
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from elasticsearch import Elasticsearch
import boto3
from google.cloud import storage

logger = structlog.get_logger()

class MonitoringService:
    def __init__(self):
        self.redis_client = None
        self.elasticsearch_client = None
        self.s3_client = None
        self.gcs_client = None
        
        # Prometheus metrics
        self.metrics = {
            "requests_total": Counter("voice_agent_requests_total", "Total requests", ["service", "endpoint"]),
            "request_duration": Histogram("voice_agent_request_duration_seconds", "Request duration", ["service"]),
            "errors_total": Counter("voice_agent_errors_total", "Total errors", ["service", "error_type"]),
            "active_sessions": Gauge("voice_agent_active_sessions", "Active sessions"),
            "stt_processing_time": Histogram("voice_agent_stt_processing_seconds", "STT processing time"),
            "intent_parsing_time": Histogram("voice_agent_intent_parsing_seconds", "Intent parsing time"),
            "planning_time": Histogram("voice_agent_planning_seconds", "Planning time"),
            "execution_time": Histogram("voice_agent_execution_seconds", "Execution time"),
            "cache_hits": Counter("voice_agent_cache_hits_total", "Cache hits", ["cache_type"]),
            "cache_misses": Counter("voice_agent_cache_misses_total", "Cache misses", ["cache_type"])
        }
        
    async def initialize(self):
        """Initialize monitoring services"""
        logger.info("Initializing Monitoring service")
        
        try:
            # Initialize Redis for caching and session management
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            
            # Initialize Elasticsearch for log storage
            es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
            self.elasticsearch_client = Elasticsearch([es_url])
            
            # Initialize cloud storage clients
            if os.getenv("AWS_ACCESS_KEY_ID"):
                self.s3_client = boto3.client('s3')
            
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                self.gcs_client = storage.Client()
            
            # Start Prometheus metrics server
            metrics_port = int(os.getenv("METRICS_PORT", "9090"))
            start_http_server(metrics_port)
            
            logger.info("Monitoring service initialized successfully", metrics_port=metrics_port)
            
        except Exception as e:
            logger.error("Failed to initialize Monitoring service", error=str(e))
            raise
    
    async def record_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric"""
        try:
            if metric_name in self.metrics:
                metric = self.metrics[metric_name]
                
                if isinstance(metric, Counter):
                    metric.labels(**tags or {}).inc(value)
                elif isinstance(metric, Histogram):
                    metric.labels(**tags or {}).observe(value)
                elif isinstance(metric, Gauge):
                    metric.set(value)
                
                logger.debug("Metric recorded", metric=metric_name, value=value, tags=tags)
                
        except Exception as e:
            logger.error("Failed to record metric", error=str(e), metric=metric_name)
    
    async def log_event(
        self, 
        level: str, 
        message: str, 
        service: str, 
        session_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Log structured event"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level,
                "service": service,
                "message": message,
                "session_id": session_id,
                "metadata": metadata or {}
            }
            
            # Log to structured logger
            getattr(logger, level.lower())(message, **log_entry)
            
            # Send to Elasticsearch if available
            if self.elasticsearch_client:
                await self._send_to_elasticsearch(log_entry)
            
            # Send to Redis for real-time monitoring
            if self.redis_client:
                await self._send_to_redis(log_entry)
                
        except Exception as e:
            logger.error("Failed to log event", error=str(e))
    
    async def _send_to_elasticsearch(self, log_entry: Dict[str, Any]):
        """Send log entry to Elasticsearch"""
        try:
            index_name = f"voice-agent-logs-{datetime.utcnow().strftime('%Y.%m.%d')}"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.elasticsearch_client.index(
                    index=index_name,
                    body=log_entry
                )
            )
            
        except Exception as e:
            logger.error("Failed to send to Elasticsearch", error=str(e))
    
    async def _send_to_redis(self, log_entry: Dict[str, Any]):
        """Send log entry to Redis for real-time monitoring"""
        try:
            # Store in Redis with TTL
            key = f"logs:{log_entry['session_id']}:{datetime.utcnow().timestamp()}"
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.setex(
                    key, 
                    3600,  # 1 hour TTL
                    json.dumps(log_entry)
                )
            )
            
        except Exception as e:
            logger.error("Failed to send to Redis", error=str(e))
    
    async def get_session_logs(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a specific session"""
        try:
            if not self.redis_client:
                return []
            
            # Get logs from Redis
            pattern = f"logs:{session_id}:*"
            keys = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.keys(pattern)
            )
            
            # Sort by timestamp (newest first)
            keys.sort(reverse=True)
            keys = keys[:limit]
            
            logs = []
            for key in keys:
                log_data = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda k=key: self.redis_client.get(k)
                )
                if log_data:
                    logs.append(json.loads(log_data))
            
            return logs
            
        except Exception as e:
            logger.error("Failed to get session logs", error=str(e), session_id=session_id)
            return []
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {}
            }
            
            # Get Prometheus metrics
            for metric_name, metric in self.metrics.items():
                if hasattr(metric, '_value'):
                    summary["metrics"][metric_name] = metric._value.get()
                elif hasattr(metric, '_sum'):
                    summary["metrics"][metric_name] = {
                        "count": metric._count.get(),
                        "sum": metric._sum.get()
                    }
            
            return summary
            
        except Exception as e:
            logger.error("Failed to get metrics summary", error=str(e))
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on monitoring services"""
        health = {
            "redis": False,
            "elasticsearch": False,
            "s3": False,
            "gcs": False,
            "prometheus": True  # Always true if we got this far
        }
        
        try:
            # Check Redis
            if self.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.redis_client.ping()
                )
                health["redis"] = True
        except Exception:
            pass
        
        try:
            # Check Elasticsearch
            if self.elasticsearch_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.elasticsearch_client.ping()
                )
                health["elasticsearch"] = True
        except Exception:
            pass
        
        try:
            # Check S3
            if self.s3_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.s3_client.list_buckets()
                )
                health["s3"] = True
        except Exception:
            pass
        
        try:
            # Check GCS
            if self.gcs_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: list(self.gcs_client.list_buckets())
                )
                health["gcs"] = True
        except Exception:
            pass
        
        return health
    
    async def export_logs(self, session_id: str, format: str = "json") -> Dict[str, Any]:
        """Export logs for a session"""
        try:
            logs = await self.get_session_logs(session_id)
            
            if format == "json":
                return {
                    "session_id": session_id,
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "logs": logs,
                    "count": len(logs)
                }
            elif format == "csv":
                # Convert to CSV format
                csv_data = []
                for log in logs:
                    csv_data.append({
                        "timestamp": log.get("timestamp"),
                        "level": log.get("level"),
                        "service": log.get("service"),
                        "message": log.get("message"),
                        "session_id": log.get("session_id")
                    })
                
                return {
                    "session_id": session_id,
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "data": csv_data,
                    "format": "csv"
                }
            
        except Exception as e:
            logger.error("Failed to export logs", error=str(e), session_id=session_id)
            raise
    
    async def shutdown(self):
        """Shutdown monitoring service"""
        logger.info("Shutting down Monitoring service")
        
        try:
            if self.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.redis_client.close()
                )
            
            if self.elasticsearch_client:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.elasticsearch_client.close()
                )
            
            logger.info("Monitoring service shutdown complete")
            
        except Exception as e:
            logger.error("Error during monitoring shutdown", error=str(e))
    
    def is_healthy(self) -> bool:
        """Check if monitoring service is healthy"""
        try:
            return (
                self.redis_client is not None or 
                self.elasticsearch_client is not None or
                self.s3_client is not None or
                self.gcs_client is not None
            )
        except Exception:
            return False
