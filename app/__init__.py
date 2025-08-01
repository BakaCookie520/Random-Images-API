"""
应用程序初始化模块
"""
import os
import logging
import datetime
from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .config.config import Config
from .routes import register_blueprints
from .utils.file_monitor import setup_file_monitor
from .utils.security import cleanup_bans, is_banned, get_real_ip

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建限流器，使用优化后的IP获取函数
limiter = Limiter(
    key_func=get_real_ip,  # 使用自定义函数获取真实IP
    default_limits=["500 per hour"],
    storage_uri="memory://"
)

def create_app(config_class=Config):
    """
    创建并配置Flask应用
    
    Args:
        config_class: 配置类
        
    Returns:
        配置好的Flask应用实例
    """
    # 创建Flask应用实例，设置模板文件夹路径
    app = Flask(__name__, template_folder=config_class.TEMPLATE_FOLDER)
    
    # 应用配置
    app.config.from_object(config_class)
    
    # 初始化限流器
    limiter.init_app(app)
    
    # 添加自定义过滤器
    @app.template_filter('datetime')
    def format_datetime(timestamp):
        """将时间戳转换为可读的日期时间格式"""
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    # 注册蓝图
    register_blueprints(app)
    
    # 设置请求前处理函数
    @app.before_request
    def check_ban_status():
        """在每次请求前检查当前路径是否被封禁"""
        # 使用优化后的get_real_ip函数获取真实IP
        client_ip = get_real_ip()
        current_path = request.path
        banned, remaining, end_time = is_banned(client_ip, current_path, config_class.BAN_DURATION)

        if banned:
            # 清理过期封禁
            cleanup_bans()

            # 返回封禁页面
            from flask import render_template
            return render_template('too_many_requests.html',
                                retry_after=int(remaining),
                                end_time=int(end_time),
                                client_ip=client_ip,
                                target_url=current_path), 429

        # 定期清理过期封禁（不是每次请求都清理，减少性能开销）
        # 使用请求计数器，每100个请求清理一次
        if hasattr(app, 'request_count'):
            app.request_count += 1
            if app.request_count >= 100:
                cleanup_bans()
                app.request_count = 0
        else:
            app.request_count = 1
    
    # 设置响应后处理函数
    @app.after_request
    def set_cache_control(response):
        """响应后处理：根据CDN请求头动态设置缓存策略"""
        if response.status_code == 200:
            # 检查请求头中是否存在 CDN: CDNRequest
            if request.headers.get('CDN') == 'CDNRequest':
                # CDN请求：设置公共缓存5分钟
                response.headers['Cache-Control'] = 'public, max-age=300'
            else:
                # 非CDN请求：强制每次验证
                response.headers['Cache-Control'] = 'no-cache'
        return response
    
    # 启动文件监控
    app.file_monitor = setup_file_monitor(config_class.IMAGE_BASE)
    
    return app