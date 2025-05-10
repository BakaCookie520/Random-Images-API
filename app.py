from flask import Flask, redirect, send_from_directory
import os
import random
import time
from threading import Lock

app = Flask(__name__)
IMAGE_BASE = '/app/images'
app_start_time = time.time()
folder_cache = {}
cache_lock = Lock()

@app.after_request
def set_cache_control(response):
    """统一设置Cache-Control: public"""
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
    
    seed = hash(f"{folder}-{app_start_time}") % (2**32)
    random.seed(seed)
    random.shuffle(images)
    
    return images or None

@app.route('/<folder>')
def serve_sequential_image(folder):
    with cache_lock:
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=50721)