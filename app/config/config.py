"""
配置类模块
"""
import os
import logging

class Config:
    """基础配置类"""
    # 应用基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    DEBUG = False
    TESTING = False
    PORT = int(os.environ.get('PORT') or 50721)  # 使用不同的端口
    APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 图像相关配置
    IMAGE_BASE = 'images'
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    THUMBNAIL_SIZE = (200, 200)
    
    # 限流相关配置
    DEFAULT_LIMITS = ["500 per hour"]
    BAN_DURATION = 3600  # 1小时封禁
    
    # 模板配置
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
    
    # 静态文件配置
    STATIC_FOLDER = 'app/static'
    
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
    # 生产环境可以从环境变量获取密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-hard-to-guess-string'
    
    # 生产环境可以调整限流策略
    DEFAULT_LIMITS = ["300 per hour"]
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
