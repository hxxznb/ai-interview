import uvicorn
import os

if __name__ == "__main__":
    # 通过环境变量读取端口，默认为 8001
    port = int(os.environ.get("PORT", 8001))
    
    # 启动 FastAPI 服务
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
