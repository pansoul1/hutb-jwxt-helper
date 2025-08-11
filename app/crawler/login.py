import requests
import json
import uuid
import traceback
import os
import base64
from io import BytesIO
from PIL import Image
from openai import OpenAI
from flask import session, request, redirect, url_for, flash
import time, tempfile
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('login_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('login')

# 导入密码加密模块
from app.crawler.password_crypto import encrypt_password

# 用户会话管理字典：存储每个用户的专用爬虫会话
user_sessions = {}

class LoginManager:
    """登录管理器，负责处理登录流程"""
    
    def __init__(self, username=None):
        """
        初始化登录管理器
        
        参数:
            username: 用户名，如果提供则创建用户专属会话
        """
        self.session = None
        self.username = username
        self.base_url = "https://cas.hutb.edu.cn/lyuapServer"
        self.login_url = f"{self.base_url}/v1/tickets"
        self.service_url = "http://jwgl.hutb.edu.cn/"
        
        # 获取或创建用户专属会话
        self.get_or_create_session()
        
        # 初始化OpenAI客户端，用于验证码识别
        self.ai_client = OpenAI(
            api_key="sk-863f29755e2c44b190836b2587fdd3e0",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 存储会话状态
        self.is_logged_in = False
        self.cookies = {}
        
        logger.debug(f"初始化LoginManager，用户名：{username}")
        
    def get_or_create_session(self):
        """获取或创建用户专属会话"""
        global user_sessions
        
        if self.username:
            logger.debug(f"为用户 {self.username} 获取或创建会话")
            # 如果用户会话已存在，使用现有会话
            if self.username in user_sessions:
                logger.debug(f"使用用户 {self.username} 的现有会话")
                self.session = user_sessions[self.username]
            else:
                # 否则创建新会话
                logger.debug(f"创建用户 {self.username} 的新会话")
                self.session = requests.Session()
                
                # 设置请求头
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'Origin': 'https://cas.hutb.edu.cn',
                    'Referer': 'https://cas.hutb.edu.cn/lyuapServer/login?service=http%3A%2F%2Fjwgl.hutb.edu.cn%2F'
                })
                
                # 存储到全局字典
                user_sessions[self.username] = self.session
        else:
            # 未提供用户名时创建临时会话
            logger.debug("创建临时会话（无用户名）")
            self.session = requests.Session()
            
            # 设置请求头
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'Origin': 'https://cas.hutb.edu.cn',
                'Referer': 'https://cas.hutb.edu.cn/lyuapServer/login?service=http%3A%2F%2Fjwgl.hutb.edu.cn%2F'
            })
            
    def recognize_captcha(self, captcha_base64):
        """使用AI识别算术验证码"""
        try:
            # 从base64中提取图片部分
            if "base64," in captcha_base64:
                captcha_base64 = captcha_base64.split("base64,")[1]
            
            # 保存图片用于处理
            try:
                img_data = base64.b64decode(captcha_base64)
                timestamp = int(time.time())
                # 将调试图片保存到系统临时目录，避免当前目录无写权限
                img_path = os.path.join(tempfile.gettempdir(), f"captcha_debug_{timestamp}.png")
                img = Image.open(BytesIO(img_data))
                img.save(img_path)
                
                # 使用图片文件路径进行识别
                with open(img_path, "rb") as img_file:
                    # 读取图片数据并转换为base64
                    img_bytes = img_file.read()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    
                    # 使用多模态模型qwen-vl-plus进行识别
                    completion = self.ai_client.chat.completions.create(
                        model="qwen-vl-plus",
                        messages=[
                            {"role": "user", 
                             "content": [
                                {"type": "image_url", 
                                 "image_url": {"url": f"data:image/png;base64,{img_base64}"}},
                                {"type": "text", 
                                 "text": "这是一个算术验证码，请直接告诉我答案，不要有任何其他文字。"}
                             ]
                            }
                        ]
                    )
                
                # 从AI响应中提取数字
                answer = completion.choices[0].message.content.strip()
                
                # 尝试提取纯数字答案
                import re
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    try:
                        os.remove(img_path)
                    except Exception:
                        pass
                    return numbers[0]
                
                # 如果没有提取到数字，直接返回答案
                try:
                    os.remove(img_path)
                except Exception:
                    pass
                return answer
                
            except Exception as e:
                traceback.print_exc()
            
        except Exception as e:
            traceback.print_exc()
        
        # 如果所有方法都失败，返回None表示识别失败
        return None
    
    def _generate_random_id(self):
        """生成随机ID"""
        return uuid.uuid4().hex
    
    def login(self, username, raw_password=None):
        """
        登录主函数
        
        参数:
            username: 用户名/学号
            raw_password: 原始密码，如果提供则尝试获取加密密码
            
        返回:
            (success, message): 登录是否成功及消息
        """
        # 更新当前用户和获取会话
        self.username = username
        self.get_or_create_session()
        
        # 首先尝试使用保存的ticket1登录
        try:
            from app.models.db import get_user_ticket1
            ticket1 = get_user_ticket1(username)
            if ticket1:
                success, message = self.login_with_ticket1(username, ticket1)
                if success:
                    return True, "登录成功"
        except Exception as e:
            pass
        
        # 使用前端同款加密算法实时生成密文
        if not raw_password:
            return False, "未提供原始密码"
            
        try:
            logger.debug(f"使用前端同款加密算法实时加密密码：{username}")
            encrypted_password = encrypt_password(raw_password)
            logger.debug(f"密码加密成功，密文前20字符：{encrypted_password[:20]}")
        except Exception as e:
            logger.error(f"密码加密失败：{str(e)}")
            return False, f"密码加密失败: {str(e)}"
        
        # 使用密文登录
        return self.login_with_encrypted_password(username, encrypted_password)
    
    def login_with_encrypted_password(self, username, encrypted_password):
        """使用加密后的密码登录"""
        try:
            logger.info(f"使用加密密码登录用户 {username}")
            
            # 首先获取验证码和uid
            captcha_url = f"{self.base_url}/kaptcha?uid="
            
            # 生成loginusertoken
            loginusertoken = self._generate_random_id() + self._generate_random_id()
            logger.debug(f"生成loginusertoken: {loginusertoken[:10]}...")
            
            # 添加logintoken头
            self.session.headers.update({
                'logintoken': 'loginToken',
                'loginusertoken': loginusertoken
            })
            logger.debug("已添加logintoken头")
            
            # 发送验证码请求
            try:
                logger.debug(f"请求验证码: {captcha_url}")
                captcha_response = self.session.get(captcha_url)
                
                if captcha_response.status_code != 200:
                    logger.error(f"获取验证码失败，状态码: {captcha_response.status_code}")
                    return False, f"获取验证码失败，状态码: {captcha_response.status_code}"
                    
            except Exception as e:
                logger.error(f"验证码请求异常: {str(e)}")
                traceback.print_exc()
                return False, f"验证码请求异常: {str(e)}"
            
            # 解析验证码响应
            try:
                captcha_data = captcha_response.json()
                logger.debug(f"验证码响应内容: {json.dumps(captcha_data)[:100]}...")
                
                uid = captcha_data.get('uid')
                captcha_content = captcha_data.get('content')  # BASE64编码的验证码图片
                captcha_type = captcha_data.get('kaptchaType')
                
                logger.debug(f"验证码类型: {captcha_type}, UID: {uid}")
                
                if not uid:
                    logger.error("获取uid失败")
                    return False, "获取uid失败"
                    
            except json.JSONDecodeError as e:
                logger.error("验证码响应解析失败")
                traceback.print_exc()
                return False, "验证码响应解析失败"
            except Exception as e:
                logger.error(f"验证码响应解析异常: {str(e)}")
                traceback.print_exc()
                return False, f"验证码响应解析异常: {str(e)}"
            
            # 使用AI识别验证码
            if captcha_content:
                try:
                    logger.debug("开始识别验证码")
                    code_value = self.recognize_captcha(captcha_content)
                    if code_value is None:
                        logger.error("验证码识别失败")
                        return False, "验证码识别失败，请重试"
                    
                    logger.debug(f"验证码识别结果: {code_value}")
                    
                    # 确保结果是数字
                    if not code_value.isdigit():
                        import re
                        numbers = re.findall(r'\d+', code_value)
                        if numbers:
                            code_value = numbers[0]
                            logger.debug(f"从识别结果提取数字: {code_value}")
                        else:
                            logger.error("验证码识别结果不包含数字")
                            return False, "验证码识别失败，无法提取数字"
                except Exception as e:
                    logger.error(f"验证码识别异常: {str(e)}")
                    traceback.print_exc()
                    return False, f"验证码识别异常: {str(e)}"
            else:
                logger.error("未获取到验证码图片")
                return False, "未获取到验证码图片"
                
            # 构建登录数据，正确格式
            login_data = {
                'username': username,
                'password': encrypted_password,
                'service': self.service_url,
                'loginType': '',  # 应该是空字符串
                'id': uid,  # id参数正确设置
                'code': code_value
            }
            logger.debug(f"登录数据: {json.dumps(login_data)}")
            
            # 添加特殊的token头
            new_token = self._generate_random_id() + self._generate_random_id()
            self.session.headers.update({
                'logintoken': 'loginToken',
                'loginusertoken': new_token  # 生成一个长的token
            })
            logger.debug(f"更新loginusertoken: {new_token[:10]}...")
            
            # 确保使用表单数据格式，并设置正确的Content-Type
            self.session.headers.update({
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            logger.debug("已设置Content-Type为application/x-www-form-urlencoded")
            
            # 构建URL编码的表单数据
            import urllib.parse
            form_data = urllib.parse.urlencode(login_data)
            
            # 发送登录请求
            try:
                # 发送POST请求
                logger.debug(f"发送登录请求到: {self.login_url}")
                response = self.session.post(self.login_url, data=form_data)
                logger.debug(f"登录响应状态码: {response.status_code}")
                
            except Exception as e:
                logger.error(f"登录请求异常: {str(e)}")
                traceback.print_exc()
                return False, f"请求异常: {str(e)}"
            
            # 检查响应
            if response.status_code == 200:
                try:
                    # 保存原始响应内容，用于调试
                    response_text = response.text
                    logger.debug(f"登录原始响应: {response_text}")
                    
                    result = response.json()
                    logger.debug(f"登录响应JSON: {json.dumps(result)}")
                    
                    # 直接检查是否有ticket字段（最简单的响应格式）
                    if 'ticket' in result:
                        ticket = result.get('ticket')
                        logger.info(f"从响应中获取到ticket: {ticket[:20] if ticket else 'None'}...")
                        
                        # 使用ticket访问服务URL，完成SSO登录
                        service_with_ticket = f"{self.service_url}?ticket={ticket}"
                        # 允许重定向
                        sso_response = self.session.get(service_with_ticket, allow_redirects=True)
                        
                        # 检查是否包含ticket1参数
                        import re
                        if "ticket1=" in sso_response.url or any("ticket1=" in r.url for r in sso_response.history):
                            # 找到ticket1
                            ticket1_url = sso_response.url
                            if "ticket1=" not in ticket1_url:
                                for r in sso_response.history:
                                    if "ticket1=" in r.url:
                                        ticket1_url = r.url
                                        break
                            
                            ticket1_match = re.search(r'ticket1=([^&]+)', ticket1_url)
                            if ticket1_match:
                                ticket1 = ticket1_match.group(1)
                                logger.debug(f"从SSO响应中获取到ticket1: {ticket1[:20]}...")
                        
                        if sso_response.status_code == 200:
                            # 保存会话状态
                            self.is_logged_in = True
                            self.username = username
                            self.cookies = dict(self.session.cookies)
                            
                            # 尝试从主页提取用户真实姓名
                            try:
                                import re
                                from bs4 import BeautifulSoup
                                
                                logger.info(f"开始提取用户 {username} 的真实姓名")
                                
                                # 获取主页
                                main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                                main_page_response = self.session.get(main_page_url)
                                logger.debug(f"获取主页响应状态码: {main_page_response.status_code}")
                                
                                if main_page_response.status_code == 200:
                                    soup = BeautifulSoup(main_page_response.text, 'html.parser')
                                    # 查找包含姓名的div元素
                                    login_name_div = soup.find('div', id='Top1_divLoginName')
                                    logger.debug(f"找到姓名div元素: {login_name_div is not None}")
                                    
                                    if login_name_div:
                                        # 提取姓名
                                        name_text = login_name_div.text.strip()
                                        logger.debug(f"姓名文本内容: '{name_text}'")
                                        # 通常格式为 "姓名(学号)"，使用正则提取姓名
                                        name_match = re.match(r'(.+?)\(', name_text)
                                        
                                        if name_match:
                                            real_name = name_match.group(1).strip()
                                            logger.info(f"成功提取到真实姓名: {real_name}")
                                            
                                            # 保存真实姓名到数据库
                                            try:
                                                from app.models.db import save_user_basic_info
                                                save_user_basic_info(username, None, real_name)
                                                logger.info(f"成功保存用户 {username} 的真实姓名: {real_name}")
                                            except Exception as e:
                                                logger.error(f"保存真实姓名失败: {str(e)}")
                                        else:
                                            logger.warning(f"无法从文本 '{name_text}' 中提取姓名，正则匹配失败")
                                    else:
                                        logger.warning("未找到包含姓名的div元素 'Top1_divLoginName'")
                                        # 尝试查找其他可能的元素
                                        all_divs = soup.find_all('div')
                                        logger.debug(f"页面中共找到 {len(all_divs)} 个div元素")
                                        for i, div in enumerate(all_divs[:10]):  # 只检查前10个
                                            if div.get('id'):
                                                logger.debug(f"div[{i}] id='{div.get('id')}' text='{div.text.strip()[:50]}'")
                                else:
                                    logger.error(f"获取主页失败，状态码: {main_page_response.status_code}")
                            except Exception as e:
                                logger.error(f"提取用户真实姓名失败: {str(e)}")
                                import traceback
                                logger.debug(f"提取真实姓名异常详情: {traceback.format_exc()}")
                            
                            return True, "登录成功"
                        else:
                            return False, f"SSO登录失败，状态码: {sso_response.status_code}"
                    
                    # 检查新的响应格式
                    elif 'meta' in result and 'data' in result:
                        # 新格式响应
                        meta = result.get('meta', {})
                        data = result.get('data', {})
                        
                        if meta.get('success') == True:
                            # 检查是否有验证码错误
                            if data.get('code') == 'CODEFALSE':
                                return False, "验证码错误，请重新尝试"
                            
                            # 检查是否有票据
                            ticket = data.get('ticket')
                            if ticket:
                                # 使用ticket访问服务URL，完成SSO登录
                                service_with_ticket = f"{self.service_url}?ticket={ticket}"
                                # 允许重定向
                                sso_response = self.session.get(service_with_ticket, allow_redirects=True)
                                
                                # 检查是否包含ticket1参数
                                import re
                                if "ticket1=" in sso_response.url or any("ticket1=" in r.url for r in sso_response.history):
                                    # 找到ticket1
                                    ticket1_url = sso_response.url
                                    if "ticket1=" not in ticket1_url:
                                        for r in sso_response.history:
                                            if "ticket1=" in r.url:
                                                ticket1_url = r.url
                                                break
                                    
                                    ticket1_match = re.search(r'ticket1=([^&]+)', ticket1_url)
                                    if ticket1_match:
                                        ticket1 = ticket1_match.group(1)
                                        logger.debug(f"从新格式响应中获取到ticket1: {ticket1[:20]}...")
                                        
                                        # 保存ticket1到数据库
                                        try:
                                            from app.models.db import save_user_ticket1
                                            save_user_ticket1(username, ticket1)
                                        except Exception as e:
                                            pass
                                
                                if sso_response.status_code == 200:
                                    # 保存会话状态
                                    self.is_logged_in = True
                                    self.username = username
                                    self.cookies = dict(self.session.cookies)
                                    
                                    # 保存cookie到数据库
                                    try:
                                        from app.models.db import save_user_cookies
                                        save_user_cookies(username, self.cookies)
                                    except Exception as e:
                                        pass
                                    
                                    # 尝试从主页提取用户真实姓名
                                    try:
                                        import re
                                        from bs4 import BeautifulSoup
                                        
                                        # 获取主页
                                        main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                                        main_page_response = self.session.get(main_page_url)
                                        
                                        if main_page_response.status_code == 200:
                                            soup = BeautifulSoup(main_page_response.text, 'html.parser')
                                            # 查找包含姓名的div元素
                                            login_name_div = soup.find('div', id='Top1_divLoginName')
                                            
                                            if login_name_div:
                                                # 提取姓名
                                                name_text = login_name_div.text.strip()
                                                # 通常格式为 "姓名(学号)"，使用正则提取姓名
                                                name_match = re.match(r'(.+?)\(', name_text)
                                                
                                                if name_match:
                                                    real_name = name_match.group(1).strip()
                                                    
                                                    # 保存真实姓名到数据库
                                                    try:
                                                        from app.models.db import save_user_basic_info
                                                        save_user_basic_info(username, None, real_name)
                                                    except Exception as e:
                                                        print(f"提取用户真实姓名失败: {str(e)}")
                                    except Exception as e:
                                        print(f"提取用户真实姓名失败: {str(e)}")
                                    
                                    return True, "登录成功"
                                else:
                                    return False, f"SSO登录失败，状态码: {sso_response.status_code}"
                            else:
                                return False, "登录响应中无ticket"
                        else:
                            error_msg = meta.get('message', '未知错误')
                            return False, f"登录失败: {error_msg}"
                    
                    # 旧格式响应处理
                    elif 'errcode' in result:
                        if result['errcode'] != 0:
                            error_msg = result.get('errmsg', '未知错误')
                            return False, f"登录失败: {error_msg}"
                        
                        # 获取ticket，用于后续请求
                        ticket = result.get('ticket')
                        if ticket:
                            # 使用ticket访问服务URL，完成SSO登录
                            service_with_ticket = f"{self.service_url}?ticket={ticket}"
                            # 允许重定向
                            sso_response = self.session.get(service_with_ticket, allow_redirects=True)
                            
                            # 检查是否包含ticket1参数
                            import re
                            if "ticket1=" in sso_response.url or any("ticket1=" in r.url for r in sso_response.history):
                                # 找到ticket1
                                ticket1_url = sso_response.url
                                if "ticket1=" not in ticket1_url:
                                    for r in sso_response.history:
                                        if "ticket1=" in r.url:
                                            ticket1_url = r.url
                                            break
                                
                                ticket1_match = re.search(r'ticket1=([^&]+)', ticket1_url)
                                if ticket1_match:
                                    ticket1 = ticket1_match.group(1)
                                    logger.debug(f"从旧格式响应中获取到ticket1: {ticket1[:20]}...")
                                    
                                    # 保存ticket1到数据库
                                    try:
                                        from app.models.db import save_user_ticket1
                                        save_user_ticket1(username, ticket1)
                                    except Exception as e:
                                        pass
                            
                            if sso_response.status_code == 200:
                                # 保存会话状态
                                self.is_logged_in = True
                                self.username = username
                                self.cookies = dict(self.session.cookies)
                                
                                # 保存cookie到数据库
                                try:
                                    from app.models.db import save_user_cookies
                                    save_user_cookies(username, self.cookies)
                                except Exception as e:
                                    pass
                                
                                # 尝试从主页提取用户真实姓名
                                try:
                                    import re
                                    from bs4 import BeautifulSoup
                                    
                                    logger.info(f"开始提取用户 {username} 的真实姓名")
                                    
                                    # 获取主页
                                    main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                                    main_page_response = self.session.get(main_page_url)
                                    logger.debug(f"获取主页响应状态码: {main_page_response.status_code}")
                                    
                                    if main_page_response.status_code == 200:
                                        soup = BeautifulSoup(main_page_response.text, 'html.parser')
                                        # 查找包含姓名的div元素
                                        login_name_div = soup.find('div', id='Top1_divLoginName')
                                        logger.debug(f"找到姓名div元素: {login_name_div is not None}")
                                        
                                        if login_name_div:
                                            # 提取姓名
                                            name_text = login_name_div.text.strip()
                                            logger.debug(f"姓名文本内容: '{name_text}'")
                                            # 通常格式为 "姓名(学号)"，使用正则提取姓名
                                            name_match = re.match(r'(.+?)\(', name_text)
                                            
                                            if name_match:
                                                real_name = name_match.group(1).strip()
                                                logger.info(f"成功提取到真实姓名: {real_name}")
                                                
                                                # 保存真实姓名到数据库
                                                try:
                                                    from app.models.db import save_user_basic_info
                                                    save_user_basic_info(username, None, real_name)
                                                    logger.info(f"成功保存用户 {username} 的真实姓名: {real_name}")
                                                except Exception as e:
                                                    logger.error(f"保存真实姓名失败: {str(e)}")
                                            else:
                                                logger.warning(f"无法从文本 '{name_text}' 中提取姓名，正则匹配失败")
                                        else:
                                            logger.warning("未找到包含姓名的div元素 'Top1_divLoginName'")
                                    else:
                                        logger.error(f"获取主页失败，状态码: {main_page_response.status_code}")
                                except Exception as e:
                                    logger.error(f"提取用户真实姓名失败: {str(e)}")
                                    import traceback
                                    logger.debug(f"提取真实姓名异常详情: {traceback.format_exc()}")
                                
                                return True, "登录成功"
                            else:
                                return False, f"SSO登录失败，状态码: {sso_response.status_code}"
                        else:
                            return False, "登录响应中无ticket"
                    else:
                        return False, "未知的响应格式"
                        
                except json.JSONDecodeError:
                    return False, "无法解析登录响应JSON"
            else:
                return False, f"登录请求失败，状态码: {response.status_code}"
                
        except Exception as e:
            traceback.print_exc()
            return False, f"登录异常: {str(e)}"
    
    def is_logged_in(self):
        """检查是否已登录"""
        return self.is_logged_in
    
    def get_cookies(self):
        """获取会话cookies"""
        if hasattr(self, 'cookies') and self.cookies:
            return self.cookies
        
        # 如果没有缓存的cookies但有用户名，尝试从数据库获取
        if hasattr(self, 'username') and self.username:
            try:
                from app.models.db import get_user_cookies
                cookies = get_user_cookies(self.username)
                if cookies:
                    self.cookies = cookies
                    return self.cookies
            except Exception as e:
                pass
        
        return {}
    
    def login_with_ticket1(self, username, ticket1):
        """使用ticket1直接登录教务系统"""
        try:
            # 构建带有ticket1的URL
            ticket1_url = f"http://jwgl.hutb.edu.cn/jsxsd/xk/LoginToXk?method=jwxt&ticket1={ticket1}"
            
            # 发送请求，允许重定向
            response = self.session.get(ticket1_url, allow_redirects=True)
            
            # 检查是否成功登录（重定向到主页）
            if response.status_code == 200 and "xsMain.jsp" in response.url:
                # 保存会话状态
                self.is_logged_in = True
                self.username = username
                self.cookies = dict(self.session.cookies)
                
                # 尝试从主页提取用户真实姓名
                try:
                    import re
                    from bs4 import BeautifulSoup
                    
                    logger.info(f"开始提取用户 {username} 的真实姓名")
                    
                    # 获取主页
                    main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                    main_page_response = self.session.get(main_page_url)
                    logger.debug(f"获取主页响应状态码: {main_page_response.status_code}")
                    
                    if main_page_response.status_code == 200:
                        soup = BeautifulSoup(main_page_response.text, 'html.parser')
                        # 查找包含姓名的div元素
                        login_name_div = soup.find('div', id='Top1_divLoginName')
                        logger.debug(f"找到姓名div元素: {login_name_div is not None}")
                        
                        if login_name_div:
                            # 提取姓名
                            name_text = login_name_div.text.strip()
                            logger.debug(f"姓名文本内容: '{name_text}'")
                            # 通常格式为 "姓名(学号)"，使用正则提取姓名
                            name_match = re.match(r'(.+?)\(', name_text)
                            
                            if name_match:
                                real_name = name_match.group(1).strip()
                                logger.info(f"成功提取到真实姓名: {real_name}")
                                
                                # 保存真实姓名到数据库
                                try:
                                    from app.models.db import save_user_basic_info
                                    save_user_basic_info(username, None, real_name)
                                    logger.info(f"成功保存用户 {username} 的真实姓名: {real_name}")
                                except Exception as e:
                                    logger.error(f"保存真实姓名失败: {str(e)}")
                            else:
                                logger.warning(f"无法从文本 '{name_text}' 中提取姓名，正则匹配失败")
                        else:
                            logger.warning("未找到包含姓名的div元素 'Top1_divLoginName'")
                    else:
                        logger.error(f"获取主页失败，状态码: {main_page_response.status_code}")
                except Exception as e:
                    logger.error(f"提取用户真实姓名失败: {str(e)}")
                    import traceback
                    logger.debug(f"提取真实姓名异常详情: {traceback.format_exc()}")
                
                # 保存cookie到数据库
                try:
                    from app.models.db import save_user_cookies
                    save_user_cookies(username, self.cookies)
                except Exception as e:
                    pass
                
                # 保存ticket1到数据库
                try:
                    from app.models.db import save_user_ticket1
                    save_user_ticket1(username, ticket1)
                except Exception as e:
                    pass
                
                return True, "登录成功"
            else:
                return False, f"登录失败，状态码: {response.status_code}"
                
        except Exception as e:
            traceback.print_exc()
            return False, f"登录异常: {str(e)}"
    
    def logout(self):
        """登出"""
        try:
            logout_url = f"{self.base_url}/logout"
            response = self.session.get(logout_url)
            
            # 重置会话状态
            self.session = requests.Session()
            self.is_logged_in = False
            self.username = None
            self.cookies = {}
            
            return True, "登出成功"
        except Exception as e:
            return False, f"登出异常: {str(e)}"

# 创建单例实例
# login_manager = LoginManager() # This line is removed as per the new_code

def handle_login_request():
    """
    处理来自login.html的登录请求
    """
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash("请提供用户名和密码")
        return redirect(url_for('login'))
    
    try:
        # 获取设备标识符
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent')
        import hashlib
        device_id = hashlib.md5(f"{ip_address}:{user_agent}".encode()).hexdigest()
        
        # 保存用户基本信息到数据库
        try:
            from app.models.db import save_user_basic_info
            save_user_basic_info(username, password, None, ip_address)
        except Exception as e:
            logger.warning(f"保存用户信息失败（不影响登录）: {str(e)}")
        
        # 为此用户创建专属登录管理器
        user_login_manager = LoginManager(username)
        
        # 使用登录管理器进行登录
        success, message = user_login_manager.login(username, password)
        
        if success:
            # 确保cookies保存到数据库
            try:
                from app.models.db import save_user_cookies, get_user_cookies
                cookies = user_login_manager.get_cookies()
                if cookies:
                    save_user_cookies(username, cookies)
                
                # 验证是否保存成功
                saved_cookies = get_user_cookies(username)
            except Exception as e:
                traceback.print_exc()
            
            # 将用户信息存储到session中，使用设备ID区分不同设备
            session['username'] = username
            session['device_id'] = device_id
            session['session_id'] = f"{username}_{device_id}"
            
            flash("登录成功")
            return redirect(url_for('dashboard'))
        else:
            # 返回错误信息
            flash(f"登录失败: {message}")
            return redirect(url_for('login'))
                
    except Exception as e:
        traceback.print_exc()
        flash(f"处理登录请求时出错: {str(e)}")
        return redirect(url_for('login')) 