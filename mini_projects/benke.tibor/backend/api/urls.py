"""
API URLs.
"""
from django.urls import path
from api.views import (
    QueryAPIView, 
    SessionHistoryAPIView, 
    ResetContextAPIView,
    GoogleDriveFilesAPIView,
    GoogleDriveFileContentAPIView,
    UsageStatsAPIView,
    CacheStatsAPIView,
    CitationFeedbackAPIView,
    FeedbackStatsAPIView,
    RegenerateAPIView,
    CreateJiraTicketAPIView,
)

urlpatterns = [
    path('query/', QueryAPIView.as_view(), name='query'),
    path('regenerate/', RegenerateAPIView.as_view(), name='regenerate'),
    path('sessions/<str:session_id>/', SessionHistoryAPIView.as_view(), name='session_history'),
    path('reset-context/', ResetContextAPIView.as_view(), name='reset_context'),
    path('google-drive/files/', GoogleDriveFilesAPIView.as_view(), name='google_drive_files'),
    path('google-drive/files/<str:file_id>/content/', GoogleDriveFileContentAPIView.as_view(), name='google_drive_file_content'),
    path('usage-stats/', UsageStatsAPIView.as_view(), name='usage_stats'),
    path('cache-stats/', CacheStatsAPIView.as_view(), name='cache_stats'),
    path('feedback/citation/', CitationFeedbackAPIView.as_view(), name='citation_feedback'),
    path('feedback/stats/', FeedbackStatsAPIView.as_view(), name='feedback_stats'),
    path('jira/ticket/', CreateJiraTicketAPIView.as_view(), name='create_jira_ticket'),
]
