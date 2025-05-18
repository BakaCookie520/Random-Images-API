from flask import Flask, redirect, send_from_directory
import os
import random
import time
from threading import Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
IMAGE_BASE = '/app/images'
folder_cache = {}
cache_lock = Lock()

# 确保路由配置正确（新增以下调试语句）
@app.route('/favicon.ico')
def favicon():
    icon_path = os.path.join(app.root_path, 'static')
    print(f"当前图标路径：{icon_path}")  # 调试路径输出
    if not os.path.exists(os.path.join(icon_path, 'favicon.ico')):
        print("错误：未找到图标文件")    # 文件存在性检查
    return send_from_directory(
        icon_path,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# 文件监控处理器
class FolderChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            folder = os.path.relpath(event.src_path, IMAGE_BASE)
            with cache_lock:
                if folder in folder_cache:
                    print(f"Detected changes in {folder}, refreshing cache...")
                    del folder_cache[folder]

    def on_created(self, event):
        if not event.is_directory:
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
            with cache_lock:
                if folder in folder_cache:
                    print(f"New file in {folder}, refreshing cache...")
                    del folder_cache[folder]

# 初始化文件监控
observer = Observer()
observer.schedule(FolderChangeHandler(), IMAGE_BASE, recursive=True)
observer.start()

@app.after_request
def set_cache_control(response):
    response.headers['Cache-Control'] = 'public'
    return response

def init_folder_cache(folder):
    folder_path = os.path.join(IMAGE_BASE, folder)
    if not os.path.exists(folder_path):
        return None
    
    images = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and 
        f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
    ]
    images.sort()
    
    seed = hash(f"{folder}-{time.time()}") % (2**32)
    random.seed(seed)
    random.shuffle(images)
    
    return images or None

@app.route('/<folder>')
def serve_sequential_image(folder):
    with cache_lock:
        # 检查缓存有效性
        if folder not in folder_cache:
            if not (images := init_folder_cache(folder)):
                return "Folder not found", 404
            folder_cache[folder] = {"images": images, "index": 0}
        
        cache = folder_cache[folder]
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

from gevent import pywsgi  

if __name__ == '__main__':  
    server = pywsgi.WSGIServer(('0.0.0.0', 50721), app)  
    server.serve_forever()
