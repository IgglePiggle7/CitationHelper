import os
from dotenv import load_dotenv
load_dotenv()

# SerpApi 配置 (系统默认额度)
SYSTEM_SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")

# LLM 配置 (使用 HF 免费资源)
HF_TOKEN = os.environ.get("HF_TOKEN", "")
# 默认的大模型请求地址与模型名称
DEFAULT_LLM_URL = "https://router.huggingface.co/v1"
DEFAULT_LLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_LLM_KEY = HF_TOKEN

# # 通义千问
# LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
# LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")