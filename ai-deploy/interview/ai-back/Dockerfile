# 1. 拉取轻量级的 Python 3.13 官方底座
FROM python:3.11-slim

# 2. 在集装箱里建一个叫 /app 的工作台
WORKDIR /app

# 3. 先把纯净的图纸放进去
COPY requirements.txt .

# 4. 照着图纸疯狂下载（加上 --no-cache-dir 可以防止产生缓存垃圾，让集装箱更小）
RUN pip install --no-cache-dir -r requirements.txt

# 5. 把你的 app 目录、run.py 等业务代码全拷进去
COPY . .

# 6. 暴露 8000 端口（假设你的后端跑在这个端口）
EXPOSE 8000

# 7. 通电启动你的主后端！
CMD ["python", "run.py"]