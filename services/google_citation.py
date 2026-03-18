import requests
import traceback
from openai import OpenAI
from config import SYSTEM_SERPAPI_KEY, DEFAULT_LLM_KEY, DEFAULT_LLM_URL, DEFAULT_LLM_MODEL
from utils import format_history
from services.prompts import google_get_citation_prompt

def google_generate_citation(paper_title, selected_styles, history):
    try:
        # 1. 安全初始化
        if history is None:
            history = []
            
        paper_title = str(paper_title).strip() if paper_title else ""

        if not paper_title:
            return "❌ 请输入文献标题。", history, format_history(history)
        if not selected_styles:
            return "❌ 请至少选择一种引用格式。", history, format_history(history)

        if not SYSTEM_SERPAPI_KEY:
            return "❌ 系统未配置 SERPAPI_KEY，请联系管理员。", history, format_history(history)
        if not DEFAULT_LLM_KEY:
            return "❌ 系统未配置大模型 Token，请联系管理员。", history, format_history(history)

        # 2. SerpApi 检索基础信息
        search_url = "https://serpapi.com/search"
        search_params = {
            "engine": "google_scholar", 
            "q": paper_title, 
            "num": 1, 
            "api_key": SYSTEM_SERPAPI_KEY
        }
        search_res = requests.get(search_url, params=search_params).json()
        
        if "error" in search_res:
            return f"⚠️ SerpApi 检索报错: {search_res['error']}", history, format_history(history)

        organic_results = search_res.get("organic_results", [])
        if not organic_results:
            return "⚠️ 未在 Google Scholar 找到该文献，请检查拼写。", history, format_history(history)
            
        real_title = organic_results[0].get("title", paper_title)
        result_id = organic_results[0].get("result_id")
        
        # 3. 抓取引文原始数据 (Cite 接口)
        cite_res = requests.get(search_url, params={
            "engine": "google_scholar_cite", 
            "q": result_id, 
            "api_key": SYSTEM_SERPAPI_KEY
        }).json()
        
        if "error" in cite_res:
            return f"⚠️ SerpApi 获取引用数据报错: {cite_res['error']}", history, format_history(history)
        
        # 🌟 优化点：数据“脱水”与结构化清洗，方便 7B 模型阅读
        citations = cite_res.get('citations', [])
        cites_context = "\n".join([f"- {c.get('title')}: {c.get('snippet')}" for c in citations])
        
        links = cite_res.get('links', [])
        links_context = "\n".join([f"- {l.get('name')}: {l.get('link')}" for l in links])
        
        # 构建干净的输入上下文
        raw_data_str = f"文献标题: {real_title}\n\n"
        raw_data_str += f"各标准引用参考数据:\n{cites_context}\n\n"
        raw_data_str += f"学术导出链接:\n{links_context}"

        # 4. 拼接 Prompt 并调用 LLM
        styles_str = ", ".join(selected_styles)
        prompt = google_get_citation_prompt(styles_str=styles_str, raw_data_str=raw_data_str)

        # 🌟 优化点：增加 timeout=60.0，防止网络拥堵时无限卡死
        client = OpenAI(api_key=DEFAULT_LLM_KEY, base_url=DEFAULT_LLM_URL, timeout=60.0)
        response = client.chat.completions.create(
            model=DEFAULT_LLM_MODEL, 
            messages=[
                {"role": "system", "content": "You are a professional academic citation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        # 5. 更新历史记录
        history.insert(0, {"title": real_title, "styles": selected_styles, "content": result})
        return result, history, format_history(history)

    except Exception as e:
        print("【后台致命错误日志】:\n", traceback.format_exc())
        # 极简且绝对安全的兜底返回
        safe_history = history if isinstance(history, list) else []
        return f"❌ 系统发生错误: {str(e)}", safe_history, format_history(safe_history)