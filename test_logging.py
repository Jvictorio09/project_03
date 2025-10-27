#!/usr/bin/env python
"""
Simple test script to verify logging configuration works
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings')
django.setup()

# Test logging
import logging
from myApp.utils.logging_config import get_company_logger

# Test basic logging
logger = logging.getLogger('myApp')
logger.info("Basic logging test - this should appear in console and logs/app.log")

# Test structured logging
company_logger = get_company_logger('test')
company_logger.info(
    "Structured logging test",
    company_id="test-company-123",
    user_id="test-user-456",
    route="/test",
    action="GET",
    status=200,
    correlation_id="test-correlation-789"
)

print("Logging test completed! Check logs/app.log for output.")
