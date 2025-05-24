from flask import Flask, redirect, send_from_directory, abort
import os
import random
import time
from threading import Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
IMAGE_BASE = '/app/images'
HTML_BASE = '/app/html'
folder_cache = {}
cache_lock = Lock()

def get_safe_path(base, *paths):
    """验证并返回安全路径"""
    full_path = os.path.abspath(os.path.join(base, *paths))
    if not full_path.startswith(os.path.abspath(base)):
        return None
    return full_path

@app.route('/')
def serve_main_page():
    main_page = get_safe_path(HTML_BASE, 'maindomain.html')
    if not main_page or not os.path.isfile(main_page):
        abort(500, description="主页面配置错误")
    return send_from_directory(HTML_BASE, 'maindomain.html')

@app.errorhandler(404)
def handle_404(e):
    error_page = get_safe_path(HTML_BASE, 'fnf.html')
    if not error_page or not os.path.isfile(error_page):
        return "404 Not Found (且错误页面配置错误)", 404
    return send_from_directory(HTML_BASE, 'fnf.html'), 404

@app.errorhandler(500)
def handle_500(e):
    return "服务器配置错误，请联系管理员", 500

@app.route('/favicon.ico')
def favicon():
    icon_path = get_safe_path(app.root_path, 'static', 'favicon.ico')
    if not icon_path or not os.path.isfile(icon_path):
        abort(404)
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/<path:folder>')
def serve_sequential_image(folder):
    folder = folder.strip('/')
    if not folder:
        return redirect('/')
    
    # 修复此处括号问题
    folder_path = get_safe_path(IMAGE_BASE, folder)  # 移除了多余的)
    if not folder_path or not os.path.isdir(folder_path):
        abort(404)
    
    with cache_lock:
        if folder not in folder_cache:
            images = init_folder_cache(folder)
            if not images:
                abort(404)
            
            seed = hash(f"{folder}-{time.time()}") % (2**32)
            random.seed(seed)
            shuffled = images.copy()
            random.shuffle(shuffled)
            
            folder_cache[folder] = {
                'images': shuffled,
                'index': 0,
                'seed': seed
            }
        
        cache = folder_cache[folder]
        if not cache['images']:
            del folder_cache[folder]
            abort(404)
        
        current_index = cache['index']
        image = cache['images'][current_index]
        cache['index'] = (current_index + 1) % len(cache['images'])
    
    return redirect(f'/{folder}/{image}')

@app.route('/<path:folder>/<filename>')
def serve_image(folder, filename):
    # 修复此处括号问题
    safe_folder = get_safe_path(IMAGE_BASE, folder)  # 移除了多余的)
    if not safe_folder:
        abort(404)
    
    file_path = get_safe_path(safe_folder, filename)  # 移除了多余的)
    if not file_path or not os.path.isfile(file_path):
        abort(404)
    
    return send_from_directory(
        safe_folder,
        filename,
        mimetype='image'
    )

class FolderChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            rel_path = os.path.relpath(event.src_path, IMAGE_BASE)
            self._invalidate_cache(rel_path, "修改")

    def on_created(self, event):
        if not event.is_directory:
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
            self._invalidate_cache(folder, "创建")

    def on_deleted(self, event):
        if not event.is_directory:
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
            self._invalidate_cache(folder, "删除")

    def _invalidate_cache(self, folder, action):
        with cache_lock:
            if folder in folder_cache:
                print(f"缓存失效: {folder} ({action})")
                del folder_cache[folder]

observer = Observer()
observer.schedule(FolderChangeHandler(), IMAGE_BASE, recursive=True)

@app.after_request
def set_cache_control(response):
    if response.status_code == 200:
        response.headers['Cache-Control'] = 'public, max-age=300'
    return response

def init_folder_cache(folder):
    """增强型缓存初始化"""
    # 修复此处括号问题
    folder_path = get_safe_path(IMAGE_BASE, folder)  # 移除了多余的)
    try:
        if not folder_path or not os.path.isdir(folder_path):
            return None
        
        valid_files = []
        for f in os.listdir(folder_path):
            # 修复此处括号问题
            file_path = get_safe_path(folder_path, f)  # 移除了多余的)
            if file_path and os.path.isfile(file_path) and f.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                valid_files.append(f)
        
        return sorted(valid_files) or None
    except Exception as e:
        print(f"初始化缓存失败: {str(e)}")
        return None

if __name__ == '__main__':
    required_files = {
        HTML_BASE: ['maindomain.html', 'fnf.html'],
        IMAGE_BASE: []
    }
    
    for base, files in required_files.items():
        if not os.path.isdir(base):
            print(f"致命错误：目录不存在 {base}")
            exit(1)
        for f in files:
            path = os.path.join(base, f)
            if not os.path.isfile(path):
                print(f"致命错误：文件不存在 {path}")
                exit(1)
        print(f"目录验证通过：{base} (权限: {'可读' if os.access(base, os.R_OK) else '不可读'})")
    
    observer.start()
    print("文件监控已启动...")
    
    try:
        from gevent import pywsgi
        server = pywsgi.WSGIServer(('0.0.0.0', 50721), app)
        print("服务器运行在 0.0.0.0:50721")
        server.serve_forever()
    except KeyboardInterrupt:
        observer.stop()
    finally:
        observer.join()
        