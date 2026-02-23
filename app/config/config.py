"""
配置类模块
"""
import os
import logging

class Config:
    """基础配置类"""
    # 应用基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    PORT = int(os.environ.get('PORT') or 50721)  # 使用不同的端口
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 图像相关配置
    IMAGE_BASE = 'images'
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    THUMBNAIL_SIZE = (300, 300)  # 管理面板中的缩略图尺寸
    
    # 限流相关配置
    DEFAULT_LIMITS = ["500 per hour"]
    BAN_DURATION = 3600  # 1小时封禁
    
    # 缓存相关配置
    CACHE_TTL = 3600  # 缓存过期时间（秒）
    
    # 可信代理配置（用于获取真实 IP）
    TRUSTED_PROXIES = []  # 可通过环境变量 TRUSTED_PROXIES 设置，如：192.168.1.0/24,10.0.0.0/8
    
    # Redis 配置（用于限流存储）
    REDIS_URL = os.environ.get('REDIS_URL')  # 如：redis://localhost:6379/0
    
    # 模板配置
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    
    # 静态文件配置（使用绝对路径）
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    
    # 日志配置
    LOG_LEVEL = logging.DEBUG
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class ProductionConfig(Config):
    """生产环境配置"""
    # 生产环境必须设置 SECRET_KEY
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # 生产环境可以调整限流策略
    DEFAULT_LIMITS = ["300 per hour"]
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 强制要求生产环境设置 SECRET_KEY
        if not cls.SECRET_KEY:
            raise RuntimeError(
                "生产环境必须设置 SECRET_KEY 环境变量！\n"
                "请运行: export SECRET_KEY='your-random-secret-key'\n"
                "或生成随机密钥: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        
        # 解析可信代理列表
        trusted_proxies = os.environ.get('TRUSTED_PROXIES', '')
        if trusted_proxies:
            cls.TRUSTED_PROXIES = [p.strip() for p in trusted_proxies.split(',') if p.strip()]
