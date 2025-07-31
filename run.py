"""
应用程序入口文件
"""
import os
import logging
from app import create_app
from app.config.config import Config
from gevent import pywsgi

# 配置日志
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
    # 检查必需文件
    if not check_required_files():
        exit(1)
    
    # 创建应用
    app = create_app()
    
    try:
        # 使用gevent WSGI服务器（高性能）
        server = pywsgi.WSGIServer(('0.0.0.0', Config.PORT), app)
        logger.info(f"服务器运行在 0.0.0.0:{Config.PORT}")
        server.serve_forever()  # 启动服务器
    except KeyboardInterrupt:
        logger.info("接收到中断信号，停止服务器...")
    except Exception as e:
        logger.error(f"服务器错误: {str(e)}")
    finally:
        if hasattr(app, 'file_monitor'):
            app.file_monitor.stop()  # 停止监控
            app.file_monitor.join()  # 等待监控线程结束
        logger.info("服务器已停止")