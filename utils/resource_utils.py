"""
Resource utility for handling file paths in both development and PyInstaller environments
"""
import os
import sys

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in development mode
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_image_path(image_name):
    """
    Get the full path to an image file, with fallback handling
    """
    # First try to get the resource path
    image_path = get_resource_path(image_name)
    
    # If file doesn't exist, try some alternative locations
    if not os.path.exists(image_path):
        # Try current directory
        alt_path = os.path.join(os.getcwd(), image_name)
        if os.path.exists(alt_path):
            image_path = alt_path
        else:
            # Try script directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            alt_path = os.path.join(parent_dir, image_name)
            if os.path.exists(alt_path):
                image_path = alt_path
    
    # Convert to forward slashes for Qt stylesheets
    return image_path.replace('\\', '/')

def get_css_safe_path(file_path):
    """
    Convert file path to CSS-safe format for Qt stylesheets
    """
    if not file_path or not os.path.exists(file_path):
        return ""
    
    # Convert to absolute path and use forward slashes
    abs_path = os.path.abspath(file_path)
    css_path = abs_path.replace('\\', '/')
    
    # For file URLs in CSS, we need file:/// prefix
    if not css_path.startswith('file:///'):
        css_path = 'file:///' + css_path
    
    return css_path
