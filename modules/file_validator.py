import os

class FileValidator:
    def __init__(self):
        self.allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".bmp"}
        self.max_file_size = 10 * 1024 * 1024
    
    def validate_file(self, file_name: str, file_size: int) -> tuple[bool, str]:
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext not in self.allowed_extensions:
            return False, f"不支持的文件类型: {file_ext}"
        
        if file_size > self.max_file_size:
            return False, f"文件大小超过限制 (最大10MB)"
        
        return True, ""
