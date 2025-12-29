# CB_System

# 竞赛证书管理系统 - 用户认证模块

## 🎯 项目简介
基于 Streamlit 框架开发的竞赛证书智能识别与信息管理平台，本模块实现了完整的用户认证与批量导入系统。

## ✨ 功能特性

### 用户认证功能
- ✅ 三种角色注册（学生、教师、管理员）
- ✅ 学号/工号格式验证（13位/8位数字）
- ✅ 密码强度验证和 bcrypt 加密存储
- ✅ 用户登录与会话管理
- ✅ 基于角色的权限控制（RBAC）
- ✅ 用户操作日志记录

### 批量导入功能
- ✅ Excel 文件批量导入用户
- ✅ 数据格式自动验证
- ✅ 重复用户检测
- ✅ 详细导入报告生成
- ✅ 模板下载功能

## 🛠️ 技术栈
- **前端框架**: Streamlit
- **后端语言**: Python 3.9+
- **数据库**: MySQL 8.0
- **加密算法**: bcrypt
- **数据处理**: pandas, openpyxl
- **ORM**: SQLAlchemy

## 📋 系统要求
- Python 3.9+
- MySQL 8.0+
- 4GB RAM
- 1GB 可用磁盘空间

## 🚀 快速开始

### 1. 环境配置
```bash
# 克隆项目
git clone <repository-url>
cd cert-system

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```
