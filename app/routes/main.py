"""
主路由模块
"""
import os
from flask import Blueprint, render_template, redirect, send_from_directory, abort
from ..utils.image_utils import get_folder_preview
from ..utils.security import get_safe_path
from ..config.config import Config

# 创建蓝图
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def serve_main_page():
    """
    主路由：显示包含所有子文件夹列表的主页
    """
    # 获取IMAGE_BASE下所有合法的子文件夹
    subfolders = [d for d in os.listdir(Config.IMAGE_BASE)
                if os.path.isdir(get_safe_path(Config.IMAGE_BASE, d))]
    
    # 获取每个文件夹的预览图
    folder_previews = {}
    for folder in subfolders:
        preview = get_folder_preview(
            Config.IMAGE_BASE, 
            folder, 
            Config.THUMBNAIL_SIZE, 
            Config.IMAGE_EXTENSIONS
        )
        if preview:
            folder_previews[folder] = preview
    
    # 渲染主页面模板并传入子文件夹列表和预览图
    return render_template('MainDomain.html', subfolders=subfolders, folder_previews=folder_previews)


@main_bp.route('/favicon.ico')
def favicon():
    """
    网站图标路由
    """
    # 使用Flask的send_from_directory函数直接发送图标文件
    return send_from_directory(
        Config.STATIC_FOLDER,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )


@main_bp.route('/browse/<path:folder>')
def browse_images(folder):
    """
    浏览文件夹中的所有图像
    """
    # 验证文件夹路径安全性
    folder_path = get_safe_path(Config.IMAGE_BASE, folder)
    if not folder_path or not os.path.isdir(folder_path):
        abort(404)
    
    # 获取文件夹中的所有图像
    images = []
    for f in os.listdir(folder_path):
        file_path = get_safe_path(folder_path, f)
        if file_path and os.path.isfile(file_path) and any(f.lower().endswith(ext) for ext in Config.IMAGE_EXTENSIONS):
            images.append(f)
    
    # 按名称排序
    images.sort()
    
    # 渲染浏览器模板
    return render_template('browser.html', folder=folder, images=images)