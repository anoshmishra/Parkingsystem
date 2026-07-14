import logging
import traceback

from django.http import JsonResponse

logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware:
    """Catch unhandled exceptions and return structured JSON responses.

    Returns: {"success": False, "message": "..."}
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            # log full traceback
            logger.error("Unhandled exception: %s", exc)
            logger.debug(traceback.format_exc())

            # Don't leak internals — provide a consistent JSON structure
            message = str(exc) if str(exc) else "Internal server error"
            return JsonResponse({"success": False, "message": message}, status=500)
