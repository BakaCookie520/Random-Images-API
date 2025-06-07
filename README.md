# Random-Images-API


一个基于Flask的Docker容器服务，支持动态子文件夹管理和随机图片展示。当访问`/子文件夹`时，将随机重定向到该文件夹下的任意图片文件。

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
- （可选）使用脚本时安装Python环境

## 快速开始

我们推荐您使用雨云一键部署

[![通过雨云一键部署](https://rainyun-apps.cn-nb1.rains3.com/materials/deploy-on-rainyun-cn.svg)](https://app.rainyun.com/apps/rca/store/6218?ref=543098)

[![Deploy on RainYun](https://rainyun-apps.cn-nb1.rains3.com/materials/deploy-on-rainyun-en.svg)](https://app.rainyun.com/apps/rca/store/6218?ref=543098)

### 从Release下载Docker镜像或者脚本压缩包

1.使用Docker

  (1)拉取镜像
  
    docker pull ghcr.io/bakacookie520/random-images-api:latest 
     
  (2)启动
  
    docker run -d \
    -p 50721:50721 \
    -v $(pwd)/images:/app/images \
    --name my-image-server \
    ghcr.io/bakacookie520/random-images-api:latest

  
2.使用脚本（仅支持Python 3.11版本）    

  （1）克隆项目

    git clone https://github.com/BakaCookie520/Random-Images-API.git

  （2）安装环境  

    pip install --no-cache-dir Flask==3.0.2 watchdog==4.0.0 gevent -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn 

  （3）启动  

    python app.py 

### 使用CDN（可选）  

推荐使用阿里云CDN

  1.在域名管理/域名/缓存配置/节点HTTP响应头中，配置`Cache-Control: no-cache`
  
  ![image](https://github.com/user-attachments/assets/134b163d-f5e9-4bfc-9776-180e44686667)


  2.在域名管理/域名/回源配置/回源HTTP请求头中，配置自定义回源请求头`CDN: CDNRequest`

  ![image](https://github.com/user-attachments/assets/7bd0cccd-6010-414a-aa68-ad406fea437e)

  3.在域名管理/域名/视频相关中，配置`Range回源：跟随客户端Range请求`  

  ![image](https://github.com/user-attachments/assets/7ba38634-964a-4b4d-9ecb-31d8fa89ee3f)

  4.在域名管理/域名/EdgeScript自定义策略中，配置规则如下：


       if match_re($uri, '^/pc') {
        set_cache_ttl('code', '301=0,302=0')
    }
        if match_re($uri, '^/mobile') {
        set_cache_ttl('code', '301=0,302=0')
    }


### 如何使用？  

部署项目后，无论您使用的是脚本还是容器，请找到映射出的（或目录内的）images文件夹，在里边再次添加子目录（比如pc），访问IP:50721/pc即可在pc这个文件夹内进行随机图片  

![Demo](https://vip.123pan.cn/1815812033/yk6baz03t0n000d7w33gztylj6ousn5aDIYPAIYPDqawDvxPAdQOAY==.png)
![Demo](https://vip.123pan.cn/1815812033/yk6baz03t0m000d7w33g8h9k66nw0ly9DIYPAIYPDqawDvxPAdQOAY==.png)
![main domain](https://vip.123pan.cn/1815812033/ymjew503t0m000d7w32xqlzu1o3n0tkrDIYPAIYPDqawDvxPAdQOAY==.png)
![404](https://vip.123pan.cn/1815812033/ymjew503t0n000d7w32y5tueh6fq0lrlDIYPAIYPDqawDvxPAdQOAY==.png)

  


