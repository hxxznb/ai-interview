import os
import shutil
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import MarkdownHeaderTextSplitter

from app.config import settings

# 确保 API Key 可用
os.environ["DASHSCOPE_API_KEY"] = settings.DASHSCOPE_API_KEY

# 动态获取项目根目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
DB_DIR = os.path.join(BASE_DIR, "chroma_db")


def load_documents_with_metadata(directory):
    """
    遍历目录及其子目录，加载文件并根据文件夹自动打上 Metadata 标签。
    - category 标签始终取顶层目录名（如 front, java, general），确保 RAG 检索能命中。
    - type 标签区分内容类型：子文件夹名含 _code 的标记为 "code"，否则为 "theory"。
    """
    documents = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)

            # 计算相对路径
            rel_path = os.path.relpath(root, directory)

            if rel_path == ".":
                # 根目录下的文件归入 general
                category = "general"
                doc_type = "theory"
            else:
                # 将路径按分隔符拆分，取第一级作为 category
                parts = rel_path.replace("\\", "/").split("/")
                category = parts[0]  # 顶层目录名，如 front, java
                # 子文件夹名含 _code 则标记为代码题
                doc_type = "code" if any("_code" in p for p in parts[1:]) else "theory"

            loader = None
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
            elif file.endswith(".txt") or file.endswith(".md"):
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                continue

            if loader:
                docs = loader.load()
                for doc in docs:
                    doc.metadata["category"] = category
                    doc.metadata["type"] = doc_type

                documents.extend(docs)
                print(f"✅ 成功加载: {file_path} | 分类: [{category}] | 类型: [{doc_type}]")

    return documents


def build_vector_db():
    print(f"🚀 开始构建带分类标签的本地知识库...")
    if os.path.exists(DB_DIR):
        print(f"发现旧的向量数据库，正在清理：{DB_DIR}")
        shutil.rmtree(DB_DIR)
        print("清理完毕。")
    print(f"📂 读取目录: {KNOWLEDGE_BASE_DIR}")

    docs = load_documents_with_metadata(KNOWLEDGE_BASE_DIR)
    if not docs:
        print("❌ 知识库为空或没有支持的文件！")
        return

    headers_to_split_on = [
        ("##", "question"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)

    split_docs = []
    for doc in docs:
        if "category" in doc.metadata:
            # 1. 按照 Markdown 标题切分
            md_docs = markdown_splitter.split_text(doc.page_content)

            for md_doc in md_docs:
                # ✅ 【关键修改】：使用 update() 把原文档的所有标签（包括 category 和 type）完整复制过来
                md_doc.metadata.update(doc.metadata)

            # 2. 再按字符长度切分
            split_docs.extend(text_splitter.split_documents(md_docs))
        else:
            split_docs.extend(text_splitter.split_documents([doc]))

    print(f"✂️ 文件已通过 Markdown 规则精准切分为 {len(split_docs)} 个文本块。")

    embeddings = DashScopeEmbeddings(model=settings.EMBEDDING_MODEL)

    print(f"💾 正在写入本地 Chroma 数据库 ({DB_DIR})...")
    vectordb = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings,
        persist_directory=DB_DIR
    )

    print("🎉 构建完成！知识库已更新。")


if __name__ == "__main__":
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        os.makedirs(KNOWLEDGE_BASE_DIR)
        print(f"📁 已在根目录创建 {KNOWLEDGE_BASE_DIR}，请放入文件后重试！")
    else:
        build_vector_db()
