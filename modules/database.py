# modules/database.py
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import bcrypt
import logging
from typing import Optional, Dict, Any, List

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Shen0315..',  # 请修改为实际密码
    'database': 'cert_system',
    'charset': 'utf8mb4'
}

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化数据库连接"""
        try:
            # 创建SQLAlchemy引擎
            connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
            self.engine = create_engine(
                connection_string,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
            
            # 创建session工厂
            self.SessionFactory = sessionmaker(bind=self.engine)
            self.Session = scoped_session(self.SessionFactory)
            
            # 测试连接
            self.test_connection()
            logger.info("数据库连接成功")
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise
    
    def test_connection(self):
        """测试数据库连接"""
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    
    @contextmanager
    def get_session(self):
        """获取数据库session的上下文管理器"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """执行查询语句"""
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            return []
    
    def execute_update(self, query: str, params: Optional[Dict] = None) -> int:
        """执行更新语句，返回影响的行数"""
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                session.commit()
                return result.rowcount
        except Exception as e:
            logger.error(f"更新执行失败: {e}")
            return 0
    
    def user_exists(self, username: str) -> bool:
        """检查用户是否存在"""
        query = "SELECT COUNT(*) as count FROM users WHERE username = :username"
        result = self.execute_query(query, {'username': username})
        return result[0]['count'] > 0 if result else False
    
    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """创建新用户"""
        try:
            # 检查用户名是否已存在
            if self.user_exists(user_data['username']):
                return False
            
            # 加密密码
            hashed_password = bcrypt.hashpw(
                user_data['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # 插入用户数据
            query = """
            INSERT INTO users (username, password, role, real_name, unit, email, phone)
            VALUES (:username, :password, :role, :real_name, :unit, :email, :phone)
            """
            
            params = {
                'username': user_data['username'],
                'password': hashed_password,
                'role': user_data['role'],
                'real_name': user_data.get('real_name', ''),
                'unit': user_data.get('unit', ''),
                'email': user_data.get('email', ''),
                'phone': user_data.get('phone', '')
            }
            
            return self.execute_update(query, params) > 0
            
        except Exception as e:
            logger.error(f"创建用户失败: {e}")
            return False
    
    def verify_user(self, username: str, password: str) -> Optional[Dict]:
        """验证用户登录"""
        try:
            query = """
            SELECT id, username, password, role, real_name, unit, email, is_active
            FROM users 
            WHERE username = :username AND is_active = TRUE
            """
            
            result = self.execute_query(query, {'username': username})
            
            if not result:
                return None
            
            user = result[0]
            
            # 验证密码
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                # 移除密码字段
                del user['password']
                
                # 更新最后登录时间
                update_query = "UPDATE users SET last_login = NOW() WHERE id = :id"
                self.execute_update(update_query, {'id': user['id']})
                
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"用户验证失败: {e}")
            return None
    
    def get_all_users(self, role: Optional[str] = None) -> List[Dict]:
        """获取所有用户（可按角色过滤）"""
        try:
            query = "SELECT id, username, role, real_name, unit, email, phone, created_at, last_login, is_active FROM users"
            params = {}
            
            if role:
                query += " WHERE role = :role"
                params['role'] = role
            
            query += " ORDER BY created_at DESC"
            
            return self.execute_query(query, params)
        except Exception as e:
            logger.error(f"获取用户列表失败: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户信息"""
        query = "SELECT id, username, role, real_name, unit, email, phone, created_at, last_login, is_active FROM users WHERE id = :id"
        result = self.execute_query(query, {'id': user_id})
        return result[0] if result else None
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """更新用户信息"""
        try:
            # 构建更新字段和参数
            update_fields = []
            params = {'id': user_id}
            
            # 允许更新的字段
            allowed_fields = ['real_name', 'unit', 'email', 'phone', 'role']
            
            for field in allowed_fields:
                if field in user_data:
                    update_fields.append(f"{field} = :{field}")
                    params[field] = user_data[field]
            
            if not update_fields:
                return True  # 没有需要更新的字段
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :id"
            return self.execute_update(query, params) > 0
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
            return False
    
    def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """重置用户密码"""
        try:
            # 加密新密码
            hashed_password = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            query = "UPDATE users SET password = :password WHERE id = :id"
            return self.execute_update(query, {'id': user_id, 'password': hashed_password}) > 0
            
        except Exception as e:
            logger.error(f"重置用户密码失败: {e}")
            return False
    
    def toggle_user_status(self, user_id: int) -> bool:
        """切换用户状态（启用/禁用）"""
        try:
            # 先获取当前状态
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 切换状态
            new_status = not user['is_active']
            query = "UPDATE users SET is_active = :is_active WHERE id = :id"
            return self.execute_update(query, {'id': user_id, 'is_active': new_status}) > 0
            
        except Exception as e:
            logger.error(f"切换用户状态失败: {e}")
            return False
    
    def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """更新用户状态"""
        query = "UPDATE users SET is_active = :is_active WHERE id = :id"
        return self.execute_update(query, {'id': user_id, 'is_active': is_active}) > 0
    
    def update_user_info(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """更新用户信息"""
        try:
            query = """
            UPDATE users SET 
                real_name = :real_name, 
                unit = :unit, 
                email = :email, 
                phone = :phone, 
                role = :role 
            WHERE id = :id
            """
            
            params = {
                'id': user_id,
                'real_name': update_data.get('real_name', ''),
                'unit': update_data.get('unit', ''),
                'email': update_data.get('email', ''),
                'phone': update_data.get('phone', ''),
                'role': update_data.get('role', 'student')
            }
            
            return self.execute_update(query, params) > 0
            
        except Exception as e:
            logger.error(f"更新用户信息失败: {e}")
            return False
    
    def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """重置用户密码"""
        try:
            # 加密新密码
            hashed_password = bcrypt.hashpw(
                new_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            query = "UPDATE users SET password = :password WHERE id = :id"
            return self.execute_update(query, {'id': user_id, 'password': hashed_password}) > 0
            
        except Exception as e:
            logger.error(f"重置用户密码失败: {e}")
            return False
    
    def log_user_action(self, user_id: int, action: str, details: str = '', 
                       ip_address: str = '', user_agent: str = ''):
        """记录用户操作日志"""
        query = """
        INSERT INTO user_logs (user_id, action, details, ip_address, user_agent)
        VALUES (:user_id, :action, :details, :ip_address, :user_agent)
        """
        
        params = {
            'user_id': user_id,
            'action': action,
            'details': details,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        
        self.execute_update(query, params)
    
    def save_uploaded_file(self, filename: str, file_path: str, file_type: str, 
                          file_size: int, user_id: int) -> bool:
        """保存上传文件信息到数据库"""
        query = """
        INSERT INTO files_uploads (filename, file_path, file_type, file_size, user_id)
        VALUES (:filename, :file_path, :file_type, :file_size, :user_id)
        """
        
        params = {
            'filename': filename,
            'file_path': file_path,
            'file_type': file_type,
            'file_size': file_size,
            'user_id': user_id
        }
        
        return self.execute_update(query, params) > 0
    
    def get_user_files(self, user_id: int) -> list:
        """获取用户的所有上传文件"""
        query = """
        SELECT id, filename, file_path, file_type, file_size, upload_time
        FROM files_uploads
        WHERE user_id = :user_id
        ORDER BY upload_time DESC
        """
        
        return self.execute_query(query, {'user_id': user_id})
    
    def get_file_by_id(self, file_id: int) -> dict:
        """根据ID获取文件信息"""
        query = """
        SELECT id, filename, file_path, file_type, file_size, upload_time, user_id
        FROM files_uploads
        WHERE id = :file_id
        """
        
        result = self.execute_query(query, {'file_id': file_id})
        return result[0] if result else None
    
    def get_user_certificates(self, user_id: int, role: str) -> List[Dict]:
        """获取用户的证书记录
        :param user_id: 用户ID
        :param role: 用户角色（student/teacher）
        :return: 证书记录列表
        """
        try:
            if role == 'student':
                # 学生：获取自己的证书记录
                query = """
                SELECT cr.*, fu.filename, fu.file_path, fu.file_type
                FROM certificate_records cr
                LEFT JOIN files_uploads fu ON cr.upload_file_id = fu.id
                WHERE cr.student_id = (SELECT username FROM users WHERE id = :user_id)
                ORDER BY cr.id DESC
                """
            else:  # teacher
                # 教师：获取自己指导的学生的证书记录
                query = """
                SELECT cr.*, fu.filename, fu.file_path, fu.file_type
                FROM certificate_records cr
                LEFT JOIN files_uploads fu ON cr.upload_file_id = fu.id
                WHERE cr.advisor_name = (SELECT real_name FROM users WHERE id = :user_id)
                ORDER BY cr.id DESC
                """
            
            return self.execute_query(query, {'user_id': user_id})
        except Exception as e:
            logger.error(f"获取证书记录失败: {e}")
            return []
    
    def get_user_certificates_by_username(self, username: str) -> List[Dict]:
        """根据用户名获取用户的证书记录
        :param username: 用户名（学号/工号）
        :return: 证书记录列表
        """
        try:
            query = """
            SELECT cr.*, fu.filename, fu.file_path, fu.file_type
            FROM certificate_records cr
            LEFT JOIN files_uploads fu ON cr.upload_file_id = fu.id
            WHERE cr.student_id = :username
            ORDER BY cr.id DESC
            """
            
            return self.execute_query(query, {'username': username})
        except Exception as e:
            logger.error(f"根据用户名获取证书记录失败: {e}")
            return []
    
    def save_certificate_record(self, student_college: str, competition_name: str, 
                               student_id: str, student_name: str, award_category: str, 
                               award_level: str, competition_type: str, organizing_unit: str, 
                               award_date: str, advisor_name: str, upload_file_id: int, 
                               user_id: int, status: str = 'draft') -> bool:
        """
        保存证书信息记录到数据库
        :param student_college: 学生所在学院
        :param competition_name: 竞赛项目
        :param student_id: 学号
        :param student_name: 学生姓名
        :param award_category: 获奖类别
        :param award_level: 获奖等级
        :param competition_type: 竞赛类型
        :param organizing_unit: 主办单位
        :param award_date: 获奖时间
        :param advisor_name: 指导教师
        :param upload_file_id: 关联的上传文件ID
        :param user_id: 操作用户ID
        :param status: 状态（draft/submitted）
        :return: 是否保存成功
        """
        try:
            # 确保award_date格式正确，如果格式不正确，使用NULL
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            # 允许空字符串，不将其转换为None
            if award_date and not re.match(date_pattern, award_date):
                award_date = None
            
            query = """
            INSERT INTO certificate_records (
                student_college, competition_name, student_id, student_name, 
                award_category, award_level, competition_type, organizing_unit, 
                award_date, advisor_name, upload_file_id, user_id, status
            ) VALUES (
                :student_college, :competition_name, :student_id, :student_name, 
                :award_category, :award_level, :competition_type, :organizing_unit, 
                :award_date, :advisor_name, :upload_file_id, :user_id, :status
            )
            """
            
            params = {
                'student_college': student_college,
                'competition_name': competition_name,
                'student_id': student_id,
                'student_name': student_name,
                'award_category': award_category,
                'award_level': award_level,
                'competition_type': competition_type,
                'organizing_unit': organizing_unit,
                'award_date': award_date,
                'advisor_name': advisor_name,
                'upload_file_id': upload_file_id,
                'user_id': user_id,
                'status': status
            }
            
            logger.info(f"准备保存证书记录，参数: {params}")
            result = self.execute_update(query, params)
            logger.info(f"保存证书记录结果: 影响行数 {result}")
            return result > 0
        except Exception as e:
            logger.error(f"保存证书记录失败: {e}", exc_info=True)
            return False
    
    def update_certificate(self, cert_id: int, student_id: str, student_name: str, 
                          student_college: str, competition_name: str, award_category: str, 
                          award_level: str, competition_type: str, organizing_unit: str, 
                          award_date: str, advisor_name: str) -> bool:
        """
        更新证书信息
        :param cert_id: 证书ID
        :param student_id: 学号
        :param student_name: 学生姓名
        :param student_college: 学生所在学院
        :param competition_name: 竞赛项目
        :param award_category: 获奖类别
        :param award_level: 获奖等级
        :param competition_type: 竞赛类型
        :param organizing_unit: 主办单位
        :param award_date: 获奖时间
        :param advisor_name: 指导教师
        :return: 是否更新成功
        """
        try:
            # 确保award_date格式正确，如果格式不正确，使用NULL
            import re
            date_pattern = r'^\d{4}-\d{2}-\d{2}$'
            # 允许空字符串，不将其转换为None
            if award_date and not re.match(date_pattern, award_date):
                award_date = None
            
            query = """
            UPDATE certificate_records SET 
                student_id = :student_id, 
                student_name = :student_name, 
                student_college = :student_college, 
                competition_name = :competition_name, 
                award_category = :award_category, 
                award_level = :award_level, 
                competition_type = :competition_type, 
                organizing_unit = :organizing_unit, 
                award_date = :award_date, 
                advisor_name = :advisor_name,
                updated_at = NOW()
            WHERE id = :cert_id AND status = 'draft'  -- 只允许更新草稿状态的证书
            """
            
            params = {
                'cert_id': cert_id,
                'student_id': student_id,
                'student_name': student_name,
                'student_college': student_college,
                'competition_name': competition_name,
                'award_category': award_category,
                'award_level': award_level,
                'competition_type': competition_type,
                'organizing_unit': organizing_unit,
                'award_date': award_date,
                'advisor_name': advisor_name
            }
            
            logger.info(f"准备更新证书记录，参数: {params}")
            result = self.execute_update(query, params)
            logger.info(f"更新证书记录结果: 影响行数 {result}")
            return result > 0
        except Exception as e:
            logger.error(f"更新证书记录失败: {e}", exc_info=True)
            return False
    
    def submit_certificate(self, cert_id: int) -> bool:
        """
        提交证书，将状态从draft改为submitted
        :param cert_id: 证书ID
        :return: 是否提交成功
        """
        try:
            query = """
            UPDATE certificate_records SET 
                status = 'submitted',
                updated_at = NOW()
            WHERE id = :cert_id AND status = 'draft'  -- 只允许提交草稿状态的证书
            """
            
            params = {
                'cert_id': cert_id
            }
            
            logger.info(f"准备提交证书，参数: {params}")
            result = self.execute_update(query, params)
            logger.info(f"提交证书结果: 影响行数 {result}")
            return result > 0
        except Exception as e:
            logger.error(f"提交证书失败: {e}", exc_info=True)
            return False
    
    def get_all_certificates(self, status: str = None) -> List[Dict]:
        """
        获取所有用户的证书数据（管理员用）
        :param status: 证书状态过滤，可选值：draft, submitted, 或 None（全部）
        :return: 证书记录列表
        """
        try:
            query = """
            SELECT cr.*, fu.filename, fu.file_path, fu.file_type
            FROM certificate_records cr
            LEFT JOIN files_uploads fu ON cr.upload_file_id = fu.id
            """
            
            params = {}
            
            # 添加状态过滤条件
            if status:
                query += " WHERE cr.status = :status"
                params['status'] = status
            
            # 添加排序
            query += " ORDER BY cr.id DESC"
            
            return self.execute_query(query, params)
        except Exception as e:
            logger.error(f"获取所有证书记录失败: {e}", exc_info=True)
            return []

# 创建全局数据库实例
db = Database()