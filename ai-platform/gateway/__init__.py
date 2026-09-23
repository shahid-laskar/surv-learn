"""
ai-platform/gateway package
"""

from ai_platform.gateway.event_gateway import AiEventGateway
from ai_platform.gateway.mqtt_adapter import FrigateMqttAdapter

__all__ = ["AiEventGateway", "FrigateMqttAdapter"]
