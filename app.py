from flask import Flask, redirect, send_from_directory, abort, render_template, request
import os
import random
import time
from threading import Lock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 创建Flask应用实例，设置模板文件夹路径
app = Flask(__name__, template_folder='html')
# 定义图像存储的基础路径
IMAGE_BASE = 'images'
# 定义HTML模板的基础路径
HTML_BASE = 'html'
# 创建文件夹缓存字典（用于存储各文件夹的图像列表）
folder_cache = {}
# 创建线程锁（确保多线程环境下的缓存操作安全）
cache_lock = Lock()

def get_safe_path(base, *paths):
    """验证并返回安全路径（防止路径遍历攻击）"""
    # 拼接完整路径并标准化
    full_path = os.path.abspath(os.path.join(base, *paths))
    # 检查路径是否在允许的基础路径内
    if not full_path.startswith(os.path.abspath(base)):
        return None  # 路径不安全返回None
    return full_path  # 安全路径

@app.route('/')
def serve_main_page():
    """主路由：显示包含所有子文件夹列表的主页"""
    # 获取IMAGE_BASE下所有合法的子文件夹
    subfolders = [d for d in os.listdir(IMAGE_BASE)
                 if os.path.isdir(get_safe_path(IMAGE_BASE, d))]
    # 渲染主页面模板并传入子文件夹列表
    return render_template('MainDomain.html', subfolders=subfolders)

@app.errorhandler(404)
def handle_404(e):
    """404错误处理：显示自定义404页面"""
    # 获取所有可用的子文件夹（用于导航）
    subfolders = [d for d in os.listdir(IMAGE_BASE)
                 if os.path.isdir(get_safe_path(IMAGE_BASE, d))]
    # 渲染404模板并传入子文件夹列表
    return render_template('fnf.html', subfolders=subfolders), 404

@app.errorhandler(500)
def handle_500(e):
    """500错误处理：返回简单错误消息"""
    return "服务器配置错误，请联系管理员", 500

@app.route('/favicon.ico')
def favicon():
    """网站图标路由"""
    # 安全获取favicon.ico路径
    icon_path = get_safe_path(app.root_path, 'static', 'favicon.ico')
    # 检查文件是否存在
    if not icon_path or not os.path.isfile(icon_path):
        abort(404)
    # 发送图标文件
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@app.route('/<path:folder>')
def serve_sequential_image(folder):
    """顺序服务图像：按预定义的随机顺序循环显示文件夹中的图像"""
    folder = folder.strip('/')  # 清理文件夹路径
    if not folder:
        return redirect('/')  # 空路径重定向到主页

    # 验证文件夹路径安全性
    folder_path = get_safe_path(IMAGE_BASE, folder)
    if not folder_path or not os.path.isdir(folder_path):
        abort(404)

    with cache_lock:  # 线程安全操作
        # 如果缓存中没有该文件夹
        if folder not in folder_cache:
            images = init_folder_cache(folder)  # 初始化缓存
            if not images:
                abort(404)  # 无有效图像

            # 创建基于文件夹和时间的随机种子
            seed = hash(f"{folder}-{time.time()}") % (2**32)
            random.seed(seed)
            shuffled = images.copy()
            random.shuffle(shuffled)  # 随机打乱图像列表

            # 将打乱后的列表存入缓存
            folder_cache[folder] = {
                'images': shuffled,
                'index': 0,  # 当前索引位置
                'seed': seed  # 使用的随机种子
            }

        cache = folder_cache[folder]
        if not cache['images']:
            del folder_cache[folder]  # 空列表则删除缓存项
            abort(404)

        # 获取当前图像并更新索引
        current_index = cache['index']
        image = cache['images'][current_index]
        # 循环索引（到达末尾后回到开头）
        cache['index'] = (current_index + 1) % len(cache['images'])

    # 重定向到实际图像URL
    return redirect(f'/{folder}/{image}')

@app.route('/random/<path:folder>')
def serve_random_image(folder):
    """随机服务图像：功能与顺序服务相同（代码结构保持一致性）"""
    # 实现逻辑与serve_sequential_image相同
    folder = folder.strip('/')
    if not folder:
        abort(404)


@app.route('/<path:folder>/<filename>')
def serve_image(folder, filename):
    """实际图像服务路由：发送图像文件"""
    # 验证文件夹路径
    safe_folder = get_safe_path(IMAGE_BASE, folder)
    if not safe_folder:
        abort(404)

    # 验证文件路径
    file_path = get_safe_path(safe_folder, filename)
    if not file_path or not os.path.isfile(file_path):
        abort(404)

    # 发送图像文件
    return send_from_directory(
        safe_folder,
        filename,
        mimetype='image'  # 通用MIME类型
    )

class FolderChangeHandler(FileSystemEventHandler):
    """文件系统事件处理器：监控文件夹变化"""

    def on_modified(self, event):
        """处理修改事件"""
        if event.is_directory:  # 只处理目录修改
            rel_path = os.path.relpath(event.src_path, IMAGE_BASE)
            self._invalidate_cache(rel_path, "修改")

    def on_created(self, event):
        """处理创建事件"""
        if not event.is_directory:  # 只处理文件创建
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
            self._invalidate_cache(folder, "创建")

    def on_deleted(self, event):
        """处理删除事件"""
        if not event.is_directory:  # 只处理文件删除
            folder = os.path.relpath(os.path.dirname(event.src_path), IMAGE_BASE)
            self._invalidate_cache(folder, "删除")

    def _invalidate_cache(self, folder, action):
        """使指定文件夹的缓存失效"""
        with cache_lock:
            if folder in folder_cache:
                print(f"缓存失效: {folder} ({action})")
                del folder_cache[folder]  # 删除缓存项

# 创建文件系统观察者
observer = Observer()
# 安排事件处理器监视IMAGE_BASE目录（递归监视）
observer.schedule(FolderChangeHandler(), IMAGE_BASE, recursive=True)

@app.after_request
def set_cache_control(response):
    """响应后处理：根据CDN请求头动态设置缓存策略"""
    if response.status_code == 200:
        # 检查请求头中是否存在 CDN: CDNRequest
        if request.headers.get('CDN') == 'CDNRequest':
            # CDN请求：设置公共缓存5分钟
            response.headers['Cache-Control'] = 'public'
        else:
            # 非CDN请求：强制每次验证
            response.headers['Cache-Control'] = 'no-cache'
    return response

def init_folder_cache(folder):
    """初始化文件夹缓存：扫描并验证图像文件"""
    folder_path = get_safe_path(IMAGE_BASE, folder)
    try:
        if not folder_path or not os.path.isdir(folder_path):
            return None

        valid_files = []
        for f in os.listdir(folder_path):
            file_path = get_safe_path(folder_path, f)
            # 验证文件存在且是支持的图像格式
            if file_path and os.path.isfile(file_path) and f.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                valid_files.append(f)

        # 返回排序后的文件列表（确保跨平台一致性）
        return sorted(valid_files) or None
    except Exception as e:
        print(f"初始化缓存失败: {str(e)}")
        return None

if __name__ == '__main__':
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