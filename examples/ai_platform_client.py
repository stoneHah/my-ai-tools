"""
AI中台服务客户端示例
演示如何使用AI中台服务的API
"""
import os
import json
import asyncio
import argparse
from typing import Dict, List, Any, Optional, AsyncGenerator
from urllib.parse import urljoin

import requests
import sseclient

# API基础URL
DEFAULT_API_BASE = "http://localhost:8000"


class AIPlatformClient:
    """AI中台服务客户端"""
    
    def __init__(self, api_base: str = DEFAULT_API_BASE):
        """
        初始化客户端
        
        Args:
            api_base: API基础URL，默认为http://localhost:8000
        """
        self.api_base = api_base
    
    def list_services(self) -> Dict[str, List[str]]:
        """
        列出所有可用的AI服务
        
        Returns:
            按类型分组的服务列表
        """
        url = urljoin(self.api_base, "/ai/services")
        response = requests.get(url)
        response.raise_for_status()
        return response.json()["services"]
    
    def chat(self, 
           service_name: str, 
           message: str,
           conversation_id: Optional[str] = None,
           **parameters) -> Dict[str, Any]:
        """
        与指定AI服务进行对话（非流式）
        
        Args:
            service_name: 服务名称，如coze
            message: 用户消息
            conversation_id: 会话ID，如果提供则在现有会话中发送消息
            **parameters: 额外参数，如bot_id等
            
        Returns:
            对话响应
        """
        url = urljoin(self.api_base, f"/ai/{service_name}/chat")
        data = {
            "message": message,
            "conversation_id": conversation_id,
            "stream": False,
            "parameters": parameters
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def stream_chat(self, 
                  service_name: str, 
                  message: str,
                  conversation_id: Optional[str] = None,
                  **parameters) -> AsyncGenerator[Dict[str, Any], None]:
        """
        与指定AI服务进行对话（流式）
        
        Args:
            service_name: 服务名称，如coze
            message: 用户消息
            conversation_id: 会话ID，如果提供则在现有会话中发送消息
            **parameters: 额外参数，如bot_id等
            
        Yields:
            流式对话响应的每个部分
        """
        url = urljoin(self.api_base, f"/ai/{service_name}/chat/stream")
        data = {
            "message": message,
            "conversation_id": conversation_id,
            "stream": True,
            "parameters": parameters
        }
        
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data == "[DONE]":
                break
            
            yield json.loads(event.data)
    
    def run_workflow(self, 
                   service_name: str, 
                   message: str,
                   conversation_id: Optional[str] = None,
                   **parameters) -> Dict[str, Any]:
        """
        运行指定工作流服务（非流式）
        
        Args:
            service_name: 服务名称，如coze_workflow
            message: 工作流输入
            conversation_id: 会话ID，如果提供则在现有会话中发送消息
            **parameters: 额外参数，如workflow_id等
            
        Returns:
            工作流运行结果
        """
        url = urljoin(self.api_base, f"/ai/workflow/{service_name}/run")
        data = {
            "message": message,
            "conversation_id": conversation_id,
            "stream": False,
            "parameters": parameters
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def stream_workflow(self, 
                      service_name: str, 
                      message: str,
                      conversation_id: Optional[str] = None,
                      **parameters) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行指定工作流服务
        
        Args:
            service_name: 服务名称，如coze_workflow
            message: 工作流输入
            conversation_id: 会话ID，如果提供则在现有会话中发送消息
            **parameters: 额外参数，如workflow_id等
            
        Yields:
            流式工作流运行结果的每个部分
        """
        url = urljoin(self.api_base, f"/ai/workflow/{service_name}/stream")
        data = {
            "message": message,
            "conversation_id": conversation_id,
            "stream": True,
            "parameters": parameters
        }
        
        response = requests.post(url, json=data, stream=True)
        response.raise_for_status()
        
        client = sseclient.SSEClient(response)
        for event in client.events():
            if event.data == "[DONE]":
                break
            
            yield json.loads(event.data)


async def interactive_chat_demo(service_name: str, bot_id: Optional[str] = None):
    """
    交互式聊天演示
    
    Args:
        service_name: 服务名称
        bot_id: 机器人ID（可选）
    """
    client = AIPlatformClient()
    conversation_id = None
    
    print(f"开始与{service_name}服务的对话（输入'exit'退出）")
    
    while True:
        user_message = input("你: ")
        if user_message.lower() == "exit":
            break
        
        params = {}
        if bot_id:
            params["bot_id"] = bot_id
        
        # 使用流式接口获取回复
        print("AI: ", end="", flush=True)
        full_response = ""
        
        # 以生成器方式处理流式回复
        try:
            for chunk in client.stream_chat(
                service_name=service_name,
                message=user_message,
                conversation_id=conversation_id,
                **params
            ):
                # 提取增量内容并打印
                if "delta" in chunk:
                    print(chunk["delta"], end="", flush=True)
                    full_response += chunk["delta"]
                
                # 更新会话ID
                if not conversation_id and "conversation_id" in chunk:
                    conversation_id = chunk["conversation_id"]
            
            print()  # 输出换行
        except Exception as e:
            print(f"\n对话出错: {e}")


async def interactive_workflow_demo(service_name: str, workflow_id: Optional[str] = None):
    """
    交互式工作流演示
    
    Args:
        service_name: 服务名称
        workflow_id: 工作流ID（可选）
    """
    client = AIPlatformClient()
    conversation_id = None
    
    print(f"开始与{service_name}工作流服务的交互（输入'exit'退出）")
    
    while True:
        user_message = input("输入: ")
        if user_message.lower() == "exit":
            break
        
        params = {}
        if workflow_id:
            params["workflow_id"] = workflow_id
        
        # 使用流式接口获取回复
        print("输出: ", end="", flush=True)
        full_response = ""
        
        # 以生成器方式处理流式回复
        try:
            for chunk in client.stream_workflow(
                service_name=service_name,
                message=user_message,
                conversation_id=conversation_id,
                **params
            ):
                # 提取增量内容并打印
                if "delta" in chunk:
                    print(chunk["delta"], end="", flush=True)
                    full_response += chunk["delta"]
                
                # 更新会话ID
                if not conversation_id and "conversation_id" in chunk:
                    conversation_id = chunk["conversation_id"]
            
            print()  # 输出换行
        except Exception as e:
            print(f"\n工作流运行出错: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI中台服务客户端示例")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 列出服务命令
    list_parser = subparsers.add_parser("list", help="列出可用的服务")
    
    # 聊天命令
    chat_parser = subparsers.add_parser("chat", help="与AI服务进行对话")
    chat_parser.add_argument("--service", "-s", default="coze", help="服务名称，默认为coze")
    chat_parser.add_argument("--bot-id", "-b", help="机器人ID（可选）")
    
    # 工作流命令
    workflow_parser = subparsers.add_parser("workflow", help="运行工作流")
    workflow_parser.add_argument("--service", "-s", default="coze_workflow", help="工作流服务名称，默认为coze_workflow")
    workflow_parser.add_argument("--workflow-id", "-w", help="工作流ID（可选）")
    
    args = parser.parse_args()
    
    # 根据命令执行相应操作
    if args.command == "list":
        client = AIPlatformClient()
        services = client.list_services()
        print("可用的AI服务:")
        for service_type, service_names in services.items():
            print(f"- {service_type}:")
            for name in service_names:
                print(f"  - {name}")
    
    elif args.command == "chat":
        asyncio.run(interactive_chat_demo(
            service_name=args.service,
            bot_id=args.bot_id
        ))
    
    elif args.command == "workflow":
        asyncio.run(interactive_workflow_demo(
            service_name=args.service,
            workflow_id=args.workflow_id
        ))
    
    else:
        parser.print_help()
