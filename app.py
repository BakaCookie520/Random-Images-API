from flask import Flask, redirect, send_from_directory
import os
import random
import time
from threading import Lock

app = Flask(__name__)
IMAGE_BASE = '/app/images'
app_start_time = time.time()  # 记录容器启动时间
folder_cache = {}             # 结构：{folder: {"images": list, "index": int}}
cache_lock = Lock()           # 线程安全锁

def init_folder_cache(folder):
    """初始化文件夹缓存，按名称排序后伪随机打乱"""
    folder_path = os.path.join(IMAGE_BASE, folder)
    if not os.path.exists(folder_path):
        return None
    
    # 获取所有图片文件并按名称排序
    images = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
        and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    ]
    images.sort()  # 按文件名自然排序
    
    # 生成基于文件夹名和启动时间的随机种子
    seed = hash(f"{folder}-{app_start_time}") % (2**32)
    random.seed(seed)
    random.shuffle(images)
    
    return images if images else None

@app.route('/<folder>')
def serve_sequential_image(folder):
    with cache_lock:  # 保证线程安全
        # 延迟初始化缓存
        if folder not in folder_cache:
            images = init_folder_cache(folder)
            if not images:
                return "No images found in this folder", 404
            folder_cache[folder] = {
                "images": images,
                "index": 0
            }
        
        cache = folder_cache[folder]
        if not cache["images"]:
            return "No images found in this folder", 404
        
        # 获取当前图片并更新索引
        current_index = cache["index"]
        image = cache["images"][current_index]
        cache["index"] = (current_index + 1) % len(cache["images"])
    
    return redirect(f'/{folder}/{image}')

@app.route('/<folder>/<filename>')
def serve_image(folder, filename):
    return send_from_directory(
        os.path.join(IMAGE_BASE, folder),
        filename,
        mimetype='image'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50721)