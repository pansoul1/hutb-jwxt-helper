#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
湖南工商大学Token生成器
基于JS逆向分析实现
"""

import hashlib
import time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64
import binascii

class HutbTokenGenerator:
    """湖南工商大学Token生成器"""
    
    def __init__(self):
        # 从JS中提取的常量
        self.GATEWAY_KEY = "lianyi2019"
        self.TAG = "lyasp"
        self.PUBLIC_EXPONENT = "010001"
        self.MODULUS = "00b5eeb166e069920e80bebd1fea4829d3d1f3216f2aabe79b6c47a3c18dcee5fd22c2e7ac519cab59198ece036dcf289ea8201e2a0b9ded307f8fb704136eaeb670286f5ad44e691005ba9ea5af04ada5367cd724b5a26fdb5120cc95b6431604bd219c6b7d83a6f8f24b43918ea988a76f93c333aa5a20991493d4eb1117e7b1"
        
        # 初始化RSA密钥
        self._init_rsa()
    
    def _init_rsa(self):
        """初始化RSA公钥"""
        try:
            # 将十六进制字符串转换为整数
            n = int(self.MODULUS, 16)
            e = int(self.PUBLIC_EXPONENT, 16)
            
            # 构造RSA公钥
            self.rsa_key = RSA.construct((n, e))
            self.cipher = PKCS1_v1_5.new(self.rsa_key)
            print(f"RSA密钥初始化成功，密钥长度: {self.rsa_key.size_in_bits()} bits")
        except Exception as ex:
            print(f"RSA密钥初始化失败: {ex}")
            self.rsa_key = None
            self.cipher = None
    
    def generate_csrf_token(self, timestamp=None):
        """
        生成CSRF Token
        
        JavaScript逻辑:
        var s = (new Date).valueOf()
        var c = a.i(p.a)("timestamp=" + s + ",key=" + d.a.GATEWAY_KEY);
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)  # JavaScript的valueOf()
        
        # 构造输入字符串
        input_string = f"timestamp={timestamp},key={self.GATEWAY_KEY}"
        
        # MD5加密
        csrf_token = hashlib.md5(input_string.encode('utf-8')).hexdigest()
        
        return csrf_token, timestamp
    
    def generate_login_user_token(self, timestamp=None):
        """
        生成LoginUserToken
        
        JavaScript逻辑:
        var i = a.i(u.b)(d.a.public_exponent, "", d.a.modulus)
        var m = a.i(u.c)(i, d.a.TAG + r);
        """
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        if not self.cipher:
            print("警告: RSA密钥未初始化，返回空token")
            return ""
        
        try:
            # 构造要加密的数据: TAG + timestamp
            data_to_encrypt = f"{self.TAG}{timestamp}"
            
            # RSA加密
            encrypted_data = self.cipher.encrypt(data_to_encrypt.encode('utf-8'))
            
            # 转换为十六进制字符串
            login_user_token = binascii.hexlify(encrypted_data).decode('utf-8')
            
            return login_user_token
            
        except Exception as e:
            print(f"生成LoginUserToken失败: {e}")
            return ""
    
    def generate_all_tokens(self):
        """一次生成所有需要的token"""
        timestamp = int(time.time() * 1000)
        
        csrf_token, _ = self.generate_csrf_token(timestamp)
        login_user_token = self.generate_login_user_token(timestamp)
        
        return {
            'csrftoken': csrf_token,
            'csrftimestamp': timestamp,
            'loginusertoken': login_user_token
        }
    
    def test_tokens(self):
        """测试token生成"""
        print("=== 湖南工商大学Token生成器测试 ===")
        
        # 测试CSRF Token
        csrf_token, timestamp = self.generate_csrf_token()
        print(f"时间戳: {timestamp}")
        print(f"输入字符串: timestamp={timestamp},key={self.GATEWAY_KEY}")
        print(f"CSRF Token: {csrf_token}")
        print(f"CSRF Token长度: {len(csrf_token)}")
        
        # 测试LoginUserToken  
        login_user_token = self.generate_login_user_token(timestamp)
        print(f"LoginUserToken: {login_user_token}")
        print(f"LoginUserToken长度: {len(login_user_token)}")
        
        # 生成完整的token集合
        all_tokens = self.generate_all_tokens()
        print("\n=== 完整Token集合 ===")
        for key, value in all_tokens.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    generator = HutbTokenGenerator()
    generator.test_tokens()