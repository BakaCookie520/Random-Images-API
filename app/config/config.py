"""
配置类模块
"""
import os

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
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 开发环境特定配置
        import logging
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(levelname)s - %(message)s')


class ProductionConfig(Config):
    """生产环境配置"""
    # 生产环境可以从环境变量获取密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-hard-to-guess-string'
    
    # 生产环境可以调整限流策略
    DEFAULT_LIMITS = ["300 per hour"]
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生产环境特定配置
        import logging
        from logging.handlers import RotatingFileHandler
        
        # 创建日志目录
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # 配置文件日志
        file_handler = RotatingFileHandler('logs/random_images_api.log',
                                          maxBytes=10485760,  # 10MB
                                          backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # 添加到应用日志
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Random Images API 启动')