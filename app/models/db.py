import pymysql
import json
import traceback

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='newhutb',
        charset='utf8mb4'
    )

def init_database():
    """初始化数据库表"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 创建users表（如果不存在）
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                encrypted_password TEXT,
                raw_password VARCHAR(255),
                cookies TEXT,
                ticket1 TEXT,
                ticket1_expiry TIMESTAMP NULL,
                real_name VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建管理员表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin', 'super_admin') DEFAULT 'admin',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
            ''')
            
            # 创建用户登录日志表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_login_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT,
                status ENUM('success', 'failed') DEFAULT 'success',
                INDEX idx_username (username),
                INDEX idx_login_time (login_time)
            )
            ''')
            
            # 创建系统使用日志表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_usage_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                action_type ENUM('score_query', 'schedule_query') NOT NULL,
                semester VARCHAR(20),
                query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                response_time INT COMMENT '响应时间(毫秒)',
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                INDEX idx_username (username),
                INDEX idx_action_type (action_type),
                INDEX idx_query_time (query_time)
            )
            ''')
            
            # 创建系统统计表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                stat_date DATE UNIQUE NOT NULL,
                total_users INT DEFAULT 0,
                active_users INT DEFAULT 0,
                score_queries INT DEFAULT 0,
                schedule_queries INT DEFAULT 0,
                total_queries INT DEFAULT 0,
                avg_response_time FLOAT DEFAULT 0,
                error_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 检查现有列，如果不存在则添加
            # 检查ticket1列
            cursor.execute('''
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'users' 
            AND column_name = 'ticket1'
            ''')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN ticket1 TEXT,
                ADD COLUMN ticket1_expiry TIMESTAMP NULL
                ''')
            
            # 检查real_name列
            cursor.execute('''
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'users' 
            AND column_name = 'real_name'
            ''')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN real_name VARCHAR(50)
                ''')
            
            # 检查raw_password列
            cursor.execute('''
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'users' 
            AND column_name = 'raw_password'
            ''')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN raw_password VARCHAR(255)
                ''')
            
            # 插入默认管理员账号（如果不存在）
            cursor.execute('SELECT COUNT(*) FROM admin_users WHERE username = %s', ('pansoul',))
            if cursor.fetchone()[0] == 0:
                # 默认密码: psy030413，使用简单的哈希
                import hashlib
                password_hash = hashlib.sha256('psy030413'.encode()).hexdigest()
                cursor.execute('''
                INSERT INTO admin_users (username, password_hash, role) 
                VALUES (%s, %s, %s)
                ''', ('pansoul', password_hash, 'super_admin'))
            
            # 删除旧的admin账号（如果存在）
            cursor.execute('DELETE FROM admin_users WHERE username = %s', ('admin',))
            
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def save_user_credentials(username, encrypted_password, cookies, raw_password=None):
    """
    将用户名、加密后的密码、原始密码和cookies保存到数据库
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 将cookies转换为JSON字符串存储
            cookies_str = json.dumps(cookies)
            
            # 检查表中是否已有raw_password列
            cursor.execute('''
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'users' 
            AND column_name = 'raw_password'
            ''')
            
            if cursor.fetchone()[0] == 0:
                # 添加raw_password列
                cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN raw_password VARCHAR(255)
                ''')
            
            # 插入或更新用户凭据
            cursor.execute('''
            INSERT INTO users (username, encrypted_password, raw_password, cookies) 
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            encrypted_password = VALUES(encrypted_password),
            raw_password = VALUES(raw_password),
            cookies = VALUES(cookies)
            ''', (username, encrypted_password, raw_password, cookies_str))
        
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def get_user_by_username(username):
    """
    通过用户名获取用户信息
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
        connection.close()
        return user
    except Exception as e:
        traceback.print_exc()
        return None

def save_user_cookies(username, cookies):
    """
    专门用于保存用户的cookies
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 将cookies转换为JSON字符串存储
            cookies_str = json.dumps(cookies)
            
            # 直接插入，如遇主键冲突则更新，避免由于 UPDATE 未改变内容 rowcount 为 0 而导致的误判
            cursor.execute('''
            INSERT INTO users (username, cookies)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            cookies = VALUES(cookies)
            ''', (username, cookies_str))
        
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def get_user_cookies(username):
    """
    获取用户的cookies
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT cookies FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
        connection.close()
        
        if result and result[0]:
            return json.loads(result[0])
        return None
    except Exception as e:
        traceback.print_exc()
        return None

def save_user_ticket1(username, ticket1, expiry_hours=24):
    """
    保存用户的ticket1和过期时间
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 设置过期时间
            cursor.execute('''
            UPDATE users SET 
            ticket1 = %s,
            ticket1_expiry = DATE_ADD(NOW(), INTERVAL %s HOUR)
            WHERE username = %s
            ''', (ticket1, expiry_hours, username))
            
            # 如果用户不存在，则创建新用户
            if cursor.rowcount == 0:
                cursor.execute('''
                INSERT INTO users (username, ticket1, ticket1_expiry) 
                VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL %s HOUR))
                ''', (username, ticket1, expiry_hours))
        
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def get_user_ticket1(username):
    """
    获取用户的ticket1，如果已过期则返回None
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
            SELECT ticket1, ticket1_expiry 
            FROM users 
            WHERE username = %s AND ticket1 IS NOT NULL AND ticket1_expiry > NOW()
            ''', (username,))
            result = cursor.fetchone()
        connection.close()
        
        if result:
            return result[0]  # 返回ticket1
        return None
    except Exception as e:
        traceback.print_exc()
        return None

def save_user_real_name(username, real_name):
    """
    保存用户的真实姓名
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 使用INSERT...ON DUPLICATE KEY UPDATE语法避免主键冲突
            cursor.execute('''
            INSERT INTO users (username, real_name) 
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE 
            real_name = VALUES(real_name)
            ''', (username, real_name))
        
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def save_user_raw_password(username, raw_password):
    """
    保存用户的明文密码
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
            UPDATE users SET raw_password = %s WHERE username = %s
            ''', (raw_password, username))
            
            # 如果用户不存在，创建新记录
            if cursor.rowcount == 0:
                cursor.execute('''
                INSERT IGNORE INTO users (username, raw_password) VALUES (%s, %s)
                ''', (username, raw_password))
        
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def get_user_real_name(username):
    """
    获取用户的真实姓名
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT real_name FROM users WHERE username = %s', (username,))
            result = cursor.fetchone()
        connection.close()
        
        if result and result[0]:
            return result[0]
        return None
    except Exception as e:
        traceback.print_exc()
        return None

# ========== 后台管理相关函数 ==========

def verify_admin_user(username, password):
    """验证管理员登录"""
    try:
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
            SELECT id, username, role, is_active 
            FROM admin_users 
            WHERE username = %s AND password_hash = %s AND is_active = TRUE
            ''', (username, password_hash))
            result = cursor.fetchone()
            
            if result:
                # 更新最后登录时间
                cursor.execute('''
                UPDATE admin_users SET last_login = NOW() WHERE id = %s
                ''', (result[0],))
                connection.commit()
        
        connection.close()
        return result
    except Exception as e:
        traceback.print_exc()
        return None

def log_user_login(username, ip_address, user_agent, status='success'):
    """记录用户登录日志"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
            INSERT INTO user_login_logs (username, ip_address, user_agent, status) 
            VALUES (%s, %s, %s, %s)
            ''', (username, ip_address, user_agent, status))
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def log_system_usage(username, action_type, semester=None, ip_address=None, response_time=None, success=True, error_message=None):
    """记录系统使用日志"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('''
            INSERT INTO system_usage_logs 
            (username, action_type, semester, ip_address, response_time, success, error_message) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (username, action_type, semester, ip_address, response_time, success, error_message))
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        traceback.print_exc()
        return False

def get_dashboard_stats():
    """获取仪表板统计数据"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 总用户数
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # 今日活跃用户数
            cursor.execute('''
            SELECT COUNT(DISTINCT username) 
            FROM user_login_logs 
            WHERE DATE(login_time) = CURDATE()
            ''')
            today_active_users = cursor.fetchone()[0]
            
            # 今日查询次数
            cursor.execute('''
            SELECT COUNT(*) 
            FROM system_usage_logs 
            WHERE DATE(query_time) = CURDATE()
            ''')
            today_queries = cursor.fetchone()[0]
            
            # 今日错误次数
            cursor.execute('''
            SELECT COUNT(*) 
            FROM system_usage_logs 
            WHERE DATE(query_time) = CURDATE() AND success = FALSE
            ''')
            today_errors = cursor.fetchone()[0]
            
            # 平均响应时间
            cursor.execute('''
            SELECT AVG(response_time) 
            FROM system_usage_logs 
            WHERE DATE(query_time) = CURDATE() AND response_time IS NOT NULL
            ''')
            avg_response_time = cursor.fetchone()[0] or 0
            
        connection.close()
        
        return {
            'total_users': total_users,
            'today_active_users': today_active_users,
            'today_queries': today_queries,
            'today_errors': today_errors,
            'avg_response_time': round(float(avg_response_time), 2)
        }
    except Exception as e:
        traceback.print_exc()
        return None

def get_user_list(page=1, per_page=20):
    """获取用户列表"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            offset = (page - 1) * per_page
            
            cursor.execute('''
            SELECT u.username, u.real_name, u.raw_password, u.encrypted_password, u.created_at,
                   (SELECT MAX(login_time) FROM user_login_logs WHERE username = u.username) as last_login,
                   (SELECT COUNT(*) FROM system_usage_logs WHERE username = u.username) as total_queries
            FROM users u
            ORDER BY u.created_at DESC
            LIMIT %s OFFSET %s
            ''', (per_page, offset))
            users = cursor.fetchall()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) FROM users')
            total = cursor.fetchone()[0]
            
        connection.close()
        
        return {
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    except Exception as e:
        traceback.print_exc()
        return None

def get_usage_stats(days=7):
    """获取使用统计数据"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 获取最近N天的查询统计
            cursor.execute('''
            SELECT DATE(query_time) as date,
                   COUNT(*) as total_queries,
                   SUM(CASE WHEN action_type = 'score_query' THEN 1 ELSE 0 END) as score_queries,
                   SUM(CASE WHEN action_type = 'schedule_query' THEN 1 ELSE 0 END) as schedule_queries,
                   COUNT(DISTINCT username) as active_users,
                   AVG(response_time) as avg_response_time
            FROM system_usage_logs 
            WHERE query_time >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            GROUP BY DATE(query_time)
            ORDER BY date DESC
            ''', (days,))
            usage_stats = cursor.fetchall()
            
        connection.close()
        return usage_stats
    except Exception as e:
        traceback.print_exc()
        return None

# 初始化数据库
init_database() 