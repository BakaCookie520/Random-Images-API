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

# 确保路由配置正确
@app.route('/favicon.ico')
def favicon():
    icon_path = os.path.join(app.root_path, 'static')
    return send_from_directory(
        icon_path,
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

# 文件监控处理器
class FolderChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        """处理文件/目录修改事件"""
        if event.is_directory:
            folder = os.path.relpath(event.src_path, IMAGE_BASE)
        else:
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
        
        self._invalidate_cache(folder, "修改")

    def on_created(self, event):
        """处理文件创建事件"""
        if not event.is_directory:
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
            self._invalidate_cache(folder, "创建")

    def on_deleted(self, event):
        """处理文件删除事件"""
        if not event.is_directory:
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
            self._invalidate_cache(folder, "删除")

    def _invalidate_cache(self, folder, action):
        """统一处理缓存失效"""
        with cache_lock:
            if folder in folder_cache:
                print(f"检测到{folder}目录的{action}操作，刷新缓存...")
                del folder_cache[folder]

# 初始化文件监控
observer = Observer()
observer.schedule(FolderChangeHandler(), IMAGE_BASE, recursive=True)
observer.start()

@app.after_request
def set_cache_control(response):
    response.headers['Cache-Control'] = 'public, max-age=300'  # 添加适当的缓存时间
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
        if folder not in folder_cache:
            if not (images := init_folder_cache(folder)):
                return "文件夹不存在", 404
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
    # 添加路径验证和调试信息
    print(f"监控路径：{IMAGE_BASE}，是否存在：{os.path.exists(IMAGE_BASE)}")
    print(f"目录权限：{os.access(IMAGE_BASE, os.R_OK | os.W_OK)}")
    
    try:
        server = pywsgi.WSGIServer(('0.0.0.0', 50721), app)
        print("服务器已启动...")
        server.serve_forever()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()