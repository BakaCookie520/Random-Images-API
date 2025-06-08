from flask import Flask, redirect, send_from_directory, abort, render_template, request, Response
import os
import random
import time
from threading import Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image
import io

# 创建Flask应用实例
app = Flask(__name__, template_folder='html')

# 配置请求限制
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"]
)

# 定义图像存储的基础路径
IMAGE_BASE = 'images'
# 定义HTML模板的基础路径
HTML_BASE = 'html'
# 创建文件夹缓存字典
folder_cache = {}
# 创建线程锁
cache_lock = Lock()


def get_safe_path(base, *paths):
    """验证并返回安全路径"""
    full_path = os.path.abspath(os.path.join(base, *paths))
    if not full_path.startswith(os.path.abspath(base)):
        return None
    return full_path


@app.route('/')
def serve_main_page():
    """主路由：显示包含所有子文件夹列表的主页"""
    subfolders = [d for d in os.listdir(IMAGE_BASE)
                  if os.path.isdir(get_safe_path(IMAGE_BASE, d))]
    return render_template('MainDomain.html', subfolders=subfolders)


@app.errorhandler(404)
def handle_404(e):
    """404错误处理"""
    subfolders = [d for d in os.listdir(IMAGE_BASE)
                  if os.path.isdir(get_safe_path(IMAGE_BASE, d))]
    return render_template('fnf.html', subfolders=subfolders), 404


@app.errorhandler(500)
def handle_500(e):
    """500错误处理"""
    return "服务器配置错误，请联系管理员", 500


@app.route('/favicon.ico')
def favicon():
    """网站图标路由"""
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
    """顺序服务图像"""
    folder = folder.strip('/')
    if not folder:
        return redirect('/')

    folder_path = get_safe_path(IMAGE_BASE, folder)
    if not folder_path or not os.path.isdir(folder_path):
        abort(404)

    with cache_lock:
        if folder not in folder_cache:
            images = init_folder_cache(folder)
            if not images:
                abort(404)

            seed = hash(f"{folder}-{time.time()}") % (2 ** 32)
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


@app.route('/random/<path:folder>')
def serve_random_image(folder):
    """随机服务图像"""
    # 实现与顺序服务相同
    folder = folder.strip('/')
    if not folder:
        abort(404)
    # ...（与serve_sequential_image相同）


@app.after_request
def add_security_headers(response):
    """添加安全相关的响应头"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


@app.route('/<path:folder>/<filename>')
@limiter.limit("10 per minute")
def serve_image(folder, filename):
    """实际图像服务路由：直接从本地文件系统发送图像"""
    safe_folder = get_safe_path(IMAGE_BASE, folder)
    if not safe_folder:
        abort(404)

    file_path = get_safe_path(safe_folder, filename)
    if not file_path or not os.path.isfile(file_path):
        abort(404)

    try:
        with Image.open(file_path) as img:
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background

            max_size = (7680, 4320)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=img.format or 'JPEG', quality=85, optimize=True)
            img_byte_arr.seek(0)

            return Response(
                img_byte_arr.getvalue(),
                mimetype=f'image/{img.format.lower() if img.format else "jpeg"}'
            )
    except Exception as e:
        print(f"图像处理错误: {str(e)}")
        abort(500)


class FolderChangeHandler(FileSystemEventHandler):
    """文件系统事件处理器：监控文件夹变化"""
    # ...（保持原有实现不变）


# 创建文件系统观察者
observer = Observer()
observer.schedule(FolderChangeHandler(), IMAGE_BASE, recursive=True)


def init_folder_cache(folder):
    """初始化文件夹缓存：扫描并验证图像文件"""
    folder_path = get_safe_path(IMAGE_BASE, folder)
    try:
        if not folder_path or not os.path.isdir(folder_path):
            return None

        valid_files = []
        for f in os.listdir(folder_path):
            file_path = get_safe_path(folder_path, f)
            if file_path and os.path.isfile(file_path) and f.lower().endswith(
                    ('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                valid_files.append(f)

        return sorted(valid_files) or None
    except Exception as e:
        print(f"初始化缓存失败: {str(e)}")
        return None


if __name__ == '__main__':
    # ...（保持原有启动代码不变）
    # 启动前检查：验证必需文件和目录存在
    required_files = {
        HTML_BASE: ['MainDomain.html', 'fnf.html'],  # 必需HTML模板
        IMAGE_BASE: []  # 只需目录存在
    }

    # 检查每个目录和文件
    for base, files in required_files.items():
        if not os.path.isdir(base):
            print(f"致命错误：目录不存在 {base}")
            exit(1)
        for f in files:
            path = os.path.join(base, f)
            if not os.path.isfile(path):
                print(f"致命错误：文件不存在 {path}")
                exit(1)
        # 打印目录访问权限
        print(f"目录验证通过：{base} (权限: {'可读' if os.access(base, os.R_OK) else '不可读'})")

    # 启动文件监控
    observer.start()
    print("文件监控已启动...")

    try:
        # 使用gevent WSGI服务器（高性能）
        from gevent import pywsgi
        # 创建服务器实例（监听所有IP的50721端口）
        server = pywsgi.WSGIServer(('0.0.0.0', 50721), app)
        print("服务器运行在 0.0.0.0:50721")
        server.serve_forever()  # 启动服务器
    except KeyboardInterrupt:
        observer.stop()  # Ctrl+C停止监控
    finally:
        observer.join()  # 等待监控线程结束