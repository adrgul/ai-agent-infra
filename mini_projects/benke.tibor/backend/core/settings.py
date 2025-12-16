"""
Django settings for KnowledgeRouter project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-test-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'corsheaders',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'hu-hu'
TIME_ZONE = 'Europe/Budapest'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# LLM Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# Vector DB Configuration
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', 6334))
QDRANT_URL = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'marketing')  # Default collection
QDRANT_COLLECTIONS = {
    'hr': os.getenv('QDRANT_COLLECTION_HR', 'hr_knowledge'),
    'it': os.getenv('QDRANT_COLLECTION_IT', 'it_knowledge'),
    'finance': os.getenv('QDRANT_COLLECTION_FINANCE', 'finance_knowledge'),
    'legal': 'legal_knowledge',
    'marketing': 'marketing',  # Using existing collection
    'general': 'general_knowledge',
}

# Embedding model
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')

# LLM settings
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', 0.7))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 2048))

# Data directories
DATA_DIR = BASE_DIR / 'data'
USERS_DIR = DATA_DIR / 'users'
SESSIONS_DIR = DATA_DIR / 'sessions'
FILES_DIR = DATA_DIR / 'files'

# Create directories if they don't exist
for directory in [USERS_DIR, SESSIONS_DIR, FILES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
