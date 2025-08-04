"""
管理员工具模块 - 提供管理员密码验证和会话管理
"""
import os
import json
import hashlib
import secrets
from functools import wraps
from flask import session, redirect, url_for, flash

# 管理员配置文件路径
ADMIN_CONFIG_FILE = 'admin_config.json'

# 默认管理员用户名
DEFAULT_ADMIN_USERNAME = 'admin'

def hash_password(password):
    """
    对密码进行哈希处理
    
    Args:
        password: 原始密码
        
    Returns:
        哈希后的密码
    """
    # 使用SHA-256算法对密码进行哈希
    return hashlib.sha256(password.encode()).hexdigest()

def is_password_set():
    """
    检查管理员密码是否已设置
    
    Returns:
        是否已设置密码
    """
    return os.path.exists(ADMIN_CONFIG_FILE)

def set_admin_password(password):
    """
    设置管理员密码
    
    Args:
        password: 要设置的密码
        
    Returns:
        是否设置成功
    """
    try:
        # 生成随机盐值
        salt = secrets.token_hex(16)
        
        # 哈希密码（加盐）
        hashed_password = hash_password(password + salt)
        
        # 保存到配置文件
        config = {
            'password_hash': hashed_password,
            'salt': salt
        }
        
        with open(ADMIN_CONFIG_FILE, 'w') as f:
            json.dump(config, f)
            
        return True
    except Exception as e:
        print(f"设置管理员密码时出错: {str(e)}")
        return False

def verify_admin_password(password):
    """
    验证管理员密码
    
    Args:
        password: 要验证的密码
        
    Returns:
        密码是否正确
    """
    try:
        # 读取配置文件
        with open(ADMIN_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
        # 获取存储的哈希密码和盐值
        stored_hash = config.get('password_hash')
        salt = config.get('salt')
        
        if not stored_hash or not salt:
            return False
            
        # 计算输入密码的哈希值
        input_hash = hash_password(password + salt)
        
        # 比较哈希值
        return input_hash == stored_hash
    except Exception as e:
        print(f"验证管理员密码时出错: {str(e)}")
        return False

def login_required(f):
    """
    管理员登录验证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('请先登录', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function