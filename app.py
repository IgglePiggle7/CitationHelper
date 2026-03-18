import gradio as gr
# import os
# os.environ["HTTP_PROXY"] = ""
# os.environ["HTTPS_PROXY"] = ""
# os.environ["no_proxy"] = "localhost,127.0.0.1"

from services.citation import generate_citation
from services.document import process_reorder

theme = gr.themes.Soft(
    primary_hue="indigo",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
)

with gr.Blocks(theme=theme, title="Academic Citation Assistant | 学术文献助手") as demo:
    # 状态存储 (每个用户的浏览器会话独立)
    history_state = gr.State([])

    gr.HTML("""
    <div style="text-align: center; max-width: 800px; margin: 0 auto; padding: 20px 0;">
        <h1 style="font-weight: 700; font-size: 2rem; margin-bottom: 0.5rem;">
            🎓 Academic Citation Assistant <br> 
            <span style="font-size: 1.5rem; color: #4f46e5;">多功能学术文献引用助手</span>
        </h1>
        <p style="color: #64748b; font-size: 1rem;">
            Standard Literature Citation Generation | Word Document Reference Auto-Reordering<br>
            标准文献引用一键生成 | Word 引用序号自动乱序重排
        </p>
    </div>
    """)
    
    with gr.Tabs():
        # 标签页 1：文献引用生成器 / Citation Generator
        with gr.TabItem("🔍 1. Citation Generator / 引用生成器"):
            gr.Markdown("Enter a paper title to generate multiple standard citation formats. / 输入论文标题，工具将生成您需要的多种标准文献引用格式")
            
            with gr.Row():
                with gr.Column(scale=1):
                    # 使用 Group 将输入区包裹为卡片样式
                    with gr.Group():
                        paper_input = gr.Textbox(
                            label="Paper Title / 输入文献标题", 
                            placeholder="e.g., Attention is all you need"
                        )
                        style_choices = gr.CheckboxGroup(
                            choices=["GB/T 7714-2015", "APA7", "MLA9", "IEEE", "Chicago", "BibTeX"],
                            value=["GB/T 7714-2015", "APA7"], 
                            label="Target Formats / 选择目标格式 (Multiple / 可多选)"
                        )
                        gen_btn = gr.Button("🚀 Generate Citation / 联网生成引用", variant="primary")
                    
                with gr.Column(scale=1):
                    with gr.Group():
                        gen_output = gr.Markdown(
                            label="Current Result / 本次生成结果", 
                            value="*Waiting for input... / 输入文献标题后在此查看生成结果...*"
                        )
                    
                    # 历史记录展示区
                    with gr.Accordion("📚 Browsing History / 历史浏览记录 (Session Only / 仅本次会话有效)", open=False):
                        history_output = gr.Markdown(value="*No history yet / 暂无历史记录*")
                        clear_history_btn = gr.Button("🗑️ Clear History / 清空历史记录", size="sm")
            
            # 绑定生成按钮事件
            gen_btn.click(
                fn=generate_citation, 
                inputs=[paper_input, style_choices, history_state], 
                outputs=[gen_output, history_state, history_output]
            )
            
            # 绑定清空历史事件
            clear_history_btn.click(
                fn=lambda: ([], "*No history yet / 暂无历史记录*"),
                inputs=None,
                outputs=[history_state, history_output]
            )

        # 标签页 2：Word 乱序重排 / Word Citation Reorder
        with gr.TabItem("📝 2. Word Citation Reorder / Word 乱序重排"):
            gr.Markdown("Upload a Word document with disordered citation marks and your raw reference list. The tool will auto-renumber them based on the text order. / 将带有乱序标记的 Word 文档和原始参考文献列表上传，工具会自动根据正文顺序重新编号。")
            
            with gr.Row():
                with gr.Column():
                    with gr.Group():
                        file_in = gr.File(
                            label="Upload Word Document / 上传 Word 文档 (.docx)", 
                            file_types=[".docx"]
                        )
                        text_in = gr.Textbox(
                            label="Paste Disordered References / 粘贴乱序的参考文献列表", 
                            lines=10, 
                            placeholder="[1] Original first paper / 原第一篇...\n[2] Original second paper / 原第二篇..."
                        )
                        reorder_btn = gr.Button("⚙️ Reorder & Download / 开始重排并下载文档", variant="primary")
                    
                with gr.Column():
                    with gr.Group():
                        file_out = gr.File(label="📥 Download Updated Doc / 下载修改好的 Word 文档")
                        text_out = gr.Textbox(
                            label="📋 Preview New References / 预览新参考文献列表", 
                            lines=14, 
                            interactive=False
                        )

            # 绑定重排按钮事件
            reorder_btn.click(
                fn=process_reorder, 
                inputs=[file_in, text_in], 
                outputs=[file_out, text_out]
            )

if __name__ == "__main__":
    demo.launch()