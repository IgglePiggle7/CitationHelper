import requests
import json
import traceback
from functools import lru_cache
from openai import OpenAI
from config import DEFAULT_LLM_KEY, DEFAULT_LLM_URL, DEFAULT_LLM_MODEL, CROSSREF_EMAIL
from utils import format_history
from services.prompts import get_citation_prompt

# 引入内存缓存：最近搜索过的 50 篇文献
@lru_cache(maxsize=50)
def fetch_crossref_metadata(paper_title):
    """通过 Crossref API 获取极其纯净的论文元数据 (耗时仅 ~0.5秒)"""
    url = "https://api.crossref.org/works"
    params = {
        "query.bibliographic": paper_title,
        "select": "title,author,issued,container-title,volume,issue,page,DOI,type",
        "rows": 1 # 只取最匹配的第一条
    }
    # 模拟浏览器请求头，防止被墙
    headers = {"User-Agent": f"CitationHelperBot/1.0 (mailto:{CROSSREF_EMAIL})"}
    
    res = requests.get(url, params=params, headers=headers, timeout=10)
    res.raise_for_status()
    data = res.json()
    
    items = data.get("message", {}).get("items",[])
    return items[0] if items else None

def generate_citation(paper_title, selected_styles, history):
    try:
        if history is None:
            history =[]
            
        paper_title = str(paper_title).strip() if paper_title else ""

        if not paper_title:
            return "❌ 请输入文献标题。", history, format_history(history)
        if not selected_styles:
            return "❌ 请至少选择一种引用格式。", history, format_history(history)

        if not DEFAULT_LLM_KEY:
            return "❌ 系统未配置大模型 Token，请联系管理员。", history, format_history(history)

        # 检索 Crossref 数据库
        try:
            paper_data = fetch_crossref_metadata(paper_title)
        except Exception as e:
            return f"⚠️ 数据库检索超时或失败: {str(e)}", history, format_history(history)
            
        if not paper_data:
            return "⚠️ 未在国际学术数据库(Crossref)中找到该文献，请检查拼写。", history, format_history(history)
            
        # 提取真实标题（处理 Crossref 返回的列表结构）
        title_list = paper_data.get("title", [paper_title])
        real_title = title_list[0] if title_list else paper_title
        
        # 将结构化的 JSON 拍平成美观的字符串喂给大模型
        raw_data_str = json.dumps(paper_data, ensure_ascii=False, indent=2)

        # 拼接 Prompt 并调用 LLM
        styles_str = ", ".join(selected_styles)
        prompt = get_citation_prompt(styles_str=styles_str, raw_data_str=raw_data_str)

        client = OpenAI(api_key=DEFAULT_LLM_KEY, base_url=DEFAULT_LLM_URL)
        response = client.chat.completions.create(
            model=DEFAULT_LLM_MODEL, 
            messages=[
                {"role": "system", "content": "You are a professional academic citation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        # 更新历史记录并返回
        history.insert(0, {"title": real_title, "styles": selected_styles, "content": result})
        return result, history, format_history(history)

    except Exception as e:
        print("【后台致命错误日志】:\n", traceback.format_exc())
        safe_history = history if isinstance(history, list) else []
        return f"❌ 系统发生错误: {str(e)}", safe_history, format_history(safe_history)