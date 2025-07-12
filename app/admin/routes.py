from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import time
from app.models.db import (
    verify_admin_user, get_dashboard_stats, get_user_list, 
    get_usage_stats, log_user_login, log_system_usage
)


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'GET':
        return render_template('admin/login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('用户名和密码不能为空')
        return render_template('admin/login.html')
    
    
    admin_user = verify_admin_user(username, password)
    if admin_user:
        session['admin_id'] = admin_user[0]
        session['admin_username'] = admin_user[1]
        session['admin_role'] = admin_user[2]
        flash('登录成功')
        return redirect(url_for('admin.dashboard'))
    else:
        flash('用户名或密码错误')
        return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """管理员退出"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    session.pop('admin_role', None)
    flash('已退出登录')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """仪表板首页"""
    stats = get_dashboard_stats()
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@admin_required
def users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    user_data = get_user_list(page=page, per_page=20)
    return render_template('admin/users.html', user_data=user_data)

@admin_bp.route('/stats')
@admin_required
def stats():
    """统计分析"""
    days = request.args.get('days', 7, type=int)
    usage_stats = get_usage_stats(days=days)
    return render_template('admin/stats.html', usage_stats=usage_stats, days=days)

@admin_bp.route('/api/dashboard-stats')
@admin_required
def api_dashboard_stats():
    """API：获取仪表板统计数据"""
    stats = get_dashboard_stats()
    return jsonify(stats)

@admin_bp.route('/api/usage-chart')
@admin_required
def api_usage_chart():
    """API：获取使用趋势图表数据"""
    days = request.args.get('days', 7, type=int)
    usage_stats = get_usage_stats(days=days)
    
    
    chart_data = {
        'dates': [],
        'total_queries': [],
        'score_queries': [],
        'schedule_queries': [],
        'active_users': []
    }
    
    if usage_stats:
        for row in usage_stats:
            chart_data['dates'].append(str(row[0]))
            chart_data['total_queries'].append(row[1])
            chart_data['score_queries'].append(row[2])
            chart_data['schedule_queries'].append(row[3])
            chart_data['active_users'].append(row[4])
    
    return jsonify(chart_data)