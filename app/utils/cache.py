"""
缓存相关工具模块
"""
import os
import random
import time
import logging
from threading import Lock
from typing import Optional, Tuple, List, Dict, Any
from .security import get_safe_path

# 配置日志
logger = logging.getLogger(__name__)

# 创建文件夹缓存字典（用于存储各文件夹的图像列表）
# 结构：{folder: {'images': [...], 'timestamp': float}}
folder_cache: Dict[str, Dict[str, Any]] = {}
# 创建线程锁（确保多线程环境下的缓存操作安全）
cache_lock = Lock()

# 缓存过期时间（秒）
CACHE_TTL = int(os.environ.get('CACHE_TTL', 3600))  # 默认1小时

def init_folder_cache(image_base, folder, image_extensions):
    """
    初始化文件夹缓存：扫描并验证图像文件
    
    Args:
        image_base: 图像基础目录
        folder: 文件夹名称
        image_extensions: 支持的图像扩展名列表
        
    Returns:
        有效文件列表或None
    """
    folder_path = get_safe_path(image_base, folder)
    try:
        if not folder_path or not os.path.isdir(folder_path):
            return None

        valid_files = []
        for f in os.listdir(folder_path):
            file_path = get_safe_path(folder_path, f)
            # 验证文件存在且是支持的图像格式
            if file_path and os.path.isfile(file_path) and any(f.lower().endswith(ext) for ext in image_extensions):
                valid_files.append(f)

        # 返回排序后的文件列表（确保跨平台一致性）
        return sorted(valid_files) or None
    except Exception as e:
        logger.error(f"初始化缓存失败: {str(e)}")
        return None


def get_random_image(image_base: str, folder: str, image_extensions: set) -> Optional[str]:
    """
    获取文件夹中的随机图像（真随机）
    
    Args:
        image_base: 图像基础目录
        folder: 文件夹名称
        image_extensions: 支持的图像扩展名列表
        
    Returns:
        随机图像文件名或None
    """
    with cache_lock:  # 线程安全操作
        current_time = time.time()
        
        # 检查缓存是否存在或已过期
        if folder in folder_cache:
            cache_entry = folder_cache[folder]
            # 检查缓存是否过期
            if current_time - cache_entry.get('timestamp', 0) > CACHE_TTL:
                logger.info(f"缓存已过期，重新加载: {folder}")
                del folder_cache[folder]
        
        # 如果缓存中没有该文件夹，初始化缓存
        if folder not in folder_cache:
            images = init_folder_cache(image_base, folder, image_extensions)
            if not images:
                return None  # 无有效图像
            # 存储图像列表到缓存（带时间戳）
            folder_cache[folder] = {
                'images': images,
                'timestamp': current_time
            }

        cache = folder_cache[folder]
        if not cache['images']:
            del folder_cache[folder]  # 空列表则删除缓存项
            return None

        # 真随机：每次都随机选择一个图像
        return random.choice(cache['images'])


def get_random_image_from_all_folders(image_base, image_extensions):
    """
    从所有文件夹中随机选择一张图片
    
    Args:
        image_base: 图像基础目录
        image_extensions: 支持的图像扩展名列表
        
    Returns:
        (文件夹名称, 图像文件名) 或 (None, None)
    """
    with cache_lock:
        # 获取所有子文件夹
        try:
            subfolders = [d for d in os.listdir(image_base)
                         if os.path.isdir(get_safe_path(image_base, d))]
        except Exception as e:
            logger.error(f"获取子文件夹列表失败: {str(e)}")
            return None, None
        
        if not subfolders:
            logger.warning("没有找到任何子文件夹")
            return None, None
        
        # 收集所有文件夹中的所有图片
        all_images = []  # 格式: [(folder, image), ...]
        
        for folder in subfolders:
            # 如果缓存中没有该文件夹，初始化缓存
            if folder not in folder_cache:
                images = init_folder_cache(image_base, folder, image_extensions)
                if images:
                    folder_cache[folder] = {'images': images}
            
            # 从缓存中获取图片列表
            if folder in folder_cache and folder_cache[folder]['images']:
                for image in folder_cache[folder]['images']:
                    all_images.append((folder, image))
        
        if not all_images:
            logger.warning("没有找到任何图片")
            return None, None
        
        # 真随机：随机选择一张图片
        return random.choice(all_images)


def invalidate_cache(folder: str) -> None:
    """
    使指定文件夹的缓存失效
    
    Args:
        folder: 文件夹名称
    """
    with cache_lock:
        if folder in folder_cache:
            logger.info(f"使缓存失效: {folder}")
            del folder_cache[folder]


def cleanup_expired_cache() -> int:
    """
    清理过期的缓存项
    
    Returns:
        清理的缓存项数量
    """
    current_time = time.time()
    expired_count = 0
    
    with cache_lock:
        folders_to_remove = []
        for folder, cache_entry in folder_cache.items():
            if current_time - cache_entry.get('timestamp', 0) > CACHE_TTL:
                folders_to_remove.append(folder)
        
        for folder in folders_to_remove:
            del folder_cache[folder]
            expired_count += 1
        
        if expired_count > 0:
            logger.info(f"已清理 {expired_count} 个过期缓存项")
    
    return expired_count