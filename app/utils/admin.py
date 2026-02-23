"""
管理员工具模块 - 提供管理员密码验证和会话管理
"""
import os
import json
import logging
import secrets
from functools import wraps
from flask import session, redirect, url_for, flash

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# 配置日志
logger = logging.getLogger(__name__)

# 管理员配置文件路径（存放在安全的配置目录）
CONFIG_DIR = os.environ.get('CONFIG_DIR', 'config')
ADMIN_CONFIG_FILE = os.path.join(CONFIG_DIR, '.admin_credentials.json')

# 默认管理员用户名
DEFAULT_ADMIN_USERNAME = 'admin'

def hash_password(password):
    """
    对密码进行哈希处理（使用 bcrypt）
    
    Args:
        password: 原始密码
        
    Returns:
        哈希后的密码（bcrypt 格式）
    """
    if BCRYPT_AVAILABLE:
        # 使用 bcrypt 进行安全的密码哈希
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    else:
        # 回退到 SHA-256（不推荐，仅用于开发环境）
        import hashlib
        logger.warning("bcrypt 未安装，使用 SHA-256 作为回退（不安全）")
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
        # 确保配置目录存在
        os.makedirs(os.path.dirname(ADMIN_CONFIG_FILE), exist_ok=True)
        
        # 哈希密码（bcrypt 已包含盐值）
        hashed_password = hash_password(password)
        
        # 保存到配置文件
        config = {
            'password_hash': hashed_password,
            'algorithm': 'bcrypt' if BCRYPT_AVAILABLE else 'sha256'
        }
        
        # 写入文件并设置权限（仅所有者可读写）
        with open(ADMIN_CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        
        # 设置文件权限（仅 Unix-like 系统）
        if os.name != 'nt':  # 非 Windows 系统
            os.chmod(ADMIN_CONFIG_FILE, 0o600)
            
        logger.info("管理员密码设置成功")
        return True
    except Exception as e:
        logger.error(f"设置管理员密码时出错: {str(e)}")
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
            
        # 获取存储的哈希密码
        stored_hash = config.get('password_hash')
        algorithm = config.get('algorithm', 'sha256')
        
        if not stored_hash:
            return False
        
        # 根据算法类型验证
        if algorithm == 'bcrypt' and BCRYPT_AVAILABLE:
            # bcrypt 验证
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        else:
            # 旧版 SHA-256 验证（向后兼容）
            salt = config.get('salt')
            if salt:
                import hashlib
                input_hash = hashlib.sha256((password + salt).encode()).hexdigest()
                return input_hash == stored_hash
            return False
    except Exception as e:
        logger.error(f"验证管理员密码时出错: {str(e)}")
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