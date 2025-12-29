# modules/user_import.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import logging
from typing import List, Dict, Tuple
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
    raise

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserImportSystem:
    """用户批量导入系统"""
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """初始化session状态"""
        if 'import_results' not in st.session_state:
            st.session_state.import_results = None
    
    def validate_import_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """验证导入数据的格式"""
        errors = []
        
        required_columns = ['username', 'real_name', 'role', 'unit', 'email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"缺少必需列: {', '.join(missing_columns)}")
            return False, errors
        
        for column in required_columns:
            if df[column].isnull().any():
                errors.append(f"{column}列存在空值")
        
        valid_roles = ['student', 'teacher', 'admin']
        invalid_roles = df[~df['role'].isin(valid_roles)]['role'].unique()
        if len(invalid_roles) > 0:
            errors.append(f"无效的角色值: {', '.join(invalid_roles)}")
        
        for _, row in df.iterrows():
            if pd.isna(row['username']):
                continue
                
            username = str(row['username']).strip()
            role = row['role']
            
            if role == 'student':
                if not username.isdigit() or len(username) != 13:
                    errors.append(f"学号格式错误: {username} (应为13位数字)")
            elif role in ['teacher', 'admin']:
                if not username.isdigit() or len(username) != 8:
                    errors.append(f"工号格式错误: {username} (应为8位数字)")
        
        return len(errors) == 0, errors
    
    def process_import_data(self, df: pd.DataFrame) -> Dict:
        """处理导入数据"""
        results = {
            'total': len(df),
            'success': 0,
            'failed': 0,
            'duplicate': 0,
            'success_records': [],
            'failed_records': [],
            'duplicate_records': []
        }
        
        for index, row in df.iterrows():
            try:
                user_data = {
                'username': str(row['username']).strip(),
                'password': str(row.get('password', '123456')).strip(),
                'role': row['role'].strip(),
                'real_name': str(row['real_name']).strip(),
                'unit': str(row['unit']).strip(),
                'email': str(row.get('email', '')).strip() if pd.notna(row.get('email')) else '',
                'phone': str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else ''
            }
                
                if db.user_exists(user_data['username']):
                    results['duplicate'] += 1
                    results['duplicate_records'].append({
                        'row': index + 2,
                        'username': user_data['username'],
                        'real_name': user_data['real_name'],
                        'reason': '用户已存在'
                    })
                    continue
                
                if db.create_user(user_data):
                    results['success'] += 1
                    results['success_records'].append({
                        'row': index + 2,
                        'username': user_data['username'],
                        'real_name': user_data['real_name'],
                        'role': user_data['role']
                    })
                else:
                    results['failed'] += 1
                    results['failed_records'].append({
                        'row': index + 2,
                        'username': user_data['username'],
                        'real_name': user_data['real_name'],
                        'reason': '创建用户失败'
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['failed_records'].append({
                    'row': index + 2,
                    'username': str(row['username']) if 'username' in row else '未知',
                    'real_name': str(row['real_name']) if 'real_name' in row else '未知',
                    'reason': str(e)
                })
        
        return results
    
    def generate_template(self):
        """生成导入模板"""
        template_data = {
            'username': ['2023000000001', '10000001', '20000001'],
            'real_name': ['张三', '李老师', '王管理员'],
            'role': ['student', 'teacher', 'admin'],
            'unit': ['计算机学院', '计算机学院', '教务处'],
            'password': ['123456', '123456', '123456'],
            'email': ['zhangsan@example.com', 'li@example.com', 'wang@example.com'],
            'phone': ['13800138001', '13800138002', '13800138003']
        }
        
        df = pd.DataFrame(template_data)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='用户模板')
        
        output.seek(0)
        return output
    
    def generate_report(self, results: Dict) -> str:
        """生成导入报告"""
        report = f"""
# 用户批量导入报告

## 📊 导入统计
- **总计**: {results['total']} 条记录
- **成功**: {results['success']} 条
- **失败**: {results['failed']} 条
- **重复**: {results['duplicate']} 条
- **成功率**: {results['success']/results['total']*100:.1f}%

"""
        
        if results['success_records']:
            report += "## ✅ 成功记录\n"
            report += "| 行号 | 学号/工号 | 姓名 | 角色 |\n"
            report += "|------|-----------|------|------|\n"
            for record in results['success_records']:
                report += f"| {record['row']} | {record['username']} | {record['real_name']} | {record['role']} |\n"
        
        if results['failed_records']:
            report += "\n## ❌ 失败记录\n"
            report += "| 行号 | 学号/工号 | 姓名 | 失败原因 |\n"
            report += "|------|-----------|------|----------|\n"
            for record in results['failed_records']:
                report += f"| {record['row']} | {record['username']} | {record['real_name']} | {record['reason']} |\n"
        
        if results['duplicate_records']:
            report += "\n## ⚠️ 重复记录\n"
            report += "| 行号 | 学号/工号 | 姓名 | 说明 |\n"
            report += "|------|-----------|------|------|\n"
            for record in results['duplicate_records']:
                report += f"| {record['row']} | {record['username']} | {record['real_name']} | {record['reason']} |\n"
        
        report += f"\n---\n*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def show(self):
        """显示批量导入页面"""
        # 显示说明和模板下载
        st.markdown("""
        ### 批量导入说明
        1. 下载导入模板
        2. 按照模板格式填写用户信息
        3. 上传填写好的Excel文件
        4. 系统将自动验证并导入用户数据
        """)
        
        # 模板下载
        col1, col2 = st.columns(2)
        with col1:
            template = self.generate_template()
            st.download_button(
                label="📥 下载导入模板",
                data=template,
                file_name="用户导入模板.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # 文件上传
        uploaded_file = st.file_uploader(
            "选择Excel文件",
            type=['xlsx', 'xls'],
            help="请上传按照模板格式填写的Excel文件"
        )
        
        if uploaded_file is not None:
            try:
                # 读取Excel文件
                df = pd.read_excel(uploaded_file)
                st.success(f"成功读取文件，共 {len(df)} 条记录")
                
                # 预览数据
                with st.expander("📋 数据预览"):
                    st.dataframe(df, use_container_width=True)
                
                # 验证数据
                st.subheader("🔍 数据验证")
                is_valid, errors = self.validate_import_data(df)
                
                if not is_valid:
                    st.error("数据验证失败：")
                    for error in errors:
                        st.error(f"- {error}")
                    return
                
                st.success("✅ 数据格式验证通过")
                
                # 导入按钮
                if st.button("🚀 开始导入", type="primary", use_container_width=True):
                    with st.spinner("正在导入用户数据..."):
                        results = self.process_import_data(df)
                        
                        # 保存结果到session
                        st.session_state.import_results = results
                        
                        # 显示结果统计
                        st.subheader("📊 导入结果")
                        
                        cols = st.columns(4)
                        cols[0].metric("总计", results['total'])
                        cols[1].metric("成功", results['success'], 
                                     delta=f"{results['success']/results['total']*100:.1f}%")
                        cols[2].metric("失败", results['failed'])
                        cols[3].metric("重复", results['duplicate'])
                        
                        # 生成报告
                        report = self.generate_report(results)
                        
                        # 下载报告
                        report_bytes = report.encode('utf-8')
                        st.download_button(
                            label="📥 下载导入报告",
                            data=report_bytes,
                            file_name=f"用户导入报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                        
                        # 显示详细报告
                        with st.expander("📄 查看详细报告"):
                            st.markdown(report)
                
            except Exception as e:
                st.error(f"文件处理失败：{str(e)}")
                logger.error(f"导入文件处理失败：{e}")