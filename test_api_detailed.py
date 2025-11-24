#!/usr/bin/env python3
"""
详细的 API 测试脚本，模拟前端调用方式
"""
import requests
import json
import time
import sys
from urllib.parse import urljoin

BASE_URL = "http://localhost:8000"


def test_stream_detailed(stream_id):
    """详细测试流式端点，模拟前端 EventSource 的行为"""
    print("=" * 80)
    print(f"详细测试流式端点: /stream/{stream_id}")
    print("=" * 80)

    # 模拟前端构建 URL 的方式
    # 前端代码: const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`;
    # 如果 API_BASE_URL 为空，url 是 "/stream/xxx"，则 fullUrl = "/stream/xxx"

    stream_url = f"/stream/{stream_id}"
    full_url = urljoin(BASE_URL, stream_url)

    print(f"Stream ID: {stream_id}")
    print(f"Stream URL (相对路径): {stream_url}")
    print(f"Full URL (完整路径): {full_url}")
    print()

    try:
        print("发送 GET 请求...")
        print(f"URL: {full_url}")
        print(f"Headers: Accept: text/event-stream")
        print()

        response = requests.get(
            full_url,
            stream=True,
            headers={
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            },
            timeout=30
        )

        print(f"✅ 请求已发送")
        print(f"状态码: {response.status_code}")
        print(f"响应头:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        print()

        if response.status_code == 404:
            print("❌ 404 错误!")
            print(f"响应内容: {response.text}")
            print()
            print("可能的原因:")
            print("1. Stream ID 不存在或已过期")
            print("2. 路由配置问题")
            print("3. Catch-all 路由拦截了请求")
            print("4. 研究任务没有成功创建队列")
            return False

        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

        print("✅ 连接成功，开始接收流式数据...")
        print("-" * 80)

        event_count = 0
        event_types = {}

        try:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    event_count += 1

                    # 解析 SSE 格式
                    if line_str.startswith("event:"):
                        event_type = line_str[6:].strip()
                        event_types[event_type] = event_types.get(
                            event_type, 0) + 1
                        print(f"[事件 {event_count}] 类型: {event_type}")
                    elif line_str.startswith("data:"):
                        data_str = line_str[5:].strip()
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("event_type", "unknown")
                            print(f"[事件 {event_count}] 数据: {event_type}")

                            # 显示关键信息
                            if event_type == "connected":
                                print(
                                    f"  ✅ 连接成功，Stream ID: {data.get('data', {}).get('stream_id')}")
                            elif event_type == "research_complete":
                                print(f"  ✅ 研究完成")
                                break
                            elif event_type == "error":
                                print(
                                    f"  ❌ 错误: {data.get('data', {}).get('message', 'Unknown error')}")
                        except json.JSONDecodeError:
                            print(
                                f"[事件 {event_count}] 数据 (非 JSON): {data_str[:100]}")

                    # 限制输出，避免太多
                    if event_count <= 20:
                        if event_count % 5 == 0:
                            print(f"  ... 已接收 {event_count} 个事件")
                    elif event_count == 21:
                        print("  ... (更多事件，已省略详细输出)")

                    # 检查完成信号
                    if "research_complete" in line_str or '"event_type":"end"' in line_str:
                        print(f"\n✅ 收到完成信号")
                        break

            print("-" * 80)
            print(f"\n✅ 流式数据接收完成")
            print(f"总共收到 {event_count} 个事件")
            print(f"\n事件类型统计:")
            for event_type, count in sorted(event_types.items()):
                print(f"  {event_type}: {count}")

            return True

        except requests.exceptions.ChunkedEncodingError as e:
            print(f"\n⚠️ 流式数据接收中断: {e}")
            print(f"已接收 {event_count} 个事件")
            return False

    except requests.exceptions.Timeout:
        print("\n❌ 请求超时（30秒）")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        print("请检查:")
        print("1. 服务是否在运行")
        print("2. 端口是否正确（默认 8000）")
        print("3. 防火墙设置")
        return False
    except Exception as e:
        print(f"\n❌ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("🔍 详细 API 测试工具")
    print(f"基础 URL: {BASE_URL}\n")

    # 如果提供了 stream_id 作为参数，直接测试
    if len(sys.argv) > 1:
        stream_id = sys.argv[1]
        test_stream_detailed(stream_id)
    else:
        # 否则先启动一个研究任务
        print("1. 启动研究任务...")
        payload = {
            "query": "什么是 Python？",
            "streaming": True,
            "minimum_effort": True,
            "provider": "openrouter",
            "model": "openai/gpt-4o-mini"
        }

        try:
            response = requests.post(
                f"{BASE_URL}/deep-research",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                stream_url = data.get("stream_url", "")
                if stream_url:
                    stream_id = stream_url.replace("/stream/", "")
                    print(f"✅ 研究任务已启动")
                    print(f"Stream ID: {stream_id}\n")

                    # 等待一下让任务初始化
                    print("等待 3 秒让任务初始化...")
                    time.sleep(3)

                    # 测试流式端点
                    test_stream_detailed(stream_id)
                else:
                    print("❌ 响应中没有 stream_url")
            else:
                print(f"❌ 启动研究任务失败，状态码: {response.status_code}")
                print(f"响应: {response.text}")
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n使用方法:")
    print("  python test_api_detailed.py              # 自动启动任务并测试")
    print("  python test_api_detailed.py <stream_id>  # 测试指定的 stream_id\n")
    main()
