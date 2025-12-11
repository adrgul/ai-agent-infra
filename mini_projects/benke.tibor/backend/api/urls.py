"""
API URLs.
"""
from django.urls import path
from api.views import QueryAPIView, SessionHistoryAPIView, ResetContextAPIView

urlpatterns = [
    path('query/', QueryAPIView.as_view(), name='query'),
    path('sessions/<str:session_id>/', SessionHistoryAPIView.as_view(), name='session_history'),
    path('reset-context/', ResetContextAPIView.as_view(), name='reset_context'),
]
