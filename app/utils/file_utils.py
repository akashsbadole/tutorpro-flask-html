import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename, allowed_extensions):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def generate_unique_filename(filename):
    """Generate a unique filename to prevent conflicts"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}" if ext else unique_id


def save_uploaded_file(file, upload_folder, allowed_extensions=None, max_size=None):
    """
    Save an uploaded file with validation
    
    Args:
        file: The uploaded file object
        upload_folder: The folder to save the file to
        allowed_extensions: Set of allowed file extensions
        max_size: Maximum file size in bytes
    
    Returns:
        dict: Contains 'success', 'message', and 'filename' keys
    """
    if not file or file.filename == '':
        return {
            'success': False,
            'message': 'No file selected',
            'filename': None
        }
    
    # Validate file extension
    if allowed_extensions and not allowed_file(file.filename, allowed_extensions):
        return {
            'success': False,
            'message': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}',
            'filename': None
        }
    
    # Validate file size
    if max_size and file.content_length > max_size:
        size_mb = max_size / (1024 * 1024)
        return {
            'success': False,
            'message': f'File too large. Maximum size: {size_mb:.1f}MB',
            'filename': None
        }
    
    # Generate secure filename
    filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(filename)
    
    # Create upload directory if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    return {
        'success': True,
        'message': 'File uploaded successfully',
        'filename': unique_filename,
        'original_filename': filename,
        'file_path': file_path,
        'file_size': file.content_length
    }


def delete_file(file_path):
    """
    Delete a file from the filesystem
    
    Args:
        file_path: Path to the file to delete
    
    Returns:
        bool: True if file was deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False


def get_file_size_mb(file_path):
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to the file
    
    Returns:
        float: File size in MB
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except OSError:
        return 0


def get_file_extension(filename):
    """
    Get the file extension from a filename
    
    Args:
        filename: The filename to extract extension from
    
    Returns:
        str: The file extension (without the dot)
    """
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def validate_image_file(file_path):
    """
    Validate if a file is a valid image
    
    Args:
        file_path: Path to the file to validate
    
    Returns:
        bool: True if valid image, False otherwise
    """
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception:
        return False


def create_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """
    Create a thumbnail for an image file
    
    Args:
        image_path: Path to the original image
        thumbnail_path: Path to save the thumbnail
        size: Tuple of (width, height) for the thumbnail
    
    Returns:
        bool: True if thumbnail was created successfully, False otherwise
    """
    try:
        from PIL import Image
        
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=85)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error creating thumbnail: {str(e)}")
        return False


def get_file_info(file_path):
    """
    Get information about a file
    
    Args:
        file_path: Path to the file
    
    Returns:
        dict: File information including size, extension, etc.
    """
    try:
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'size_mb': stat.st_size / (1024 * 1024),
            'extension': get_file_extension(file_path),
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'is_image': get_file_extension(file_path) in {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
        }
    except OSError:
        return None


def secure_course_material_path(file_path):
    """
    Ensure the file path is within the course materials directory
    
    Args:
        file_path: The file path to check
    
    Returns:
        bool: True if path is secure, False otherwise
    """
    try:
        upload_folder = current_app.config['COURSE_MATERIALS_FOLDER']
        abs_upload_folder = os.path.abspath(upload_folder)
        abs_file_path = os.path.abspath(file_path)
        
        return abs_file_path.startswith(abs_upload_folder)
    except Exception:
        return False


def secure_assignment_path(file_path):
    """
    Ensure the file path is within the assignment submissions directory
    
    Args:
        file_path: The file path to check
    
    Returns:
        bool: True if path is secure, False otherwise
    """
    try:
        upload_folder = current_app.config['ASSIGNMENT_SUBMISSIONS_FOLDER']
        abs_upload_folder = os.path.abspath(upload_folder)
        abs_file_path = os.path.abspath(file_path)
        
        return abs_file_path.startswith(abs_upload_folder)
    except Exception:
        return False