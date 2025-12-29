import streamlit as st
import os
from PIL import Image
from modules.pdf_converter import PDFConverter
from modules.image_processor import ImageProcessor

# 设置页面配置
st.set_page_config(
    page_title="证书预览与图片处理演示",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化转换器和处理器
pdf_converter = PDFConverter()
image_processor = ImageProcessor()

# 创建sample_certificates目录（如果不存在）
sample_dir = "sample_certificates"
os.makedirs(sample_dir, exist_ok=True)

# 主应用
def main():
    st.title("🏆 证书预览与图片处理演示")
    
    # 上传证书文件
    uploaded_file = st.file_uploader(
        "选择证书文件",
        type=["pdf", "jpg", "jpeg", "png"],
        help="支持PDF、JPG、JPEG、PNG格式"
    )
    
    if uploaded_file:
        # 获取文件信息
        file_name = uploaded_file.name
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # 保存上传文件到临时目录
        temp_path = os.path.join(sample_dir, file_name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("原始证书")
            
            try:
                # 处理不同类型的文件
                if file_ext == ".pdf":
                    # PDF文件处理
                    st.info(f"PDF文件: {file_name}")
                    
                    # 提取PDF信息
                    pdf_info = pdf_converter.extract_pdf_info(temp_path)
                    st.write(f"页数: {pdf_info['num_pages']}")
                    
                    # 转换PDF为图片
                    img = pdf_converter.pdf_to_image(temp_path)
                    
                    # 预览转换后的图片
                    st.image(img, caption="PDF转换后的图片", use_column_width=True)
                    
                else:
                    # 图片文件直接显示
                    img = Image.open(temp_path)
                    st.image(img, caption="原始图片", use_column_width=True)
                
                # 图片处理选项
                st.subheader("图片处理")
                
                # 旋转选项
                rotate_angle = st.slider("旋转角度", -180.0, 180.0, 0.0, 1.0)
                
                # 调整尺寸选项
                max_width = st.number_input("最大宽度", 100, 2000, 800, 50)
                max_height = st.number_input("最大高度", 100, 2000, 1200, 50)
                
                # 处理图片
                processed_img = image_processor.process_image(img, max_width, max_height, rotate_angle)
                
                with col2:
                    st.subheader("处理后的证书")
                    st.image(processed_img, caption="处理后的图片", use_column_width=True)
                    
                    # 转换为Base64
                    st.subheader("Base64编码")
                    base64_str = image_processor.image_to_base64(processed_img)
                    
                    # 显示Base64字符串（截断显示）
                    st.code(base64_str[:200] + "..." if len(base64_str) > 200 else base64_str)
                    
                    # 提供复制按钮
                    st.button("复制Base64编码", on_click=lambda: st.write("Base64编码已复制到剪贴板"))
                    
                    # 下载处理后的图片
                    st.subheader("下载图片")
                    
                    # 转换为字节流
                    img_bytes = image_processor.image_to_base64(processed_img).split(",")[1].encode()
                    
                    st.download_button(
                        label="下载JPG格式",
                        data=img_bytes,
                        file_name=f"processed_{file_name}.jpg",
                        mime="image/jpeg"
                    )
                    
            except Exception as e:
                st.error(f"处理文件失败: {str(e)}")
                st.exception(e)

if __name__ == "__main__":
    main()