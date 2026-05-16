# 第 1 步：告诉 Docker，给我拉取一个官方的 Nginx 服务器集装箱。
# 尾巴上的 alpine 代表我们选用的是极其精简的 Linux 底层，整个集装箱只有十几兆！
FROM nginx:alpine

# 第 2 步（可选但推荐）：把 Nginx 原本自带的那个丑陋的欢迎页面给删干净。
RUN rm -rf /usr/share/nginx/html/*

# 第 3 步：把你的心血结晶！也就是本地的 dist 文件夹里的所有死文件，
# 原封不动地复制到 Nginx 集装箱的“展台”目录里。
COPY dist/ /usr/share/nginx/html/

# 第 4 步：在集装箱上开一个洞，暴露 80 端口（这是互联网默认的网页浏览端口）。
EXPOSE 80

# 第 5 步：通电开机！让 Nginx 作为一个后台守护神，永远不要停止运行，持续接待外部访客。
CMD ["nginx", "-g", "daemon off;"]