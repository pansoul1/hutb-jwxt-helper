import requests
import traceback
import logging
from app.models.db import get_user_cookies

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('score_crawler_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('score_crawler')

# 用户会话管理字典：存储每个用户的专用爬虫会话
user_score_sessions = {}

class ScoreCrawler:
    """成绩爬虫，用于获取学生成绩原始数据"""
    
    def __init__(self, username=None):
        """
        初始化成绩爬虫
        
        参数:
            username: 用户名，如果提供则创建用户专属会话
        """
        self.username = username
        self.session = None
        self.get_or_create_session()
        
        self.base_url = "http://jwgl.hutb.edu.cn"
        self.score_url = f"{self.base_url}/jsxsd/kscj/cjcx_list"
        self.query_url = f"{self.base_url}/jsxsd/kscj/cjcx_query?Ves632DSdyV=NEW_XSD_XJCJ"
        
        logger.debug(f"初始化ScoreCrawler，用户名：{username}")
    
    def get_or_create_session(self):
        """获取或创建用户专属会话"""
        global user_score_sessions
        
        if self.username:
            logger.debug(f"为用户 {self.username} 获取或创建成绩查询会话")
            # 如果用户会话已存在，使用现有会话
            if self.username in user_score_sessions:
                logger.debug(f"使用用户 {self.username} 的现有成绩查询会话")
                self.session = user_score_sessions[self.username]
            else:
                # 否则创建新会话
                logger.debug(f"为用户 {self.username} 创建新的成绩查询会话")
                self.session = requests.Session()
                # 存储到全局字典
                user_score_sessions[self.username] = self.session
        else:
            # 未提供用户名时创建临时会话
            logger.debug("创建临时成绩查询会话（无用户名）")
            self.session = requests.Session()
    
    def get_scores_html(self, username, semester=None, course_type=None, course_name=None, display_mode=None):
        """
        获取学生成绩原始HTML数据
        
        参数:
            username: 学生学号
            semester: 学期，例如"2024-2025-2"
            course_type: 课程性质
            course_name: 课程名称
            display_mode: 显示方式
            
        返回:
            (success, data): 是否成功及数据(HTML或错误信息)
        """
        try:
            # 更新当前用户和会话
            self.username = username
            self.get_or_create_session()
            
            logger.info(f"尝试获取学号 {username} 的成绩数据，学期: {semester}")
            
            # 从数据库获取用户的cookies
            cookies = get_user_cookies(username)
            if not cookies:
                logger.error(f"未找到学号 {username} 的cookies")
                return False, "未找到用户cookies"
            
            # 记录cookies信息
            logger.debug(f"用户 {username} 的cookies键: {list(cookies.keys())}")
            
            # 设置cookies
            for cookie_name, cookie_value in cookies.items():
                self.session.cookies.set(cookie_name, cookie_value)
                logger.debug(f"设置cookie: {cookie_name}={cookie_value[:10] if cookie_value and len(cookie_value) > 10 else cookie_value}...")
            
            # 设置请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": self.query_url,
                "Origin": self.base_url,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
            self.session.headers.update(headers)
            logger.debug("已设置HTTP请求头")
            
            # 构建请求参数
            params = {}
            if semester:
                params["kksj"] = semester
            if course_type:
                params["kcxz"] = course_type
            if course_name:
                params["kcmc"] = course_name
            if display_mode:
                params["xsfs"] = display_mode
            else:
                params["xsfs"] = "all"
            
            logger.debug(f"发送成绩查询请求，参数: {params}")
            
            # 发送请求
            logger.debug(f"POST请求URL: {self.score_url}")
            response = self.session.post(self.score_url, data=params)
            
            # 检查响应
            logger.debug(f"成绩查询响应状态码: {response.status_code}")
            logger.debug(f"响应头: {dict(response.headers)}")
            
            if response.status_code == 200:
                html_content = response.text
                logger.debug(f"成功获取成绩HTML，长度: {len(html_content)} 字符")
                
                # 检查是否是重定向到登录页面
                if "请登录" in html_content or "login" in response.url.lower():
                    logger.error(f"会话已过期，已重定向到登录页面: {response.url}")
                    # 记录HTML的前500个字符，帮助诊断问题
                    logger.debug(f"HTML前500个字符: {html_content[:500]}")
                    return False, "会话已过期，请重新登录"
                
                # 检查HTML内容是否有效
                if "课程成绩查询" in html_content or "学生个人考试成绩" in html_content:
                    # 记录HTML的前500个字符，确认内容正常
                    logger.debug(f"有效成绩HTML前500个字符: {html_content[:500]}")
                    # 返回原始HTML
                    return True, html_content
                else:
                    logger.error("成绩HTML内容无效，可能是cookie已过期")
                    # 记录HTML的前500个字符，帮助诊断问题
                    logger.debug(f"无效HTML前500个字符: {html_content[:500]}")
                    return False, "无法获取有效成绩数据，cookie可能已过期"
            else:
                logger.error(f"查询失败，状态码: {response.status_code}")
                return False, f"查询失败，状态码: {response.status_code}"
        
        except Exception as e:
            logger.error(f"获取成绩异常: {str(e)}")
            traceback.print_exc()
            return False, f"获取成绩异常: {str(e)}"

# 修改为提供特定于用户的爬虫
def get_student_scores_html(username, semester=None, course_type=None, course_name=None, display_mode=None):
    """获取学生成绩原始HTML的便捷函数"""
    logger.info(f"开始获取学生 {username} 的成绩HTML，学期: {semester}")
    # 为用户创建专属爬虫实例
    user_score_crawler = ScoreCrawler(username)
    return user_score_crawler.get_scores_html(username, semester, course_type, course_name, display_mode)