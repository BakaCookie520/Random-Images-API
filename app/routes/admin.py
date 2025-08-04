"""
管理员路由模块
"""
import os
import shutil
from io import BytesIO
from PIL import Image
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, abort
from werkzeug.utils import secure_filename
from ..utils.admin import is_password_set, set_admin_password, verify_admin_password, login_required, DEFAULT_ADMIN_USERNAME
from ..utils.security import get_safe_path
from ..config.config import Config

# 创建蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/@manage')

@admin_bp.route('/')
def index():
    """
    管理员首页
    """
    # 检查是否已登录
    if not session.get('admin_logged_in'):
        # 检查是否已设置密码
        if not is_password_set():
            return redirect(url_for('admin.setup'))
        else:
            return redirect(url_for('admin.login'))
    
    # 获取所有图片文件夹
    image_base = Config.IMAGE_BASE
    folders = []
    
    if os.path.exists(image_base) and os.path.isdir(image_base):
        folders = [d for d in os.listdir(image_base) 
                  if os.path.isdir(os.path.join(image_base, d))]
    
    # 获取消息提示（如果有）
    message = session.pop('message', None)
    success = session.pop('success', True)
    
    return render_template('admin_panel.html', 
                          folders=folders,
                          message=message,
                          success=success)

@admin_bp.route('/setup', methods=['GET', 'POST'])
def setup():
    """
    首次设置管理员密码
    """
    # 如果已经设置了密码，重定向到登录页面
    if is_password_set():
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 验证密码
        if not password or len(password) < 6:
            return render_template('admin_setup.html', error='密码长度必须至少为6个字符')
        
        if password != confirm_password:
            return render_template('admin_setup.html', error='两次输入的密码不一致')
        
        # 设置密码
        if set_admin_password(password):
            flash('管理员密码设置成功，请登录', 'success')
            return redirect(url_for('admin.login'))
        else:
            return render_template('admin_setup.html', error='设置密码时出错，请重试')
    
    return render_template('admin_setup.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    管理员登录
    """
    # 如果未设置密码，重定向到设置页面
    if not is_password_set():
        return redirect(url_for('admin.setup'))
    
    # 如果已登录，重定向到管理面板
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.index'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if verify_admin_password(password):
            session['admin_logged_in'] = True
            flash('登录成功', 'success')
            return redirect(url_for('admin.index'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    return render_template('admin_login.html')

@admin_bp.route('/logout')
def logout():
    """
    管理员退出登录
    """
    session.pop('admin_logged_in', None)
    flash('已退出登录', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    """
    创建新的图片集合文件夹
    """
    folder_name = request.form.get('folder_name')
    
    if not folder_name:
        session['message'] = '文件夹名称不能为空'
        session['success'] = False
        return redirect(url_for('admin.index'))
    
    # 安全处理文件夹名称
    folder_name = secure_filename(folder_name)
    
    # 创建文件夹
    folder_path = os.path.join(Config.IMAGE_BASE, folder_name)
    
    if os.path.exists(folder_path):
        session['message'] = f'文件夹 {folder_name} 已存在'
        session['success'] = False
    else:
        try:
            os.makedirs(folder_path)
            session['message'] = f'文件夹 {folder_name} 创建成功'
            session['success'] = True
        except Exception as e:
            session['message'] = f'创建文件夹时出错: {str(e)}'
            session['success'] = False
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/delete_folder', methods=['POST'])
@login_required
def delete_folder():
    """
    删除图片集合文件夹
    """
    folder_name = request.form.get('folder_name')
    
    if not folder_name:
        session['message'] = '文件夹名称不能为空'
        session['success'] = False
        return redirect(url_for('admin.index'))
    
    # 安全处理文件夹路径
    folder_path = get_safe_path(Config.IMAGE_BASE, folder_name)
    
    if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        session['message'] = f'文件夹 {folder_name} 不存在'
        session['success'] = False
    else:
        try:
            shutil.rmtree(folder_path)
            session['message'] = f'文件夹 {folder_name} 已删除'
            session['success'] = True
        except Exception as e:
            session['message'] = f'删除文件夹时出错: {str(e)}'
            session['success'] = False
    
    return redirect(url_for('admin.index'))

@admin_bp.route('/folder/<folder_name>')
@login_required
def view_folder(folder_name):
    """
    查看文件夹内容
    """
    # 安全处理文件夹路径
    folder_path = get_safe_path(Config.IMAGE_BASE, folder_name)
    
    if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        abort(404)
    
    # 获取文件夹中的所有图片
    images = []
    for f in os.listdir(folder_path):
        file_path = os.path.join(folder_path, f)
        if os.path.isfile(file_path) and any(f.lower().endswith(ext) for ext in Config.IMAGE_EXTENSIONS):
            images.append(f)
    
    # 按名称排序
    images.sort()
    
    # 获取消息提示（如果有）
    message = session.pop('message', None)
    success = session.pop('success', True)
    
    return render_template('admin_folder_view.html', 
                          folder_name=folder_name,
                          images=images,
                          message=message,
                          success=success)

@admin_bp.route('/folder/<folder_name>/upload', methods=['POST'])
@login_required
def upload_image(folder_name):
    """
    上传图片到指定文件夹
    """
    # 安全处理文件夹路径
    folder_path = get_safe_path(Config.IMAGE_BASE, folder_name)
    
    if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        abort(404)
    
    # 检查是否有文件上传
    if 'image_file' not in request.files:
        session['message'] = '没有选择文件'
        session['success'] = False
        return redirect(url_for('admin.view_folder', folder_name=folder_name))
    
    file = request.files['image_file']
    
    # 如果用户没有选择文件
    if file.filename == '':
        session['message'] = '没有选择文件'
        session['success'] = False
        return redirect(url_for('admin.view_folder', folder_name=folder_name))
    
    # 检查文件类型
    if not any(file.filename.lower().endswith(ext) for ext in Config.IMAGE_EXTENSIONS):
        session['message'] = '不支持的文件类型，请上传图片文件'
        session['success'] = False
        return redirect(url_for('admin.view_folder', folder_name=folder_name))
    
    # 安全处理文件名
    filename = secure_filename(file.filename)
    file_path = os.path.join(folder_path, filename)
    
    # 保存文件
    try:
        file.save(file_path)
        session['message'] = f'图片 {filename} 上传成功'
        session['success'] = True
    except Exception as e:
        session['message'] = f'上传图片时出错: {str(e)}'
        session['success'] = False
    
    return redirect(url_for('admin.view_folder', folder_name=folder_name))

@admin_bp.route('/folder/<folder_name>/delete', methods=['POST'])
@login_required
def delete_image(folder_name):
    """
    从指定文件夹删除图片
    """
    # 安全处理文件夹路径
    folder_path = get_safe_path(Config.IMAGE_BASE, folder_name)
    
    if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        abort(404)
    
    image_name = request.form.get('image_name')
    
    if not image_name:
        session['message'] = '图片名称不能为空'
        session['success'] = False
        return redirect(url_for('admin.view_folder', folder_name=folder_name))
    
    # 安全处理文件路径
    file_path = get_safe_path(folder_path, image_name)
    
    if not file_path or not os.path.exists(file_path) or not os.path.isfile(file_path):
        session['message'] = f'图片 {image_name} 不存在'
        session['success'] = False
    else:
        try:
            os.remove(file_path)
            session['message'] = f'图片 {image_name} 已删除'
            session['success'] = True
        except Exception as e:
            session['message'] = f'删除图片时出错: {str(e)}'
            session['success'] = False
    
    return redirect(url_for('admin.view_folder', folder_name=folder_name))

@admin_bp.route('/folder/<folder_name>/download/<image_name>')
@login_required
def download_image(folder_name, image_name):
    """
    下载指定文件夹中的图片
    """
    # 安全处理文件夹路径
    folder_path = get_safe_path(Config.IMAGE_BASE, folder_name)
    
    if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        abort(404)
    
    # 安全处理文件路径
    file_path = get_safe_path(folder_path, image_name)
    
    if not file_path or not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    return send_file(file_path, as_attachment=True)

@admin_bp.route('/folder/<folder_name>/thumbnail/<image_name>')
@login_required
def get_image_thumbnail(folder_name, image_name):
    """
    获取指定图片的缩略图
    """
    # 安全处理文件夹路径
    folder_path = get_safe_path(Config.IMAGE_BASE, folder_name)
    
    if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        abort(404)
    
    # 安全处理文件路径
    file_path = get_safe_path(folder_path, image_name)
    
    if not file_path or not os.path.exists(file_path) or not os.path.isfile(file_path):
        abort(404)
    
    try:
        # 创建缩略图
        img = Image.open(file_path)
        img.thumbnail(Config.THUMBNAIL_SIZE)
        
        # 将图片转换为字节流
        img_io = BytesIO()
        img_format = img.format or 'JPEG'
        img.save(img_io, format=img_format)
        img_io.seek(0)
        
        return send_file(img_io, mimetype=f'image/{img_format.lower()}')
    except Exception as e:
        print(f"生成缩略图时出错: {str(e)}")
        abort(500)