# 1. 专门为语音服务拉取 Python 3.11 的底座
FROM python:3.11-slim

# 2. 同样建立工作台
WORKDIR /app

# 3. 放入你刚刚把显卡尾巴砍掉的、带有 CPU 暗号的图纸
COPY requirements.txt .

# 4. 这一步可能要跑久一点，因为它要下载纯 CPU 版的 PyTorch
RUN pip install --no-cache-dir -r requirements.txt

# 5. 把源码放入集装箱 (注意：不要把 models_cache 庞大的模型文件夹放进来了，可以在 .dockerignore 里忽略它，或者以后传到服务器上映射)
COPY . .

# 6. 暴露你的语音微服务端口（假设是 8001）
EXPOSE 8001

# 7. 通电启动！(看截图你有 main.py 和 run.py，这里假设你用 run.py 启动)
CMD ["python", "run.py"]