"""
API URLs.
"""
from django.urls import path
from api.views import (
    QueryAPIView, 
    SessionHistoryAPIView, 
    ResetContextAPIView,
    GoogleDriveFilesAPIView,
    GoogleDriveFileContentAPIView
)

urlpatterns = [
    path('query/', QueryAPIView.as_view(), name='query'),
    path('sessions/<str:session_id>/', SessionHistoryAPIView.as_view(), name='session_history'),
    path('reset-context/', ResetContextAPIView.as_view(), name='reset_context'),
    path('google-drive/files/', GoogleDriveFilesAPIView.as_view(), name='google_drive_files'),
    path('google-drive/files/<str:file_id>/content/', GoogleDriveFileContentAPIView.as_view(), name='google_drive_file_content'),
]
