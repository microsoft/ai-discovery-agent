"""
Test fixtures for AI Discovery Workshop Agent tests.

This module provides reusable test data and mock objects.
"""

from typing import Any

# Sample configuration data for testing
SAMPLE_AGENT_CONFIG = {
    "agents": {
        "facilitator": {
            "persona": "prompts/facilitator_persona.md",
            "document": "prompts/workshop_guide.md",
            "model": "gpt-4o",
            "temperature": 0.7,
        },
        "expert": {
            "persona": "prompts/expert_persona.md",
            "documents": [
                "prompts/domain_knowledge.md",
                "prompts/best_practices.md",
            ],
            "model": "gpt-4o-mini",
            "temperature": 1.0,
        },
    },
    "sections": {
        "main": [
            {
                "type": "agent",
                "agent": "facilitator",
                "title": "Workshop Facilitator",
                "header": "Facilitator",
                "subtitle": "AI Workshop Facilitator",
                "icon": "🎯",
                "url": "/facilitator",
                "default": True,
            },
            {
                "type": "agent",
                "agent": "expert",
                "title": "Expert Advisor",
                "header": "Expert",
                "subtitle": "Domain Expert",
                "icon": "🧠",
                "url": "/expert",
                "admin_only": True,
            },
        ]
    },
}

SAMPLE_AUTH_CONFIG = {
    "credentials": {
        "usernames": {
            "testuser": {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "password": "$2b$12$sample.hashed.password.for.testing",
                "roles": ["user"],
            },
            "admin": {
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "password": "$2b$12$sample.hashed.password.for.admin",
                "roles": ["admin", "user"],
            },
        }
    }
}


def create_mock_user(
    identifier: str = "testuser",
    metadata: dict[str, Any] = None,
) -> dict[str, Any]:
    """Create a mock user object for testing."""
    if metadata is None:
        metadata = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "roles": ["user"],
        }

    return {
        "identifier": identifier,
        "metadata": metadata,
    }


def create_mock_admin_user() -> dict[str, Any]:
    """Create a mock admin user for testing."""
    return create_mock_user(
        identifier="admin",
        metadata={
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "roles": ["admin", "user"],
        },
    )
