import os
import tempfile
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from funasr import AutoModel


current_dir = os.path.dirname(os.path.abspath(__file__))
cache_path = os.path.join(current_dir, "models_cache")
os.environ["MODELSCOPE_CACHE"] = cache_path

# 实例化一个 FastAPI 应用程序
app = FastAPI(title="AI 听觉微服务")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 允许所有源（开发环境适用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("正在预热 AI 听觉神经 (模型加载中)...")
# 把模型放在外层，这样它只会伴随服务器启动加载一次，以后每次请求都是秒出！
model = AutoModel(
    model="paraformer-zh",
    vad_model="fsmn-vad",
    punc_model="ct-punc",
    disable_update=True
)
print("听觉神经准备就绪，正在监听 8001 端口！")


# 定义一个接收音频的 API 接口
@app.post("/api/recognize")
async def recognize_audio(file: UploadFile = File(...)):
    # 1. 接收前端或主后端发来的音频流，暂存到系统的临时文件中
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    file_size = len(content)
    # 粗略计算 WAV 时长 (16kHz, 16bit, mono → 32000 bytes/s)
    estimated_duration = max(0, (file_size - 44)) / 32000
    print(f"[收到音频] 文件名: {file.filename}, 大小: {file_size} bytes, 估算时长: {estimated_duration:.2f}s")

    try:
        # 2. 召唤 FunASR 进行识别
        res = model.generate(input=tmp_path)
        # 提取识别出的文字
        recognized_text = res[0]["text"] if res else ""
        print(f"[识别结果] 文字长度: {len(recognized_text)}, 内容: '{recognized_text[:100]}'")

        # 3. 包装成标准的 JSON 格式返回
        return {
            "code": 200,
            "text": recognized_text,
            "msg": "识别成功"
        }
    except Exception as e:
        print(f"[识别出错] {str(e)}")
        return {"code": 500, "text": "", "msg": f"识别出错: {str(e)}"}
    finally:
        # 4. 阅后即焚：识别完立刻删掉临时音频文件，绝不占用硬盘空间
        if os.path.exists(tmp_path):
            os.remove(tmp_path)