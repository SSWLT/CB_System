import os
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

class PDFConverter:
    def __init__(self):
        pass
    
    def pdf_to_image(self, pdf_path: str, page_num: int = 0) -> Image.Image:
        """
        将PDF文件转换为图片
        :param pdf_path: PDF文件路径
        :param page_num: 要转换的页码，默认为首页
        :return: PIL Image对象
        """
        try:
            # 打开PDF文件
            pdf_document = fitz.open(pdf_path)
            
            if page_num < 0 or page_num >= len(pdf_document):
                page_num = 0  # 默认使用首页
            
            # 获取指定页面
            page = pdf_document[page_num]
            
            # 将页面转换为图片
            pix = page.get_pixmap(dpi=300, alpha=False)
            
            # 转换为PIL Image
            img = Image.open(BytesIO(pix.tobytes()))
            
            # 关闭PDF文件
            pdf_document.close()
            
            return img
        except Exception as e:
            raise Exception(f"PDF转图片失败: {str(e)}")
    
    def pdf_to_bytes(self, pdf_path: str, page_num: int = 0, image_format: str = "JPEG") -> bytes:
        """
        将PDF转换为字节流
        :param pdf_path: PDF文件路径
        :param page_num: 页码
        :param image_format: 输出图片格式
        :return: 图片字节流
        """
        img = self.pdf_to_image(pdf_path, page_num)
        
        buffer = BytesIO()
        img.save(buffer, format=image_format, quality=95)
        return buffer.getvalue()
    
    def extract_pdf_info(self, pdf_path: str) -> dict:
        """
        提取PDF文件信息
        :param pdf_path: PDF文件路径
        :return: PDF信息字典
        """
        try:
            pdf_document = fitz.open(pdf_path)
            info = {
                "num_pages": len(pdf_document),
                "title": pdf_document.metadata.get("title", ""),
                "author": pdf_document.metadata.get("author", ""),
                "subject": pdf_document.metadata.get("subject", ""),
                "creator": pdf_document.metadata.get("creator", ""),
                "producer": pdf_document.metadata.get("producer", ""),
                "creation_date": pdf_document.metadata.get("creationDate", ""),
                "mod_date": pdf_document.metadata.get("modDate", "")
            }
            pdf_document.close()
            return info
        except Exception as e:
            raise Exception(f"提取PDF信息失败: {str(e)}")