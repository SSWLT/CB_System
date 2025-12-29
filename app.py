# app.py
import streamlit as st
import sys
import os
from PIL import Image

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加当前目录到Python路径
sys.path.append(current_dir)

# 设置页面配置（只能调用一次）
st.set_page_config(
    page_title="竞赛证书管理系统",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入自定义模块
try:
    from modules.auth_system import AuthSystem
    from modules.database import db
except ImportError as e:
    st.error(f"模块导入失败: {e}")
    st.error(f"当前目录: {current_dir}")
    st.error(f"Python路径: {sys.path}")
    raise

def init_session_state():
    """初始化session状态"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    if 'show_users' not in st.session_state:
        st.session_state.show_users = False

def show_login_page():
    """显示登录页面"""
    st.title("🔐 竞赛证书管理系统")
    
    # 创建认证系统实例
    auth = AuthSystem()
    
    if 'show_register' in st.session_state and st.session_state.show_register:
        auth.register_user()
        if st.button("返回登录"):
            st.session_state.show_register = False
            st.rerun()
    else:
        auth.login_user()
        
        # 在侧边栏显示注册链接
        if st.sidebar.button("📝 注册新账户"):
            st.session_state.show_register = True
            st.rerun()

def show_main_page():
    """显示主页面"""
    auth = AuthSystem()
    user = auth.get_current_user()
    
    # 显示用户信息
    st.sidebar.title("👤 个人信息")
    st.sidebar.markdown(f"**姓名：** {user['real_name']}")
    st.sidebar.markdown(f"**身份：** {auth.get_role_name(user['role'])}")
    st.sidebar.markdown(f"**学号/工号：** {user['username']}")
    
    # 导航菜单
    st.sidebar.markdown("---")
    st.sidebar.title("📋 功能菜单")
    
    # 根据角色显示不同菜单
    if user['role'] == 'admin':
        menu_options = ["主页", "批量导入", "用户管理", "证书管理"]
        page = st.sidebar.selectbox("选择功能", menu_options, key="admin_menu_selectbox")
        
        if page == "主页":
            show_admin_dashboard(auth)
        elif page == "批量导入":
            # 这里不需要跳转，因为多页面会自动处理
            st.info("请点击上方导航栏中的 📤 批量导入 页面")
        elif page == "用户管理":
            show_user_management(auth)
        elif page == "证书管理":
            show_certificate_management()
    else:
        menu_options = ["主页", "我的证书", "上传证书", "个人设置"]
        page = st.sidebar.selectbox("选择功能", menu_options)
        
        if page == "主页":
            if user['role'] == 'student':
                show_student_dashboard()
            else:
                show_teacher_dashboard()
        elif page == "我的证书":
            show_my_certificates(user)
        elif page == "上传证书":
            # 证书上传功能
            st.title("📤 上传证书")
            
            uploaded_file = st.file_uploader(
                "选择证书文件",
                type=["pdf", "jpg", "jpeg", "png", "bmp"],
                help="支持PDF、JPG、JPEG、PNG、BMP格式，最大10MB"
            )
            
            if uploaded_file:
                from modules.file_upload import FileUploader
                from modules.file_validator import FileValidator
                from modules.pdf_converter import PDFConverter
                from modules.image_processor import ImageProcessor
                
                file_uploader = FileUploader()
                file_validator = FileValidator()
                pdf_converter = PDFConverter()
                image_processor = ImageProcessor()
                
                file_info = file_uploader.save_file(uploaded_file, 1)
                if file_info:
                    is_valid, error_msg = file_validator.validate_file(uploaded_file.name, len(uploaded_file.getvalue()))
                    if not is_valid:
                        st.error(f"文件验证失败: {error_msg}")
                    else:
                        # 保存原始文件到磁盘
                        file_path = file_uploader.save_to_disk(file_info)
                        
                        # 证书预览和处理
                        st.subheader("📋 证书预览与处理")
                        
                        # 先处理图片，生成base64字符串，供两个列使用
                        file_ext = file_info["file_ext"].lower()
                        original_img = None
                        
                        if file_ext == ".pdf":
                            # PDF文件处理
                            pdf_info = pdf_converter.extract_pdf_info(file_path)
                            num_pages = pdf_info["num_pages"]
                            page_num = 0
                            
                            # 根据选择的页码转换PDF为图片
                            original_img = pdf_converter.pdf_to_image(file_path, page_num)
                        else:
                            # 图片文件处理
                            original_img = Image.open(file_path)
                        
                        # 创建两列
                        col1, col2 = st.columns(2)
                        
                        # -------------------- 第一列：原始证书和信息提取 --------------------
                        with col1:
                            st.markdown("### 原始证书")
                            
                            if file_ext == ".pdf":
                                st.info(f"PDF总页数: {num_pages}")
                                st.image(original_img, caption=f"PDF第{page_num + 1}页", use_column_width=True)
                            else:
                                st.image(original_img, caption="原始图片", use_column_width=True)
                            
                            # 添加信息提取按钮
                            st.markdown("---")
                            st.markdown("### 智能信息提取")
                            extract_button = st.button("🔍 提取证书信息", type="primary", use_container_width=True)
                            
                            if extract_button:
                                with st.spinner("正在智能提取证书信息..."):
                                    try:
                                        # 从session状态获取之前生成的base64字符串
                                        if "certificate_base64" not in st.session_state:
                                            st.error("未找到证书的Base64编码，请先上传并处理证书图片")
                                            st.stop()
                                        
                                        base64_str = st.session_state["certificate_base64"]
                                        
                                        # 调用证书提取器，直接传入base64字符串
                                        from modules.certificate_extractor import CertificateExtractor
                                        extractor = CertificateExtractor(api_key="869009c52642440daa5b791e2b3c61b7.FooxInR1ve4l4M7h") 
                                        extracted_info = extractor.extract_certificate_info(base64_str)
                                        
                                        # 验证提取结果
                                        validated_info = extractor.validate_extracted_data(extracted_info)
                                        
                                        # 保存到session状态
                                        st.session_state["extracted_info"] = validated_info
                                        st.session_state["show_extracted_info"] = True
                                        
                                        st.success("证书信息提取成功！")
                                        
                                    except Exception as e:
                                        st.error(f"信息提取失败: {str(e)}")
                                        st.info("建议您手动录入或重新上传清晰证书")
                            
                            # 显示提取结果表单
                            if "show_extracted_info" in st.session_state and st.session_state.show_extracted_info:
                                st.markdown("### 提取结果核实与修改")
                                
                                # 获取当前登录用户信息
                                user = st.session_state.user_info
                                
                                # 提取字段
                                extracted_info = st.session_state.get("extracted_info", {})
                                
                                # 表单区域 - 只包含信息核实与修改
                                with st.form("certificate_info_form"):
                                    # 基本信息
                                    st.markdown("#### 基本信息")
                                    form_col1, form_col2 = st.columns(2)
                                    
                                    with form_col1:
                                        # 学号处理
                                        student_id = extracted_info.get("学号", "")
                                        if user['role'] == 'student':
                                            # 学生用户：学号不可修改，自动填充当前学号
                                            student_id = user['username']
                                            st.text_input("学号", value=student_id, disabled=True)
                                        else:
                                            # 教师用户：学号可编辑
                                            student_id = st.text_input("学号", value=student_id, help="13位学号")
                                    
                                    with form_col2:
                                        # 学生姓名处理
                                        student_name = extracted_info.get("学生姓名", "")
                                        if user['role'] == 'student':
                                            # 学生用户：姓名不可修改，自动填充当前姓名
                                            student_name = user['real_name']
                                            st.text_input("学生姓名", value=student_name, disabled=True)
                                        else:
                                            # 教师用户：姓名可编辑
                                            student_name = st.text_input("学生姓名", value=student_name, help="填写被指导学生姓名")
                                    
                                    form_col3, form_col4 = st.columns(2)
                                    
                                    with form_col3:
                                        # 学院信息
                                        student_college = st.text_input("学生所在学院", value=extracted_info.get("学生所在学院", ""))
                                    
                                    with form_col4:
                                        # 竞赛项目
                                        competition_name = st.text_input("竞赛项目", value=extracted_info.get("竞赛项目", ""))
                                    
                                    # 获奖信息
                                    st.markdown("#### 获奖信息")
                                    form_col5, form_col6 = st.columns(2)
                                    
                                    with form_col5:
                                        # 获奖类别
                                        award_category = st.selectbox(
                                            "获奖类别",
                                            ["", "国家级", "省级"],
                                            index=["", "国家级", "省级"].index(extracted_info.get("获奖类别", "")) if extracted_info.get("获奖类别", "") in ["", "国家级", "省级"] else 0
                                        )
                                    
                                    with form_col6:
                                        # 获奖等级
                                        award_level = st.selectbox(
                                            "获奖等级",
                                            ["", "一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"],
                                            index=["", "一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"].index(extracted_info.get("获奖等级", "")) if extracted_info.get("获奖等级", "") in ["", "一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"] else 0
                                        )
                                    
                                    form_col7, form_col8 = st.columns(2)
                                    
                                    with form_col7:
                                        # 竞赛类型
                                        competition_type = st.selectbox(
                                            "竞赛类型",
                                            ["", "A类", "B类"],
                                            index=["", "A类", "B类"].index(extracted_info.get("竞赛类型", "")) if extracted_info.get("竞赛类型", "") in ["", "A类", "B类"] else 0
                                        )
                                    
                                    with form_col8:
                                        # 获奖时间
                                        award_date = st.text_input("获奖时间", value=extracted_info.get("获奖时间", ""), help="格式：YYYY-MM-DD")
                                    
                                    # 其他信息
                                    st.markdown("#### 其他信息")
                                    form_col9, form_col10 = st.columns(2)
                                    
                                    with form_col9:
                                        # 主办单位
                                        organizing_unit = st.text_input("主办单位", value=extracted_info.get("主办单位", ""))
                                    
                                    with form_col10:
                                        # 指导教师处理
                                        advisor = extracted_info.get("指导教师", "")
                                        if user['role'] == 'teacher':
                                            # 教师用户：指导教师不可修改，自动填充当前教师姓名
                                            advisor = user['real_name']
                                            st.text_input("指导教师", value=advisor, disabled=True)
                                        else:
                                            # 学生用户：指导教师必填
                                            advisor = st.text_input("指导教师", value=advisor, help="必填字段")
                                    
                                    # 表单操作
                                    st.markdown("---")
                                    form_submit_col1, form_submit_col2 = st.columns(2)
                                    
                                    with form_submit_col1:
                                        save_draft = st.form_submit_button("💾 保存草稿")
                                    
                                    
                                    
                                    with form_submit_col2:
                                        submit_data = st.form_submit_button("📤 批量提交", type="primary")
                                    
                                    if save_draft:
                                        # 保存草稿到数据库
                                        try:
                                            from modules.database import db
                                            
                                            # 获取session状态中保存的上传文件ID
                                            uploaded_file_id = st.session_state.get("uploaded_file_id", 0)
                                            
                                            success = db.save_certificate_record(
                                                student_college=student_college,
                                                competition_name=competition_name,
                                                student_id=student_id,
                                                student_name=student_name,
                                                award_category=award_category,
                                                award_level=award_level,
                                                competition_type=competition_type,
                                                organizing_unit=organizing_unit,
                                                award_date=award_date,
                                                advisor_name=advisor,
                                                upload_file_id=uploaded_file_id,
                                                user_id=user["id"],
                                                status="draft"  # 保存为草稿状态
                                            )
                                            
                                            if success:
                                                st.success("草稿已成功保存！")
                                            else:
                                                st.error("草稿保存失败")
                                        except Exception as e:
                                            st.error(f"草稿保存失败: {str(e)}")
                                    
                                    if submit_data:
                                        # 提交前验证
                                        validation_passed = True
                                        validation_messages = []
                                        
                                        # 1. 必填字段完整性检查
                                        required_fields = {
                                            "学号": student_id,
                                            "学生姓名": student_name,
                                            "获奖类别": award_category,
                                            "获奖等级": award_level,
                                            "竞赛类型": competition_type,
                                            "指导教师": advisor
                                        }
                                        
                                        for field_name, field_value in required_fields.items():
                                            if not field_value:
                                                validation_passed = False
                                                validation_messages.append(f"{field_name}为必填字段")
                                        
                                        # 2. 学号格式验证（学生13位，教师工号不出现在学号字段）
                                        import re
                                        if student_id:
                                            # 学生学号必须为13位数字
                                            if not re.match(r'^\d{13}$', student_id):
                                                validation_passed = False
                                                validation_messages.append("学生学号必须为13位数字")
                                        
                                        # 3. 获奖时间格式验证
                                        if award_date:
                                            if not re.match(r'^\d{4}-\d{2}-\d{2}$', award_date):
                                                validation_passed = False
                                                validation_messages.append("获奖时间格式必须为YYYY-MM-DD")
                                        
                                        # 如果验证不通过，显示错误信息
                                        if not validation_passed:
                                            for message in validation_messages:
                                                st.error(message)
                                        else:
                                            # 验证通过，执行批量提交
                                            try:
                                                # 保存到数据库
                                                from modules.database import db
                                                
                                                # 获取session状态中保存的上传文件ID
                                                uploaded_file_id = st.session_state.get("uploaded_file_id", 0)
                                                
                                                success = db.save_certificate_record(
                                                    student_college=student_college,
                                                    competition_name=competition_name,
                                                    student_id=student_id,
                                                    student_name=student_name,
                                                    award_category=award_category,
                                                    award_level=award_level,
                                                    competition_type=competition_type,
                                                    organizing_unit=organizing_unit,
                                                    award_date=award_date,
                                                    advisor_name=advisor,
                                                    upload_file_id=uploaded_file_id,  # 使用实际的上传文件ID
                                                    user_id=user["id"],  # 当前用户ID
                                                    status="submitted"
                                                )
                                                
                                                if success:
                                                    st.success("数据已成功提交并保存到数据库！")
                                                    # 清空提取信息，准备处理新证书
                                                    st.session_state.pop("extracted_info", None)
                                                    st.session_state.pop("show_extracted_info", None)
                                                else:
                                                    st.error("数据提交失败，无法保存到数据库！")
                                            except Exception as e:
                                                st.error(f"数据提交失败: {str(e)}")
                                                st.exception(e)
                        
                        # -------------------- 第二列：处理后的证书和下载 --------------------
                        with col2:
                            st.markdown("### 处理后的证书")
                            
                            # 图片处理选项
                            st.markdown("#### 图片处理")
                            rotate_angle = st.slider("旋转角度", -180.0, 180.0, 0.0, 1.0, key="rotate_slider")
                            max_width = st.number_input("最大宽度", 100, 2000, 800, 50, key="width_input")
                            max_height = st.number_input("最大高度", 100, 2000, 1200, 50, key="height_input")
                            
                            # 处理图片
                            processed_img = image_processor.process_image(original_img, max_width, max_height, rotate_angle)
                            
                            # 添加预览控制
                            st.markdown("#### 预览控制")
                            processed_zoom = st.slider("缩放比例", 0.1, 3.0, 1.0, 0.1, key="zoom_slider_processed")
                            
                            # 显示处理后的图片 - 移除use_column_width=True，让width参数生效
                            st.image(
                                processed_img,
                                caption="处理后的图片预览",
                                width=int(processed_img.width * processed_zoom)
                            )
                            
                            # Base64编码生成
                            st.markdown("#### Base64编码")
                            base64_str = image_processor.image_to_base64(processed_img)
                            # 将base64_str保存到session状态中，供提取按钮使用
                            st.session_state["certificate_base64"] = base64_str
                            st.code(base64_str[:200] + "..." if len(base64_str) > 200 else base64_str, language="text")
                            
                            # 复制Base64按钮 - 使用HTML按钮配合JavaScript，避免Streamlit表单限制
                            copy_button_html = '''
                            <script>
                            function copyToClipboard() {
                                navigator.clipboard.writeText('%s');
                                alert("Base64编码已复制到剪贴板！");
                            }
                            </script>
                            <button onclick="copyToClipboard()" style="background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                                📋 复制Base64编码
                            </button>
                            ''' % base64_str
                            st.markdown(copy_button_html, unsafe_allow_html=True)
                            
                            # 下载处理后的图片 - 现在不在表单内部
                            st.markdown("#### 下载图片")
                            
                            # 正确处理base64字符串，解码为图片字节
                            import base64
                            base64_data = base64_str.split(",")[1]  # 获取base64数据部分
                            processed_img_bytes = base64.b64decode(base64_data)  # 解码为图片字节
                            
                            # 生成正确的文件名，确保使用.jpg扩展名
                            base_name = os.path.splitext(uploaded_file.name)[0]
                            st.download_button(
                                label="下载处理后的图片",
                                data=processed_img_bytes,
                                file_name=f"processed_{base_name}.jpg",
                                mime="image/jpeg"
                            )
                        
                        # 保存处理后的文件
                        from modules.database import db
                        success = db.save_uploaded_file(
                            filename=uploaded_file.name,
                            file_path=file_path,
                            file_type=file_info["file_ext"][1:],
                            file_size=file_info["file_size"],
                            user_id=user["id"]  # 使用当前用户ID
                        )
                        
                        # 获取上传文件的ID，用于后续保存证书记录
                        # 这里简化处理，获取最新上传的文件ID
                        uploaded_file_id = 0
                        if success:
                            # 获取当前用户最近上传的文件
                            user_files = db.get_user_files(user_id=user["id"])
                            if user_files:
                                # 按上传时间降序排列，取第一个
                                uploaded_file_id = user_files[0]["id"]
                            
                            # 将上传文件ID保存到session状态，供表单使用
                            st.session_state["uploaded_file_id"] = uploaded_file_id
                            
                            st.success(f"证书上传成功！已保存至根目录下的 uploads 文件夹。文件ID: {uploaded_file_id}")
                        else:
                            st.error("保存文件信息失败")
        elif page == "个人设置":
            show_personal_settings(user)
    
    # 退出登录按钮
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 退出登录"):
        auth.logout()

def show_admin_dashboard(auth):
    """显示管理员仪表板"""
    st.title("🏆 管理员控制台")
    st.subheader("欢迎使用竞赛证书管理系统")
    
    # 系统统计
    st.markdown("### 📊 系统统计")
    stats_cols = st.columns(3)
    
    users = db.get_all_users()
    students = [u for u in users if u['role'] == 'student']
    teachers = [u for u in users if u['role'] == 'teacher']
    
    with stats_cols[0]:
        st.metric("总用户数", len(users))
    with stats_cols[1]:
        st.metric("学生数", len(students))
    with stats_cols[2]:
        st.metric("教师数", len(teachers))
    
    # 最新活动
    st.markdown("### 📝 最近活动")
    # 这里可以显示最近的操作日志

def show_student_dashboard():
    """显示学生仪表板"""
    st.title("🎓 学生控制台")
    st.info("学生功能：上传证书、查看证书、个人信息管理")
    
    # 删除了控制台下方的按钮，只保留侧边栏导航
    st.markdown("---")
    st.subheader("使用提示")
    st.markdown("请通过左侧导航菜单选择您需要的功能")
    st.markdown("- 上传证书：上传新的竞赛证书")
    st.markdown("- 我的证书：查看已上传的证书")
    st.markdown("- 个人设置：修改个人信息")

def show_teacher_dashboard():
    """显示教师仪表板"""
    st.title("👨‍🏫 教师控制台")
    st.info("教师功能：指导学生、查看学生证书、审核证书")
    
    # 删除了控制台下方的按钮，只保留侧边栏导航
    st.markdown("---")
    st.subheader("使用提示")
    st.markdown("请通过左侧导航菜单选择您需要的功能")
    st.markdown("- 上传证书：上传新的竞赛证书")
    st.markdown("- 我的证书：查看已上传的证书")
    st.markdown("- 个人设置：修改个人信息")

def show_certificate_management():
    """显示所有用户提交的证书数据（管理员用）"""
    st.title("📄 证书管理")
    
    # 证书筛选
    st.markdown("---")
    st.subheader("证书筛选")
    
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "按状态筛选",
            ["全部", "草稿", "已提交"],
            index=0
        )
    
    status_map = {
        "全部": None,
        "草稿": "draft",
        "已提交": "submitted"
    }
    
    # 获取所有证书数据
    certificates = db.get_all_certificates(status=status_map[status_filter])
    
    if not certificates:
        st.info("暂无证书记录")
        return
    
    # 证书导出功能
    st.markdown("---")
    st.subheader("证书导出")
    
    # 导出格式选择
    export_format = st.selectbox(
        "选择导出格式",
        ["CSV", "XLSX"],
        index=0
    )
    
    # 导出按钮
    if st.button("📤 导出证书数据"):
        with st.spinner("正在导出证书数据..."):
            try:
                import pandas as pd
                from datetime import datetime
                
                # 准备导出数据
                export_data = []
                for cert in certificates:
                    export_data.append({
                        "证书ID": cert["id"],
                        "竞赛项目": cert["competition_name"],
                        "获奖类别": cert["award_category"],
                        "获奖等级": cert["award_level"],
                        "竞赛类型": cert["competition_type"],
                        "获奖时间": cert["award_date"],
                        "学生姓名": cert["student_name"],
                        "学生学号": cert["student_id"],
                        "学生学院": cert["student_college"],
                        "指导教师": cert["advisor_name"],
                        "主办单位": cert["organizing_unit"],
                        "状态": "草稿" if cert["status"] == "draft" else "已提交",
                        "文件名": cert["filename"] if cert["filename"] else "",
                        "创建时间": cert["created_at"],
                        "更新时间": cert["updated_at"]
                    })
                
                # 创建DataFrame
                df = pd.DataFrame(export_data)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                
                if export_format == "CSV":
                    # 导出为CSV
                    csv_data = df.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="下载CSV文件",
                        data=csv_data,
                        file_name=f"certificates_export_{timestamp}.csv",
                        mime="text/csv"
                    )
                    st.success("CSV文件导出成功！")
                else:
                    # 导出为XLSX
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='证书数据')
                    output.seek(0)
                    st.download_button(
                        label="下载XLSX文件",
                        data=output,
                        file_name=f"certificates_export_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("XLSX文件导出成功！")
            except Exception as e:
                st.error(f"导出失败: {str(e)}")
    
    # 显示证书列表
    st.markdown("---")
    st.subheader("证书列表")
    
    # 准备表格数据
    table_data = []
    for cert in certificates:
        cert_copy = cert.copy()
        # 转换字段名和值为中文
        cert_copy['status'] = "草稿" if cert['status'] == "draft" else "已提交"
        cert_copy['award_category'] = "国家级" if cert['award_category'] == "国家级" else "省级"
        # 移除不需要显示的字段
        cert_copy.pop('file_path', None)
        table_data.append(cert_copy)
    
    st.dataframe(
        table_data,
        column_config={
            "id": "ID",
            "student_id": "学号",
            "student_name": "姓名",
            "student_college": "学院",
            "competition_name": "竞赛项目",
            "award_category": "获奖类别",
            "award_level": "获奖等级",
            "competition_type": "竞赛类型",
            "organizing_unit": "主办单位",
            "award_date": "获奖时间",
            "advisor_name": "指导教师",
            "filename": "证书文件",
            "file_type": "文件类型",
            "status": "状态",
            "created_at": "创建时间",
            "updated_at": "更新时间"
        },
        hide_index=True,
        use_container_width=True,
        height=400
    )


def show_user_management(auth):
    """显示用户管理页面"""
    st.title("👥 用户管理")
    
    # 初始化session状态
    if 'editing_user' not in st.session_state:
        st.session_state.editing_user = None
    if 'resetting_password' not in st.session_state:
        st.session_state.resetting_password = None
    
    # 用户筛选
    col1, col2 = st.columns(2)
    with col1:
        filter_role = st.selectbox(
            "按角色筛选",
            ["全部", "学生", "教师", "管理员"],
            key="role_filter_selectbox"
        )
    
    role_map = {
        "全部": None,
        "学生": "student",
        "教师": "teacher",
        "管理员": "admin"
    }
    
    # 获取用户列表
    users = db.get_all_users(role=role_map[filter_role])
    
    if not users:
        st.info("暂无用户数据")
        return
    
    # 用户操作区
    st.markdown("---")
    st.subheader("用户操作")
    
    # 选择要操作的用户
    selected_user_id = st.selectbox(
        "选择用户",
        [user["id"] for user in users],
        format_func=lambda user_id: next((f"{u['real_name']} ({u['username']}) - {auth.get_role_name(u['role'])} - {'启用' if u['is_active'] else '禁用'}" for u in users if u['id'] == user_id), ""),
        index=None,
        placeholder="请选择要操作的用户"
    )
    
    if selected_user_id:
        selected_user = next((u for u in users if u['id'] == selected_user_id), None)
        
        if selected_user:
            # 操作按钮组
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📝 编辑用户信息", type="primary"):
                    st.session_state.editing_user = selected_user
                    st.session_state.resetting_password = None
                    st.session_state.viewing_certificates = None
            
            with col2:
                if st.button("🔄 重置密码"):
                    st.session_state.resetting_password = selected_user
                    st.session_state.editing_user = None
                    st.session_state.viewing_certificates = None
            
            with col3:
                if selected_user['is_active']:
                    if st.button("🔒 禁用账号", type="primary"):
                        if db.update_user_status(selected_user['id'], False):
                            st.success(f"已成功禁用用户: {selected_user['real_name']}")
                            st.rerun()
                        else:
                            st.error("禁用账号失败")
                else:
                    if st.button("🔓 启用账号", type="secondary"):
                        if db.update_user_status(selected_user['id'], True):
                            st.success(f"已成功启用用户: {selected_user['real_name']}")
                            st.rerun()
                        else:
                            st.error("启用账号失败")
            
            # 查看证书按钮
            st.markdown("---")
            if st.button("📄 查看用户证书"):
                st.session_state.viewing_certificates = selected_user
                st.session_state.editing_user = None
                st.session_state.resetting_password = None
            
            # 查看证书区域
            if hasattr(st.session_state, 'viewing_certificates') and st.session_state.viewing_certificates == selected_user:
                st.markdown("---")
                st.subheader(f"📄 {selected_user['real_name']}的证书")
                
                # 获取用户证书
                certificates = db.get_user_certificates_by_username(selected_user['username'])
                
                if not certificates:
                    st.info("该用户暂无证书记录")
                else:
                    # 证书导出功能
                    st.markdown("### 证书导出")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        cert_export_format = st.selectbox(
                            "选择导出格式",
                            ["CSV", "XLSX"],
                            index=0,
                            key="cert_export_format"
                        )
                    
                    with col2:
                        if st.button("📤 导出证书数据"):
                            with st.spinner("正在导出证书数据..."):
                                try:
                                    import pandas as pd
                                    from datetime import datetime
                                    
                                    # 准备导出数据
                                    export_data = []
                                    for cert in certificates:
                                        export_data.append({
                                            "证书ID": cert["id"],
                                            "竞赛项目": cert["competition_name"],
                                            "获奖类别": cert["award_category"],
                                            "获奖等级": cert["award_level"],
                                            "竞赛类型": cert["competition_type"],
                                            "获奖时间": cert["award_date"],
                                            "学生姓名": cert["student_name"],
                                            "学生学号": cert["student_id"],
                                            "学生学院": cert["student_college"],
                                            "指导教师": cert["advisor_name"],
                                            "主办单位": cert["organizing_unit"],
                                            "状态": "草稿" if cert["status"] == "draft" else "已提交",
                                            "文件名": cert["filename"] if cert["filename"] else ""
                                        })
                                    
                                    # 创建DataFrame
                                    df = pd.DataFrame(export_data)
                                    
                                    # 生成文件名
                                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                                    
                                    if cert_export_format == "CSV":
                                        # 导出为CSV
                                        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
                                        st.download_button(
                                            label="下载CSV文件",
                                            data=csv_data,
                                            file_name=f"certificates_{selected_user['username']}_{timestamp}.csv",
                                            mime="text/csv"
                                        )
                                        st.success("CSV文件导出成功！")
                                    else:
                                        # 导出为XLSX
                                        import io
                                        output = io.BytesIO()
                                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                            df.to_excel(writer, index=False, sheet_name='证书数据')
                                        output.seek(0)
                                        st.download_button(
                                            label="下载XLSX文件",
                                            data=output,
                                            file_name=f"certificates_{selected_user['username']}_{timestamp}.xlsx",
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                        )
                                        st.success("XLSX文件导出成功！")
                                except Exception as e:
                                    st.error(f"导出失败: {str(e)}")
                    
                    # 显示证书列表 - 使用容器稳定布局
                    st.markdown("---")
                    st.markdown("### 证书列表")
                    
                    # 添加容器稳定布局
                    with st.container():
                        # 准备表格数据
                        table_data = []
                        for cert in certificates:
                            table_data.append({
                                "id": cert["id"],
                                "competition_name": cert["competition_name"],
                                "award_category": cert["award_category"],
                                "award_level": cert["award_level"],
                                "award_date": cert["award_date"],
                                "status": "草稿" if cert["status"] == "draft" else "已提交"
                            })
                        
                        # 使用固定高度稳定布局
                        st.dataframe(
                            table_data,
                            column_config={
                                "id": "ID",
                                "competition_name": "竞赛项目",
                                "award_category": "获奖类别",
                                "award_level": "获奖等级",
                                "award_date": "获奖时间",
                                "status": "状态"
                            },
                            hide_index=True,
                            use_container_width=True,
                            height=300  # 固定高度，减少布局变化
                        )
                    
                    # 证书详情
                    st.markdown("---")
                    st.subheader("证书详情")
                    
                    selected_cert_id = st.selectbox(
                        "选择要查看的证书",
                        [cert["id"] for cert in certificates],
                        format_func=lambda cert_id: next((f"{c['competition_name']} - {c['award_level']}" for c in certificates if c['id'] == cert_id), ""),
                        index=None,
                        placeholder="请选择证书"
                    )
                    
                    if selected_cert_id:
                        selected_cert = next((c for c in certificates if c['id'] == selected_cert_id), None)
                        if selected_cert:
                            # 显示证书详细信息
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown(f"**竞赛项目:** {selected_cert['competition_name']}")
                                st.markdown(f"**获奖类别:** {selected_cert['award_category']}")
                                st.markdown(f"**获奖等级:** {selected_cert['award_level']}")
                                st.markdown(f"**竞赛类型:** {selected_cert['competition_type']}")
                                st.markdown(f"**主办单位:** {selected_cert['organizing_unit']}")
                            
                            with col2:
                                st.markdown(f"**获奖时间:** {selected_cert['award_date']}")
                                st.markdown(f"**学生姓名:** {selected_cert['student_name']}")
                                st.markdown(f"**学生学号:** {selected_cert['student_id']}")
                                st.markdown(f"**学生学院:** {selected_cert['student_college']}")
                                st.markdown(f"**指导教师:** {selected_cert['advisor_name']}")
                                st.markdown(f"**状态:** {'草稿' if selected_cert['status'] == 'draft' else '已提交'}")
                            
                            # 证书文件预览
                            if selected_cert['file_path']:
                                st.markdown("---")
                                st.markdown("### 证书预览")
                                
                                try:
                                    if selected_cert['file_type'] == 'pdf':
                                        # PDF文件预览
                                        st.markdown(f"**文件名:** {selected_cert['filename']}")
                                        st.markdown(f"**文件类型:** PDF")
                                        st.info("PDF文件预览功能开发中，可直接下载查看")
                                    else:
                                        # 图片文件预览
                                        from PIL import Image
                                        image = Image.open(selected_cert['file_path'])
                                        st.image(image, caption=selected_cert['filename'], use_column_width=True)
                                except Exception as e:
                                    st.error(f"预览失败: {str(e)}")
                                
                                # 文件下载
                                st.markdown("---")
                                st.markdown("### 文件下载")
                                
                                try:
                                    with open(selected_cert['file_path'], "rb") as f:
                                        file_data = f.read()
                                    
                                    st.download_button(
                                        label="下载证书文件",
                                        data=file_data,
                                        file_name=selected_cert['filename'],
                                        mime=f"application/{selected_cert['file_type']}" if selected_cert['file_type'] == 'pdf' else f"image/{selected_cert['file_type']}"
                                    )
                                except Exception as e:
                                    st.error(f"下载失败: {str(e)}")
    
    # 编辑用户信息表单
    if st.session_state.editing_user:
        st.markdown("---")
        st.subheader(f"编辑用户信息: {st.session_state.editing_user['real_name']}")
        
        user = st.session_state.editing_user
        
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                real_name = st.text_input("姓名", value=user['real_name'])
                unit = st.text_input("单位", value=user['unit'])
                email = st.text_input("邮箱", value=user['email'])
            
            with col2:
                # 角色选择使用中文显示
                role_options = {
                    "学生": "student",
                    "教师": "teacher",
                    "管理员": "admin"
                }
                current_role_name = [name for name, value in role_options.items() if value == user['role']][0]
                selected_role_name = st.selectbox(
                    "角色",
                    list(role_options.keys()),
                    index=list(role_options.keys()).index(current_role_name)
                )
                role = role_options[selected_role_name]
                phone = st.text_input("电话", value=user['phone'])
                username = st.text_input("学号/工号", value=user['username'], disabled=True)
            
            # 表单操作按钮
            form_col1, form_col2 = st.columns(2)
            
            with form_col1:
                save_changes = st.form_submit_button("💾 保存修改", type="primary")
            
            with form_col2:
                cancel_edit = st.form_submit_button("取消")
            
            if cancel_edit:
                st.session_state.editing_user = None
                st.rerun()
            
            if save_changes:
                # 更新用户信息
                update_data = {
                    'real_name': real_name,
                    'unit': unit,
                    'email': email,
                    'phone': phone,
                    'role': role
                }
                
                if db.update_user_info(user['id'], update_data):
                    st.success("用户信息更新成功！")
                    st.session_state.editing_user = None
                    st.rerun()
                else:
                    st.error("用户信息更新失败")
    
    # 重置密码表单
    if st.session_state.resetting_password:
        st.markdown("---")
        st.subheader(f"重置用户密码: {st.session_state.resetting_password['real_name']}")
        
        user = st.session_state.resetting_password
        
        with st.form("reset_password_form"):
            new_password = st.text_input("新密码", type="password")
            confirm_password = st.text_input("确认新密码", type="password")
            
            # 表单操作按钮
            form_col1, form_col2 = st.columns(2)
            
            with form_col1:
                reset_password = st.form_submit_button("🔄 重置密码", type="primary")
            
            with form_col2:
                cancel_reset = st.form_submit_button("取消")
            
            if cancel_reset:
                st.session_state.resetting_password = None
                st.rerun()
            
            if reset_password:
                if new_password != confirm_password:
                    st.error("两次输入的密码不一致，请重新输入")
                elif len(new_password) < 6:
                    st.error("密码长度不能少于6位")
                else:
                    if db.reset_user_password(user['id'], new_password):
                        st.success("密码重置成功！")
                        st.session_state.resetting_password = None
                        st.rerun()
                    else:
                        st.error("密码重置失败")
    
    # 用户导出功能
    st.markdown("---")
    st.subheader("用户导出")
    
    # 导出格式选择
    export_format = st.selectbox(
        "选择导出格式",
        ["CSV", "XLSX"],
        index=0
    )
    
    # 导出按钮
    if st.button("📤 导出用户数据"):
        with st.spinner("正在导出用户数据..."):
            try:
                import pandas as pd
                from datetime import datetime
                
                # 准备导出数据
                export_data = []
                for user in users:
                    export_data.append({
                        "ID": user["id"],
                        "学号/工号": user["username"],
                        "角色": auth.get_role_name(user["role"]),
                        "姓名": user["real_name"],
                        "单位": user["unit"],
                        "邮箱": user["email"],
                        "电话": user["phone"],
                        "注册时间": user["created_at"],
                        "最后登录": user["last_login"],
                        "状态": "启用" if user["is_active"] else "禁用"
                    })
                
                # 创建DataFrame
                df = pd.DataFrame(export_data)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                
                if export_format == "CSV":
                    # 导出为CSV
                    csv_data = df.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="下载CSV文件",
                        data=csv_data,
                        file_name=f"users_export_{timestamp}.csv",
                        mime="text/csv"
                    )
                    st.success("CSV文件导出成功！")
                else:
                    # 导出为XLSX
                    import io
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='用户数据')
                    output.seek(0)
                    st.download_button(
                        label="下载XLSX文件",
                        data=output,
                        file_name=f"users_export_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    st.success("XLSX文件导出成功！")
            except Exception as e:
                st.error(f"导出失败: {str(e)}")
    
    # 用户列表显示 - 使用容器稳定布局
    st.markdown("---")
    st.subheader("用户列表")
    
    # 添加一个容器来稳定布局
    with st.container():
        # 准备显示数据，转换角色和状态为中文
        display_users = []
        for user in users:
            display_user = user.copy()
            display_user['role'] = auth.get_role_name(user['role'])
            display_user['is_active'] = "启用" if user['is_active'] else "禁用"
            display_users.append(display_user)
        
        # 使用更高效的数据框显示方式
        st.dataframe(
            display_users,
            column_config={
                "id": "ID",
                "username": "学号/工号",
                "role": "角色",
                "real_name": "姓名",
                "unit": "单位",
                "email": "邮箱",
                "phone": "电话",
                "created_at": "注册时间",
                "last_login": "最后登录",
                "is_active": "状态"
            },
            hide_index=True,
            use_container_width=True,
            height=400  # 添加固定高度，减少布局变化
        )

def show_my_certificates(user):
    """显示用户的证书"""
    st.title("📄 我的证书")
    
    # 获取用户证书记录
    certificates = db.get_user_certificates(user['id'], user['role'])
    
    if not certificates:
        st.info("暂无证书记录")
        return
    
    # 证书筛选
    st.markdown("---")
    st.subheader("证书筛选")
    
    # 获取所有竞赛项目
    competition_names = list(set(cert['competition_name'] for cert in certificates))
    competition_names.insert(0, "全部")
    
    selected_competition = st.selectbox(
        "按竞赛项目筛选",
        competition_names,
        index=0
    )
    
    # 根据筛选条件过滤证书
    filtered_certificates = certificates
    if selected_competition != "全部":
        filtered_certificates = [cert for cert in certificates if cert['competition_name'] == selected_competition]
    
    # 显示证书列表
    st.markdown("---")
    st.subheader("证书列表")
    
    # 准备表格数据
    table_data = []
    for cert in filtered_certificates:
        cert_copy = cert.copy()
        # 转换字段名和值为中文
        cert_copy['award_category'] = "国家级" if cert['award_category'] == "国家级" else "省级"
        cert_copy['status'] = "草稿" if cert['status'] == "draft" else "已提交"
        # 移除不需要显示的字段
        cert_copy.pop('id', None)
        cert_copy.pop('user_id', None)
        cert_copy.pop('file_path', None)
        table_data.append(cert_copy)
    
    st.dataframe(
        table_data,
        column_config={
            "student_id": "学号",
            "student_name": "姓名",
            "student_college": "学院",
            "competition_name": "竞赛项目",
            "award_category": "获奖类别",
            "award_level": "获奖等级",
            "competition_type": "竞赛类型",
            "organizing_unit": "主办单位",
            "award_date": "获奖时间",
            "advisor_name": "指导教师",
            "filename": "证书文件",
            "file_type": "文件类型",
            "status": "状态"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 证书详情
    st.markdown("---")
    st.subheader("证书详情")
    
    # 选择证书查看详情
    selected_cert_id = st.selectbox(
        "选择要查看的证书",
        [cert['id'] for cert in filtered_certificates],
        format_func=lambda cert_id: next((f"{cert['competition_name']} - {cert['student_name']} - {cert['award_level']}" for cert in filtered_certificates if cert['id'] == cert_id), ""),
        index=None,
        placeholder="请选择证书"
    )
    
    if selected_cert_id:
        selected_cert = next((cert for cert in filtered_certificates if cert['id'] == selected_cert_id), None)
        if selected_cert:
            # 显示证书详情
            st.markdown(f"### {selected_cert['competition_name']}")
            
            # 证书基本信息
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**学号/工号:** {selected_cert['student_id']}")
                st.markdown(f"**姓名:** {selected_cert['student_name']}")
                st.markdown(f"**学院:** {selected_cert['student_college']}")
                st.markdown(f"**竞赛类型:** {selected_cert['competition_type']}")
                st.markdown(f"**获奖类别:** {'国家级' if selected_cert['award_category'] == '国家级' else '省级'}")
            
            with col2:
                st.markdown(f"**获奖等级:** {selected_cert['award_level']}")
                st.markdown(f"**主办单位:** {selected_cert['organizing_unit']}")
                st.markdown(f"**获奖时间:** {selected_cert['award_date']}")
                st.markdown(f"**指导教师:** {selected_cert['advisor_name']}")
                st.markdown(f"**状态:** {'草稿' if selected_cert['status'] == 'draft' else '已提交'}")
            
            # 编辑和提交草稿功能 - 仅对草稿状态的证书显示
            if selected_cert['status'] == 'draft':
                st.markdown("---")
                
                # 检查是否处于编辑模式
                if not hasattr(st.session_state, 'editing_certificate'):
                    st.session_state.editing_certificate = None
                
                if st.session_state.editing_certificate == selected_cert['id']:
                    # 显示编辑表单
                    st.subheader("编辑证书信息")
                    
                    with st.form(f"edit_cert_form_{selected_cert['id']}"):
                        # 基本信息
                        form_col1, form_col2 = st.columns(2)
                        
                        with form_col1:
                            student_id = st.text_input("学号", value=selected_cert['student_id'])
                            student_name = st.text_input("姓名", value=selected_cert['student_name'])
                            student_college = st.text_input("学院", value=selected_cert['student_college'])
                            competition_name = st.text_input("竞赛项目", value=selected_cert['competition_name'])
                        
                        with form_col2:
                            # 获奖类别
                            award_category = st.selectbox(
                                "获奖类别",
                                ["", "国家级", "省级"],
                                index=["", "国家级", "省级"].index(selected_cert['award_category']) if selected_cert['award_category'] in ["", "国家级", "省级"] else 0
                            )
                            
                            # 获奖等级
                            award_level = st.selectbox(
                                "获奖等级",
                                ["", "一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"],
                                index=["", "一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"].index(selected_cert['award_level']) if selected_cert['award_level'] in ["", "一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖", "优秀奖"] else 0
                            )
                            
                            # 竞赛类型
                            competition_type = st.selectbox(
                                "竞赛类型",
                                ["", "A类", "B类"],
                                index=["", "A类", "B类"].index(selected_cert['competition_type']) if selected_cert['competition_type'] in ["", "A类", "B类"] else 0
                            )
                            
                            # 获奖时间 - 带实时格式验证
                            award_date = st.text_input("获奖时间", value=selected_cert['award_date'], help="格式：YYYY-MM-DD")
                            import re
                            if award_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', award_date):
                                st.warning("获奖时间格式必须为YYYY-MM-DD")
                        
                        # 其他信息
                        form_col3, form_col4 = st.columns(2)
                        
                        with form_col3:
                            organizing_unit = st.text_input("主办单位", value=selected_cert['organizing_unit'])
                        
                        with form_col4:
                            advisor_name = st.text_input("指导教师", value=selected_cert['advisor_name'])
                        
                        # 表单操作按钮
                        form_col5, form_col6 = st.columns(2)
                        
                        with form_col5:
                            save_changes = st.form_submit_button("💾 保存修改", type="primary")
                        
                        with form_col6:
                            cancel_edit = st.form_submit_button("取消")
                        
                        if cancel_edit:
                            st.session_state.editing_certificate = None
                            st.rerun()
                        
                        if save_changes:
                            # 验证必填字段
                            validation_passed = True
                            validation_messages = []
                            
                            required_fields = {
                                "学号": student_id,
                                "学生姓名": student_name,
                                "获奖类别": award_category,
                                "获奖等级": award_level,
                                "竞赛类型": competition_type,
                                "指导教师": advisor_name
                            }
                            
                            for field_name, field_value in required_fields.items():
                                if not field_value:
                                    validation_passed = False
                                    validation_messages.append(f"{field_name}为必填字段")
                            
                            # 学号格式验证
                            if student_id and not re.match(r'^\d{13}$', student_id):
                                validation_passed = False
                                validation_messages.append("学生学号必须为13位数字")
                            
                            # 获奖时间格式验证
                            if award_date and not re.match(r'^\d{4}-\d{2}-\d{2}$', award_date):
                                validation_passed = False
                                validation_messages.append("获奖时间格式必须为YYYY-MM-DD")
                            
                            if not validation_passed:
                                for message in validation_messages:
                                    st.error(message)
                            else:
                                # 更新证书信息
                                try:
                                    # 调用数据库更新方法
                                    success = db.update_certificate(
                                        cert_id=selected_cert['id'],
                                        student_id=student_id,
                                        student_name=student_name,
                                        student_college=student_college,
                                        competition_name=competition_name,
                                        award_category=award_category,
                                        award_level=award_level,
                                        competition_type=competition_type,
                                        organizing_unit=organizing_unit,
                                        award_date=award_date,
                                        advisor_name=advisor_name
                                    )
                                    
                                    if success:
                                        st.success("证书信息已成功更新！")
                                        st.session_state.editing_certificate = None
                                        st.rerun()
                                    else:
                                        st.error("证书信息更新失败")
                                except Exception as e:
                                    st.error(f"更新失败: {str(e)}")
                else:
                    # 显示编辑和提交按钮
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📝 编辑证书", type="primary"):
                            st.session_state.editing_certificate = selected_cert['id']
                            st.rerun()
                    
                    with col2:
                        if st.button("📤 提交证书"):
                            # 导入re模块
                            import re
                            # 提交证书前验证必填字段
                            validation_passed = True
                            validation_messages = []
                            
                            required_fields = {
                                "学号": selected_cert['student_id'],
                                "学生姓名": selected_cert['student_name'],
                                "获奖类别": selected_cert['award_category'],
                                "获奖等级": selected_cert['award_level'],
                                "竞赛类型": selected_cert['competition_type'],
                                "指导教师": selected_cert['advisor_name']
                            }
                            
                            for field_name, field_value in required_fields.items():
                                if not field_value:
                                    validation_passed = False
                                    validation_messages.append(f"{field_name}为必填字段")
                            
                            # 学号格式验证
                            if selected_cert['student_id']:
                                # 确保student_id是字符串类型
                                student_id_str = str(selected_cert['student_id'])
                                if not re.match(r'^\d{13}$', student_id_str):
                                    validation_passed = False
                                    validation_messages.append("学生学号必须为13位数字")
                            
                            # 获奖时间格式验证
                            if selected_cert['award_date']:
                                # 确保award_date是字符串类型
                                award_date_str = str(selected_cert['award_date'])
                                if not re.match(r'^\d{4}-\d{2}-\d{2}$', award_date_str):
                                    validation_passed = False
                                    validation_messages.append("获奖时间格式必须为YYYY-MM-DD")
                            
                            if not validation_passed:
                                for message in validation_messages:
                                    st.error(message)
                            else:
                                # 提交证书
                                try:
                                    success = db.submit_certificate(selected_cert['id'])
                                    
                                    if success:
                                        st.success("证书已成功提交！")
                                        st.rerun()
                                    else:
                                        st.error("证书提交失败")
                                except Exception as e:
                                    st.error(f"提交失败: {str(e)}")
            
            # 证书文件预览
            if selected_cert['file_path']:
                st.markdown("---")
                st.markdown("### 证书预览")
                
                try:
                    if selected_cert['file_type'] == 'pdf':
                        # PDF文件预览
                        st.markdown(f"**文件名:** {selected_cert['filename']}")
                        st.markdown(f"**文件类型:** PDF")
                        st.info("PDF文件预览功能开发中，可直接下载查看")
                    else:
                        # 图片文件预览
                        from PIL import Image
                        image = Image.open(selected_cert['file_path'])
                        st.image(image, caption=selected_cert['filename'], use_column_width=True)
                except Exception as e:
                    st.error(f"预览失败: {str(e)}")
                
                # 文件下载
                st.markdown("---")
                st.markdown("### 文件下载")
                
                try:
                    with open(selected_cert['file_path'], "rb") as f:
                        file_data = f.read()
                    
                    st.download_button(
                        label="下载证书文件",
                        data=file_data,
                        file_name=selected_cert['filename'],
                        mime=f"{selected_cert['file_type']}/{selected_cert['file_type']}"
                    )
                except Exception as e:
                    st.error(f"下载失败: {str(e)}")


def show_personal_settings(user):
    """显示个人设置页面"""
    st.title("⚙️ 个人设置")
    
    # 获取用户当前信息
    current_user = db.get_user_by_id(user['id'])
    if not current_user:
        st.error("获取用户信息失败")
        return
    
    # 个人信息编辑
    st.markdown("---")
    st.subheader("基本信息")
    
    with st.form("personal_settings_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            real_name = st.text_input("姓名", value=current_user['real_name'])
            unit = st.text_input("学院/单位", value=current_user['unit'])
        
        with col2:
            email = st.text_input("邮箱", value=current_user['email'])
            phone = st.text_input("电话", value=current_user['phone'])
        
        # 只读字段
        st.markdown("---")
        st.subheader("账户信息")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("学号/工号", value=current_user['username'], disabled=True)
        with col2:
            st.text_input("角色", value="学生" if current_user['role'] == 'student' else "教师" if current_user['role'] == 'teacher' else "管理员", disabled=True)
        
        # 表单操作
        st.markdown("---")
        form_col1, form_col2 = st.columns(2)
        
        with form_col1:
            save_changes = st.form_submit_button("💾 保存修改", type="primary")
        
        with form_col2:
            cancel_edit = st.form_submit_button("取消")
        
        if cancel_edit:
            st.rerun()
        
        if save_changes:
            # 更新用户信息
            update_data = {
                'real_name': real_name,
                'unit': unit,
                'email': email,
                'phone': phone
            }
            
            if db.update_user_info(user['id'], update_data):
                st.success("个人信息更新成功！")
                # 更新session中的用户信息
                st.session_state.user_info = db.get_user_by_id(user['id'])
                st.rerun()
            else:
                st.error("个人信息更新失败")


def main():
    """主函数"""
    # 初始化session状态
    init_session_state()
    
    # 检查登录状态
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_main_page()

if __name__ == "__main__":
    main()