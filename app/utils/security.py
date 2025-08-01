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
    # 快速检查：如果IP不在记录中，直接返回
    if client_ip not in ban_records:
        return False, 0, 0

    current_time = time.time()
    ip_records = ban_records[client_ip]

    # 1. 检查精确路径匹配（优化：直接查询字典）
    if path in ip_records:
        end_time, _ = ip_records[path]
        if current_time < end_time:
            return True, max(0, end_time - current_time), end_time

    # 2. 检查全局IP封禁（新增功能：全局IP封禁）
    if '*' in ip_records:
        end_time, _ = ip_records['*']
        if current_time < end_time:
            return True, max(0, end_time - current_time), end_time

    # 3. 检查目录封禁（优化：预处理路径）
    # 规范化请求路径，移除尾部斜杠以便一致性比较
    normalized_path = path.rstrip('/')
    path_parts = normalized_path.split('/')
    
    # 构建可能的父目录路径列表，从最具体到最一般
    possible_parent_paths = []
    for i in range(len(path_parts), 0, -1):
        parent_path = '/'.join(path_parts[:i])
        if parent_path:
            possible_parent_paths.append(parent_path)
            possible_parent_paths.append(parent_path + '/')
    
    # 检查所有可能的父目录路径
    for parent_path in possible_parent_paths:
        if parent_path in ip_records:
            end_time, is_directory = ip_records[parent_path]
            if is_directory and current_time < end_time:
                return True, max(0, end_time - current_time), end_time

    return False, 0, 0


# 存储IP违规计数（用于智能封禁）
ip_violation_counts = {}
# 存储最后一次封禁时间（用于累进封禁）
last_ban_times = {}

def add_ban(client_ip, path, is_directory, ban_duration):
    """
    添加封禁记录，实现智能封禁机制
    
    Args:
        client_ip: 客户端IP
        path: 请求路径
        is_directory: 是否为目录
        ban_duration: 基础封禁时长
        
    Returns:
        封禁结束时间
    """
    current_time = time.time()
    
    # 更新违规计数
    if client_ip not in ip_violation_counts:
        ip_violation_counts[client_ip] = 1
    else:
        ip_violation_counts[client_ip] += 1
    
    # 计算智能封禁时长（累进制）
    violation_count = ip_violation_counts[client_ip]
    
    # 检查是否是短时间内重复违规（30分钟内）
    repeated_violation = False
    if client_ip in last_ban_times:
        time_since_last_ban = current_time - last_ban_times[client_ip]
        if time_since_last_ban < 1800:  # 30分钟
            repeated_violation = True
    
    # 记录本次封禁时间
    last_ban_times[client_ip] = current_time
    
    # 计算实际封禁时长
    actual_ban_duration = ban_duration
    
    # 累进封禁策略
    if repeated_violation:
        # 短时间内重复违规，封禁时间翻倍
        actual_ban_duration = ban_duration * min(2 ** (violation_count - 1), 24)  # 最多封禁24倍时长
    elif violation_count > 1:
        # 非短时间重复但有历史违规，增加50%时长
        actual_ban_duration = ban_duration * min(1.5 * (violation_count - 1), 12)  # 最多增加12倍
    
    # 获取该IP的封禁结束时间（如果已有封禁则使用相同结束时间）
    if client_ip in ban_records:
        # 查找该IP现有的最长封禁结束时间
        ip_records = ban_records[client_ip]
        existing_end_time = None
        
        for record in ip_records.values():
            if record[0] > current_time and (existing_end_time is None or record[0] > existing_end_time):
                existing_end_time = record[0]
        
        # 如果已有封禁时间，取较长的一个
        if existing_end_time:
            end_time = max(existing_end_time, current_time + actual_ban_duration)
        else:
            end_time = current_time + actual_ban_duration
    else:
        # 新IP封禁
        end_time = current_time + actual_ban_duration
        ban_records[client_ip] = {}
    
    # 添加封禁记录
    ban_records[client_ip][path] = (end_time, is_directory)
    
    # 对于严重违规（多次违规），考虑添加全局IP封禁
    if violation_count >= 5 or (repeated_violation and violation_count >= 3):
        ban_records[client_ip]['*'] = (end_time, False)  # 全局封禁标记
    
    return end_time


def cleanup_bans():
    """
    清理过期封禁记录和过期违规计数
    """
    current_time = time.time()
    ips_to_remove = []
    
    # 清理封禁记录
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
    
    # 清理过期违规计数（超过7天的违规记录）
    ips_to_reset = []
    for ip, last_time in list(last_ban_times.items()):
        if current_time - last_time > 604800:  # 7天 = 604800秒
            ips_to_reset.append(ip)
    
    # 重置过期违规计数
    for ip in ips_to_reset:
        if ip in ip_violation_counts:
            del ip_violation_counts[ip]
        if ip in last_ban_times:
            del last_ban_times[ip]


def get_real_ip():
    """
    获取客户端真实IP地址，支持多种代理头
    
    Returns:
        客户端IP地址
    """
    # 按优先级检查各种代理头
    headers_to_check = [
        'X-Forwarded-For',
        'X-Real-IP',
        'CF-Connecting-IP',  # Cloudflare
        'True-Client-IP',    # Akamai/Cloudflare
        'X-Client-IP',       # Amazon CloudFront
        'Fastly-Client-IP',  # Fastly
        'X-Cluster-Client-IP'
    ]
    
    for header in headers_to_check:
        if header in request.headers:
            value = request.headers.get(header, '')
            if value:
                # 如果是逗号分隔的列表（如X-Forwarded-For），取第一个值
                return value.split(',')[0].strip()
    
    # 如果没有找到任何代理头，使用远程地址
    return request.remote_addr
