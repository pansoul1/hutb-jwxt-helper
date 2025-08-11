#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
湖南工商大学忘记密码功能路由
集成到Flask应用
"""

from flask import Blueprint, render_template, request, jsonify, session, current_app
import requests
import json
import time
import re
import uuid
from typing import Dict, Tuple, Optional
import logging
import base64
import tempfile
import os
import traceback
from io import BytesIO
from PIL import Image
from openai import OpenAI
from app.utils.token_generator import HutbTokenGenerator

# 创建忘记密码蓝图
password_reset_bp = Blueprint('password_reset', __name__, url_prefix='/forgot-password')

# 设置日志
logger = logging.getLogger(__name__)

class PasswordResetService:
    """密码重置服务类"""
    
    def __init__(self):
        self.base_url = "https://cas.hutb.edu.cn/sc"
        self.token_generator = HutbTokenGenerator()
        
        # 初始化AI客户端，用于验证码识别
        self.ai_client = OpenAI(
            api_key="..",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 设置基本headers
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://cas.hutb.edu.cn',
            'Referer': 'https://cas.hutb.edu.cn/sc/',
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def _generate_session_id(self) -> str:
        """生成会话ID"""
        return str(uuid.uuid4()).replace('-', '')
    
    def _generate_tokens(self) -> Dict[str, str]:
        """生成所有需要的token"""
        tokens = self.token_generator.generate_all_tokens()
        logger.debug(f"生成Token: csrftoken={tokens['csrftoken'][:8]}..., timestamp={tokens['csrftimestamp']}")
        return tokens
    
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
    
    def _make_request(self, method: str, url: str, headers: Dict = None, data: Dict = None) -> Tuple[bool, Dict]:
        """统一的HTTP请求方法"""
        try:
            request_headers = self.default_headers.copy()
            if headers:
                request_headers.update(headers)
            
            response = requests.request(method, url, headers=request_headers, json=data, timeout=30)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return True, result
                except json.JSONDecodeError:
                    return False, {'error': '响应格式错误'}
            else:
                return False, {'error': f'HTTP错误: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"请求异常: {e}")
            return False, {'error': f'网络请求失败: {str(e)}'}
    
    def get_captcha(self) -> Tuple[bool, str, bytes]:
        """获取验证码图片"""
        try:
            # 生成验证码会话ID
            session_id = self._generate_session_id()
            kaptcha_id = session_id + 'lyasp'
            
            timestamp = int(time.time() * 1000)
            captcha_url = f"{self.base_url}/api/uap/unauthorize/safe/pass/kaptcha/{kaptcha_id}?t={timestamp}"
            
            logger.info(f"获取验证码: {captcha_url}")
            response = requests.get(captcha_url, headers=self.default_headers, timeout=30)
            
            if response.status_code == 200:
                # 保存到session
                session['reset_state'] = session.get('reset_state', {})
                session['reset_state']['kaptcha_id'] = kaptcha_id
                session['reset_state']['current_step'] = 1
                session.permanent = True  # 设置session持久化
                
                logger.info("验证码获取成功")
                return True, "验证码获取成功", response.content
            else:
                return False, f"验证码获取失败: {response.status_code}", b''
                
        except Exception as e:
            logger.error(f"获取验证码异常: {e}")
            return False, f"获取验证码异常: {e}", b''
    
    def verify_captcha(self, captcha_code: str) -> Tuple[bool, str]:
        """验证验证码"""
        reset_state = session.get('reset_state', {})
        kaptcha_id = reset_state.get('kaptcha_id')
        
        if not kaptcha_id:
            return False, "会话已过期，请重新获取验证码"
        
        try:
            url = f"{self.base_url}/api/uap/unauthorize/safe/pass/kaptcha/{kaptcha_id}"
            tokens = self._generate_tokens()
            
            headers = {
                'Content-Type': 'application/json',
                'csrftimestamp': str(tokens['csrftimestamp']),
                'csrftoken': tokens['csrftoken'],
                'loginusertoken': tokens['loginusertoken'],
            }
            
            data = {"kaptcha": captcha_code}
            
            success, result = self._make_request('POST', url, headers, data)
            
            if success and result.get('meta', {}).get('success'):
                captcha_pass_id = result.get('data')
                
                # 更新session状态
                session['reset_state']['captcha_pass_id'] = captcha_pass_id
                session['reset_state']['current_step'] = 2
                
                logger.info(f"验证码验证成功: {captcha_pass_id}")
                return True, "验证码验证成功"
            else:
                return False, result.get('meta', {}).get('message', '验证码验证失败')
                
        except Exception as e:
            logger.error(f"验证码验证异常: {e}")
            return False, f"验证码验证异常: {e}"
    
    def identity_verification(self, username: str, id_card: str) -> Tuple[bool, str]:
        """身份验证"""
        reset_state = session.get('reset_state', {})
        
        if not reset_state.get('captcha_pass_id'):
            return False, "请先完成验证码验证"
        
        try:
            url = f"{self.base_url}/api/uap/unauthorize/safe/pass/identityAuth"
            tokens = self._generate_tokens()
            
            headers = {
                'Content-Type': 'application/json',
                'csrftimestamp': str(tokens['csrftimestamp']),
                'csrftoken': tokens['csrftoken'],
                'loginuserid': username,
                'loginusertoken': tokens['loginusertoken'],
            }
            
            data = {
                "account": username,
                "idCard": id_card,
                "kaptchaId": reset_state['kaptcha_id'],
                "kaptchaPassId": reset_state['captcha_pass_id']
            }
            
            success, result = self._make_request('POST', url, headers, data)
            
            if success and result.get('meta', {}).get('success'):
                data_info = result.get('data', {})
                
                # 更新session状态
                session['reset_state']['identity_pass_id'] = data_info.get('identityBaseInfoPassId')
                session['reset_state']['login_user_id'] = data_info.get('loginUserId')
                session['reset_state']['username'] = username
                session['reset_state']['current_step'] = 3
                
                logger.info(f"身份验证成功")
                return True, "身份验证成功"
            else:
                return False, result.get('meta', {}).get('message', '身份验证失败')
                
        except Exception as e:
            logger.error(f"身份验证异常: {e}")
            return False, f"身份验证异常: {e}"
    
    def get_recovery_options(self) -> Tuple[bool, str, str]:
        """获取找回方式"""
        reset_state = session.get('reset_state', {})
        
        if not reset_state.get('identity_pass_id'):
            return False, "请先完成身份验证", ""
        
        try:
            tokens = self._generate_tokens()
            timestamp = tokens['csrftimestamp']
            url = f"{self.base_url}/api/uap/unauthorize/safe/pass/recoverPass?_t={timestamp}"
            
            headers = {
                'identitybaseinfopassid': reset_state['identity_pass_id'],
                'loginuserid': reset_state['login_user_id'],
                'csrftimestamp': str(timestamp),
                'csrftoken': tokens['csrftoken'],
                'loginusertoken': tokens['loginusertoken']
            }
            
            success, result = self._make_request('GET', url, headers)
            
            if success and result.get('meta', {}).get('success'):
                data_info = result.get('data', {})
                encrypted_phone = data_info.get('phone')
                phone_hide = data_info.get('phoneHide')
                
                # 更新session状态
                session['reset_state']['encrypted_phone'] = encrypted_phone
                session['reset_state']['phone_hide'] = phone_hide
                session['reset_state']['current_step'] = 4
                
                logger.info(f"找回方式获取成功，手机号: {phone_hide}")
                return True, "找回方式获取成功", phone_hide
            else:
                return False, result.get('meta', {}).get('message', '获取找回方式失败'), ""
                
        except Exception as e:
            logger.error(f"获取找回方式异常: {e}")
            return False, f"获取找回方式异常: {e}", ""
    
    def send_sms_code(self) -> Tuple[bool, str]:
        """发送短信验证码"""
        reset_state = session.get('reset_state', {})
        logger.info(f"发送短信验证码，当前状态: {reset_state}")
        
        if not reset_state.get('encrypted_phone'):
            logger.warning("没有加密手机号，无法发送短信")
            return False, "请先获取找回方式"
        
        try:
            url = f"{self.base_url}/api/uap/unauthorize/accountSecurity/account/mobile/generateCode"
            
            # 生成token并设置headers（可能需要认证）
            tokens = self._generate_tokens()
            
            headers = {
                'Content-Type': 'application/json',
                'csrftimestamp': str(tokens['csrftimestamp']),
                'csrftoken': tokens['csrftoken'],
                'loginusertoken': tokens['loginusertoken'],
                'identitybaseinfopassid': reset_state.get('identity_pass_id', ''),
                'loginuserid': reset_state.get('login_user_id', ''),
            }
            
            data = {
                "mobile": reset_state['encrypted_phone'],
                "isRecord": "2",
                "type": "msmContentFoundPassword"
            }
            
            logger.info(f"发送短信请求: {url}")
            logger.info(f"请求数据: {data}")
            logger.info(f"请求头: {headers}")
            
            success, result = self._make_request('POST', url, headers, data)
            
            logger.info(f"短信发送响应: success={success}, result={result}")
            
            if success and result.get('meta', {}).get('success'):
                session['reset_state']['current_step'] = 5
                logger.info("短信验证码发送成功")
                return True, "短信验证码发送成功"
            else:
                error_msg = result.get('meta', {}).get('message', '短信发送失败')
                logger.warning(f"短信发送失败: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"发送短信异常: {e}")
            return False, f"发送短信异常: {e}"
    
    def verify_sms_code(self, sms_code: str) -> Tuple[bool, str]:
        """验证短信验证码"""
        reset_state = session.get('reset_state', {})
        
        if not reset_state.get('encrypted_phone'):
            return False, "请先发送短信验证码"
        
        try:
            url = f"{self.base_url}/api/uap/unauthorize/accountSecurity/account/mobile/validate"
            
            # 添加认证headers
            tokens = self._generate_tokens()
            
            headers = {
                'Content-Type': 'application/json',
                'csrftimestamp': str(tokens['csrftimestamp']),
                'csrftoken': tokens['csrftoken'],
                'loginusertoken': tokens['loginusertoken'],
                'identitybaseinfopassid': reset_state.get('identity_pass_id', ''),
                'loginuserid': reset_state.get('login_user_id', ''),
            }
            
            data = {
                "mobile": reset_state['encrypted_phone'],
                "code": sms_code,
                "type": "2"
            }
            
            logger.info(f"验证短信请求: {url}")
            logger.info(f"请求数据: {data}")
            
            success, result = self._make_request('POST', url, headers, data)
            
            if success and result.get('meta', {}).get('success') and result.get('data') is True:
                session['reset_state']['current_step'] = 6
                logger.info("短信验证码验证成功")
                return True, "短信验证码验证成功"
            else:
                error_msg = result.get('meta', {}).get('message', '短信验证码错误')
                logger.warning(f"短信验证失败: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"验证短信异常: {e}")
            return False, f"验证短信异常: {e}"
    
    def set_new_password(self, new_password: str) -> Tuple[bool, str]:
        """设置新密码"""
        reset_state = session.get('reset_state', {})
        username = reset_state.get('username')
        
        if not username or reset_state.get('current_step') != 6:
            return False, "请完成前面的验证步骤"
        
        # 验证密码强度
        if not self._validate_password(new_password):
            return False, "密码不符合要求：8-24位，至少包含1位数字、1位小写字母、1位特殊字符，不能包含空格"
        
        try:
            url = f"{self.base_url}/api/uap/unauthorize/safe/pass/found"
            
            # 添加认证headers
            tokens = self._generate_tokens()
            
            headers = {
                'Content-Type': 'application/json',
                'csrftimestamp': str(tokens['csrftimestamp']),
                'csrftoken': tokens['csrftoken'],
                'loginusertoken': tokens['loginusertoken'],
                'identitybaseinfopassid': reset_state.get('identity_pass_id', ''),
                'loginuserid': reset_state.get('login_user_id', ''),
            }
            
            data = {
                "userId": username,
                "userPassword": new_password,
                "passStrong": 4,
                "foundType": "1"
            }
            
            logger.info(f"设置新密码请求: {url}")
            logger.info(f"请求数据: {data}")
            
            success, result = self._make_request('POST', url, headers, data)
            
            if success and result.get('meta', {}).get('success') and result.get('data') is True:
                # 清除session状态
                session.pop('reset_state', None)
                logger.info("密码设置成功")
                return True, "密码重置成功"
            else:
                error_msg = result.get('meta', {}).get('message', '密码设置失败')
                logger.warning(f"密码设置失败: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"设置密码异常: {e}")
            return False, f"设置密码异常: {e}"
    
    def _validate_password(self, password: str) -> bool:
        """验证密码强度"""
        if len(password) < 8 or len(password) > 24:
            return False
        if ' ' in password:
            return False
        
        has_digit = bool(re.search(r'\d', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_special = bool(re.search(r'[^a-zA-Z0-9]', password))
        
        return has_digit and has_lower and has_special


# 创建服务实例
password_reset_service = PasswordResetService()


@password_reset_bp.route('/', methods=['GET'])
def forgot_password_page():
    """忘记密码页面"""
    # 清除旧的session状态
    session.pop('reset_state', None)
    return render_template('forgot_password.html')


@password_reset_bp.route('/step1', methods=['POST'])
def step1_get_captcha():
    """第一步：获取验证码并自动识别"""
    try:
        success, message, captcha_image = password_reset_service.get_captcha()
        
        if success:
            # 转换为base64用于AI识别
            import base64
            captcha_base64 = base64.b64encode(captcha_image).decode('utf-8')
            captcha_data_url = f'data:image/png;base64,{captcha_base64}'
            
            # 使用AI自动识别验证码
            logger.info("开始AI识别验证码...")
            ai_result = password_reset_service.recognize_captcha(captcha_data_url)
            
            if ai_result:
                logger.info(f"AI识别验证码成功: {ai_result}")
                
                # 自动验证识别结果
                verify_success, verify_message = password_reset_service.verify_captcha(ai_result)
                
                if verify_success:
                    logger.info("验证码自动验证成功")
                    return jsonify({
                        'success': True,
                        'message': f'验证码自动识别成功: {ai_result}',
                        'captcha_image': captcha_data_url,
                        'ai_result': ai_result,
                        'auto_verified': True
                    })
                else:
                    logger.warning(f"AI识别结果验证失败: {verify_message}")
                    return jsonify({
                        'success': False,
                        'message': f'AI识别验证码失败({ai_result})，请手动输入: {verify_message}',
                        'captcha_image': captcha_data_url,
                        'ai_result': ai_result,
                        'auto_verified': False
                    })
            else:
                logger.warning("AI识别验证码失败")
                return jsonify({
                    'success': False,
                    'message': 'AI识别验证码失败，请手动输入',
                    'captcha_image': captcha_data_url,
                    'ai_result': None,
                    'auto_verified': False
                })
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"获取验证码异常: {e}")
        return jsonify({'success': False, 'message': f'系统异常: {str(e)}'})


@password_reset_bp.route('/step2', methods=['POST'])
def step2_verify_captcha():
    """第二步：验证验证码"""
    try:
        data = request.get_json()
        captcha_code = data.get('captcha_code', '').strip()
        
        if not captcha_code:
            return jsonify({'success': False, 'message': '请输入验证码'})
        
        success, message = password_reset_service.verify_captcha(captcha_code)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"验证验证码异常: {e}")
        return jsonify({'success': False, 'message': f'系统异常: {str(e)}'})


@password_reset_bp.route('/step3', methods=['POST'])
def step3_identity_verification():
    """第三步：身份验证"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        id_card = data.get('id_card', '').strip()
        
        if not username or not id_card:
            return jsonify({'success': False, 'message': '请输入学号和身份证号'})
        
        success, message = password_reset_service.identity_verification(username, id_card)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"身份验证异常: {e}")
        return jsonify({'success': False, 'message': f'系统异常: {str(e)}'})


@password_reset_bp.route('/step4', methods=['POST'])
def step4_get_recovery_options():
    """第四步：获取找回方式"""
    try:
        success, message, phone_hide = password_reset_service.get_recovery_options()
        
        return jsonify({
            'success': success,
            'message': message,
            'phone_hide': phone_hide if success else ''
        })
        
    except Exception as e:
        logger.error(f"获取找回方式异常: {e}")
        return jsonify({'success': False, 'message': f'系统异常: {str(e)}'})


@password_reset_bp.route('/step5', methods=['POST'])
def step5_send_sms():
    """第五步：发送短信验证码"""
    try:
        success, message = password_reset_service.send_sms_code()
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"发送短信异常: {e}")
        return jsonify({'success': False, 'message': f'系统异常: {str(e)}'})


@password_reset_bp.route('/step6', methods=['POST'])
def step6_verify_sms():
    """第六步：验证短信验证码"""
    try:
        data = request.get_json()
        sms_code = data.get('sms_code', '').strip()
        
        if not sms_code:
            return jsonify({'success': False, 'message': '请输入短信验证码'})
        
        success, message = password_reset_service.verify_sms_code(sms_code)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"验证短信异常: {e}")
        return jsonify({'success': False, 'message': f'系统异常: {str(e)}'})


@password_reset_bp.route('/step7', methods=['POST'])
def step7_set_password():
    """第七步：设置新密码"""
    try:
        data = request.get_json()
        new_password = data.get('new_password', '').strip()
        
        if not new_password:
            return jsonify({'success': False, 'message': '请输入新密码'})
        
        success, message = password_reset_service.set_new_password(new_password)
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        logger.error(f"设置密码异常: {e}")
        return jsonify({'success': False, 'message': f'系统异常: {str(e)}'})


@password_reset_bp.route('/status', methods=['GET'])
def get_reset_status():
    """获取当前重置状态"""
    reset_state = session.get('reset_state', {})
    current_step = reset_state.get('current_step', 0)
    
    return jsonify({
        'current_step': current_step,
        'phone_hide': reset_state.get('phone_hide', ''),
        'has_session': bool(reset_state)
    })