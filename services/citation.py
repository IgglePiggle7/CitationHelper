import requests
from openai import OpenAI
from config import SYSTEM_SERPAPI_KEY, DEFAULT_LLM_KEY, DEFAULT_LLM_URL, DEFAULT_LLM_MODEL
from utils import format_history

def generate_citation(paper_title, selected_styles, user_serpapi_key, user_api_key, user_base_url, user_model, history):
    """
    基于 SerpApi (Google Scholar) 检索文献，并通过大模型生成指定格式引用。
    """
    if history is None:
        history =[]
        
    if not paper_title.strip():
        return "❌ 请输入文献标题。", history, format_history(history)
    if not selected_styles:
        return "❌ 请至少选择一种引用格式。", history, format_history(history)

    # 动态确定凭证 (优先使用用户自带的 Key，防止系统池被刷爆)
    current_serpapi_key = user_serpapi_key.strip() if user_serpapi_key.strip() else SYSTEM_SERPAPI_KEY
    current_api_key = user_api_key.strip() if user_api_key.strip() else DEFAULT_LLM_KEY
    current_base_url = user_base_url.strip() if user_base_url.strip() else DEFAULT_LLM_URL
    current_model = user_model.strip() if user_model.strip() else DEFAULT_LLM_MODEL

    if not current_serpapi_key:
        return "❌ 系统未配置 SERPAPI_KEY，且您未提供自带的 Key。请在高级设置中填写。", history, format_history(history)
    if not current_api_key:
        return "❌ 系统未配置大模型 Token，且您未提供自己的 API Key。请在高级设置中填写。", history, format_history(history)

    try:
        # 第一步：在 Google Scholar 搜索文献
        search_url = "https://serpapi.com/search"
        search_params = {
            "engine": "google_scholar",
            "q": paper_title,
            "api_key": current_serpapi_key,
            "num": 1
        }
        search_res = requests.get(search_url, params=search_params).json()
        
        # 错误处理：检查是否因为 SerpApi 额度耗尽报错
        if "error" in search_res:
            return f"⚠️ SerpApi 报错: {search_res['error']} (可能是搜索额度耗尽，请尝试在高级设置中填入您自己的 SerpApi Key)", history, format_history(history)

        organic_results = search_res.get("organic_results",[])
        if not organic_results:
            return "⚠️ 未在 Google Scholar 找到该文献，请检查标题是否拼写正确。", history, format_history(history)
            
        result_id = organic_results[0].get("result_id")
        real_title = organic_results[0].get("title", paper_title)
        
        # 第二步：获取多种引用格式原始数据
        cite_params = {
            "engine": "google_scholar_cite",
            "q": result_id,
            "api_key": current_serpapi_key
        }
        cite_res = requests.get(search_url, params=cite_params).json()
        raw_citations = cite_res.get("citations", [])
        links = cite_res.get("links",[])
        
        raw_data_str = f"文献标题: {real_title}\n"
        raw_data_str += "SerpApi 提供的基础格式:\n" + str(raw_citations) + "\n"
        raw_data_str += "SerpApi 提供的链接(含BibTeX等):\n" + str(links)

        # 第三步：调用大模型进行精准格式化
        client = OpenAI(api_key=current_api_key, base_url=current_base_url)
        styles_str = ", ".join(selected_styles)
        
        prompt = f"""
你是一个严格的学术参考文献格式生成专家。
任务：基于以下 Google Scholar 提供的原始引用数据，**仅**生成用户指定的格式，并直接以标准的 **Markdown** 格式输出。

【用户指定的格式】: {styles_str}

【原始引用数据】:
{raw_data_str}

【格式规范库】:
1. **GB/T 7714-2015**: 
   - 格式：AUTHOR A. Title[J]. Journal, Year, Vol(Issue): Pages.
   - 必须提取卷号和期号，如 27(11): 22-30。
   - 除了结尾的"."外，"."、","、":"等英文的标点符号后面都加空格，全部都是半角输入。
   - 作者规则: 3位以内全部列出；超过3位，仅列出前3位，后加 ", et al." (英文) 或 ", 等." (中文)，绝对不能截断中间的作者。
   - 文献类型标识：普通图书 [M] 期刊文章 [J] 论文集 [C] 学位论文 [D] 报告 [R] 标准 [S] 电子资源 [EB/OL]
   - 作者署名：中文作者：姓氏全拼+名字首字母（如：张华 → Zhang H），3人以内全部列出，超过3人则前3人+等或et al.。外文作者：姓氏全大写+名字首字母（如：SMITH J），3人以内全部列出，超过3人则前3人+等或et al.。
   - 严禁在结尾添加 "URL: https://..."，除非该文章是纯网络首发且没有页码。如果有 DOI，仅在 APA/MLA 中展示，国标通常省略 DOI 除非特定要求。
2. **APA7**:
   - 格式：Author, A. (Year). Title. *Journal, Vol*(Issue), Pages. (期刊名和卷号用 Markdown 斜体)
   - **作者规则**: **列出多达 20 位作者**。只有人数超过20个的时候才能在最后写 "et al." ，但绝对不能截断中间的作者。
   - **作者格式**: Author, A., & Author, B. (Year). ... (注意最后一位作者前用 "&")。
3. **MLA9**:
   - 格式：Author, A. "Title." *Journal*, vol. V, no. I, Year, pp. P. (期刊名斜体)
   - **作者规则**: **3位或以上作者，仅列出第一位作者，后加 ", et al."**。
   - **作者格式**: Author, A., et al. "Title." ...
   - 2位作者则写: Author, A., and B. Author.
4. **IEEE**:
   - 格式：[1] J. K. Author, "Title of paper," *Abbrev. Title of Journal*, vol. x, no. x, pp. xxx-xxx, Abbrev. Month, Year.
   - 注意：作者名字首字母在前；文章名加双引号；期刊名斜体。
   - **作者规则**: 列出所有作者。如果作者人数极多(>6)，可列第一位 + "et al."，绝对不能截断中间的作者。
   - 作者格式: [1] J. K. Author, "Title," ... (名缩写在前，姓在后)。
5. **Chicago (Bibliography)**:
   - 格式：Author, First. "Title of Article." *Journal Title* Volume, no. Issue (Year): Pages.
   - **作者规则**: 参考书目(Bibliography)中，列出多达 10 位作者；超过 10 位列出前 7 位 + "et al."。
   
【特殊数据处理】:
如果输入元数据中的作者列表已经被截断（例如包含 "..." 或 "Horizontal ellipsis"），且无法获取完整名单：
- GB/T 和 MLA: 请确保符合上述 "et al." 规则。
- APA 和 IEEE: 列出所有已知作者，并在末尾保留 "et al." 以示严谨，不要生造名字。

【输出要求】:
1. 严禁输出用户未选择的格式。
2. 如果原始数据缺失卷期号，尽力从 BibTeX 链接或其他格式中推断，若无则留空。
3. 请直接输出结果，不要包含任何如“好的”、“为您生成”等闲聊废话。使用 Markdown 的 `### 格式名` 作为小标题。
"""
        response = client.chat.completions.create(
            model=current_model, 
            messages=[
                {"role": "system", "content": "You are a professional academic citation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        # 将新结果加入到历史记录中 (插入在最前面)
        history.insert(0, {
            "title": real_title,
            "styles": selected_styles,
            "content": result
        })
        
        return result, history, format_history(history)

    except Exception as e:
        return f"❌ 运行过程中发生错误: {str(e)}", history, format_history(history)