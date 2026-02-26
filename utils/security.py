import bleach
import logging
import os
from logging.handlers import RotatingFileHandler

# Allowed HTML tags (if we want to allow some rich text in the future)
# For now, we strip mostly everything to prevent XSS.
ALLOWED_TAGS = [
    'b', 'i', 'u', 'strong', 'em', 'p', 'br', 'span', 'div', 
    'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
]

# Allowed attributes for the tags
ALLOWED_ATTRIBUTES = {
    '*': ['class', 'style'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'width', 'height']
}

def sanitize_input(text):
    """
    Sanitize input text using bleach to prevent XSS.
    Strips scripts, iframes, etc.
    """
    if not isinstance(text, str):
         return text
         
    return bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

def get_security_logger():
    """
    Returns a logger specifically for security-related events.
    Logs to a rotating file 'security.log'.
    """
    logger = logging.getLogger('security_logger')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'security.log')
        handler = RotatingFileHandler(log_file, maxBytes=1048576, backupCount=5)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
