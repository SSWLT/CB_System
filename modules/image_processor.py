import base64
from PIL import Image, ImageOps
from io import BytesIO
import numpy as np

class ImageProcessor:
    def __init__(self):
        pass
    
    def resize_image(self, img: Image.Image, max_width: int = 800, max_height: int = 1200) -> Image.Image:
        """
        调整图片尺寸，保持原始比例
        :param img: PIL Image对象
        :param max_width: 最大宽度
        :param max_height: 最大高度
        :return: 调整后的Image对象
        """
        try:
            img.thumbnail((max_width, max_height), Image.LANCZOS)
            return img
        except Exception as e:
            raise Exception(f"调整图片尺寸失败: {str(e)}")
    
    def rotate_image(self, img: Image.Image, angle: float) -> Image.Image:
        """
        旋转图片
        :param img: PIL Image对象
        :param angle: 旋转角度（度）
        :return: 旋转后的Image对象
        """
        try:
            rotated_img = img.rotate(angle, expand=True, fillcolor="white")
            return rotated_img
        except Exception as e:
            raise Exception(f"旋转图片失败: {str(e)}")
    
    def image_to_base64(self, img: Image.Image, image_format: str = "JPEG") -> str:
        """
        将图片转换为Base64编码
        :param img: PIL Image对象
        :param image_format: 图片格式
        :return: Base64编码字符串
        """
        try:
            buffer = BytesIO()
            img.save(buffer, format=image_format, quality=95)
            img_bytes = buffer.getvalue()
            
            # 编码为Base64
            base64_str = base64.b64encode(img_bytes).decode("utf-8")
            
            # 添加数据类型前缀
            mime_type = f"image/{image_format.lower()}"
            return f"data:{mime_type};base64,{base64_str}"
        except Exception as e:
            raise Exception(f"图片转Base64失败: {str(e)}")
    
    def bytes_to_base64(self, img_bytes: bytes, image_format: str = "JPEG") -> str:
        """
        将字节流转换为Base64编码
        :param img_bytes: 图片字节流
        :param image_format: 图片格式
        :return: Base64编码字符串
        """
        try:
            base64_str = base64.b64encode(img_bytes).decode("utf-8")
            mime_type = f"image/{image_format.lower()}"
            return f"data:{mime_type};base64,{base64_str}"
        except Exception as e:
            raise Exception(f"字节流转Base64失败: {str(e)}")
    
    def process_image(self, img: Image.Image, max_width: int = 800, max_height: int = 1200, 
                     rotate_angle: float = 0) -> Image.Image:
        """
        综合处理图片（调整尺寸、旋转）
        :param img: PIL Image对象
        :param max_width: 最大宽度
        :param max_height: 最大高度
        :param rotate_angle: 旋转角度
        :return: 处理后的Image对象
        """
        try:
            # 旋转图片
            if rotate_angle != 0:
                img = self.rotate_image(img, rotate_angle)
            
            # 调整尺寸
            img = self.resize_image(img, max_width, max_height)
            
            return img
        except Exception as e:
            raise Exception(f"处理图片失败: {str(e)}")
    
    def normalize_image(self, img: Image.Image) -> Image.Image:
        """
        标准化图片（调整亮度、对比度）
        :param img: PIL Image对象
        :return: 标准化后的Image对象
        """
        try:
            # 转换为灰度图（如果需要）
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # 调整对比度和亮度
            img = ImageOps.autocontrast(img, cutoff=1)
            img = ImageOps.equalize(img)
            
            return img
        except Exception as e:
            raise Exception(f"标准化图片失败: {str(e)}")