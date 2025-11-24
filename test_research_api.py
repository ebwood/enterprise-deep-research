#!/usr/bin/env python3
"""
使用 API 调用研究服务的测试脚本
"""
import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"


def start_research(query, provider="openrouter", model="openai/gpt-4o-mini", minimum_effort=False):
    """启动研究任务"""
    print("=" * 80)
    print("启动研究任务")
    print("=" * 80)
    print(f"查询: {query}")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print(f"Minimum Effort: {minimum_effort}")
    print()

    payload = {
        "query": query,
        "streaming": True,
        "minimum_effort": minimum_effort,
        "provider": provider,
        "model": model
    }

    try:
        print("发送请求到 /deep-research...")
        response = requests.post(
            f"{BASE_URL}/deep-research",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"状态码: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ 请求失败!")
            print(f"响应: {response.text}")
            return None

        data = response.json()
        stream_url = data.get("stream_url", "")

        if not stream_url:
            print("❌ 响应中没有 stream_url")
            print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return None

        stream_id = stream_url.replace("/stream/", "")
        print(f"✅ 研究任务已启动")
        print(f"Stream URL: {stream_url}")
        print(f"Stream ID: {stream_id}")
        print()

        return stream_id

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def receive_stream(stream_id, max_wait_time=600):
    """接收流式数据"""
    print("=" * 80)
    print(f"连接流式端点: /stream/{stream_id}")
    print("=" * 80)

    stream_url = f"{BASE_URL}/stream/{stream_id}"

    try:
        print(f"连接到: {stream_url}")
        print("等待流式数据...")
        print("-" * 80)

        response = requests.get(
            stream_url,
            stream=True,
            headers={
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache"
            },
            timeout=max_wait_time
        )

        if response.status_code == 404:
            print(f"❌ 404 错误: Stream {stream_id} 不存在或已过期")
            return False

        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False

        print("✅ 连接成功，开始接收数据...\n")

        # 存储所有事件
        events = []
        event_count = 0
        last_heartbeat = time.time()
        research_complete = False

        # 用于存储关键信息
        activities = []
        errors = []
        final_report = None

        try:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    event_count += 1

                    # 解析 SSE 格式
                    if line_str.startswith("event:"):
                        event_type = line_str[6:].strip()
                    elif line_str.startswith("data:"):
                        data_str = line_str[5:].strip()
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("event_type", "unknown")

                            # 存储事件
                            events.append({
                                "type": event_type,
                                "data": data,
                                "timestamp": datetime.now().isoformat()
                            })

                            # 处理不同类型的事件
                            if event_type == "connected":
                                print(f"✅ [{event_count}] 连接成功")
                                print(
                                    f"   Stream ID: {data.get('data', {}).get('stream_id')}")

                            elif event_type == "activity_generated":
                                activity_data = data.get("data", {})
                                activity = activity_data.get("activity")
                                node_name = activity_data.get(
                                    "node_name", "unknown")

                                if activity:
                                    activities.append(activity)
                                    print(f"📝 [{event_count}] 活动: {node_name}")
                                    print(f"   {activity[:100]}..." if len(
                                        activity) > 100 else f"   {activity}")

                            elif event_type == "node_start":
                                node_data = data.get("data", {})
                                node_name = node_data.get(
                                    "node_name", "unknown")
                                print(f"🔄 [{event_count}] 节点开始: {node_name}")

                            elif event_type == "node_end":
                                node_data = data.get("data", {})
                                node_name = node_data.get(
                                    "node_name", "unknown")
                                print(f"✅ [{event_count}] 节点完成: {node_name}")

                            elif event_type == "token_stream":
                                # 流式输出token，不打印太多
                                if event_count % 50 == 0:
                                    print(f"💬 [{event_count}] 接收token流...")

                            elif event_type == "research_complete":
                                research_complete = True
                                complete_data = data.get("data", {})
                                print(f"\n🎉 [{event_count}] 研究完成!")

                                if "report" in complete_data:
                                    final_report = complete_data["report"]
                                    print(f"\n📄 最终报告预览:")
                                    print("-" * 80)
                                    print(
                                        final_report[:500] + "..." if len(final_report) > 500 else final_report)
                                    print("-" * 80)

                            elif event_type == "error":
                                error_data = data.get("data", {})
                                error_msg = error_data.get(
                                    "message", "Unknown error")
                                errors.append(error_msg)
                                print(f"\n❌ [{event_count}] 错误: {error_msg}")

                            elif event_type == "heartbeat":
                                last_heartbeat = time.time()
                                # 不打印心跳，避免输出太多

                            elif event_type == "end":
                                print(f"\n🏁 [{event_count}] 流结束")
                                break

                        except json.JSONDecodeError:
                            print(f"[{event_count}] 非JSON数据: {data_str[:100]}")

                    # 检查超时
                    if time.time() - last_heartbeat > 60 and not research_complete:
                        print(f"\n⚠️ 超过60秒没有收到数据，可能连接已断开")
                        break

                    # 如果研究完成，等待一下然后退出
                    if research_complete and event_count > 0:
                        # 再等待几秒看看有没有更多数据
                        time.sleep(2)
                        break

            print("\n" + "=" * 80)
            print("流式数据接收完成")
            print("=" * 80)
            print(f"总共收到 {event_count} 个事件")
            print(f"活动数量: {len(activities)}")
            print(f"错误数量: {len(errors)}")

            if errors:
                print("\n❌ 错误列表:")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")

            if final_report:
                print(f"\n📄 最终报告长度: {len(final_report)} 字符")

            return True

        except requests.exceptions.ChunkedEncodingError:
            print(f"\n⚠️ 流式数据接收中断（已接收 {event_count} 个事件）")
            return False

    except requests.exceptions.Timeout:
        print(f"\n❌ 请求超时（{max_wait_time}秒）")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    query = "What are the latest developments in renewable energy technologies?"
    # 使用 OpenAI 而不是 OpenRouter（因为 OPENROUTER_API_KEY 未设置）
    provider = "openai"
    model = "gpt-4o-mini"  # OpenAI 的模型名称格式不同

    print("\n" + "=" * 80)
    print("Enterprise Deep Research API 测试")
    print("=" * 80)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"基础 URL: {BASE_URL}")
    print()

    # 1. 启动研究任务
    stream_id = start_research(query, provider, model, minimum_effort=False)

    if not stream_id:
        print("\n❌ 无法启动研究任务")
        sys.exit(1)

    # 2. 等待一下让任务初始化
    print("\n等待 3 秒让研究任务初始化...")
    time.sleep(3)

    # 3. 接收流式数据
    success = receive_stream(stream_id, max_wait_time=600)  # 最多等待10分钟

    if success:
        print("\n✅ 测试完成!")
    else:
        print("\n⚠️ 测试过程中出现问题")


if __name__ == "__main__":
    main()
