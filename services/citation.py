import requests
import json
import traceback
from openai import OpenAI
from config import DEFAULT_LLM_KEY, DEFAULT_LLM_URL, DEFAULT_LLM_MODEL, CROSSREF_EMAIL
from utils import format_history
from services.prompts import get_citation_prompt

# 全局自定义缓存字典：将搜索过的结果永久保存在内存中
CITATION_CACHE = {}

def get_best_crossref_match(paper_title):
    """从 Crossref 获取前 5 个结果，并在本地进行精确标题匹配"""
    url = "https://api.crossref.org/works"
    params = {
        "query.title": paper_title, 
        "select": "title,author,issued,container-title,volume,issue,page,DOI,type",
        "rows": 5  # 取前 5 个最相关的
    }
    headers = {"User-Agent": f"CitationHelperBot/1.0 (mailto:{CROSSREF_EMAIL})"}
    
    res = requests.get(url, params=params, headers=headers, timeout=10)
    res.raise_for_status()
    items = res.json().get("message", {}).get("items",[])
    
    if not items:
        return None
        
    target_lower = paper_title.lower().strip()
    
    # 策略 1：绝对精确匹配 (如果某篇标题和用户输入一模一样，直接秒选它)
    for item in items:
        title = item.get("title", [""])[0].lower().strip()
        if target_lower == title:
            return item
            
    # 策略 2：包含匹配 (应对用户输入不全，或者带了额外标点符号的情况)
    for item in items:
        title = item.get("title", [""])[0].lower().strip()
        if target_lower in title or title in target_lower:
            return item
            
    # 策略 3：如果都不完全匹配，相信 Crossref 的默认相关性，返回第一个结果
    return items[0]

def generate_citation(paper_title, selected_styles, history):
    try:
        # 1. 变量安全初始化
        if history is None:
            history =[]
            
        paper_title = str(paper_title).strip() if paper_title else ""

        if not paper_title:
            return "❌ 请输入文献标题。", history, format_history(history)
        if not selected_styles:
            return "❌ 请至少选择一种引用格式。", history, format_history(history)
        if not DEFAULT_LLM_KEY:
            return "❌ 系统未配置大模型 Token，请联系管理员。", history, format_history(history)

        # 2. 生成唯一缓存 Key (标题 + 格式)
        sorted_styles = tuple(sorted(selected_styles))
        cache_key = (paper_title.lower(), sorted_styles)

        # 命中缓存拦截：直接从字典拿结果
        if cache_key in CITATION_CACHE:
            real_title, cached_result = CITATION_CACHE[cache_key]
            # 构造新的 history，避免修改原列表引发不可预知状态
            new_history =[{"title": real_title, "styles": selected_styles, "content": cached_result}] + history
            return cached_result, new_history, format_history(new_history)

        # 3. 极速检索 Crossref 数据库
        try:
            paper_data = get_best_crossref_match(paper_title)
        except Exception as e:
            return f"⚠️ 数据库检索超时或失败: {str(e)}", history, format_history(history)
            
        if not paper_data:
            return "⚠️ 未在国际学术数据库(Crossref)中找到该文献，请检查拼写。", history, format_history(history)
            
        real_title = paper_data.get("title", [paper_title])[0]
        raw_data_str = json.dumps(paper_data, ensure_ascii=False, indent=2)
        
        # 4. 拼接 Prompt 并调用大模型
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
        
        # 5. 生成成功，将结果写入全局缓存
        CITATION_CACHE[cache_key] = (real_title, result)
        
        # 6. 更新前端历史记录并返回
        history.insert(0, {"title": real_title, "styles": selected_styles, "content": result})
        return result, history, format_history(history)

    except Exception as e:
        print("【后台致命错误日志】:\n", traceback.format_exc())
        safe_history = history if isinstance(history, list) else []
        return f"❌ 系统发生错误: {str(e)}", safe_history, format_history(safe_history)