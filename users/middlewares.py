import logging
from django.http import JsonResponse
import json
import time
from datetime import datetime
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.deprecation import MiddlewareMixin


logger = logging.getLogger(__name__)


logger = logging.getLogger(__name__)

class ExceptionMiddleware:
    """Middleware to handle all unexpected errors globally"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled server error: {e}", exc_info=True)
            return JsonResponse({"error": "An internal server error occurred."}, status=500)
    
    def process_exception(self, request, exception):
        """This method is explicitly called for unhandled exceptions."""
        logger.error(f"Exception caught in middleware: {exception}", exc_info=True)
        return JsonResponse({"error": "An internal server error occurred."}, status=500)

class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log requests and responses with additional details."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authenticator = JWTAuthentication()

    def __call__(self, request):
        start_time = time.time()
        
        # Attempt JWT authentication first
        username = "Anonymous"
        role = "visitor"
        
        try:
            auth_result = self.jwt_authenticator.authenticate(request)
            if auth_result:
                username = auth_result[0].username  # Extract username
                role = getattr(auth_result[0], "role", "unknown")
            else:
                # If JWT auth fails, check session authentication (useful for Django Admin)
                if request.user.is_authenticated:
                    username = request.user.username
                    role = getattr(request.user, "role", "admin")

        except Exception as e:
            logger.error(f"JWT Authentication failed: {e}")

        ip_address = self.get_client_ip(request)

        relevant_headers = {
            "User-Agent": request.headers.get("User-Agent", "Unknown"),
            "Referer": request.headers.get("Referer", "None"),
            "Content-Type": request.headers.get("Content-Type", "Unknown"),
            "Authorization": "Present" if "Authorization" in request.headers else "None",
            "Accept-Language": request.headers.get("Accept-Language", "Unknown"),
        }

        request_data = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "role": role,
            "method": request.method,
            "path": request.path,
            "ip": ip_address,
            "headers": relevant_headers,
        }

        logger.info(f"Request: {json.dumps(request_data, indent=2)}")
        response = self.get_response(request)
        request_data["status_code"] = response.status_code
        request_data["duration"] = round(time.time() - start_time, 4)
        logger.info(f"Response: {json.dumps(request_data, indent=2)}")

        with open("requests.log", "a") as log_file:
            log_file.write(json.dumps(request_data) + "\n")

        return response

    def get_client_ip(self, request):
        """Extracts the client IP address from the request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "Unknown")
        return ip

