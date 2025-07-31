"""
路由模块初始化文件
"""
from .main import main_bp
from .images import images_bp
from .errors import errors_bp

def register_blueprints(app):
    """
    注册所有蓝图
    
    Args:
        app: Flask应用实例
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(errors_bp)