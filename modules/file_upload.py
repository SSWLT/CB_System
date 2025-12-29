import os
import uuid
import streamlit as st
from datetime import datetime

class FileUploader:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
    
    def save_file(self, uploaded_file, user_id: int) -> dict:
        try:
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            file_size = len(uploaded_file.getvalue())
            
            file_info = {
                "filename": uploaded_file.name,
                "file_ext": file_ext,
                "file_size": file_size,
                "content": uploaded_file.getvalue()
            }
            
            return file_info
        except Exception as e:
            st.error(f"读取文件失败: {str(e)}")
            return None
    
    def validate_file(self, file_info: dict) -> tuple[bool, str]:
        allowed_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".bmp"]
        max_size = 10 * 1024 * 1024
        
        if file_info["file_ext"] not in allowed_extensions:
            return False, f"不支持的文件类型: {file_info['file_ext']}"
        
        if file_info["file_size"] > max_size:
            return False, f"文件大小超过限制 (最大10MB)"
        
        return True, ""
    
    def save_to_disk(self, file_info: dict) -> str:
        unique_name = str(uuid.uuid4()) + file_info["file_ext"]
        file_path = os.path.join(self.upload_dir, unique_name)
        
        with open(file_path, "wb") as f:
            f.write(file_info["content"])
        
        return file_path
