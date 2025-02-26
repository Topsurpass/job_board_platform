import logging
from django.http import JsonResponse
from django.core.exceptions import MiddlewareNotUsed

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
