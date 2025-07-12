import requests
from app.models.db import get_user_cookies

# 用户会话管理字典：存储每个用户的专用爬虫会话
user_schedule_sessions = {}

class ScheduleCrawler:
    """课表爬虫，用于获取学生课表原始数据"""
    
    def __init__(self, username=None):
        """
        初始化课表爬虫
        
        参数:
            username: 用户名，如果提供则创建用户专属会话
        """
        self.username = username
        self.session = None
        self.get_or_create_session()
        
        self.base_url = "http://jwgl.hutb.edu.cn"
        self.schedule_url = f"{self.base_url}/jsxsd/xskb/xskb_list.do"
    
    def get_or_create_session(self):
        """获取或创建用户专属会话"""
        global user_schedule_sessions
        
        if self.username:
            # 如果用户会话已存在，使用现有会话
            if self.username in user_schedule_sessions:
                self.session = user_schedule_sessions[self.username]
            else:
                # 否则创建新会话
                self.session = requests.Session()
                # 存储到全局字典
                user_schedule_sessions[self.username] = self.session
        else:
            # 未提供用户名时创建临时会话
            self.session = requests.Session()
    
    def get_schedule_html(self, username, semester=None):
        """
        获取学生课表原始HTML数据
        
        参数:
            username: 学生学号
            semester: 学期，例如"2024-2025-2"
            
        返回:
            (success, data): 是否成功及数据(HTML或错误信息)
        """
        try:
            # 更新当前用户和会话
            self.username = username
            self.get_or_create_session()
            
            # 从数据库获取用户的cookies
            cookies = get_user_cookies(username)
            if not cookies:
                return False, "未找到用户cookies"
            
            # 设置cookies
            for cookie_name, cookie_value in cookies.items():
                self.session.cookies.set(cookie_name, cookie_value)
            
            # 设置请求头
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": self.base_url,
                "Origin": self.base_url
            })
            
            # 构建请求参数
            params = {}
            if semester:
                params["xnxq01id"] = semester
            
            # 发送请求
            response = self.session.post(self.schedule_url, data=params)
            
            # 检查响应
            if response.status_code == 200:
                # 返回原始HTML
                return True, response.text
            else:
                return False, f"查询失败，状态码: {response.status_code}"
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"获取课表异常: {str(e)}"
    
# 修改为提供特定于用户的爬虫
def get_student_schedule_html(username, semester=None):
    """获取学生课表原始HTML的便捷函数"""
    # 为用户创建专属爬虫实例
    user_schedule_crawler = ScheduleCrawler(username)
    return user_schedule_crawler.get_schedule_html(username, semester) 