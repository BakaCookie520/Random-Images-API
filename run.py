"""
应用程序入口文件
"""
import os
import logging
import sys
from app import create_app
from app.config.config import Config, DevelopmentConfig, ProductionConfig
from gevent import pywsgi

# 获取日志记录器
logger = logging.getLogger(__name__)

def check_required_files():
    """
    检查必需的文件和目录是否存在
    
    Returns:
        是否通过检查
    """
    # 启动前检查：验证必需文件和目录存在
    template_folder = Config.TEMPLATE_FOLDER
    image_base = Config.IMAGE_BASE
    
    # 检查模板目录
    if not os.path.isdir(template_folder):
        logger.fatal(f"致命错误：模板目录不存在 {template_folder}")
        return False
    
    # 检查必需的模板文件
    required_templates = ['MainDomain.html', 'fnf.html', 'too_many_requests.html']
    for template in required_templates:
        template_path = os.path.join(template_folder, template)
        if not os.path.isfile(template_path):
            logger.fatal(f"致命错误：模板文件不存在 {template_path}")
            return False
    
    # 检查图片目录
    if not os.path.isdir(image_base):
        logger.fatal(f"致命错误：图片目录不存在 {image_base}")
        return False
    
    # 打印目录访问权限
    logger.info(f"目录验证通过：{template_folder} (权限: {'可读' if os.access(template_folder, os.R_OK) else '不可读'})")
    logger.info(f"目录验证通过：{image_base} (权限: {'可读' if os.access(image_base, os.R_OK) else '不可读'})")
    
    return True

if __name__ == '__main__':
    # 根据环境变量或命令行参数选择配置
    # 可以通过设置环境变量 FLASK_ENV=production 或者命令行参数 --env=production 来切换环境
    env = os.environ.get('FLASK_ENV', 'development')
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--env='):
                env = arg.split('=')[1]
    
    # 根据环境选择配置
    if env == 'production':
        config = ProductionConfig
        log_level = "INFO"
        print("正在以生产环境启动...")
    else:
        config = DevelopmentConfig
        log_level = "DEBUG"
        print("正在以开发环境启动...")
    
    # 检查必需文件
    if not check_required_files():
        logger.fatal("启动前检查失败，程序退出")
        exit(1)
    
    # 创建应用
    app = create_app(config)
    
    try:
        # 使用gevent WSGI服务器（高性能）
        server = pywsgi.WSGIServer(('0.0.0.0', config.PORT), app, log=None)  # 禁用内置日志，使用我们的日志系统
        logger.info(f"服务器启动于 0.0.0.0:{config.PORT} (环境: {env})")
        logger.info(f"日志级别: {log_level}")
        server.serve_forever()  # 启动服务器
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止服务器...")
    except Exception as e:
        logger.error(f"服务器错误: {str(e)}", exc_info=True)  # 添加异常堆栈信息
    finally:
        if hasattr(app, 'file_monitor'):
            logger.info("正在停止文件监控...")
            app.file_monitor.stop()  # 停止监控
            app.file_monitor.join()  # 等待监控线程结束
        logger.info("服务器已成功停止")
