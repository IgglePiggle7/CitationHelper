import gradio as gr
import docx
import re
import os

def process_citations(doc_file_path, ref_text):
    if not doc_file_path or not ref_text.strip():
        return None, "错误：请先上传 Word 文档并粘贴参考文献！"
        
    try:
        doc = docx.Document(doc_file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        doc_text_str = "\n".join(full_text)

        def expand_range(range_str):
            try:
                range_str = range_str.replace('–', '-')
                if '-' in range_str:
                    s, e = range_str.split('-')
                    return [str(i) for i in range(int(s), int(e) + 1)]
                return [range_str]
            except: return []

        def compress_range(nums):
            if not nums: return ""
            nums = sorted(list(set(nums)))
            ranges = []
            start = nums[0]
            prev = nums[0]
            for x in nums[1:]:
                if x == prev + 1:
                    prev = x
                else:
                    if start == prev: ranges.append(str(start))
                    else: ranges.append(f"{start}-{prev}")
                    start = x
                    prev = x
            if start == prev: ranges.append(str(start))
            else: ranges.append(f"{start}-{prev}")
            return ", ".join(ranges)

        matches = re.findall(r'\[([\d\s,，\-–]+)\]', doc_text_str)
        doc_order = []
        seen = set()

        for content in matches:
            parts = re.split(r'[,，]', content.replace(" ", ""))
            for part in parts:
                if not part: continue
                for pid in expand_range(part):
                    if pid.isdigit() and pid not in seen:
                        seen.add(pid)
                        doc_order.append(pid)

        ref_map = {}
        lines = ref_text.strip().split('\n')
        pattern = re.compile(r'^\s*(?:\[(\d+)\]|(\d+)\.)\s*(.*)')
        for line in lines:
            line = line.strip()
            match = pattern.match(line)
            if match:
                oid = match.group(1) or match.group(2)
                ref_map[oid] = match.group(3)

        mapping = {}    # 旧ID -> 新ID (int)
        new_ref_list = []
        current_idx = 1

        for old_id in doc_order:
            if old_id in ref_map:
                mapping[old_id] = current_idx
                new_ref_list.append(f"[{current_idx}] {ref_map[old_id]}")
                del ref_map[old_id]
                current_idx += 1

        for old_id, content in ref_map.items():
            mapping[old_id] = current_idx 
            new_ref_list.append(f"[{current_idx}] {content}")
            current_idx += 1

        def replace_callback(match):
            content = match.group(1)
            parts = re.split(r'[,，]', content)
            new_ids = []
            
            for part in parts:
                part = part.strip()
                expanded = expand_range(part)
                for old_id in expanded:
                    if old_id in mapping:
                        new_ids.append(mapping[old_id])
                    else:
                        if old_id.isdigit(): new_ids.append(int(old_id))
            
            return f"[{compress_range(new_ids)}]"

        for para in doc.paragraphs:
            if "[" in para.text:
                try:
                    new_text = re.sub(r'\[([\d\s,，\-–]+)\]', replace_callback, para.text)
                    if new_text != para.text:
                        para.text = new_text
                except Exception as e:
                    pass

        doc.add_paragraph("\n")
        heading = doc.add_paragraph("参考文献 (Auto Generated)")
        
        for ref in new_ref_list:
            doc.add_paragraph(ref)

        output_filename = "Fixed_Document.docx"
        doc.save(output_filename)
        
        return output_filename, "\n".join(new_ref_list)
        
    except Exception as e:
        return None, f"❌ 处理出错: {str(e)}"

# 网页界面 (Gradio)
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📄 Word 文献引用自动重排工具")
    gr.Markdown("上传您的 Word 文档和乱序的参考文献列表，工具将自动根据正文引用顺序重排序号，并生成可下载的新 Word 文档。")
    
    with gr.Row():
        # 左侧：输入区
        with gr.Column():
            file_in = gr.File(label="1. 上传 Word 文档 (.docx)", file_types=[".docx"])
            text_in = gr.Textbox(label="2. 粘贴参考文献列表 (乱序)", lines=12, placeholder="[1] Vaswani, A. ...\n[2] Devlin, J. ...")
            submit_btn = gr.Button("🚀 一键处理并下载", variant="primary")
            
        # 右侧：输出区
        with gr.Column():
            file_out = gr.File(label="📥 点击此处下载修改好的 Word")
            text_out = gr.Textbox(label="📋 预览新的参考文献列表", lines=15, interactive=False)

    # 绑定按钮点击事件
    submit_btn.click(
        fn=process_citations,
        inputs=[file_in, text_in],
        outputs=[file_out, text_out]
    )

# 启动应用
if __name__ == "__main__":
    demo.launch()