"""
Metrics and monitoring routes.
"""

import time
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any

from api.deps import get_current_user

router = APIRouter()


class SystemMetrics(BaseModel):
    uptime: float
    total_queries: int
    successful_queries: int
    average_response_time: float
    active_connections: int
    documents_indexed: int


@router.get("/system", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """Get system performance metrics."""
    try:
        app_state = request.app.state
        
        # Get workflow metrics
        workflow_metrics = {}
        if hasattr(app_state, 'workflow'):
            workflow_metrics = app_state.workflow.get_metrics()
        
        # Get vector store info
        documents_count = 0
        if hasattr(app_state, 'vector_store'):
            try:
                info = await app_state.vector_store.get_collection_info()
                documents_count = info.get('points_count', 0)
            except:
                pass
        
        # Get connection count
        active_connections = 0
        if hasattr(app_state, 'connection_manager'):
            active_connections = app_state.connection_manager.get_connection_count()
        
        return SystemMetrics(
            uptime=time.time(),  # Simplified uptime
            total_queries=workflow_metrics.get('total_queries', 0),
            successful_queries=workflow_metrics.get('successful_queries', 0),
            average_response_time=workflow_metrics.get('average_execution_time', 0.0),
            active_connections=active_connections,
            documents_indexed=documents_count
        )
        
    except Exception as e:
        return SystemMetrics(
            uptime=time.time(),
            total_queries=0,
            successful_queries=0,
            average_response_time=0.0,
            active_connections=0,
            documents_indexed=0
        )