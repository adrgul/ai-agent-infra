"""
API views - REST endpoints.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

from domain.models import QueryRequest
from infrastructure.error_handling import APICallError, check_token_limit, estimate_tokens

logger = logging.getLogger(__name__)
class QueryAPIView(APIView):
    """
    POST /api/query/ - Process user query through agent.
    Example: HR vacation request, IT support, etc.
    """

    def post(self, request: Request) -> Response:
        """Handle query request with input validation."""
        try:
            # Validate request
            data = request.data
            query_text = data.get("query", "")
            
            # Check if query is empty
            if not query_text or not query_text.strip():
                return Response(
                    {"success": False, "error": "Query cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Check token limit for user input (max 10k tokens for safety)
            # This prevents malicious/accidental huge inputs
            try:
                check_token_limit(query_text, max_tokens=10000)
                estimated = estimate_tokens(query_text)
                logger.info(f"Query token estimate: {estimated}")
            except ValueError as token_error:
                logger.warning(f"Query too long: {token_error}")
                return Response(
                    {
                        "success": False,
                        "error": "Query is too long. Please shorten your question to under 10,000 tokens (~40,000 characters)."
                    },
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )
            
            query_request = QueryRequest(
                user_id=data.get("user_id", "guest"),
                session_id=data.get("session_id"),
                query=query_text,
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

        except ValueError as e:
            # Bad request - invalid input
            logger.warning(f"Invalid query request: {e}")
            return Response(
                {"success": False, "error": f"Invalid request: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        except APICallError as e:
            # OpenAI API error (rate limit, timeout, etc.)
            logger.error(f"API call failed: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Service temporarily unavailable. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        
        except Exception as e:
            # Unexpected server error
            logger.error(f"Unexpected query error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Internal server error. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        except FileNotFoundError as e:
            # Session not found
            logger.warning(f"Session not found: {session_id}")
            return Response(
                {"success": False, "error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        except Exception as e:
            # Server error
            logger.error(f"History error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to retrieve session history"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        except ValueError as e:
            # Invalid session ID
            logger.warning(f"Invalid session ID: {e}")
            return Response(
                {"success": False, "error": "Invalid session ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        except Exception as e:
            # Server error
            logger.error(f"Reset context error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to reset context"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GoogleDriveFilesAPIView(APIView):
    """
    GET /api/google-drive/files/ - List files from Google Drive shared folder.
    Query params:
        - folder_id: Google Drive folder ID (optional, defaults to marketing folder)
        - mime_type: Filter by MIME type (optional)
    """

    def get(self, request: Request) -> Response:
        """List files in Google Drive folder."""
        try:
            from infrastructure.google_drive_client import get_drive_client
            
            # Get folder ID from query params or use default marketing folder
            folder_id = request.query_params.get(
                'folder_id', 
                '1Jo5doFrRgTscczqR0c6bsS2H0a7pS2ZR'  # Default marketing folder
            )
            mime_type_filter = request.query_params.get('mime_type', None)
            
            # Get Google Drive client
            drive_client = get_drive_client()
            
            # Authenticate if not already authenticated
            if not drive_client.service:
                drive_client.authenticate()
            
            # List files
            files = drive_client.list_files_in_folder(
                folder_id=folder_id,
                mime_type_filter=mime_type_filter
            )
            
            # Format response
            files_data = [
                {
                    'id': f['id'],
                    'name': f['name'],
                    'mimeType': f.get('mimeType', 'unknown'),
                    'size': f.get('size', 'N/A'),
                    'createdTime': f.get('createdTime', ''),
                    'modifiedTime': f.get('modifiedTime', ''),
                    'webViewLink': f.get('webViewLink', '')
                }
                for f in files
            ]
            
            return Response(
                {
                    "success": True,
                    "folder_id": folder_id,
                    "file_count": len(files_data),
                    "files": files_data
                },
                status=status.HTTP_200_OK
            )
            
        except FileNotFoundError as e:
            logger.error(f"Google Drive credentials error: {e}")
            return Response(
                {
                    "success": False,
                    "error": "Google Drive credentials not found. Please add client_secret.json to backend/credentials/"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Google Drive API error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleDriveFileContentAPIView(APIView):
    """
    GET /api/google-drive/files/{file_id}/content - Download and parse file content.
    Returns extracted text from PDF or DOCX files.
    """

    def get(self, request: Request, file_id: str) -> Response:
        """Download and parse file content."""
        try:
            from infrastructure.google_drive_client import get_drive_client
            from infrastructure.document_parser import DocumentParser
            
            # Get Google Drive client
            drive_client = get_drive_client()
            
            # Authenticate if not already authenticated
            if not drive_client.service:
                drive_client.authenticate()
            
            # Get file metadata first
            file_metadata = drive_client.get_file_metadata(file_id)
            file_name = file_metadata.get('name', 'unknown')
            mime_type = file_metadata.get('mimeType', '')
            
            # Download file content
            logger.info(f"Downloading file: {file_name} ({mime_type})")
            content = drive_client.download_file_content(file_id)
            
            # Parse content based on MIME type
            try:
                text = DocumentParser.parse_document(content, mime_type)
                metadata = DocumentParser.get_document_metadata(text)
                
                return Response(
                    {
                        "success": True,
                        "file_id": file_id,
                        "file_name": file_name,
                        "mime_type": mime_type,
                        "text": text,
                        "metadata": metadata
                    },
                    status=status.HTTP_200_OK
                )
            
            except ValueError as parse_error:
                # Unsupported file type
                logger.warning(f"Unsupported file type: {mime_type}")
                return Response(
                    {
                        "success": False,
                        "error": str(parse_error),
                        "file_name": file_name,
                        "mime_type": mime_type
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except FileNotFoundError as e:
            logger.error(f"Google Drive credentials error: {e}")
            return Response(
                {
                    "success": False,
                    "error": "Google Drive credentials not found. Please add client_secret.json to backend/credentials/"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Google Drive file content error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UsageStatsAPIView(APIView):
    """
    GET /api/usage-stats/ - Get OpenAI token usage statistics.
    DELETE /api/usage-stats/ - Reset usage statistics.
    """

    def get(self, request: Request) -> Response:
        """Get usage statistics."""
        try:
            from infrastructure.openai_clients import OpenAIClientFactory
            
            stats = OpenAIClientFactory.get_usage_stats()
            
            return Response(
                {
                    "success": True,
                    "data": stats,
                    "message": "Token usage statistics since last reset"
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Usage stats error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to retrieve usage stats"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def delete(self, request: Request) -> Response:
        """Reset usage statistics."""
        try:
            from infrastructure.openai_clients import OpenAIClientFactory
            
            OpenAIClientFactory.reset_usage_stats()
            
            return Response(
                {
                    "success": True,
                    "message": "Usage statistics reset"
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Reset usage stats error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to reset usage stats"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
