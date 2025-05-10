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

  python app.py  
 

  


