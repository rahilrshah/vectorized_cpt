"""
API Gateway Package
Unified entry point for all microservices with API key authentication
"""

from .main import app
from .auth import api_key_manager
from .billing_router import billing_router
from .models import *

__version__ = "1.0.0"