"""
图像处理相关工具模块
"""
import os
import base64
import random
from io import BytesIO
from PIL import Image
import logging
from .security import get_safe_path

# 配置日志
logger = logging.getLogger(__name__)

def get_folder_preview(image_base, folder, thumbnail_size, image_extensions):
    """
    获取文件夹的预览图像
    
    Args:
        image_base: 图像基础目录
        folder: 文件夹名称
        thumbnail_size: 缩略图尺寸
        image_extensions: 支持的图像扩展名
        
    Returns:
        包含预览图数据和图像数量的字典或None
    """
    folder_path = get_safe_path(image_base, folder)
    if not folder_path or not os.path.isdir(folder_path):
        return None
    
    # 获取文件夹中的所有图像
    images = []
    for f in os.listdir(folder_path):
        file_path = get_safe_path(folder_path, f)
        if file_path and os.path.isfile(file_path) and any(f.lower().endswith(ext) for ext in image_extensions):
            images.append(f)
    
    if not images:
        return None
    
    # 随机选择一张图片作为预览
    preview_image = random.choice(images)
    preview_path = get_safe_path(folder_path, preview_image)
    
    try:
        # 创建缩略图
        img = Image.open(preview_path)
        img.thumbnail(thumbnail_size)
        
        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format=img.format or 'JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'data': f"data:image/{img.format.lower() if img.format else 'jpeg'};base64,{img_str}",
            'count': len(images)
        }
    except Exception as e:
        logger.error(f"创建预览图失败: {str(e)}")
        return None