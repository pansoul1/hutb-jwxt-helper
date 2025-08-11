import os
import time
import shutil
import random
import string
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import traceback
import re
from flask import session, request, redirect, url_for, flash
import json
from time import sleep
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('browser_login_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('browser_login')

# 导入数据库模块
from app.models.db import save_user_credentials, get_user_by_username

# 用户浏览器会话字典：存储每个用户的专用浏览器会话
user_browser_sessions = {}

def setup_browser(headless=True, user_agent=None):
    """
    设置Chrome浏览器实例
    
    参数:
        headless: 是否使用无头模式（默认为True）
        user_agent: 自定义User Agent（可选）
    
    返回:
        browser: WebDriver实例
    """
    try:
        logger.info("开始设置浏览器...")
        # 获取项目根目录的绝对路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logger.debug(f"项目根目录: {project_root}")
        
        # 设置Chrome选项
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
            logger.debug("启用无头模式")
        
        # 禁用图片加载，提高性能
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        
        # 添加其他性能选项
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 如果提供了自定义User Agent，则设置
        if user_agent:
            chrome_options.add_argument(f'--user-agent={user_agent}')
            logger.debug(f"设置自定义User Agent: {user_agent}")
        
        # 尝试使用项目中包含的Chrome可执行文件和驱动
        chrome_path = os.path.join(project_root, 'chrome-linux64', 'chrome')
        chromedriver_path = os.path.join(project_root, 'chromedriver', 'chromedriver')
        
        logger.debug(f"Chrome路径: {chrome_path}, 存在: {os.path.exists(chrome_path)}")
        logger.debug(f"ChromeDriver路径: {chromedriver_path}, 存在: {os.path.exists(chromedriver_path)}")
        
        if os.path.exists(chrome_path) and os.path.exists(chromedriver_path):
            # 设置Chrome二进制文件路径
            chrome_options.binary_location = chrome_path
            # 创建WebDriver实例，使用Service对象指定ChromeDriver路径
            logger.info("使用项目内置Chrome和ChromeDriver")
            service = Service(executable_path=chromedriver_path)
            browser = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # 如果项目内的Chrome不可用，使用系统Chrome
            logger.info("使用系统Chrome和ChromeDriver")
            browser = webdriver.Chrome(options=chrome_options)
        
        # 设置页面加载超时（秒）
        browser.set_page_load_timeout(30)
        
        # 设置窗口大小
        browser.set_window_size(1366, 768)
        
        logger.info("浏览器设置成功")
        return browser
        
    except Exception as e:
        logger.error(f"设置浏览器失败: {str(e)}")
        traceback.print_exc()
        raise Exception(f"设置浏览器失败: {str(e)}")

def get_or_create_browser_session(username=None):
    """
    获取或创建用户专属的浏览器会话
    
    参数:
        username: 用户名，如果为None则创建临时会话
    
    返回:
        browser: WebDriver实例
    """
    global user_browser_sessions
    
    if username:
        logger.info(f"为用户 {username} 获取或创建浏览器会话")
        # 如果用户会话已存在，使用现有会话
        if username in user_browser_sessions:
            try:
                # 尝试使用现有会话
                browser = user_browser_sessions[username]
                # 测试浏览器是否仍然可用
                current_url = browser.current_url
                logger.debug(f"使用现有会话，当前URL: {current_url}")
                return browser
            except Exception as e:
                logger.warning(f"现有会话已失效: {str(e)}，创建新会话")
                # 如果会话已失效，关闭并创建新会话
                try:
                    browser.quit()
                    logger.debug("已关闭失效会话")
                except:
                    logger.debug("关闭失效会话失败")
                    pass
        
        # 创建新的浏览器会话
        browser = setup_browser()
        user_browser_sessions[username] = browser
        logger.info(f"为用户 {username} 创建了新的浏览器会话")
        return browser
    else:
        # 未提供用户名时创建临时会话
        logger.info("创建临时浏览器会话（无用户名）")
        return setup_browser()

def close_browser_session(username=None, browser=None):
    """
    关闭浏览器会话
    
    参数:
        username: 用户名，如果提供则关闭用户专属会话
        browser: 浏览器实例，如果提供则直接关闭
    """
    global user_browser_sessions
    
    if username and username in user_browser_sessions:
        logger.info(f"关闭用户 {username} 的浏览器会话")
        try:
            user_browser_sessions[username].quit()
            del user_browser_sessions[username]
            logger.debug(f"成功关闭用户 {username} 的会话")
        except Exception as e:
            logger.error(f"关闭用户 {username} 会话失败: {str(e)}")
            pass
    elif browser:
        logger.info("关闭指定浏览器会话")
        try:
            browser.quit()
            logger.debug("成功关闭指定浏览器会话")
        except Exception as e:
            logger.error(f"关闭指定浏览器会话失败: {str(e)}")
            pass

def get_encrypted_password(username, raw_password):
    """
    使用 Selenium 模拟浏览器获取教务系统前端加密后的密码（Linux 适配版）。

    参数:
        username: 学号
        raw_password: 原始密码

    返回:
        (success, encrypted_password_or_error): 是否成功以及加密后的密码或错误信息
    """
    driver = None
    try:
        logger.info(f"开始获取用户 {username} 的加密密码（Linux 适配）")

        # --------- 1. 浏览器配置 ---------
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--blink-settings=imagesEnabled=false')

        # 指定项目自带的 Chrome 二进制（如果存在）
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chrome_binary = os.path.join(project_root, 'chrome-linux64', 'chrome')
        if os.path.exists(chrome_binary):
            chrome_options.binary_location = chrome_binary
            logger.debug(f"使用项目内置 Chrome: {chrome_binary}")
        else:
            logger.debug("使用系统 Chrome")

        # chromedriver 路径（Linux 无 .exe 后缀）
        chromedriver_path = os.path.join(project_root, 'chromedriver', 'chromedriver')
        if not os.path.exists(chromedriver_path):
            logger.error(f"找不到 chromedriver: {chromedriver_path}")
            return False, "chromedriver 不存在，请确认路径"
        logger.debug(f"chromedriver 路径: {chromedriver_path}")

        # 启动浏览器
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30)

        # --------- 2. 打开登录页 ---------
        login_url = 'https://cas.hutb.edu.cn/lyuapServer/login?service=http://jwgl.hutb.edu.cn/'
        logger.info(f"访问登录页面: {login_url}")
        driver.get(login_url)

        # 等待用户名输入框出现
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'userName'))
        )
        logger.debug("登录页面加载完毕")

        # --------- 3. 注入 JS Hook 捕获 XHR 中的加密密码 ---------
        driver.execute_script("""
        (function () {
            if (window.__hutb_hook_installed__) {return;}
            const OriginalXHR = window.XMLHttpRequest;
            let captured = false;
            let encPwd = null;
            window.XMLHttpRequest = function () {
                const xhr = new OriginalXHR();
                const origOpen = xhr.open;
                const origSend = xhr.send;
                xhr.open = function () {
                    this._url = arguments[1];
                    return origOpen.apply(this, arguments);
                };
                xhr.send = function (body) {
                    try {
                        if (this._url && this._url.includes('/v1/tickets') && typeof body === 'string' && body.includes('password=')) {
                            const pwdStart = body.indexOf('password=') + 9;
                            const pwdEnd = body.indexOf('&', pwdStart) === -1 ? body.length : body.indexOf('&', pwdStart);
                            encPwd = body.substring(pwdStart, pwdEnd);
                            captured = true;
                        }
                    } catch (e) {console.error(e);}
                    return origSend.apply(this, arguments);
                };
                return xhr;
            };
            window.__hutb_hook_installed__ = true;
            window.__hutb_pwd_captured__ = () => captured;
            window.__hutb_get_pwd__ = () => encPwd;
        })();
        """)
        logger.debug("已注入 XHR Hook")

        # --------- 4. 输入凭据并触发登录 ---------
        driver.find_element(By.ID, 'userName').send_keys(username)
        driver.find_element(By.ID, 'password').send_keys(raw_password)

        # 如果存在验证码输入框，输入固定占位值（教务系统常规处理）
        try:
            captcha_field = driver.find_element(By.ID, 'captcha')
            captcha_field.send_keys('hutb')
            logger.debug("已输入验证码占位值")
        except Exception:
            pass  # 无验证码时忽略

        # 点击登录按钮或回车
        try:
            login_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'ant-btn') and .//span[text()='登 录']]")
            login_btn.click()
            logger.debug("点击登录按钮")
        except Exception:
            # 备用方案：在密码输入框回车
            driver.find_element(By.ID, 'password').send_keys('\ue007')
            logger.debug("通过回车键提交登录")

        # --------- 5. 轮询等待加密密码被捕获 ---------
        max_wait_seconds = 10
        poll_interval = 0.5
        waited = 0
        while waited < max_wait_seconds:
            if driver.execute_script('return window.__hutb_pwd_captured__ && window.__hutb_pwd_captured__();'):
                break
            time.sleep(poll_interval)
            waited += poll_interval

        if driver.execute_script('return window.__hutb_pwd_captured__ && window.__hutb_pwd_captured__();'):
            encrypted_password = driver.execute_script('return window.__hutb_get_pwd__ && window.__hutb_get_pwd__();')
            logger.info("成功捕获加密密码")
            logger.debug(f"加密密码前 20 位: {encrypted_password[:20] if encrypted_password else 'None'}")

            # 保存到数据库
            save_user_credentials(username, encrypted_password, {}, raw_password)
            return True, encrypted_password

        # --------- 6. Fallback：解析页面源码或 URL ---------
        logger.warning("XHR Hook 未捕获到密码，尝试从页面源码/URL 提取")
        page_source = driver.page_source
        password_patterns = [
            r'password\s*[=:]\s*[\'\"]([a-f0-9]{60,})[\'\"]',
            r'password\s*[=:]\s*[\'\"]([^\"\']{30,})[\'\"]',
            r'name="password"\s+value="([^"]+)"'
        ]
        for pattern in password_patterns:
            matches = re.findall(pattern, page_source)
            if matches:
                potential_pwd = matches[0]
                if len(potential_pwd) > 30:
                    logger.info("从页面源码提取到加密密码")
                    save_user_credentials(username, potential_pwd, {}, raw_password)
                    return True, potential_pwd

        current_url = driver.current_url
        if 'ticket=' in current_url:
            ticket_match = re.search(r'ticket=([^&]+)', current_url)
            if ticket_match:
                ticket = ticket_match.group(1)
                logger.info("从 URL 提取到 ticket 作为密码")
                save_user_credentials(username, ticket, {}, raw_password)
                return True, ticket

        logger.error("无法获取加密密码")
        return False, "无法获取加密密码"

    except Exception as e:
        logger.error(f"浏览器操作错误: {str(e)}")
        traceback.print_exc()
        return False, f"浏览器操作错误: {str(e)}"

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

def handle_login_request():
    """
    处理来自login.html的登录请求
    """
    username = request.form.get('username')
    password = request.form.get('password')
    
    logger.info(f"处理用户 {username} 的登录请求")
    
    if not username or not password:
        logger.warning("缺少用户名或密码")
        flash("请提供用户名和密码")
        return redirect(url_for('login'))
    
    # 检查数据库中是否已有该用户的登录凭证
    try:
        user = get_user_by_username(username)
        
        if user:
            # 用户已存在，返回密文信息
            encrypted_password = user[2]  # 假设第三列是encrypted_password
            logger.info(f"用户 {username} 已存在于数据库")
            logger.debug(f"数据库中的密文前20个字符: {encrypted_password[:20] if encrypted_password else 'None'}")
            
            session['username'] = username
            flash(f"用户 {username} 已存在，成功获取密文")
            return redirect(url_for('dashboard'))
        else:
            # 用户不存在，尝试获取密文
            logger.info(f"用户 {username} 不存在，尝试获取密文")
            success, result = get_encrypted_password(username, password)
            
            if success:
                logger.info(f"成功获取用户 {username} 的密文")
                session['username'] = username
                flash(f"成功获取密文: {result[:20]}...")
                return redirect(url_for('dashboard'))
            else:
                logger.error(f"获取用户 {username} 密文失败: {result}")
                flash(f"获取密文失败: {result}")
                return redirect(url_for('login'))
                
    except Exception as e:
        logger.error(f"处理登录请求时出错: {str(e)}")
        traceback.print_exc()
        flash(f"处理登录请求时出错: {str(e)}")
        return redirect(url_for('login')) 