import gradio as gr

from services.citation import generate_citation
from services.document import process_reorder

theme = gr.themes.Soft(
    primary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
)

with gr.Blocks(title="多功能学术文献引用助手") as demo:
    # 状态存储 (每个用户的浏览器会话独立)
    history_state = gr.State([])
    
    gr.Markdown("<center><h1>🎓 多功能学术文献引用助手</h1></center>")
    gr.Markdown("<center>Google Scholar 抓取生成 | Word 引用序号自动重排</center>")
    
    with gr.Tabs():
        # 标签页 1：文献格式生成器
        with gr.TabItem("🔍 1. 引用格式生成器"):
            gr.Markdown("输入论文标题，自动从 Google Scholar 抓取最准确的数据并格式化为您需要的标准引用。")
            
            # 【核心改动】：防刷爆高级设置区
            with gr.Accordion("⚙️ API Key 自定义 (报错时请填入)", open=False):
                gr.Markdown("*说明：如果系统自带的免费搜索或大模型额度用尽导致报错，您可以在此处填入自己的 Key。*")
                with gr.Row():
                    user_serpapi_key = gr.Textbox(label="SerpApi Key (用于 Google Scholar)", placeholder="不填则使用系统内置免费池", type="password")
                    user_api_key = gr.Textbox(label="大模型 API Key", placeholder="sk-... (不填使用系统池)", type="password")
                with gr.Row():
                    user_base_url = gr.Textbox(label="大模型 Base URL", placeholder="如: https://api.deepseek.com/v1")
                    user_model = gr.Textbox(label="大模型名称", placeholder="如: deepseek-chat")
                    
            with gr.Row():
                with gr.Column(scale=1):
                    paper_input = gr.Textbox(label="输入文献标题", placeholder="例如：Attention is all you need")
                    style_choices = gr.CheckboxGroup(
                        choices=["GB/T 7714-2015", "APA7", "MLA9", "IEEE", "Chicago", "BibTeX"],
                        value=["GB/T 7714-2015", "APA7"], 
                        label="选择目标格式 (可多选)"
                    )
                    gen_btn = gr.Button("🚀 联网生成引用", variant="primary")
                    
                with gr.Column(scale=1):
                    gen_output = gr.Markdown(label="本次生成结果", value="*输入文献标题后在此查看生成结果...*")
                    
                    # 历史记录展示区
                    with gr.Accordion("📚 历史浏览记录 (仅本次网页会话有效)", open=False):
                        history_output = gr.Markdown(value="*暂无历史记录*")
                        clear_history_btn = gr.Button("🗑️ 清空历史记录", size="sm")
            
            # 绑定生成按钮事件
            gen_btn.click(
                fn=generate_citation, 
                inputs=[
                    paper_input, style_choices, 
                    user_serpapi_key, user_api_key, user_base_url, user_model, 
                    history_state
                ], 
                outputs=[gen_output, history_state, history_output]
            )
            
            # 绑定清空历史事件
            clear_history_btn.click(
                fn=lambda: ([], "*暂无历史记录*"),
                inputs=None,
                outputs=[history_state, history_output]
            )

        # 标签页 2：Word 乱序重排
        with gr.TabItem("📝 2. Word 引用乱序重排"):
            gr.Markdown("将带有乱序标记的 Word 文档和原始参考文献列表上传，工具会自动根据正文顺序重新编号。")
            with gr.Row():
                with gr.Column():
                    file_in = gr.File(label="上传 Word 文档 (.docx)", file_types=[".docx"])
                    text_in = gr.Textbox(label="粘贴乱序的参考文献列表", lines=10, placeholder="[1] 原第一篇...\n[2] 原第二篇...")
                    reorder_btn = gr.Button("⚙️ 开始重排并下载文档", variant="primary")
                    
                with gr.Column():
                    file_out = gr.File(label="📥 下载修改好的 Word 文档")
                    text_out = gr.Textbox(label="📋 预览新参考文献列表", lines=14, interactive=False)

            # 绑定重排按钮事件
            reorder_btn.click(fn=process_reorder, inputs=[file_in, text_in], outputs=[file_out, text_out])

if __name__ == "__main__":
    demo.launch(theme=theme)