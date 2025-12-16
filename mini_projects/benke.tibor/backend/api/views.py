"""
API views - REST endpoints.
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

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

