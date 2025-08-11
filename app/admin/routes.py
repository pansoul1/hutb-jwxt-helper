from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import time
from app.models.db import (
    verify_admin_user, get_dashboard_stats, get_user_list, 
    get_usage_stats, log_user_login, log_system_usage
)

# 创建后台管理蓝图
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
    
    # 验证管理员
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
    
    # 格式化数据供图表使用
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

@admin_bp.route('/delete_user/<username>', methods=['POST'])
@admin_required
def delete_user(username):
    """删除用户"""
    try:
        # 导入删除用户的函数
        from app.models.db import delete_user_by_username
        
        # 执行删除操作
        success = delete_user_by_username(username)
        
        if success:
            # 记录删除操作日志
            log_system_usage(
                username=session.get('admin_username', 'admin'),
                action_type='delete_user',
                ip_address=request.remote_addr,
                success=True
            )
            
            return jsonify({
                'success': True,
                'message': f'用户 {username} 已成功删除'
            })
        else:
            # 记录删除失败日志
            log_system_usage(
                username=session.get('admin_username', 'admin'),
                action_type='delete_user',
                ip_address=request.remote_addr,
                success=False,
                error_message='用户不存在或数据库错误'
            )
            
            return jsonify({
                'success': False,
                'message': '删除失败：用户不存在或数据库错误'
            })
            
    except Exception as e:
        # 记录错误日志
        log_system_usage(
            username=session.get('admin_username', 'admin'),
            action_type='delete_user',
            ip_address=request.remote_addr,
            success=False,
            error_message=f'删除用户失败: {str(e)}'
        )
        
        return jsonify({
            'success': False,
            'message': f'删除失败：{str(e)}'
        })