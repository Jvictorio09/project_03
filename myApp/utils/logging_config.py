"""
Structured logging configuration for observability
"""
import logging
import json
from django.conf import settings
from django.utils import timezone


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'company_id'):
            log_entry['company_id'] = record.company_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'route'):
            log_entry['route'] = record.route
        if hasattr(record, 'action'):
            log_entry['action'] = record.action
        if hasattr(record, 'status'):
            log_entry['status'] = record.status
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class CompanyAwareLogger:
    """Logger that automatically includes company context"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def _log_with_context(self, level, message, company_id=None, user_id=None, route=None, action=None, status=None, correlation_id=None, **kwargs):
        extra = {
            'company_id': company_id,
            'user_id': user_id,
            'route': route,
            'action': action,
            'status': status,
            'correlation_id': correlation_id,
        }
        extra.update(kwargs)
        
        getattr(self.logger, level)(message, extra=extra)
    
    def info(self, message, **kwargs):
        self._log_with_context('info', message, **kwargs)
    
    def warning(self, message, **kwargs):
        self._log_with_context('warning', message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log_with_context('error', message, **kwargs)
    
    def debug(self, message, **kwargs):
        self._log_with_context('debug', message, **kwargs)


def get_company_logger(name):
    """Get a company-aware logger"""
    return CompanyAwareLogger(name)


def mask_pii(data):
    """Mask PII in log data"""
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if key.lower() in ['email', 'phone', 'name']:
                if key.lower() == 'email' and '@' in str(value):
                    masked[key] = f"{str(value)[:3]}***@{str(value).split('@')[1]}"
                elif key.lower() == 'phone':
                    masked[key] = f"+63****{str(value)[-4:]}"
                else:
                    masked[key] = f"{str(value)[:2]}***"
            else:
                masked[key] = value
        return masked
    return data
