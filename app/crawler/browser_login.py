from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import traceback
import re
from flask import session, request, redirect, url_for, flash


from app.models.db import save_user_credentials, get_user_by_username

def get_encrypted_password(username, password):
    """
    使用Selenium模拟浏览器获取加密后的密码
    """
    print(f"\n===== 开始获取加密密码 {username} =====")
   
    chrome_options = Options()
   
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    print("Chrome选项已设置，无头模式已启用")
    
    
    chromedriver_path = "chromedriver/chromedriver.exe"
    print(f"chromedriver路径: {chromedriver_path}")
    
    try:
        
        service = Service(executable_path=chromedriver_path)
        print("创建WebDriver服务...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome浏览器已启动")
        
       
        print("正在访问教务系统登录页面...")
        driver.get("https://cas.hutb.edu.cn/lyuapServer/login?service=http://jwgl.hutb.edu.cn/")
        
       
        print("等待页面元素加载...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "userName"))
        )
        print("页面元素已加载")
        
       
        print("注入JavaScript拦截器...")
        driver.execute_script("""
        // 创建原始XMLHttpRequest的引用
        window.originalXHR = window.XMLHttpRequest;
        window.passwordCaptured = false;
        window.capturedPassword = null;
        
        // 创建新的XMLHttpRequest构造函数
        window.XMLHttpRequest = function() {
            var xhr = new window.originalXHR();
            var originalOpen = xhr.open;
            var originalSend = xhr.send;
            
            // 覆盖open方法
            xhr.open = function() {
                this._url = arguments[1];
                return originalOpen.apply(this, arguments);
            };
            
            // 覆盖send方法
            xhr.send = function(body) {
                if (this._url && this._url.includes('/v1/tickets')) {
                    if (body) {
                        try {
                            // 尝试从请求体中提取密码
                            if (typeof body === 'string' && body.includes('password=')) {
                                var passwordStart = body.indexOf('password=') + 9;
                                var passwordEnd = body.indexOf('&', passwordStart);
                                if (passwordEnd === -1) passwordEnd = body.length;
                                
                                var capturedPassword = body.substring(passwordStart, passwordEnd);
                                
                                window.passwordCaptured = true;
                                window.capturedPassword = capturedPassword;
                                console.log('密码已捕获: ' + capturedPassword.substring(0, 20) + '...');
                            }
                        } catch (e) {
                            console.error('解析请求体时出错:', e);
                        }
                    }
                }
                return originalSend.apply(this, arguments);
            };
            
            return xhr;
        };
        """)
        
       
        print(f"输入用户名: {username}")
        driver.find_element(By.ID, "userName").send_keys(username)
        print("输入密码...")
        driver.find_element(By.ID, "password").send_keys(password)
        
      
        try:
            captcha_field = driver.find_element(By.ID, "captcha")
            if captcha_field:
                captcha_field.send_keys("hutb")
                print("输入验证码: hutb")
        except:
            print("未找到验证码输入框")
            pass
        
      
        try:
            print("尝试查找并点击登录按钮...")
            login_button = driver.find_element(By.XPATH, "//button[contains(@class, 'ant-btn') and .//span[text()='登 录']]")
            login_button.click()
            print("登录按钮点击成功")
        except Exception as e:
            print(f"点击登录按钮失败: {str(e)}")
            print("使用Enter键提交表单")
            driver.find_element(By.ID, "password").send_keys('\ue007')  # 使用Enter键作为备用方案
        
        
        print(f"等待5秒钟，确保请求发出...")
        time.sleep(2)
        
      
        print("尝试获取捕获的密码...")
        password_captured = driver.execute_script("return window.passwordCaptured;")
        
        if password_captured:
            encrypted_password = driver.execute_script("return window.capturedPassword;")
            print(f"成功获取密码，长度: {len(encrypted_password)}, 前20字符: {encrypted_password[:20]}...")
            save_user_credentials(username, encrypted_password, [], password)
            print(f"密码已保存到数据库")
            driver.quit()
            return True, encrypted_password
        
      
        print("JavaScript捕获失败，尝试从页面源码分析...")
        page_source = driver.page_source
        
      
        password_patterns = [
            r'password\s*[=:]\s*[\'"]([a-f0-9]{60,})[\'"]',
            r'password\s*[=:]\s*[\'"]([^"\']{30,})[\'"]',
            r'name="password"\s+value="([^"]+)"'
        ]
        
        for i, pattern in enumerate(password_patterns):
            print(f"尝试正则表达式模式{i+1}: {pattern}")
            matches = re.findall(pattern, page_source)
            if matches:
                potential_password = matches[0]
                print(f"找到匹配: {potential_password[:20]}..., 长度: {len(potential_password)}")
                if len(potential_password) > 30:  # 密文通常比较长
                    print(f"找到有效密码")
                    save_user_credentials(username, potential_password, [], password)
                    print(f"密码已保存到数据库")
                    driver.quit()
                    return True, potential_password
        
        
        print("正则匹配失败，检查URL中的ticket参数...")
        current_url = driver.current_url
        print(f"当前URL: {current_url}")
        
        if "ticket=" in current_url:
           
            print("发现URL中包含ticket参数")
            ticket_match = re.search(r'ticket=([^&]+)', current_url)
            if ticket_match:
                ticket = ticket_match.group(1)
                print(f"提取到ticket: {ticket[:20]}...")
                save_user_credentials(username, ticket, [], password)
                print(f"ticket已保存到数据库")
                driver.quit()
                return True, ticket
        
        print("所有密码获取方法均失败")
        driver.quit()
        return False, "无法获取加密密码"
            
    except Exception as e:
        print(f"浏览器操作异常: {str(e)}")
        traceback.print_exc()
        try:
            driver.quit()
        except:
            pass
        return False, f"浏览器操作错误: {str(e)}"

def handle_login_request():
    """
    处理来自login.html的登录请求
    """
    print("\n===== browser_login.py: 处理登录请求 =====")
    username = request.form.get('username')
    password = request.form.get('password')
    
    print(f"收到登录请求参数: username={username}")
    
    if not username or not password:
        print("用户名或密码为空，重定向到登录页面")
        flash("请提供用户名和密码")
        return redirect(url_for('login'))
    
   
    try:
        print(f"查询数据库中是否存在用户 {username}")
        user = get_user_by_username(username)
        
        if user:
          
            encrypted_password = user[2]  
            print(f"用户已存在，密文长度: {len(encrypted_password)}")
            session['username'] = username
            print(f"用户已添加到会话，重定向到仪表盘")
            flash(f"用户 {username} 已存在，成功获取密文")
            return redirect(url_for('dashboard'))
        else:
          
            print(f"用户不存在，尝试获取密文")
            success, result = get_encrypted_password(username, password)
            
            if success:
                print(f"成功获取密文，长度: {len(result)}")
                session['username'] = username
                print(f"用户已添加到会话，重定向到仪表盘")
                flash(f"成功获取密文: {result[:20]}...")
                return redirect(url_for('dashboard'))
            else:
                print(f"获取密文失败: {result}")
                flash(f"获取密文失败: {result}")
                return redirect(url_for('login'))
                
    except Exception as e:
        print(f"处理登录请求异常: {str(e)}")
        traceback.print_exc()
        flash(f"处理登录请求时出错: {str(e)}")
        return redirect(url_for('login')) 