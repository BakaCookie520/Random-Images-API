"""
安全相关工具模块
"""
import os
import time
from flask import request

# 存储封禁信息（结构：{ip: {path: (end_time, is_directory)}}）
ban_records = {}

def get_safe_path(base, *paths):
    """
    验证并返回安全路径（防止路径遍历攻击）
    
    Args:
        base: 基础路径
        *paths: 路径组件
        
    Returns:
        安全路径或None（如果路径不安全）
    """
    # 拼接完整路径并标准化
    full_path = os.path.abspath(os.path.join(base, *paths))
    # 检查路径是否在允许的基础路径内
    if not full_path.startswith(os.path.abspath(base)):
        return None  # 路径不安全返回None
    return full_path  # 安全路径


def is_banned(client_ip, path, ban_duration):
    """
    检查指定IP和路径是否已被封禁
    
    Args:
        client_ip: 客户端IP
        path: 请求路径
        ban_duration: 封禁时长
        
    Returns:
        (是否被封禁, 剩余时间, 结束时间)
    """
    if client_ip not in ban_records:
        return False, 0, 0

    current_time = time.time()
    ip_records = ban_records[client_ip]

    # 1. 检查精确匹配
    if path in ip_records:
        end_time, _ = ip_records[path]
        if current_time < end_time:
            return True, max(0, end_time - current_time), end_time

    # 2. 检查目录封禁
    for banned_path, (end_time, is_directory) in ip_records.items():
        # 只检查目录封禁
        if not is_directory or current_time >= end_time:
            continue

        # 规范化目录路径：确保以斜杠结尾
        if not banned_path.endswith('/'):
            normalized_banned_path = banned_path + '/'
        else:
            normalized_banned_path = banned_path

        # 检查路径是否以规范化目录路径开头
        if path == normalized_banned_path.rstrip('/') or path.startswith(normalized_banned_path):
            return True, max(0, end_time - current_time), end_time

    return False, 0, 0


def add_ban(client_ip, path, is_directory, ban_duration):
    """
    添加封禁记录，确保相同IP的封禁时间一致
    
    Args:
        client_ip: 客户端IP
        path: 请求路径
        is_directory: 是否为目录
        ban_duration: 封禁时长
        
    Returns:
        封禁结束时间
    """
    current_time = time.time()

    # 获取该IP的封禁结束时间（如果已有封禁则使用相同结束时间）
    if client_ip in ban_records:
        # 查找该IP现有的封禁结束时间
        ip_records = ban_records[client_ip]
        existing_end_time = None

        # 查找现有的封禁结束时间
        for record in ip_records.values():
            if record[0] > current_time:  # 只考虑未过期的封禁
                existing_end_time = record[0]
                break

        # 使用现有封禁时间或创建新时间
        end_time = existing_end_time or (current_time + ban_duration)
    else:
        # 新IP封禁
        end_time = current_time + ban_duration
        ban_records[client_ip] = {}

    # 添加封禁记录
    ban_records[client_ip][path] = (end_time, is_directory)
    return end_time


def cleanup_bans():
    """
    清理过期封禁记录
    """
    current_time = time.time()
    ips_to_remove = []

    for ip, records in list(ban_records.items()):
        # 移除过期记录
        valid_records = {}
        for path, (end_time, is_directory) in records.items():
            if end_time > current_time:
                valid_records[path] = (end_time, is_directory)

        # 更新或移除IP记录
        if valid_records:
            ban_records[ip] = valid_records
        else:
            ips_to_remove.append(ip)

    # 移除无记录的IP
    for ip in ips_to_remove:
        del ban_records[ip]


def get_real_ip():
    """
    获取客户端真实IP地址
    
    Returns:
        客户端IP地址
    """
    forwarded_for = request.headers.get('X-Forwarded-For', '')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.headers.get('X-Real-IP', request.remote_addr)