"""
错误处理路由模块
"""
import os
import time
from flask import Blueprint, render_template, request
from ..utils.security import get_safe_path, get_real_ip, add_ban
from ..config.config import Config

# 创建蓝图
errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def handle_404(e):
    """
    404错误处理：显示自定义404页面
    """
    # 获取所有可用的子文件夹（用于导航）
    subfolders = [d for d in os.listdir(Config.IMAGE_BASE)
                if os.path.isdir(get_safe_path(Config.IMAGE_BASE, d))]
    # 渲染404模板并传入子文件夹列表
    return render_template('fnf.html', subfolders=subfolders), 404


@errors_bp.app_errorhandler(429)
def handle_ratelimit_exceeded(e):
    """
    自定义429错误处理，记录封禁信息并显示封禁页面
    """
    client_ip = get_real_ip()
    target_url = request.path

    # 确定路径类型（文件或目录）
    is_directory = not any(target_url.lower().endswith(ext) for ext in Config.IMAGE_EXTENSIONS)

    # 添加封禁记录（确保使用相同的封禁时间）
    end_time = add_ban(client_ip, target_url, is_directory, Config.BAN_DURATION)

    # 计算剩余封禁时间
    current_time = time.time()
    remaining = max(0, end_time - current_time)

    return render_template('too_many_requests.html',
                           retry_after=int(remaining),
                           end_time=int(end_time),
                           client_ip=client_ip,
                           target_url=target_url), 429


@errors_bp.app_errorhandler(500)
def handle_500(e):
    """
    500错误处理：返回简单错误消息
    """
    return "服务器配置错误，请联系管理员", 500