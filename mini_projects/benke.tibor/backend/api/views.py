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
            import time
            
            start_time = time.time()
            response = asyncio.run(chat_service.process_query(query_request))
            total_latency = round((time.time() - start_time) * 1000, 2)  # ms
            
            # Calculate telemetry
            chunk_count = len(response.citations)
            max_score = max([c.score for c in response.citations], default=0.0)
            
            user_id = data.get("user_id", "guest")
            session_id = data.get("session_id")
            
            return Response(
                {
                    "success": True,
                    "data": {
                        "domain": response.domain,
                        "answer": response.answer,
                        "citations": [c.model_dump() for c in response.citations],
                        "workflow": response.workflow,
                        "confidence": response.confidence,
                        "telemetry": {
                            "total_latency_ms": total_latency,
                            "chunk_count": chunk_count,
                            "max_similarity_score": round(max_score, 3),
                            "retrieval_latency_ms": None,  # TODO: measure RAG separately
                            "request": {
                                "user_id": user_id,
                                "session_id": session_id,
                                "query": query_text
                            },
                            "response": {
                                "domain": response.domain,
                                "answer_length": len(response.answer),
                                "citation_count": chunk_count,
                                "workflow_triggered": response.workflow is not None
                            },
                            "rag": {
                                "context": response.rag_context,
                                "chunk_count": chunk_count
                            },
                            "llm": {
                                "prompt": response.llm_prompt,
                                "response": response.llm_response,
                                "prompt_length": len(response.llm_prompt) if response.llm_prompt else 0,
                                "response_length": len(response.llm_response) if response.llm_response else 0
                            }
                        }
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
        except FileNotFoundError:
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


class CacheStatsAPIView(APIView):
    """
    GET /api/cache-stats/ - Get Redis cache statistics and top queries.
    DELETE /api/cache-stats/ - Clear cache (with optional domain filter).
    """

    def get(self, request: Request) -> Response:
        """Get cache statistics and top queries."""
        try:
            from infrastructure.redis_client import redis_cache
            
            # Get overall cache stats
            stats = redis_cache.get_cache_stats()
            
            # Get top queries
            top_queries = redis_cache.get_top_queries(limit=10)
            
            return Response(
                {
                    "success": True,
                    "data": {
                        "stats": stats,
                        "top_queries": top_queries
                    },
                    "message": "Cache statistics and popular queries"
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Cache stats error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to retrieve cache stats"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    def delete(self, request: Request) -> Response:
        """Clear cache (optionally filtered by domain)."""
        try:
            from infrastructure.redis_client import redis_cache
            
            domain = request.query_params.get("domain")  # Optional domain filter
            
            if domain:
                redis_cache.invalidate_query_cache(domain=domain)
                message = f"Cache cleared for domain: {domain}"
            else:
                redis_cache.clear_all()
                message = "All cache cleared"
            
            return Response(
                {
                    "success": True,
                    "message": message
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Clear cache error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to clear cache"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CitationFeedbackAPIView(APIView):
    """
    POST /api/feedback/citation/ - Submit citation feedback (like/dislike).
    """

    def post(self, request: Request) -> Response:
        """Submit citation feedback."""
        try:
            import json
            from domain.models import CitationFeedback, FeedbackType
            from infrastructure.postgres_client import postgres_client
            
            # Parse JSON body manually
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return Response(
                    {"success": False, "error": "Invalid JSON body"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate request data
            required_fields = ["citation_id", "domain", "user_id", "session_id", "query_text", "feedback_type"]
            
            for field in required_fields:
                if field not in data:
                    return Response(
                        {"success": False, "error": f"Missing required field: {field}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate feedback_type
            if data["feedback_type"] not in ["like", "dislike"]:
                return Response(
                    {"success": False, "error": "feedback_type must be 'like' or 'dislike'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create feedback model
            feedback = CitationFeedback(
                citation_id=data["citation_id"],
                domain=data["domain"],
                user_id=data["user_id"],
                session_id=data["session_id"],
                query_text=data["query_text"],
                query_embedding=data.get("query_embedding"),  # Optional
                feedback_type=FeedbackType(data["feedback_type"]),
                citation_rank=data.get("citation_rank")  # Optional
            )
            
            # Schedule feedback save as background task (non-blocking)
            # This avoids event loop conflicts
            import threading
            
            def save_feedback_background():
                """Background thread to save feedback."""
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    feedback_id = loop.run_until_complete(postgres_client.save_citation_feedback_standalone(feedback))
                    logger.info(f"Feedback saved: {feedback_id}")
                    # Refresh stats
                    loop.run_until_complete(postgres_client.refresh_stats())
                except Exception as e:
                    logger.error(f"Background feedback save failed: {e}")
                finally:
                    loop.close()
            
            # Start background thread
            thread = threading.Thread(target=save_feedback_background, daemon=True)
            thread.start()
            
            # Return immediately (optimistic response)
            return Response(
                {
                    "success": True,
                    "message": "Feedback received and will be processed"
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Citation feedback error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to save feedback"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedbackStatsAPIView(APIView):
    """
    GET /api/feedback/stats/ - Get feedback statistics.
    Query params:
        - domain: Filter by domain (optional)
    """

    def get(self, request: Request) -> Response:
        """Get feedback statistics."""
        try:
            from infrastructure.postgres_client import postgres_client
            from asgiref.sync import async_to_sync
            
            domain = request.query_params.get("domain")  # Optional domain filter
            
            stats = async_to_sync(postgres_client.get_feedback_stats)(domain=domain)
            
            return Response(
                {
                    "success": True,
                    "data": stats.dict(),
                    "domain_filter": domain if domain else "all"
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Feedback stats error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to retrieve feedback stats"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RegenerateAPIView(APIView):
    """
    POST /api/regenerate/ - Regenerate response using cached context.
    
    This endpoint skips intent detection and RAG retrieval, using cached
    domain and citations from the session. This is 70% faster and 80% cheaper
    than full re-execution.
    
    Request body:
        - session_id: Session to get cached context from
        - query: Original query (for context building)
    """

    def post(self, request: Request) -> Response:
        """Regenerate response with cached domain + citations."""
        try:
            session_id = request.data.get("session_id")
            query = request.data.get("query", "")
            
            if not session_id:
                return Response(
                    {"success": False, "error": "session_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            if not query or not query.strip():
                return Response(
                    {"success": False, "error": "query cannot be empty"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            # Get chat service
            from django.apps import apps
            django_app = apps.get_app_config('api')
            chat_service = django_app.chat_service
            
            # Get last response from session to extract cached data
            import asyncio
            history = asyncio.run(chat_service.get_session_history(session_id))
            
            if not history or len(history.get("messages", [])) < 2:
                return Response(
                    {"success": False, "error": "No previous response found in session"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            # Find last bot message
            messages = history.get("messages", [])
            last_bot_message = None
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    last_bot_message = msg
                    break
            
            if not last_bot_message:
                return Response(
                    {"success": False, "error": "No bot response found in session"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            
            # Extract cached domain and citations
            cached_domain = last_bot_message.get("domain", "general")
            cached_citations = last_bot_message.get("citations", [])
            
            logger.info(f"Regenerating with cached context: domain={cached_domain}, citations={len(cached_citations)}")
            
            # Call agent.regenerate() instead of full run()
            user_id = request.data.get("user_id", "guest")
            response = asyncio.run(
                chat_service.agent.regenerate(
                    query=query,
                    domain=cached_domain,
                    citations=cached_citations,
                    user_id=user_id
                )
            )
            
            # Save to session history
            from domain.models import Message
            asyncio.run(chat_service.conversation_repo.save_message(
                session_id=session_id,
                message=Message(
                    role="assistant",
                    content=response.answer,
                    domain=response.domain,
                    citations=[c.model_dump() for c in response.citations],
                    workflow=response.workflow,
                    regenerated=True  # Flag to indicate cached regeneration
                )
            ))
            
            return Response(
                {
                    "success": True,
                    "data": {
                        "domain": response.domain,
                        "answer": response.answer,
                        "citations": [c.model_dump() for c in response.citations],
                        "workflow": response.workflow,
                        "regenerated": True,  # Flag for frontend
                        "cache_info": {
                            "skipped_nodes": ["intent_detection", "retrieval"],
                            "executed_nodes": ["generation", "workflow"],
                            "cached_citations_count": len(cached_citations)
                        }
                    }
                },
                status=status.HTTP_200_OK,
            )
            
        except FileNotFoundError:
            logger.warning(f"Session not found: {session_id}")
            return Response(
                {"success": False, "error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        except Exception as e:
            logger.error(f"Regenerate error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": "Failed to regenerate response"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateJiraTicketAPIView(APIView):
    """
    POST /api/jira/ticket/ - Create a Jira support ticket.
    Used for IT domain when user requests ticket creation.
    """

    def post(self, request: Request) -> Response:
        """Create Jira ticket based on user query."""
        from infrastructure.atlassian_client import atlassian_client
        import asyncio
        
        try:
            data = request.data
            summary = data.get("summary", "")
            description = data.get("description", "")
            issue_type = data.get("issue_type", "Task")
            priority = data.get("priority", "Medium")
            
            if not summary or not description:
                return Response(
                    {"success": False, "error": "Summary and description are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            logger.info(f"Creating Jira ticket: {summary[:50]}...")
            
            # Create ticket using Atlassian client
            result = asyncio.run(
                atlassian_client.create_jira_ticket(
                    summary=summary,
                    description=description,
                    issue_type=issue_type,
                    priority=priority
                )
            )
            
            if result:
                logger.info(f"✅ Jira ticket created: {result['key']}")
                return Response(
                    {
                        "success": True,
                        "ticket": {
                            "key": result["key"],
                            "url": result["url"]
                        }
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                logger.error("Failed to create Jira ticket")
                return Response(
                    {"success": False, "error": "Failed to create Jira ticket"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
                
        except Exception as e:
            logger.error(f"Jira ticket creation error: {e}", exc_info=True)
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
