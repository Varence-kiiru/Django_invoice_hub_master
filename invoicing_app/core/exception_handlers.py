"""Custom exception handlers for consistent API error responses."""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that formats all API errors consistently.
    
    Returns error responses in format:
    {
        "success": false,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "One or more fields have errors.",
            "details": {
                "field_name": ["error message 1", "error message 2"],
                ...
            }
        }
    }
    """
    
    # Call the default exception handler first
    response = exception_handler(exc, context)
    
    # If response is None, no exception was handled by DRF
    if response is None:
        # Log unhandled exceptions
        logger.error(
            f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
            exc_info=True
        )
        
        # Return generic 500 error
        return Response(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred.",
                    "details": None
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Format the response data
    error_response = format_error_response(response, exc)
    
    return Response(error_response, status=response.status_code)


def format_error_response(response, exc):
    """
    Format error response with standard structure.
    
    Args:
        response: DRF response object
        exc: Exception object
    
    Returns:
        Formatted error response dict
    """
    
    status_code = response.status_code
    
    # Determine error code based on status
    error_code = get_error_code(status_code, exc)
    
    # Get error message
    message = get_error_message(status_code, exc)
    
    # Extract and format details
    details = extract_error_details(response.data, status_code)
    
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details if details else None
        }
    }


def get_error_code(status_code, exc):
    """Get standardized error code based on status and exception."""
    
    if status_code == 400:
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            return "VALIDATION_ERROR"
        elif 'invalid' in str(exc).lower():
            return "INVALID_REQUEST"
        return "BAD_REQUEST"
    
    elif status_code == 401:
        return "UNAUTHORIZED"
    
    elif status_code == 403:
        return "PERMISSION_DENIED"
    
    elif status_code == 404:
        return "NOT_FOUND"
    
    elif status_code == 405:
        return "METHOD_NOT_ALLOWED"
    
    elif status_code == 409:
        return "CONFLICT"
    
    elif status_code == 429:
        return "RATE_LIMITED"
    
    elif status_code == 500:
        return "INTERNAL_SERVER_ERROR"
    
    elif status_code == 503:
        return "SERVICE_UNAVAILABLE"
    
    else:
        return "ERROR"


def get_error_message(status_code, exc):
    """Get user-friendly error message based on status and exception."""
    
    messages = {
        400: "The request contains invalid data. Please check the details below.",
        401: "Authentication required. Please log in.",
        403: "You don't have permission to access this resource.",
        404: "The requested resource was not found.",
        405: "The HTTP method used is not allowed for this resource.",
        409: "The request conflicts with existing data.",
        429: "Too many requests. Please wait before trying again.",
        500: "An internal server error occurred. Please try again later.",
        503: "The service is temporarily unavailable. Please try again later.",
    }
    
    return messages.get(status_code, "An error occurred while processing your request.")


def extract_error_details(data, status_code):
    """
    Extract and format error details from response data.
    
    Args:
        data: Response data (dict or list)
        status_code: HTTP status code
    
    Returns:
        Formatted error details dict
    """
    
    if status_code == 400:
        # For validation errors, data is usually a dict
        if isinstance(data, dict):
            # Flatten nested structures
            details = {}
            for key, value in data.items():
                details[key] = flatten_error_list(value)
            return details
        elif isinstance(data, list):
            return {"detail": flatten_error_list(data)}
    
    elif status_code == 404:
        if isinstance(data, dict):
            return {"detail": data.get('detail', 'Not found')}
        return {"detail": "Not found"}
    
    elif status_code == 403:
        if isinstance(data, dict):
            detail = data.get('detail', 'Access denied')
        else:
            detail = str(data) if data else 'Access denied'
        return {"detail": detail}
    
    elif status_code == 401:
        if isinstance(data, dict):
            detail = data.get('detail', 'Not authenticated')
        else:
            detail = str(data) if data else 'Not authenticated'
        return {"detail": detail}
    
    # For other status codes, return data as-is
    return data if isinstance(data, dict) else {"detail": str(data)}


def flatten_error_list(errors):
    """
    Convert error list to flat list of strings.
    
    Handles nested structures from serializer errors.
    """
    if isinstance(errors, list):
        result = []
        for error in errors:
            if hasattr(error, 'message'):
                result.append(error.message)
            elif isinstance(error, dict):
                # Recursive for nested dicts
                for v in error.values():
                    if isinstance(v, list):
                        result.extend(flatten_error_list(v))
                    else:
                        result.append(str(v))
            else:
                result.append(str(error))
        return result
    
    elif isinstance(errors, dict):
        result = []
        for value in errors.values():
            if isinstance(value, list):
                result.extend(flatten_error_list(value))
            else:
                result.append(str(value))
        return result
    
    else:
        return [str(errors)]


class ErrorResponseFormatter:
    """Utility class for formatting consistent error responses."""
    
    @staticmethod
    def validation_error(field_errors, message=None):
        """
        Format a validation error response.
        
        Args:
            field_errors: Dict of field names to error messages
            message: Optional custom message
        
        Returns:
            Formatted response dict
        """
        return {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message or "Validation failed. Please check the details.",
                "details": field_errors
            }
        }
    
    @staticmethod
    def permission_error(message=None, details=None):
        """Format a permission denied error response."""
        return {
            "success": False,
            "error": {
                "code": "PERMISSION_DENIED",
                "message": message or "You don't have permission to access this resource.",
                "details": details
            }
        }
    
    @staticmethod
    def not_found_error(resource_type="Resource", details=None):
        """Format a not found error response."""
        return {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": f"{resource_type} not found.",
                "details": details
            }
        }
    
    @staticmethod
    def business_logic_error(message, code="BUSINESS_LOGIC_ERROR", details=None):
        """Format a business logic error response."""
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            }
        }
    
    @staticmethod
    def success_response(data, message="Success", status_code=200):
        """
        Format a success response.
        
        Args:
            data: Response data
            message: Optional custom message
            status_code: HTTP status code
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        
        return response, status_code
