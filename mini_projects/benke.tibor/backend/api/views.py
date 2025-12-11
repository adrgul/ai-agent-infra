"""
API views - REST endpoints.
"""
import logging
import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from asgiref.sync import sync_to_async

from domain.models import QueryRequest

logger = logging.getLogger(__name__)


class QueryAPIView(APIView):
    """
    POST /api/query/ - Process user query through agent.
    Example: HR vacation request, IT support, etc.
    """

    def post(self, request: Request) -> Response:
        """Handle query request."""
        try:
            # Validate request
            data = request.data
            query_request = QueryRequest(
                user_id=data.get("user_id", "guest"),
                session_id=data.get("session_id"),
                query=data.get("query", ""),
                organisation=data.get("organisation", "Default Org"),
            )

            # Get chat service from app context
            from django.apps import apps
            django_app = apps.get_app_config('api')
            chat_service = django_app.chat_service

            # Process through agent
            import asyncio
            response = asyncio.run(chat_service.process_query(query_request))

            return Response(
                {
                    "success": True,
                    "data": {
                        "domain": response.domain,
                        "answer": response.answer,
                        "citations": [c.model_dump() for c in response.citations],
                        "workflow": response.workflow,
                        "confidence": response.confidence,
                    }
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Query error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SessionHistoryAPIView(APIView):
    """
    GET /api/sessions/{session_id}/ - Get conversation history.
    """

    def get(self, request: Request, session_id: str) -> Response:
        """Get session history."""
        try:
            from django.apps import apps
            django_app = apps.get_app_config('api')
            chat_service = django_app.chat_service

            import asyncio
            history = asyncio.run(chat_service.get_session_history(session_id))

            return Response(
                {"success": True, "data": history},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"History error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResetContextAPIView(APIView):
    """
    POST /api/reset-context/ - Clear session history.
    """

    def post(self, request: Request) -> Response:
        """Reset context (clear history but keep profile)."""
        try:
            session_id = request.data.get("session_id")
            
            from django.apps import apps
            django_app = apps.get_app_config('api')
            chat_service = django_app.chat_service

            import asyncio
            asyncio.run(chat_service.conversation_repo.clear_history(session_id))

            return Response(
                {
                    "success": True,
                    "message": "Kontextus visszaállítva. Új beszélgetést kezdünk, de a beállítások megmaradnak.",
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Reset context error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
