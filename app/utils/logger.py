"""
日志工具模块 - 提供统一的日志配置
"""
import os
import logging
from logging.handlers import RotatingFileHandler
import time
from flask import request

class RequestFormatter(logging.Formatter):
    """自定义日志格式化器，添加请求信息"""
    
    def format(self, record):
        """格式化日志记录，添加请求信息"""
        # 添加请求信息（如果在请求上下文中）
        if hasattr(record, 'request_id'):
            pass  # 已经有请求ID
        else:
            try:
                from flask import has_request_context, request
                if has_request_context():
                    record.request_id = request.headers.get('X-Request-ID', '-')
                    record.remote_addr = request.remote_addr
                    record.method = request.method
                    record.path = request.path
                else:
                    record.request_id = '-'
                    record.remote_addr = '-'
                    record.method = '-'
                    record.path = '-'
            except (RuntimeError, ImportError):
                # 不在请求上下文中或Flask未导入
                record.request_id = '-'
                record.remote_addr = '-'
                record.method = '-'
                record.path = '-'
            
        return super().format(record)

def setup_logger(app, config):
    """
    设置应用日志
    
    Args:
        app: Flask应用实例
        config: 配置类
    """
    # 确保日志目录存在
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # 创建根日志记录器
    logger = logging.getLogger()
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 设置日志级别
    log_level = getattr(config, 'LOG_LEVEL', logging.INFO)
    logger.setLevel(log_level)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 创建详细的日志格式
    verbose_formatter = RequestFormatter(
        '[%(asctime)s] [%(levelname)s] [%(request_id)s] '
        '%(remote_addr)s - %(method)s %(path)s - '
        '%(name)s:%(lineno)d - %(message)s'
    )
    
    # 设置控制台处理器格式
    console_handler.setFormatter(verbose_formatter)
    
    # 添加控制台处理器到根日志记录器
    logger.addHandler(console_handler)
    
    # 创建访问日志记录器（所有环境都需要）
    access_logger = logging.getLogger('access')
    access_logger.propagate = False  # 不传播到父记录器
    access_logger.setLevel(log_level)
    
    # 创建访问日志控制台处理器
    access_console_handler = logging.StreamHandler()
    access_console_handler.setLevel(log_level)
    access_formatter = RequestFormatter(
        '[%(asctime)s] [ACCESS] [%(request_id)s] '
        '%(remote_addr)s - %(method)s %(path)s - '
        '%(message)s'
    )
    access_console_handler.setFormatter(access_formatter)
    access_logger.addHandler(access_console_handler)
    
    # 在生产环境中添加文件处理器
    if not config.DEBUG:
        # 创建按大小轮转的文件处理器
        file_handler = RotatingFileHandler(
            'logs/random_images_api.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(verbose_formatter)
        logger.addHandler(file_handler)
        
        # 创建错误日志文件处理器
        error_file_handler = RotatingFileHandler(
            'logs/error.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(verbose_formatter)
        logger.addHandler(error_file_handler)
        
        # 创建访问日志文件处理器
        access_file_handler = RotatingFileHandler(
            'logs/access.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        access_file_handler.setLevel(log_level)
        access_file_handler.setFormatter(access_formatter)
        access_logger.addHandler(access_file_handler)
    
    # 设置Flask应用日志处理器
    app.logger.handlers = []
    for handler in logger.handlers:
        app.logger.addHandler(handler)
    
    # 设置Werkzeug日志处理器
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.handlers = []
    for handler in logger.handlers:
        werkzeug_logger.addHandler(handler)
    
    # 记录应用启动信息
    app.logger.info(f"Random Images API 启动于 {'开发' if config.DEBUG else '生产'}环境")
    
    return logger