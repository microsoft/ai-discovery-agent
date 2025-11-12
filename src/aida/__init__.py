# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""AI Discovery Agent package.

This package provides an AI-powered workshop facilitation system built with
Chainlit and FastAPI. The main application factory is exposed for use in
WSGI servers and testing.
"""

from .app import create_app, init_app

__all__ = ["create_app", "init_app"]
