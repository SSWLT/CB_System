# modules/auth_system.py
import streamlit as st
import re
import bcrypt
from datetime import datetime
import logging
from typing import Optional, Dict, Any
import sys
import os

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 添加父目录到Python路径
sys.path.append(parent_dir)

# 导入数据库模块
try:
    from modules.database import db
except ImportError as e:
    st.error(f"数据库模块导入失败: {e}")
    st.error(f"当前路径: {current_dir}")
    raise

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthSystem:
    """用户认证系统"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """初始化session状态"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
    
    def validate_username_format(self, username: str, role: str) -> bool:
        """验证学号/工号格式"""
        if role == 'student':
            # 13位学号，全数字
            pattern = r'^\d{13}$'
            error_msg = "学号必须为13位数字"
        elif role == 'teacher':
            # 8位工号，全数字
            pattern = r'^\d{8}$'
            error_msg = "工号必须为8位数字"
        elif role == 'admin':
            # 8位工号，全数字
            pattern = r'^\d{8}$'
            error_msg = "管理员工号必须为8位数字"
        else:
            return False
        
        if not re.match(pattern, username):
            st.error(error_msg)
            return False
        
        return True
    
    def validate_password(self, password: str) -> bool:
        """验证密码强度"""
        if len(password) < 8:
            st.error("密码长度至少8位")
            return False
        
        if not re.search(r'[A-Za-z]', password):
            st.error("密码必须包含字母")
            return False
        
        if not re.search(r'\d', password):
            st.error("密码必须包含数字")
            return False
        
        return True
    
    def register_user(self):
        """用户注册功能"""
        st.title("📝 用户注册")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                role = st.selectbox(
                    "选择角色",
                    ["学生", "教师", "管理员"],
                    help="学生：13位学号，教师/管理员：8位工号"
                )
                
                role_map = {
                    "学生": "student",
                    "教师": "teacher",
                    "管理员": "admin"
                }
                role_value = role_map[role]
                
                username = st.text_input(
                    "学号/工号",
                    placeholder="请输入13位学号或8位工号",
                    max_chars=13
                )
                
                real_name = st.text_input("真实姓名")
                
                unit = st.text_input("所属单位", placeholder="请输入学院或部门名称", help="所属学院或部门") 
                
            with col2:
                password = st.text_input("密码", type="password")
                confirm_password = st.text_input("确认密码", type="password")
                email = st.text_input("邮箱")
                phone = st.text_input("电话")
            
            submit_button = st.form_submit_button("注册")
            
            if submit_button:
                if not all([username, password, confirm_password, real_name]):
                    st.error("请填写所有必填字段")
                    return
                
                if not self.validate_username_format(username, role_value):
                    return
                
                if not self.validate_password(password):
                    return
                
                if password != confirm_password:
                    st.error("两次输入的密码不一致")
                    return
                
                if db.user_exists(username):
                    st.error("该学号/工号已注册")
                    return
                
                user_data = {
                    'username': username,
                    'password': password,
                    'role': role_value,
                    'real_name': real_name,
                    'unit': unit,
                    'email': email,
                    'phone': phone
                }
                
                if db.create_user(user_data):
                    st.success("注册成功！")
                    st.info("请使用您的学号/工号登录系统")
                else:
                    st.error("注册失败，请稍后重试")
    
    def login_user(self):
        """用户登录功能"""
        st.title("🔐 用户登录")
        
        with st.form("login_form"):
            username = st.text_input("学号/工号")
            password = st.text_input("密码", type="password")
            
            login_button = st.form_submit_button("登录")
            
            if login_button:
                if not username or not password:
                    st.error("请输入学号/工号和密码")
                    return
                
                # 先检查用户是否存在
                if not db.user_exists(username):
                    st.error("该学（工）号不存在，请注册或联系管理员导入信息")
                else:
                    # 验证密码
                    user = db.verify_user(username, password)
                    
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user_info = user
                        
                        db.log_user_action(
                            user_id=user['id'],
                            action="LOGIN",
                            details="用户登录成功"
                        )
                        
                        st.success(f"登录成功！欢迎您，{user['real_name']}")
                        st.rerun()
                    else:
                        st.error("密码错误")
    
    def logout(self):
        """用户登出"""
        if st.session_state.user_info:
            db.log_user_action(
                user_id=st.session_state.user_info['id'],
                action="LOGOUT",
                details="用户登出系统"
            )
        
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.success("已成功登出")
        st.rerun()
    
    def get_current_user(self) -> Optional[Dict]:
        """获取当前登录用户信息"""
        return st.session_state.user_info if st.session_state.authenticated else None
    
    def check_permission(self, required_role: str = None) -> bool:
        """检查用户权限"""
        if not st.session_state.authenticated:
            return False
        
        if required_role and st.session_state.user_info['role'] != required_role:
            return False
        
        return True
    
    def show_user_profile(self):
        """显示用户个人信息"""
        user = self.get_current_user()
        
        if not user:
            return
        
        st.sidebar.title("👤 个人信息")
        st.sidebar.markdown(f"**姓名：** {user['real_name']}")
        st.sidebar.markdown(f"**身份：** {self.get_role_name(user['role'])}")
        st.sidebar.markdown(f"**学号/工号：** {user['username']}")
        if 'unit' in user and user['unit']:
            st.sidebar.markdown(f"**单位：** {user['unit']}")
        
        if st.sidebar.button("🚪 退出登录"):
            self.logout()
    
    def get_role_name(self, role_key: str) -> str:
        """获取角色名称"""
        role_names = {
            'student': '学生',
            'teacher': '教师',
            'admin': '管理员'
        }
        return role_names.get(role_key, role_key)
    
    def show_all_users(self):
        """显示所有用户（管理员功能）"""
        st.title("👥 用户管理")
        
        users = db.get_all_users()
        
        if not users:
            st.info("暂无用户数据")
            return
        
        st.dataframe(
            users,
            column_config={
                "id": "ID",
                "username": "学号/工号",
                "role": "角色",
                "real_name": "姓名",
                "email": "邮箱",
                "created_at": "注册时间",
                "last_login": "最后登录",
                "is_active": "状态"
            },
            hide_index=True,
            use_container_width=True
        )