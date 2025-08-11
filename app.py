from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import pymysql
import json
import requests
import time
import hashlib
import logging
from datetime import timedelta
from app.crawler.login import LoginManager
from app.crawler.score_crawler import get_student_scores_html
from app.crawler.schedule_crawler import get_student_schedule_html
from app.models.db import log_user_login, log_system_usage, get_user_by_username
import traceback

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('app')

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# 配置Flask应用 - 使用固定的secret_key代替动态生成
app.secret_key = "hutb_jwxt_secret_key_2024"  # 固定密钥

# 配置会话
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # 会话有效期

# 优先使用Redis作为会话存储，如果不可用则使用文件系统
try:
    import redis
    from flask_session import Session
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_REDIS'] = redis.Redis(host='localhost', port=6379, db=0)
    Session(app)
    print("使用Redis作为会话存储")
except ImportError:
    try:
        from flask_session import Session
        app.config['SESSION_TYPE'] = 'filesystem'
        
        # 确保会话文件存储在有写权限的目录
        session_dir = '/tmp/flask_session'
        if not os.path.exists(session_dir):
            try:
                os.makedirs(session_dir)
            except:
                session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
                if not os.path.exists(session_dir):
                    os.makedirs(session_dir)
        
        app.config['SESSION_FILE_DIR'] = session_dir
        Session(app)
        print(f"使用文件系统作为会话存储，路径：{session_dir}")
    except Exception as e:
        print(f"配置文件系统会话存储失败：{str(e)}")
        print("回退到默认会话管理（不推荐用于生产环境）")
        app.config['SESSION_TYPE'] = None

# 配置OpenAI
DASHSCOPE_API_KEY = "sk-863f29755e2c44b190836b2587fdd3e0"

# 注册后台管理蓝图
from app.admin.routes import admin_bp
app.register_blueprint(admin_bp)

# 注册忘记密码蓝图
from app.password_reset import password_reset_bp
app.register_blueprint(password_reset_bp)

# 数据库配置在db.py中已设置，密码加密使用password_crypto.py

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@app.route('/process_login', methods=['POST'])
def process_login():
    start_time = time.time()
    
    # 获取客户端信息
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.headers.get('User-Agent')
    
    # 生成设备标识符
    device_id = hashlib.md5(f"{ip_address}:{user_agent}".encode()).hexdigest()
    
    # 处理登录
    from app.crawler.login import handle_login_request
    result = handle_login_request()
    
    # 记录登录日志
    if 'username' in session:
        username = session['username']
        status = 'success'
        log_user_login(username, ip_address, user_agent, status, device_id, 'password')
        
        # 添加设备标识符到会话
        session['device_id'] = device_id
        # 使用设备ID和用户名组合作为会话标识符
        session['session_id'] = f"{username}_{device_id}"
        
        # 强制保存会话
        session.modified = True
    
    return result

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('请先登录')
        return redirect(url_for('login'))
    
    username = session['username']
    
    # 验证会话是否完整
    if 'device_id' not in session or 'session_id' not in session:
        device_id = hashlib.md5(f"{request.environ.get('REMOTE_ADDR')}:{request.headers.get('User-Agent')}".encode()).hexdigest()
        session['device_id'] = device_id
        session['session_id'] = f"{username}_{device_id}"
        session.modified = True
    
    # 获取用户真实姓名
    try:
        from app.models.db import get_user_real_name
        real_name = get_user_real_name(username)
    except Exception as e:
        real_name = None
    
    # 如果无法获取真实姓名，则使用用户名代替
    if not real_name:
        real_name = username
    
    return render_template('dashboard.html', username=username, real_name=real_name)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('device_id', None)
    session.pop('session_id', None)
    session.modified = True
    flash('已退出登录')
    return redirect(url_for('login'))

# 添加一个路由来显示当前会话信息（调试用）
@app.route('/debug/session')
def debug_session():
    if not app.debug:
        return "只在调试模式可用", 403
    return jsonify({
        'session_data': dict(session),
        'session_type': app.config.get('SESSION_TYPE'),
        'session_file_dir': app.config.get('SESSION_FILE_DIR'),
    })

# 添加成绩查询API
@app.route('/api/scores', methods=['GET'])
def get_scores():
    if 'username' not in session:
        return jsonify({"success": False, "message": "请先登录"}), 401
    
    username = session['username']
    device_id = session.get('device_id')
    session_id = session.get('session_id')
    print(f"成绩查询API: 用户 {username}, 设备ID {device_id}, 会话ID {session_id}")  # 调试日志
    
    semester = request.args.get('semester', None)
    start_time = time.time()
    
    # 获取客户端信息
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    
    # 确保用户名与当前会话匹配
    if not session_id or not session_id.startswith(f"{username}_"):
        return jsonify({"success": False, "message": "会话已失效，请重新登录"}), 401
    
    success, result = get_student_scores_html(username, semester)
    
    # 计算响应时间
    response_time = int((time.time() - start_time) * 1000)
    
    # 记录使用日志
    log_system_usage(
        username=username,
        action_type='score_query',
        semester=semester,
        ip_address=ip_address,
        response_time=response_time,
        success=success,
        error_message=None if success else result
    )
    
    if success:
        return jsonify({"success": True, "html": result})
    else:
        return jsonify({"success": False, "message": result}), 500

# 添加课表查询API
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    if 'username' not in session:
        return jsonify({"success": False, "message": "请先登录"}), 401
    
    username = session['username']
    device_id = session.get('device_id')
    session_id = session.get('session_id')
    print(f"课表查询API: 用户 {username}, 设备ID {device_id}, 会话ID {session_id}")  # 调试日志
    
    semester = request.args.get('semester', None)
    start_time = time.time()
    
    # 获取客户端信息
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    
    # 确保用户名与当前会话匹配
    if not session_id or not session_id.startswith(f"{username}_"):
        return jsonify({"success": False, "message": "会话已失效，请重新登录"}), 401
    
    success, result = get_student_schedule_html(username, semester)
    
    # 计算响应时间
    response_time = int((time.time() - start_time) * 1000)
    
    # 记录使用日志
    log_system_usage(
        username=username,
        action_type='schedule_query',
        semester=semester,
        ip_address=ip_address,
        response_time=response_time,
        success=success,
        error_message=None if success else result
    )
    
    if success:
        return jsonify({"success": True, "html": result})
    else:
        return jsonify({"success": False, "message": result}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 