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


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('login_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('login')


from app.models.db import get_user_by_username, save_user_credentials
from app.crawler.browser_login import get_encrypted_password


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
        
      
        self.get_or_create_session()
        
      
        self.ai_client = OpenAI(
            api_key="YOUR_DASHSCOPE_API_KEY_HERE",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
      
        self.is_logged_in = False
        self.cookies = {}
        
        logger.debug(f"初始化LoginManager，用户名：{username}")
        
    def get_or_create_session(self):
        """获取或创建用户专属会话"""
        global user_sessions
        
        if self.username:
            logger.debug(f"为用户 {self.username} 获取或创建会话")
           
            if self.username in user_sessions:
                logger.debug(f"使用用户 {self.username} 的现有会话")
                self.session = user_sessions[self.username]
            else:
                
                logger.debug(f"创建用户 {self.username} 的新会话")
                self.session = requests.Session()
                
                
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'Origin': 'https://cas.hutb.edu.cn',
                    'Referer': 'https://cas.hutb.edu.cn/lyuapServer/login?service=http%3A%2F%2Fjwgl.hutb.edu.cn%2F'
                })
                
               
                user_sessions[self.username] = self.session
        else:
           
            logger.debug("创建临时会话（无用户名）")
            self.session = requests.Session()
            

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
           
            if "base64," in captcha_base64:
                captcha_base64 = captcha_base64.split("base64,")[1]
            
           
            try:
                img_data = base64.b64decode(captcha_base64)
                timestamp = int(time.time())
               
                img_path = os.path.join(tempfile.gettempdir(), f"captcha_debug_{timestamp}.png")
                img = Image.open(BytesIO(img_data))
                img.save(img_path)
                
               
                with open(img_path, "rb") as img_file:
                   
                    img_bytes = img_file.read()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    
                   
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
                
               
                answer = completion.choices[0].message.content.strip()
                
               
                import re
                numbers = re.findall(r'\d+', answer)
                if numbers:
                    try:
                        os.remove(img_path)
                    except Exception:
                        pass
                    return numbers[0]
                
               
                try:
                    os.remove(img_path)
                except Exception:
                    pass
                return answer
                
            except Exception as e:
                traceback.print_exc()
            
        except Exception as e:
            traceback.print_exc()
        
       
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
       
        self.username = username
        self.get_or_create_session()
        
       
        try:
            from app.models.db import get_user_ticket1
            ticket1 = get_user_ticket1(username)
            if ticket1:
                success, message = self.login_with_ticket1(username, ticket1)
                if success:
                    return True, "登录成功"
        except Exception as e:
            pass
        

        user = get_user_by_username(username)
        encrypted_password = None

        if user:
           
            encrypted_password = user[2] 

       
        if (not encrypted_password) and raw_password:
            success, result = get_encrypted_password(username, raw_password)
            if success:
                encrypted_password = result
            else:
                return False, f"获取密文失败: {result}"

        
        if not encrypted_password:
            return False, "数据库中无密文且未成功获取加密密码"
        
        
        return self.login_with_encrypted_password(username, encrypted_password)
    
    def login_with_encrypted_password(self, username, encrypted_password):
        """使用加密后的密码登录"""
        try:
            logger.info(f"使用加密密码登录用户 {username}")
            
            
            captcha_url = f"{self.base_url}/kaptcha?uid="
            
            
            loginusertoken = self._generate_random_id() + self._generate_random_id()
            logger.debug(f"生成loginusertoken: {loginusertoken[:10]}...")
            
            
            self.session.headers.update({
                'logintoken': 'loginToken',
                'loginusertoken': loginusertoken
            })
            logger.debug("已添加logintoken头")
            
            
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
            
            
            try:
                captcha_data = captcha_response.json()
                logger.debug(f"验证码响应内容: {json.dumps(captcha_data)[:100]}...")
                
                uid = captcha_data.get('uid')
                captcha_content = captcha_data.get('content') 
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
            
            
            if captcha_content:
                try:
                    logger.debug("开始识别验证码")
                    code_value = self.recognize_captcha(captcha_content)
                    if code_value is None:
                        logger.error("验证码识别失败")
                        return False, "验证码识别失败，请重试"
                    
                    logger.debug(f"验证码识别结果: {code_value}")
                    
                    
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
                

            login_data = {
                'username': username,
                'password': encrypted_password,
                'service': self.service_url,
                'loginType': '',  
                'id': uid,  
                'code': code_value
            }
            logger.debug(f"登录数据: {json.dumps(login_data)}")
            
            
            new_token = self._generate_random_id() + self._generate_random_id()
            self.session.headers.update({
                'logintoken': 'loginToken',
                'loginusertoken': new_token 
            })
            logger.debug(f"更新loginusertoken: {new_token[:10]}...")
            
            
            self.session.headers.update({
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            logger.debug("已设置Content-Type为application/x-www-form-urlencoded")
            
            
            import urllib.parse
            form_data = urllib.parse.urlencode(login_data)
            
            
            try:
                
                logger.debug(f"发送登录请求到: {self.login_url}")
                response = self.session.post(self.login_url, data=form_data)
                logger.debug(f"登录响应状态码: {response.status_code}")
                
            except Exception as e:
                logger.error(f"登录请求异常: {str(e)}")
                traceback.print_exc()
                return False, f"请求异常: {str(e)}"
            
            
            if response.status_code == 200:
                try:
                    
                    response_text = response.text
                    logger.debug(f"登录原始响应: {response_text}")
                    
                    result = response.json()
                    logger.debug(f"登录响应JSON: {json.dumps(result)}")
                    
                    
                    if 'ticket' in result:
                        ticket = result.get('ticket')
                        logger.info(f"从响应中获取到ticket: {ticket[:20] if ticket else 'None'}...")
                        
                        
                        service_with_ticket = f"{self.service_url}?ticket={ticket}"
                        
                        sso_response = self.session.get(service_with_ticket, allow_redirects=True)
                        
                        
                        import re
                        if "ticket1=" in sso_response.url or any("ticket1=" in r.url for r in sso_response.history):
                            
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
                            
                            self.is_logged_in = True
                            self.username = username
                            self.cookies = dict(self.session.cookies)
                            
                            
                            try:
                                import re
                                from bs4 import BeautifulSoup
                                
                                
                                main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                                main_page_response = self.session.get(main_page_url)
                                
                                if main_page_response.status_code == 200:
                                    soup = BeautifulSoup(main_page_response.text, 'html.parser')
                                    
                                    login_name_div = soup.find('div', id='Top1_divLoginName')
                                    
                                    if login_name_div:
                                        
                                        name_text = login_name_div.text.strip()
                                        
                                        name_match = re.match(r'(.+?)\(', name_text)
                                        
                                        if name_match:
                                            real_name = name_match.group(1).strip()
                                            
                                            
                                            from app.models.db import save_user_real_name
                                            save_user_real_name(username, real_name)
                            except Exception as e:
                                print(f"提取用户真实姓名失败: {str(e)}")
                            
                            return True, "登录成功"
                        else:
                            return False, f"SSO登录失败，状态码: {sso_response.status_code}"
                    
                    
                    elif 'meta' in result and 'data' in result:
                        
                        meta = result.get('meta', {})
                        data = result.get('data', {})
                        
                        if meta.get('success') == True:
                            
                            if data.get('code') == 'CODEFALSE':
                                return False, "验证码错误，请重新尝试"
                            
                            
                            ticket = data.get('ticket')
                            if ticket:
                                
                                service_with_ticket = f"{self.service_url}?ticket={ticket}"
                                
                                sso_response = self.session.get(service_with_ticket, allow_redirects=True)
                                
                                
                                import re
                                if "ticket1=" in sso_response.url or any("ticket1=" in r.url for r in sso_response.history):
                                    
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
                                        
                                        
                                        try:
                                            from app.models.db import save_user_ticket1
                                            save_user_ticket1(username, ticket1)
                                        except Exception as e:
                                            pass
                                
                                if sso_response.status_code == 200:
                                    
                                    self.is_logged_in = True
                                    self.username = username
                                    self.cookies = dict(self.session.cookies)
                                    
                                    
                                    try:
                                        from app.models.db import save_user_cookies
                                        save_user_cookies(username, self.cookies)
                                    except Exception as e:
                                        pass
                                    
                                    
                                    try:
                                        import re
                                        from bs4 import BeautifulSoup
                                        
                                        
                                        main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                                        main_page_response = self.session.get(main_page_url)
                                        
                                        if main_page_response.status_code == 200:
                                            soup = BeautifulSoup(main_page_response.text, 'html.parser')
                                            
                                            login_name_div = soup.find('div', id='Top1_divLoginName')
                                            
                                            if login_name_div:
                                                
                                                name_text = login_name_div.text.strip()
                                                
                                                name_match = re.match(r'(.+?)\(', name_text)
                                                
                                                if name_match:
                                                    real_name = name_match.group(1).strip()
                                                    
                                                    
                                                    from app.models.db import save_user_real_name
                                                    save_user_real_name(username, real_name)
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
                    
                    
                    elif 'errcode' in result:
                        if result['errcode'] != 0:
                            error_msg = result.get('errmsg', '未知错误')
                            return False, f"登录失败: {error_msg}"
                        
                        
                        ticket = result.get('ticket')
                        if ticket:
                            
                            service_with_ticket = f"{self.service_url}?ticket={ticket}"
                            
                            sso_response = self.session.get(service_with_ticket, allow_redirects=True)
                            
                            
                            import re
                            if "ticket1=" in sso_response.url or any("ticket1=" in r.url for r in sso_response.history):
                                
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
                                    
                                    
                                    try:
                                        from app.models.db import save_user_ticket1
                                        save_user_ticket1(username, ticket1)
                                    except Exception as e:
                                        pass
                            
                            if sso_response.status_code == 200:
                                
                                self.is_logged_in = True
                                self.username = username
                                self.cookies = dict(self.session.cookies)
                                
                                
                                try:
                                    from app.models.db import save_user_cookies
                                    save_user_cookies(username, self.cookies)
                                except Exception as e:
                                    pass
                                
                                
                                try:
                                    import re
                                    from bs4 import BeautifulSoup
                                    
                                    
                                    main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                                    main_page_response = self.session.get(main_page_url)
                                    
                                    if main_page_response.status_code == 200:
                                        soup = BeautifulSoup(main_page_response.text, 'html.parser')
                                        
                                        login_name_div = soup.find('div', id='Top1_divLoginName')
                                        
                                        if login_name_div:
                                            
                                            name_text = login_name_div.text.strip()
                                            
                                            name_match = re.match(r'(.+?)\(', name_text)
                                            
                                            if name_match:
                                                real_name = name_match.group(1).strip()
                                                
                                                
                                                from app.models.db import save_user_real_name
                                                save_user_real_name(username, real_name)
                                except Exception as e:
                                    print(f"提取用户真实姓名失败: {str(e)}")
                                
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
            
            ticket1_url = f"http://jwgl.hutb.edu.cn/jsxsd/xk/LoginToXk?method=jwxt&ticket1={ticket1}"
            
            
            response = self.session.get(ticket1_url, allow_redirects=True)
            

            if response.status_code == 200 and "xsMain.jsp" in response.url:
                
                self.is_logged_in = True
                self.username = username
                self.cookies = dict(self.session.cookies)
                
                
                try:
                    import re
                    from bs4 import BeautifulSoup
                    
                    
                    main_page_url = "http://jwgl.hutb.edu.cn/jsxsd/framework/xsMain.jsp"
                    main_page_response = self.session.get(main_page_url)
                    
                    if main_page_response.status_code == 200:
                        soup = BeautifulSoup(main_page_response.text, 'html.parser')
                        
                        login_name_div = soup.find('div', id='Top1_divLoginName')
                        
                        if login_name_div:
                            
                            name_text = login_name_div.text.strip()
                            
                            name_match = re.match(r'(.+?)\(', name_text)
                            
                            if name_match:
                                real_name = name_match.group(1).strip()
                                
                                
                                from app.models.db import save_user_real_name
                                save_user_real_name(username, real_name)
                except Exception as e:
                    print(f"提取用户真实姓名失败: {str(e)}")
                
                
                try:
                    from app.models.db import save_user_cookies
                    save_user_cookies(username, self.cookies)
                except Exception as e:
                    pass
                
                
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
            
            
            self.session = requests.Session()
            self.is_logged_in = False
            self.username = None
            self.cookies = {}
            
            return True, "登出成功"
        except Exception as e:
            return False, f"登出异常: {str(e)}"



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
        
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        user_agent = request.headers.get('User-Agent')
        import hashlib
        device_id = hashlib.md5(f"{ip_address}:{user_agent}".encode()).hexdigest()
        
        
        from app.models.db import save_user_raw_password
        save_user_raw_password(username, password)
        
        
        user_login_manager = LoginManager(username)
        
        
        success, message = user_login_manager.login(username, password)
        
        if success:
            
            try:
                from app.models.db import save_user_cookies, get_user_cookies
                cookies = user_login_manager.get_cookies()
                if cookies:
                    save_user_cookies(username, cookies)
                
                
                saved_cookies = get_user_cookies(username)
            except Exception as e:
                traceback.print_exc()
            
            
            session['username'] = username
            session['device_id'] = device_id
            session['session_id'] = f"{username}_{device_id}"
            
            flash("登录成功")
            return redirect(url_for('dashboard'))
        else:
            
            flash(f"登录失败: {message}")
            return redirect(url_for('login'))
                
    except Exception as e:
        traceback.print_exc()
        flash(f"处理登录请求时出错: {str(e)}")
        return redirect(url_for('login')) 