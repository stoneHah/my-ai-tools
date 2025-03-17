"""
Coze工作流使用示例
演示如何使用Coze工作流API
"""
import os
import json
import asyncio
from typing import Optional
import sseclient
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# API地址
API_BASE_URL = "http://localhost:8000"
# 从环境变量获取工作流ID
DEFAULT_WORKFLOW_ID = os.getenv("COZE_DEFAULT_WORKFLOW_ID", "")


def run_workflow(message: str, workflow_id: Optional[str] = None):
    """
    运行工作流（非流式）
    
    Args:
        message: 输入消息
        workflow_id: 工作流ID，如果不提供则使用环境变量中的默认值
    
    Returns:
        工作流运行结果
    """
    workflow_id = workflow_id or DEFAULT_WORKFLOW_ID
    if not workflow_id:
        raise ValueError("未提供workflow_id，请指定或设置COZE_DEFAULT_WORKFLOW_ID环境变量")
    
    url = f"{API_BASE_URL}/ai/workflow/coze_workflow/run"
    data = {
        "message": message,
        "stream": False,
        "parameters": {
            "workflow_id": workflow_id
        }
    }
    
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()


def stream_workflow(message: str, workflow_id: Optional[str] = None):
    """
    流式运行工作流
    
    Args:
        message: 输入消息
        workflow_id: 工作流ID，如果不提供则使用环境变量中的默认值
    
    Returns:
        完整输出结果
    """
    workflow_id = workflow_id or DEFAULT_WORKFLOW_ID
    if not workflow_id:
        raise ValueError("未提供workflow_id，请指定或设置COZE_DEFAULT_WORKFLOW_ID环境变量")
    
    url = f"{API_BASE_URL}/ai/workflow/coze_workflow/stream"
    data = {
        "message": message,
        "stream": True,
        "parameters": {
            "workflow_id": workflow_id
        }
    }
    
    response = requests.post(url, json=data, stream=True)
    response.raise_for_status()
    
    # 使用SSE客户端处理事件流
    client = sseclient.SSEClient(response)
    
    full_content = ""
    for event in client.events():
        if event.data == "[DONE]":
            break
        
        try:
            data = json.loads(event.data)
            if "delta" in data:
                full_content += data["delta"]
                print(data["delta"], end="", flush=True)
        except json.JSONDecodeError:
            print(f"无法解析JSON: {event.data}")
    
    print()  # 换行
    return full_content


def interactive_demo():
    """交互式工作流演示"""
    print("=== Coze工作流交互式演示 ===")
    print("工作流ID:", DEFAULT_WORKFLOW_ID or "未设置")
    
    if not DEFAULT_WORKFLOW_ID:
        workflow_id = input("请输入工作流ID: ")
    else:
        workflow_id = DEFAULT_WORKFLOW_ID
        
    if not workflow_id:
        print("未提供工作流ID，退出演示")
        return
    
    print("\n开始与工作流交互（输入'exit'退出）")
    
    conversation_id = None
    
    while True:
        user_input = input("\n输入: ")
        if user_input.lower() == "exit":
            break
        
        print("输出: ", end="")
        try:
            data = {
                "message": user_input,
                "parameters": {
                    "workflow_id": workflow_id
                }
            }
            
            if conversation_id:
                data["conversation_id"] = conversation_id
            
            url = f"{API_BASE_URL}/ai/workflow/coze_workflow/stream"
            response = requests.post(url, json=data, stream=True)
            response.raise_for_status()
            
            # 处理流式响应
            client = sseclient.SSEClient(response)
            for event in client.events():
                if event.data == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(event.data)
                    if "delta" in chunk:
                        print(chunk["delta"], end="", flush=True)
                    
                    if not conversation_id and "conversation_id" in chunk:
                        conversation_id = chunk["conversation_id"]
                except:
                    pass
            
            print()  # 换行
            
        except Exception as e:
            print(f"出错: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Coze工作流示例")
    parser.add_argument("--interactive", "-i", action="store_true", help="启动交互式演示")
    parser.add_argument("--message", "-m", help="工作流输入消息")
    parser.add_argument("--workflow-id", "-w", help="工作流ID")
    parser.add_argument("--stream", "-s", action="store_true", help="使用流式响应")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_demo()
    elif args.message:
        try:
            if args.stream:
                result = stream_workflow(args.message, args.workflow_id)
            else:
                result = run_workflow(args.message, args.workflow_id)
                print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"出错: {e}")
    else:
        parser.print_help()
