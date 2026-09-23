"""
ai-platform/schemas package
"""

from ai_platform.schemas.events import (
    BaseAiEvent,
    BoundingBox,
    ObjectDetectionPayload,
    SpatialRuleEventPayload,
    AnprEventPayload,
    PeopleCountingPayload,
    CrowdDensityPayload,
    QueueAnalyticsPayload,
    FallDetectionPayload,
    FaceMatchPayload,
)

__all__ = [
    "BaseAiEvent",
    "BoundingBox",
    "ObjectDetectionPayload",
    "SpatialRuleEventPayload",
    "AnprEventPayload",
    "PeopleCountingPayload",
    "CrowdDensityPayload",
    "QueueAnalyticsPayload",
    "FallDetectionPayload",
    "FaceMatchPayload",
]
