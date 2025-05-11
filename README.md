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

我们推荐您使用雨云一键部署

[![通过雨云一键部署](https://rainyun-apps.cn-nb1.rains3.com/materials/deploy-on-rainyun-cn.svg)](https://app.rainyun.com/apps/rca/store/5?ref=543098)

[![Deploy on RainYun](https://rainyun-apps.cn-nb1.rains3.com/materials/deploy-on-rainyun-en.svg)](https://app.rainyun.com/apps/rca/store/5?ref=543098)

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

部署项目后，无论您使用的是脚本还是容器，请找到映射出的（或目录内的）images文件夹，在里边再次添加子目录（比如pc），访问IP:50721/pc即可在pc这个文件夹内进行随机图片  

![Demo](https://vip.123pan.cn/1815812033/yk6baz03t0n000d7w33gztylj6ousn5aDIYPAIYPDqawDvxPAdQOAY==.png)
![Demo](https://vip.123pan.cn/1815812033/yk6baz03t0l000d7w33fd6idz4tm1327DIYPAIYPDqawDvxPAdQOAY==.png)
 

  


