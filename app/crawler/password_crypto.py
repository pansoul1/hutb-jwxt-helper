# -*- coding: utf-8 -*-
"""
HUTB 教务系统密码加密（前端同款 RSA/PKCS#1 v1.5）
"""
import binascii
import logging
from Crypto.PublicKey import RSA

# 配置日志
logger = logging.getLogger('password_crypto')

class PasswordCrypto:
    """
    教务系统密码加密器
    实现与前端JavaScript完全一致的RSA加密算法
    """
    
    def __init__(self):
        """初始化加密器，设置固定的RSA公钥参数"""
        # 固定公钥参数（从前端JS逆向得到）
        self.MODULUS_HEX = (
            "00b5eeb166e069920e80bebd1fea4829d3d1f3216f2aabe79b6c47a3c18dcee5"
            "fd22c2e7ac519cab59198ece036dcf289ea8201e2a0b9ded307f8fb704136eae"
            "b670286f5ad44e691005ba9ea5af04ada5367cd724b5a26fdb5120cc95b64316"
            "04bd219c6b7d83a6f8f24b43918ea988a76f93c333aa5a20991493d4eb1117e7"
            "b1"
        )
        self.EXPONENT_HEX = "010001"  # 65537
        
        # 构造RSA公钥对象
        n = int(self.MODULUS_HEX, 16)
        e = int(self.EXPONENT_HEX, 16)
        self.pub_key = RSA.construct((n, e))
        
        # 计算密钥长度参数
        self.KEY_BYTE_LEN = (self.pub_key.size_in_bits() + 7) // 8  # 256 字节
        self.CHUNK_SIZE = self.KEY_BYTE_LEN - 2                      # 254 字节
        
        logger.debug(f"密码加密器初始化完成，密钥长度: {self.KEY_BYTE_LEN} 字节")
    
    def encrypt_password(self, plaintext_password):
        """
        加密密码，使用与前端JS完全一致的算法
        
        参数:
            plaintext_password: 明文密码字符串
            
        返回:
            str: 加密后的十六进制字符串
        """
        try:
            logger.debug(f"开始加密密码，长度: {len(plaintext_password)}")
            
            # 转换为字节
            if isinstance(plaintext_password, str):
                plaintext = plaintext_password.encode('utf-8')
            else:
                plaintext = plaintext_password
            
            # 检查密码长度
            if len(plaintext) > self.CHUNK_SIZE:
                raise ValueError(f"密码长度超出限制：{len(plaintext)} > {self.CHUNK_SIZE}")
            
            # 按前端算法补零到254字节（256-2）
            padded = bytearray(plaintext)
            padded.extend(b"\x00" * (self.CHUNK_SIZE - len(padded)))
            logger.debug(f"填充后长度: {len(padded)} 字节")
            
            # 按小端序转成整数（前端每两个字节组成16bit little-endian单元）
            plain_int = int.from_bytes(padded, byteorder="little")
            
            # 模幂运算（c = m^e mod n）
            cipher_int = pow(plain_int, self.pub_key.e, self.pub_key.n)
            
            # 转成固定256字节的大端字节串，再十六进制输出
            cipher_bytes = cipher_int.to_bytes(self.KEY_BYTE_LEN, byteorder="big")
            cipher_hex = binascii.hexlify(cipher_bytes).decode()
            
            logger.debug(f"密码加密成功，密文长度: {len(cipher_hex)} 字符")
            logger.debug(f"密文前20字符: {cipher_hex[:20]}")
            
            return cipher_hex
            
        except Exception as e:
            logger.error(f"密码加密失败: {str(e)}")
            raise e
    
    def test_encryption(self, test_password="Psy20030413.."):
        """
        测试加密功能
        
        参数:
            test_password: 测试密码
            
        返回:
            str: 加密结果
        """
        logger.info(f"测试密码加密功能，测试密码: {test_password}")
        try:
            result = self.encrypt_password(test_password)
            logger.info(f"测试成功，结果: {result[:40]}...")
            return result
        except Exception as e:
            logger.error(f"测试失败: {str(e)}")
            raise e

# 创建全局加密器实例
password_crypto = PasswordCrypto()

def encrypt_password(plaintext_password):
    """
    便捷的密码加密函数
    
    参数:
        plaintext_password: 明文密码
        
    返回:
        str: 加密后的十六进制字符串
    """
    return password_crypto.encrypt_password(plaintext_password)

# 测试加密功能（如果直接运行此文件）
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # 测试加密
    test_crypto = PasswordCrypto()
    test_result = test_crypto.test_encryption()
    print(f"测试结果: {test_result}")