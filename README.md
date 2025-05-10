# Random-Images-API


一个基于Flask的Docker容器服务，支持动态子文件夹管理和随机图片展示。当访问`/子文件夹名称`时，将随机重定向到该文件夹下的任意图片文件。

## Demo

random-image-api.bakacookie520.top/pc

## 功能特性

✅ 动态子文件夹检测  
✅ 支持常见图片格式（PNG/JPG/JPEG/GIF/WEBP）  
✅ 实时文件更新（无需重启服务）  
✅ 随机图片重定向  
✅ 一个服务部署多个API

### 前置要求
- Docker 20.10+
- 至少100MB可用磁盘空间
- （可选）使用脚本使安装Python环境

## 快速开始

### 从Release下载Docker镜像或者脚本压缩包

1.使用Docker

  (1)导入
  
     docker import ria < Random-Images-API.tar 
     
  (2)启动
  
    docker run -d \
    -p 50721:50721 \
    -v $(pwd)/images:/app/images \
    --name my-image-server \
    ria:latest

  
2.使用脚本  

  `python app.py`

### 如何使用？  

部署项目后，无论您使用的是脚本还是容器，请找到映射出的（或目录内的）images文件夹，在里边再次添加子目录（比如pc），访问IP:50721/pc即可在pc这个文件夹内进行随即图片  

![Demo](https://alist.bakacookie520.top/d/123/%E5%9B%BE%E5%BA%8A/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202025-05-10%20081825.png?sign=3gPJ0_hDG3PXdKH4P4ahoBzTQvfJB-n-lM_2XCgildM=:0)
![Demo](https://alist.bakacookie520.top/d/123/%E5%9B%BE%E5%BA%8A/%E5%B1%8F%E5%B9%95%E6%88%AA%E5%9B%BE%202025-05-10%20081933.png?sign=LCGsdYVvgrYP_DqL-TjVxwm6RiU4F741D1xk7oMQyog=:0)
 

  


