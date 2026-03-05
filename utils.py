def format_history(history_list):
    """
    将历史记录列表格式化为 Markdown 字符串，供前端展示。
    """
    if not history_list:
        return "*暂无历史记录*"
    
    md_lines =[]
    for i, item in enumerate(history_list):
        md_lines.append(f"### 🕒 历史记录 {i+1}: {item['title']}")
        md_lines.append(f"**目标格式**: {', '.join(item['styles'])}")
        md_lines.append(item['content'])
        md_lines.append("---")
    return "\n\n".join(md_lines)