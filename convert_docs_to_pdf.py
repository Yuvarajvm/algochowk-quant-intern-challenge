"""
convert_docs_to_pdf.py
Converts RESEARCH_NOTE.md and AI_USAGE_NOTE.md into professional PDF documents.
"""

import markdown
from xhtml2pdf import pisa

CSS_STYLE = """
<style>
    @page {
        size: a4 portrait;
        margin: 1.5cm;
    }
    body {
        font-family: Helvetica, Arial, sans-serif;
        font-size: 9.5pt;
        line-height: 1.35;
        color: #1e293b;
    }
    h1 {
        font-size: 16pt;
        color: #0f172a;
        margin-bottom: 2px;
        padding-bottom: 4px;
        border-bottom: 2px solid #2563eb;
    }
    h2 {
        font-size: 13pt;
        color: #1e3a8a;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    h3 {
        font-size: 11pt;
        color: #1e40af;
        margin-top: 8px;
        margin-bottom: 3px;
    }
    h4 {
        font-size: 10pt;
        color: #334155;
        margin-top: 6px;
        margin-bottom: 2px;
    }
    p {
        margin-top: 3px;
        margin-bottom: 4px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 6px;
        margin-bottom: 8px;
        font-size: 8.5pt;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 4px 6px;
        text-align: left;
    }
    th {
        background-color: #f1f5f9;
        color: #0f172a;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background-color: #f8fafc;
    }
    blockquote {
        margin: 4px 0;
        padding: 4px 10px;
        background-color: #f1f5f9;
        border-left: 3px solid #2563eb;
        font-style: italic;
    }
    ul, ol {
        margin-top: 2px;
        margin-bottom: 4px;
        padding-left: 18px;
    }
    li {
        margin-bottom: 2px;
    }
    code {
        font-family: Courier, monospace;
        font-size: 8.5pt;
        background-color: #f1f5f9;
        padding: 1px 3px;
    }
    hr {
        border: 0;
        height: 1px;
        background: #cbd5e1;
        margin: 6px 0;
    }
</style>
"""

def md_to_pdf(md_path, pdf_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    html_content = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
    full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'>{CSS_STYLE}</head><body>{html_content}</body></html>"
    
    with open(pdf_path, 'wb') as f:
        pisa_status = pisa.CreatePDF(full_html, dest=f)
    
    if pisa_status.err:
        print(f"Error creating {pdf_path}")
    else:
        print(f"Successfully generated {pdf_path}")

if __name__ == "__main__":
    md_to_pdf("RESEARCH_NOTE.md", "RESEARCH_NOTE.pdf")
    md_to_pdf("AI_USAGE_NOTE.md", "AI_USAGE_NOTE.pdf")
