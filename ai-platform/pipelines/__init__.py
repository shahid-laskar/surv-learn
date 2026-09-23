"""
ai-platform/pipelines package
"""

from ai_platform.pipelines.object_pipeline import ObjectAnalyticsPipeline
from ai_platform.pipelines.anpr_pipeline import AnprPipeline, normalize_indian_plate
from ai_platform.pipelines.crowd_pipeline import CrowdAnalyticsPipeline

__all__ = [
    "ObjectAnalyticsPipeline",
    "AnprPipeline",
    "normalize_indian_plate",
    "CrowdAnalyticsPipeline",
]
