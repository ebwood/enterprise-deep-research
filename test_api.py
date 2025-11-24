#!/usr/bin/env python3
"""
测试 API 调用的脚本，用于诊断问题
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"


def test_root():
    """测试根端点"""
    print("=" * 60)
    print("1. 测试根端点 /")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(
            f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")

        # 尝试解析 JSON，如果不是 JSON 就显示文本
        try:
            data = response.json()
            print(
                f"响应 (JSON): {json.dumps(data, indent=2, ensure_ascii=False)}")
        except:
            print(f"响应 (文本): {response.text[:500]}")

        return response.status_code == 200
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_start_research():
    """测试启动研究任务（流式）"""
    print("\n" + "=" * 60)
    print("2. 测试启动研究任务 /deep-research (流式)")
    print("=" * 60)

    payload = {
        "query": "什么是人工智能？",
        "streaming": True,
        "minimum_effort": True,  # 使用最小努力，快速测试
        "provider": "openrouter",
        "model": "openai/gpt-4o-mini"
    }

    try:
        print(f"发送请求到: {BASE_URL}/deep-research")
        print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        response = requests.post(
            f"{BASE_URL}/deep-research",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"\n状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

            if "stream_url" in result:
                stream_url = result["stream_url"]
                print(f"\n✅ 研究任务已启动!")
                print(f"流式 URL: {stream_url}")
                return stream_url
            else:
                print("\n⚠️ 响应中没有 stream_url")
                return None
        else:
            print(f"\n❌ 请求失败!")
            print(f"响应内容: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print("\n❌ 请求超时")
        return None
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_stream(stream_url):
    """测试流式端点"""
    if not stream_url:
        print("\n跳过流式测试（没有 stream_url）")
        return

    print("\n" + "=" * 60)
    print("3. 测试流式端点")
    print("=" * 60)

    # 从 stream_url 中提取 stream_id
    # stream_url 格式: /stream/{stream_id}
    stream_id = stream_url.split("/")[-1]
    full_url = f"{BASE_URL}{stream_url}"

    print(f"流式 URL: {full_url}")
    print(f"Stream ID: {stream_id}")

    try:
        print("\n开始接收流式数据...")
        print("-" * 60)

        response = requests.get(
            full_url,
            stream=True,
            headers={"Accept": "text/event-stream"},
            timeout=30
        )

        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")

        if response.status_code == 404:
            print(f"\n❌ 404 错误!")
            print(f"响应内容: {response.text}")
            print(f"\n可能的原因:")
            print("1. Stream ID 不存在或已过期")
            print("2. 路由配置问题（catch-all 路由拦截了 /stream/ 路径）")
            print("3. 研究任务没有成功创建队列")
            return

        if response.status_code != 200:
            print(f"\n❌ 请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return

        # 读取流式数据
        event_count = 0
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                event_count += 1

                if event_count <= 10:  # 只显示前10个事件
                    print(f"事件 {event_count}: {line_str[:200]}")
                elif event_count == 11:
                    print("... (更多事件)")

                # 检查是否是结束信号
                if "research_complete" in line_str or "end" in line_str.lower():
                    print(f"\n✅ 收到完成信号")
                    break

        print(f"\n总共收到 {event_count} 个事件")

    except requests.exceptions.Timeout:
        print("\n❌ 流式请求超时")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def test_docs():
    """测试 API 文档"""
    print("\n" + "=" * 60)
    print("4. 测试 API 文档端点 /docs")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ API 文档可访问")
        else:
            print(f"⚠️ API 文档返回状态码: {response.status_code}")
    except Exception as e:
        print(f"错误: {e}")


def main():
    print("🚀 开始测试 Enterprise Deep Research API")
    print(f"基础 URL: {BASE_URL}\n")

    # 1. 测试根端点
    if not test_root():
        print("\n❌ 根端点测试失败，服务可能未运行")
        sys.exit(1)

    # 2. 测试 API 文档
    test_docs()

    # 3. 测试启动研究任务
    stream_url = test_start_research()

    # 4. 等待一下，让任务有时间创建队列
    if stream_url:
        print("\n等待 2 秒，让研究任务初始化...")
        time.sleep(2)

        # 5. 测试流式端点
        test_stream(stream_url)

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
