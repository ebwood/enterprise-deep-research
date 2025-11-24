#!/usr/bin/env python3
"""
演示如何获取和保存研究报告的示例脚本
"""
import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

BASE_URL = "http://localhost:8000"

def save_report_to_file(report_content, query, output_dir="reports"):
    """保存报告到文件"""
    # 创建输出目录
    Path(output_dir).mkdir(exist_ok=True)
    
    # 生成文件名（使用时间戳和查询的前20个字符）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c for c in query[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_query = safe_query.replace(' ', '_')
    
    # 保存为 Markdown
    md_filename = f"{output_dir}/report_{timestamp}_{safe_query}.md"
    with open(md_filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"✅ Markdown 报告已保存: {md_filename}")
    
    # 保存为 HTML（如果内容是 HTML）
    if '<div' in report_content or '<h1' in report_content:
        html_filename = f"{output_dir}/report_{timestamp}_{safe_query}.html"
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Research Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
{report_content}
</body>
</html>"""
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ HTML 报告已保存: {html_filename}")
    
    # 保存为 JSON（包含元数据）
    json_filename = f"{output_dir}/report_{timestamp}_{safe_query}.json"
    json_data = {
        "query": query,
        "timestamp": timestamp,
        "report_content": report_content,
        "content_length": len(report_content),
        "content_type": "html" if '<div' in report_content else "markdown"
    }
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON 报告已保存: {json_filename}")
    
    return md_filename, json_filename

def get_research_report(query, provider="openai", model="gpt-4o-mini", save_to_file=True):
    """获取研究报告并保存"""
    print("=" * 80)
    print("获取研究报告")
    print("=" * 80)
    print(f"查询: {query}")
    print(f"Provider: {provider}, Model: {model}")
    print()
    
    # 1. 启动研究任务
    payload = {
        "query": query,
        "streaming": True,
        "minimum_effort": False,
        "provider": provider,
        "model": model
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/deep-research",
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 启动研究任务失败: {response.status_code}")
            return None
        
        data = response.json()
        stream_id = data.get("stream_url", "").replace("/stream/", "")
        
        if not stream_id:
            print("❌ 无法获取 stream_id")
            return None
        
        print(f"✅ 研究任务已启动，Stream ID: {stream_id}")
        print("等待研究完成...")
        print()
        
        # 2. 连接流式端点，等待报告
        stream_url = f"{BASE_URL}/stream/{stream_id}"
        report_content = None
        
        response = requests.get(
            stream_url,
            stream=True,
            headers={"Accept": "text/event-stream"},
            timeout=600  # 最多等待10分钟
        )
        
        if response.status_code != 200:
            print(f"❌ 连接流式端点失败: {response.status_code}")
            return None
        
        print("✅ 已连接，接收数据中...")
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                if line_str.startswith("data:"):
                    data_str = line_str[5:].strip()
                    try:
                        event_data = json.loads(data_str)
                        event_type = event_data.get("event_type", "")
                        
                        if event_type == "research_complete":
                            report_data = event_data.get("data", {})
                            report_content = report_data.get("report", "")
                            
                            if report_content:
                                print(f"\n✅ 研究报告已接收!")
                                print(f"报告长度: {len(report_content)} 字符")
                                print()
                                
                                # 保存到文件
                                if save_to_file:
                                    md_file, json_file = save_report_to_file(
                                        report_content, query
                                    )
                                    print(f"\n📁 报告已保存到:")
                                    print(f"   - {md_file}")
                                    print(f"   - {json_file}")
                                
                                # 显示报告预览
                                print("\n" + "=" * 80)
                                print("报告预览（前500字符）:")
                                print("=" * 80)
                                print(report_content[:500])
                                if len(report_content) > 500:
                                    print("...")
                                print("=" * 80)
                                
                                return report_content
                            else:
                                print("⚠️ 研究报告为空")
                                return None
                                
                    except json.JSONDecodeError:
                        continue
        
        print("⚠️ 未收到研究报告")
        return None
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("研究报告获取和保存示例")
    print("=" * 80)
    print()
    print("研究报告存储位置说明:")
    print("1. 流式响应中: 通过 SSE 事件发送，存储在 research_complete 事件的 data.report 字段")
    print("2. 前端内存中: 存储在 React 组件的 state 中")
    print("3. 前端可下载: 通过 FinalReport 组件可以下载为 PDF、HTML、DOCX")
    print("4. 后端不持久化: 研究报告不会自动保存到文件系统")
    print()
    print("=" * 80)
    print()
    
    # 示例：获取研究报告
    query = "What are the latest developments in renewable energy technologies?"
    report = get_research_report(
        query,
        provider="openai",
        model="gpt-4o-mini",
        save_to_file=True
    )
    
    if report:
        print("\n✅ 成功获取研究报告!")
    else:
        print("\n❌ 未能获取研究报告")
