"""
缓存相关工具模块
"""
import os
import random
import time
import logging
from threading import Lock
from .security import get_safe_path

# 配置日志
logger = logging.getLogger(__name__)

# 创建文件夹缓存字典（用于存储各文件夹的图像列表）
folder_cache = {}
# 创建线程锁（确保多线程环境下的缓存操作安全）
cache_lock = Lock()

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


def get_random_image(image_base, folder, image_extensions):
    """
    获取文件夹中的随机图像
    
    Args:
        image_base: 图像基础目录
        folder: 文件夹名称
        image_extensions: 支持的图像扩展名列表
        
    Returns:
        随机图像文件名或None
    """
    with cache_lock:  # 线程安全操作
        # 如果缓存中没有该文件夹
        if folder not in folder_cache:
            images = init_folder_cache(image_base, folder, image_extensions)  # 初始化缓存
            if not images:
                return None  # 无有效图像

            # 创建基于文件夹和时间的随机种子
            seed = hash(f"{folder}-{time.time()}") % (2 ** 32)
            random.seed(seed)
            shuffled = images.copy()
            random.shuffle(shuffled)  # 随机打乱图像列表

            # 将打乱后的列表存入缓存
            folder_cache[folder] = {
                'images': shuffled,
                'index': 0,  # 当前索引位置
                'seed': seed  # 使用的随机种子
            }

        cache = folder_cache[folder]
        if not cache['images']:
            del folder_cache[folder]  # 空列表则删除缓存项
            return None

        # 获取当前图像并更新索引
        current_index = cache['index']
        image = cache['images'][current_index]
        # 循环索引（到达末尾后回到开头）
        cache['index'] = (current_index + 1) % len(cache['images'])
        
        return image


def invalidate_cache(folder):
    """
    使指定文件夹的缓存失效
    
    Args:
        folder: 文件夹名称
    """
    with cache_lock:
        if folder in folder_cache:
            logger.info(f"使缓存失效: {folder}")
            del folder_cache[folder]