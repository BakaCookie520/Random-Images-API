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
    增强的文件系统事件处理器：处理文件创建、删除、修改和移动事件
    """
    def __init__(self, image_base, image_extensions):
        """
        初始化处理器
        
        Args:
            image_base: 图像基础目录
            image_extensions: 支持的图片扩展名集合
        """
        self.image_base = os.path.abspath(image_base)
        self.image_extensions = image_extensions
        super().__init__()

    def _is_image_file(self, file_path):
        """
        检查文件是否为图片文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为图片文件
        """
        return any(file_path.lower().endswith(ext) for ext in self.image_extensions)

    def on_deleted(self, event):
        """
        处理文件删除事件
        """
        if not event.is_directory:
            if self._is_image_file(event.src_path):
                self._handle_file_event(os.path.dirname(event.src_path))

    def on_created(self, event):
        """
        处理文件创建事件
        """
        if not event.is_directory:
            if self._is_image_file(event.src_path):
                self._handle_file_event(os.path.dirname(event.src_path))

    def on_modified(self, event):
        """
        处理文件修改事件
        """
        if not event.is_directory:
            if self._is_image_file(event.src_path):
                self._handle_file_event(os.path.dirname(event.src_path))

    def on_moved(self, event):
        """
        处理文件移动事件（视为删除+新建）
        """
        if not event.is_directory:
            # 源文件或目标文件是图片文件时才处理
            if self._is_image_file(event.src_path):
                self._handle_file_event(os.path.dirname(event.src_path))
            if self._is_image_file(event.dest_path):
                self._handle_file_event(os.path.dirname(event.dest_path))

    def _handle_file_event(self, folder_path):
        """
        处理文件事件：使父目录缓存失效
        
        Args:
            folder_path: 文件夹路径
        """
        try:
            folder_path = os.path.abspath(folder_path)
            
            # 如果文件夹路径就是 image_base 本身，跳过处理
            if folder_path == self.image_base:
                logger.debug(f"跳过根目录的缓存失效: {folder_path}")
                return
            
            # 获取相对于IMAGE_BASE的文件夹路径
            rel_path = os.path.relpath(folder_path, self.image_base)
            
            # 如果 rel_path 是 '.'，说明有问题，跳过
            if rel_path == '.':
                logger.debug(f"跳过无效的相对路径: {folder_path}")
                return
            
            # 使缓存失效
            logger.info(f"检测到文件变化，使缓存失效: {rel_path}")
            invalidate_cache(rel_path)
        except Exception as e:
            logger.error(f"处理文件事件时出错: {str(e)}")


def setup_file_monitor(image_base, image_extensions=None):
    """
    设置文件监控
    
    Args:
        image_base: 图像基础目录
        image_extensions: 支持的图片扩展名集合，默认为常见图片格式
        
    Returns:
        Observer实例
    """
    # 默认图片扩展名
    if image_extensions is None:
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    
    # 创建文件系统观察者
    observer = Observer()
    # 安排事件处理器监视IMAGE_BASE目录（递归监视）
    observer.schedule(
        FolderChangeHandler(image_base, image_extensions), 
        image_base, 
        recursive=True
    )
    
    try:
        observer.start()
        logger.info(f"文件监控已启动，监控目录: {image_base}")
    except Exception as e:
        logger.error(f"启动文件监控失败: {str(e)}")
    
    return observer