from .settings import *
import os

# Allow external connections
ALLOWED_HOSTS = ['138.67.190.221', 'localhost', '127.0.0.1', 'isengard.mines.edu', '*']

# Serve React frontend
STATICFILES_DIRS = [
    os.path.join(BASE_DIR.parent, 'gps-frontend', 'build', 'static'),
]

TEMPLATES[0]['DIRS'] = [os.path.join(BASE_DIR.parent, 'gps-frontend', 'build')]

# React frontend URL patterns
REACT_BUILD_DIR = os.path.join(BASE_DIR.parent, 'gps-frontend', 'build')

# Media files for large uploads
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Large file handling
FILE_UPLOAD_MAX_MEMORY_SIZE = 300 * 1024 * 1024  # 300MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 300 * 1024 * 1024