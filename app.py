from flask import Flask, redirect, send_from_directory  # 新增导入
import os
import random

app = Flask(__name__)
IMAGE_BASE = '/app/images'

def get_random_image(folder):
    folder_path = os.path.join(IMAGE_BASE, folder)
    if not os.path.exists(folder_path):
        return None
    
    images = [f for f in os.listdir(folder_path) 
             if os.path.isfile(os.path.join(folder_path, f)) 
             and f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    
    if not images:
        return None
    
    return random.choice(images)

@app.route('/<folder>')
def serve_random_image(folder):
    image = get_random_image(folder)
    if image:
        return redirect(f'/{folder}/{image}')
    return "No images found in this folder", 404

# 新增静态文件路由
@app.route('/<folder>/<filename>')
def serve_image(folder, filename):
    return send_from_directory(
        os.path.join(IMAGE_BASE, folder), 
        filename,
        mimetype='image'  # 自动识别MIME类型
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50721)