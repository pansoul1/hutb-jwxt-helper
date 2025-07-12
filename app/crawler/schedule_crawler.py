import requests
from app.models.db import get_user_cookies

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
            if self.username in user_schedule_sessions:
                self.session = user_schedule_sessions[self.username]
            else:
                self.session = requests.Session()
                user_schedule_sessions[self.username] = self.session
        else:
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
            self.username = username
            self.get_or_create_session()
            
            cookies = get_user_cookies(username)
            if not cookies:
                return False, "未找到用户cookies"
            
            for cookie_name, cookie_value in cookies.items():
                self.session.cookies.set(cookie_name, cookie_value)
            
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": self.base_url,
                "Origin": self.base_url
            })
            
            params = {}
            if semester:
                params["xnxq01id"] = semester
            
            response = self.session.post(self.schedule_url, data=params)
            
            if response.status_code == 200:
                return True, response.text
            else:
                return False, f"查询失败，状态码: {response.status_code}"
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"获取课表异常: {str(e)}"
    
def get_student_schedule_html(username, semester=None):
    """获取学生课表原始HTML的便捷函数"""
    user_schedule_crawler = ScheduleCrawler(username)
    return user_schedule_crawler.get_schedule_html(username, semester) 