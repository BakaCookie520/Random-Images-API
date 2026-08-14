

# Random-Images-API

<div align="center">

[![Docker Build](https://img.shields.io/badge/Docker-Supported-blue?logo=docker)](https://www.docker.com/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

一个轻量级的随机图片 API 服务，支持多文件夹管理和真随机访问

[在线演示](http://random-image-api.bakacookie520.top/pc) · [报告问题](https://github.com/BakaCookie520/Random-Images-API/issues) · [功能建议](https://github.com/BakaCookie520/Random-Images-API/issues)

</div>

---

## ✨ 功能特性

- 🎲 **真随机访问** - 每次请求都随机选择图片，无固定顺序
- 📁 **多文件夹管理** - 支持动态子文件夹，一个服务管理多个图库
- 🌐 **全局随机** - `/random` 路径可从所有文件夹中随机选择图片
- 🔄 **实时更新** - 文件监控自动刷新缓存，无需重启服务
- 🛡️ **安全防护** - 路径遍历防护、IP 封禁、请求限流
- 🐳 **容器化部署** - 支持 Docker 一键部署

## 📦 快速部署

### 方式一：Docker（推荐）

```bash
# 拉取镜像
docker pull ghcr.io/bakacookie520/random-images-api:latest

# 启动服务
docker run -d \
  -p 50721:50721 \
  -v $(pwd)/images:/app/images \
  -v $(pwd)/config:/app/config \
  --name random-images-api \
  ghcr.io/bakacookie520/random-images-api:latest
```

### 方式二：雨云一键部署

[![通过雨云一键部署](https://rainyun-apps.cn-nb1.rains3.com/materials/deploy-on-rainyun-cn.svg)](https://app.rainyun.com/apps/rca/store/6218?ref=543098)
[![Deploy on RainYun](https://rainyun-apps.cn-nb1.rains3.com/materials/deploy-on-rainyun-en.svg)](https://app.rainyun.com/apps/rca/store/6218?ref=543098)

### 方式三：Python 脚本

```bash
# 克隆项目
git clone https://github.com/BakaCookie520/Random-Images-API.git
cd Random-Images-API

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 创建图片目录
mkdir images

# 启动服务
python run.py
```

## 🚀 使用指南

### 1. 准备图片

在 `images` 目录下创建子文件夹并添加图片：

```
images/
├── pc/          # 电脑壁纸
│   ├── img1.jpg
│   └── img2.png
├── mobile/      # 手机壁纸
│   └── img3.jpg
└── anime/       # 动漫图片
    └── img4.webp
```

### 2. API 接口

| 接口路径 | 说明 | 示例 |
|---------|------|------|
| `/` | 主页，显示所有文件夹 | `http://localhost:50721/` |
| `/{folder}` | 随机返回指定文件夹中的图片 | `http://localhost:50721/pc` |
| `/random` | 从所有文件夹中随机返回图片 | `http://localhost:50721/random` |
| `/browse/{folder}` | 浏览文件夹中的所有图片 | `http://localhost:50721/browse/pc` |

### 3. 支持的图片格式

PNG、JPG、JPEG、GIF、WEBP

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `PORT` | 50721 | 服务端口 |
| `FLASK_ENV` | development | 运行环境（development/production） |
| `SECRET_KEY` | 随机生成 | Flask 密钥 |

### CDN 配置（可选）

如需使用 CDN 加速，请配置以下设置：

1. **节点响应头**：`Cache-Control: no-cache`
2. **回源请求头**：`CDN: CDNRequest`
3. **Range 回源**：跟随客户端 Range 请求

## 📸 效果展示

<div align="center">

![主页展示](https://github.com/user-attachments/assets/9fefa530-adb7-4491-b66a-50f937537a6d)

![浏览模式](https://github.com/user-attachments/assets/f210625b-5a97-4638-b5b1-b6fa766ab01c)

</div>

## 🛠️ 技术栈

- **后端框架**：Flask 2.3.3
- **WSGI 服务器**：gevent 23.9.1
- **图片处理**：Pillow 11.3.0
- **限流保护**：flask-limiter 3.5.0
- **文件监控**：watchdog 6.0.0

## 📝 更新日志

### v2.0.0
- ✨ 新增 `/random` 接口，支持从所有文件夹随机选择图片
- 🎲 将随机逻辑改为真随机，每次访问都随机选择
- 🎨 优化代码结构，提升性能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目基于 [MIT](LICENSE.txt) 许可证开源。

---

<div align="center">

如果这个项目对你有帮助，请给个 ⭐️ 支持一下！

</div>
