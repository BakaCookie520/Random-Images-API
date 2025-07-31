"""
图像路由模块
"""
import os
import logging
from flask import Blueprint, redirect, send_from_directory, abort, request, render_template
from ..utils.security import get_safe_path, is_banned
from ..utils.cache import get_random_image, invalidate_cache
from ..config.config import Config

# 配置日志
logger = logging.getLogger(__name__)

# 创建蓝图
images_bp = Blueprint('images', __name__)

@images_bp.route('/<path:folder>')
def serve_sequential_image(folder):
    """
    顺序服务图像：按预定义的随机顺序循环显示文件夹中的图像
    """
    # 首先检查封禁状态
    client_ip = request.remote_addr
    current_path = request.path
    banned, remaining, end_time = is_banned(client_ip, current_path, Config.BAN_DURATION)

    if banned:
        # 如果被封禁，直接返回封禁页面
        return render_template('too_many_requests.html',
                               retry_after=int(remaining),
                               end_time=int(end_time),
                               client_ip=client_ip,
                               target_url=current_path), 429

    # 然后处理路径和文件夹逻辑
    folder = folder.strip('/')  # 清理文件夹路径
    if not folder:
        return redirect('/')  # 空路径重定向到主页

    # 验证文件夹路径安全性
    folder_path = get_safe_path(Config.IMAGE_BASE, folder)
    if not folder_path or not os.path.isdir(folder_path):
        abort(404)

    max_attempts = 3  # 最大重试次数
    attempt = 0

    while attempt < max_attempts:
        # 获取随机图像
        image = get_random_image(Config.IMAGE_BASE, folder, Config.IMAGE_EXTENSIONS)
        if not image:
            abort(404)  # 无有效图像

        # 检查图像文件是否存在
        image_path = get_safe_path(folder_path, image)
        if image_path and os.path.isfile(image_path):
            # 重定向到实际图像URL
            return redirect(f'/{folder}/{image}')

        # 文件不存在：记录日志并尝试重建缓存
        logger.warning(f"图像文件不存在: {image_path}, 尝试 {attempt + 1}/{max_attempts}")
        attempt += 1

        # 使缓存失效
        invalidate_cache(folder)

    # 多次尝试后仍失败
    logger.error(f"无法找到有效图像: {folder}")
    abort(404)


@images_bp.route('/<path:folder>/<filename>')
def serve_image(folder, filename):
    """
    实际图像服务路由：发送图像文件
    """
    # 验证文件夹路径
    safe_folder = get_safe_path(Config.IMAGE_BASE, folder)
    if not safe_folder:
        abort(404)

    # 验证文件路径
    file_path = get_safe_path(safe_folder, filename)
    if not file_path or not os.path.isfile(file_path):
        # 文件不存在时使缓存失效
        invalidate_cache(folder)
        abort(404)

    # 发送图像文件
    return send_from_directory(
        safe_folder,
        filename,
        mimetype='image'  # 通用MIME类型
    )