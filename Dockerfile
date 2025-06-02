FROM python:3.9-slim

WORKDIR /app

# 设置清华PyPI镜像源
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn
    
COPY app.py .
COPY static ./static
COPY html ./html


EXPOSE 50721

CMD ["python","-u","app.py"]