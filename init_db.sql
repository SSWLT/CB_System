-- 创建数据库
CREATE DATABASE IF NOT EXISTS cert_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cert_system;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(20) UNIQUE NOT NULL COMMENT '学号/工号',
    password VARCHAR(255) NOT NULL COMMENT '加密后的密码',
    role ENUM('student', 'teacher', 'admin') NOT NULL COMMENT '用户角色',
    real_name VARCHAR(50) NOT NULL COMMENT '真实姓名',
    unit VARCHAR(100) COMMENT '所属学院或部门',
    email VARCHAR(100) COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '电话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建默认管理员账户（密码：admin123）
INSERT INTO users (username, password, role, real_name, unit, email, is_active) 
VALUES ('00000000', '$12$uKuX7r9e4s7gmuDK4tsaP.Lwcejmxrc606.KKOPs7vsE1O0TUsVxS', 'admin', '系统管理员','人计学院', 'admin@example.com', TRUE);

-- 用户操作日志表
CREATE TABLE IF NOT EXISTS user_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    action VARCHAR(50) NOT NULL COMMENT '操作类型',
    details TEXT COMMENT '操作详情',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 文件上传表
CREATE TABLE IF NOT EXISTS files_uploads (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(255) NOT NULL COMMENT '文件路径',
    file_type VARCHAR(50) NOT NULL COMMENT '文件类型',
    file_size INT NOT NULL COMMENT '文件大小(字节)',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 证书信息表
CREATE TABLE IF NOT EXISTS certificate_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    student_college VARCHAR(100) COMMENT '学生所在学院',
    competition_name VARCHAR(255) COMMENT '竞赛项目',
    student_id VARCHAR(20) NOT NULL COMMENT '学号',
    student_name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    award_category VARCHAR(20) COMMENT '获奖类别',
    award_level VARCHAR(20) COMMENT '获奖等级',
    competition_type VARCHAR(10) COMMENT '竞赛类型',
    organizing_unit VARCHAR(255) COMMENT '主办单位',
    award_date DATE COMMENT '获奖时间',
    advisor_name VARCHAR(50) NOT NULL COMMENT '指导教师',
    upload_file_id INT NOT NULL COMMENT '关联上传文件ID',
    user_id INT NOT NULL COMMENT '上传用户ID',
    status ENUM('draft', 'submitted') DEFAULT 'draft' COMMENT '状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (upload_file_id) REFERENCES files_uploads(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;