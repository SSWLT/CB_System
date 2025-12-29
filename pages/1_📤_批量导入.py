# pages/1_📤_批量导入.py
import streamlit as st
import sys
import os

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# 添加父目录到Python路径
sys.path.append(parent_dir)

# 导入自定义模块
try:
    from modules.user_import import UserImportSystem
    from modules.auth_system import AuthSystem
except ImportError as e:
    st.error(f"模块导入失败: {e}")
    st.error(f"当前目录: {current_dir}")
    raise

def main():
    """批量导入页面主函数"""
    # 检查登录状态
    auth = AuthSystem()
    if not auth.check_permission():
        st.warning("请先登录系统")
        return
    
    # 检查权限（仅管理员）
    user = auth.get_current_user()
    if user['role'] != 'admin':
        st.warning("⚠️ 只有管理员可以访问此页面")
        return
    
    # 显示批量导入页面
    st.title("📤 用户批量导入")
    st.markdown("---")
    

    # 创建导入系统实例并显示页面
    import_system = UserImportSystem()
    import_system.show()

if __name__ == "__main__":
    main()