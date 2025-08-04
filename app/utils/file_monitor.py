"""
文件监控相关工具模块
"""
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .cache import invalidate_cache

# 配置日志
logger = logging.getLogger(__name__)
logger.propagate = True  # 允许日志传播到根记录器，但不添加额外的处理器

class FolderChangeHandler(FileSystemEventHandler):
    """
    增强的文件系统事件处理器：只处理删除和新建事件
    """
    def __init__(self, image_base):
        """
        初始化处理器
        
        Args:
            image_base: 图像基础目录
        """
        self.image_base = image_base
        super().__init__()

    def on_deleted(self, event):
        """
        处理文件删除事件
        """
        if not event.is_directory:
            self._handle_file_event(os.path.dirname(event.src_path))

    def on_created(self, event):
        """
        处理文件创建事件
        """
        if not event.is_directory:
            self._handle_file_event(os.path.dirname(event.src_path))

    def on_moved(self, event):
        """
        处理文件移动事件（视为删除+新建）
        """
        if not event.is_directory:
            # 源文件被删除
            self._handle_file_event(os.path.dirname(event.src_path))
            # 目标文件被创建
            self._handle_file_event(os.path.dirname(event.dest_path))

    def _handle_file_event(self, folder_path):
        """
        处理文件事件：使父目录缓存失效
        
        Args:
            folder_path: 文件夹路径
        """
        try:
            # 获取相对于IMAGE_BASE的文件夹路径
            rel_path = os.path.relpath(folder_path, self.image_base)
            # 使缓存失效
            invalidate_cache(rel_path)
        except Exception as e:
            logger.error(f"处理文件事件时出错: {str(e)}")


def setup_file_monitor(image_base):
    """
    设置文件监控
    
    Args:
        image_base: 图像基础目录
        
    Returns:
        Observer实例
    """
    # 创建文件系统观察者
    observer = Observer()
    # 安排事件处理器监视IMAGE_BASE目录（递归监视）
    observer.schedule(FolderChangeHandler(image_base), image_base, recursive=True)
    
    try:
        observer.start()
        logger.info("文件监控已启动...")
    except Exception as e:
        logger.error(f"启动文件监控失败: {str(e)}")
    
    return observer