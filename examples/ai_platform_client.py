"""
AI中台服务客户端示例
演示如何与AI中台服务交互
"""
import json
import asyncio
import sseclient
import requests
from typing import Dict, Any, Optional, Callable, List

class AIPlatformClient:
    """AI中台服务客户端"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        初始化客户端
        
        Args:
            api_url: API服务的URL
        """
        self.api_url = api_url
    
    def list_services(self) -> Dict[str, Any]:
        """
        获取可用服务列表
        
        Returns:
            服务列表响应
        """
        url = f"{self.api_url}/ai/services"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def chat(self, 
           service_name: str, 
           messages: List[Dict[str, str]], 
           parameters: Optional[Dict[str, Any]] = None, 
           service_type: str = "chat") -> Dict[str, Any]:
        """
        发送聊天请求（非流式）
        
        Args:
            service_name: 服务名称
            messages: 消息列表
            parameters: 额外参数
            service_type: 服务类型
            
        Returns:
            聊天完成响应
        """
        url = f"{self.api_url}/ai/chat"
        payload = {
            "service_name": service_name,
            "service_type": service_type,
            "messages": messages,
            "parameters": parameters or {},
            "stream": False
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def stream_chat(self, 
                  service_name: str, 
                  messages: List[Dict[str, str]], 
                  parameters: Optional[Dict[str, Any]] = None, 
                  service_type: str = "chat",
                  callback: Optional[Callable] = None) -> str:
        """
        发送流式聊天请求
        
        Args:
            service_name: 服务名称
            messages: 消息列表
            parameters: 额外参数
            service_type: 服务类型
            callback: 处理每个响应块的回调函数
            
        Returns:
            完整响应文本
        """
        url = f"{self.api_url}/ai/chat/stream"
        payload = {
            "service_name": service_name,
            "service_type": service_type,
            "messages": messages,
            "parameters": parameters or {},
            "stream": True
        }
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        # 使用SSE客户端处理事件流
        client = sseclient.SSEClient(response)
        
        full_text = ""
        for event in client.events():
            if event.data == "[DONE]":
                break
                
            try:
                data = json.loads(event.data)
                # 提取块中的文本
                chunk_text = ""
                for choice in data.get("choices", []):
                    delta = choice.get("delta", {})
                    chunk_text += delta.get("content", "")
                
                # 累积完整文本
                full_text += chunk_text
                
                # 如果提供了回调，执行回调
                if callback and callable(callback):
                    callback(data, chunk_text, full_text)
                    
            except json.JSONDecodeError:
                print(f"无法解析JSON: {event.data}")
                
        return full_text
    
    def workflow(self,
               service_name: str,
               parameters: Dict[str, Any],
               input_text: Optional[str] = None,
               service_type: str = "workflow") -> Dict[str, Any]:
        """
        运行工作流（非流式）
        
        Args:
            service_name: 服务名称
            parameters: 工作流参数，包括workflow_id
            input_text: 输入文本
            service_type: 服务类型
            
        Returns:
            工作流运行结果
        """
        messages = []
        if input_text:
            messages = [{"role": "user", "content": input_text}]
            
        return self.chat(
            service_name=service_name,
            messages=messages,
            parameters=parameters,
            service_type=service_type
        )
    
    def stream_workflow(self,
                      service_name: str,
                      parameters: Dict[str, Any],
                      input_text: Optional[str] = None,
                      service_type: str = "workflow",
                      callback: Optional[Callable] = None) -> str:
        """
        流式运行工作流
        
        Args:
            service_name: 服务名称
            parameters: 工作流参数，包括workflow_id
            input_text: 输入文本
            service_type: 服务类型
            callback: 处理每个响应块的回调函数
            
        Returns:
            完整响应文本
        """
        messages = []
        if input_text:
            messages = [{"role": "user", "content": input_text}]
            
        return self.stream_chat(
            service_name=service_name,
            messages=messages,
            parameters=parameters,
            service_type=service_type,
            callback=callback
        )

# 使用示例
async def main():
    client = AIPlatformClient()
    
    # 获取可用服务列表
    print("=== 可用服务列表 ===")
    try:
        services = client.list_services()
        print(json.dumps(services, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"获取服务列表失败: {e}")
    
    # 非流式聊天示例
    print("\n=== 非流式聊天示例 ===")
    try:
        response = client.chat(
            service_name="coze",
            messages=[
                {"role": "user", "content": "你好，请介绍一下自己"}
            ]
        )
        print("响应:", json.dumps(response, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"非流式聊天失败: {e}")
    
    # 流式聊天示例
    print("\n=== 流式聊天示例 ===")
    
    def print_chunk(data, chunk_text, full_text):
        """处理每个接收到的数据块"""
        print(f"接收到新块: {chunk_text}")
    
    try:
        full_response = client.stream_chat(
            service_name="coze",
            messages=[
                {"role": "user", "content": "请给我讲个故事，100字左右"}
            ],
            callback=print_chunk
        )
        print("\n完整响应:", full_response)
    except Exception as e:
        print(f"流式聊天失败: {e}")
    
    # 非流式工作流示例
    print("\n=== 非流式工作流示例 ===")
    try:
        workflow_id = "your_workflow_id_here"  # 替换为你的Coze工作流ID
        response = client.workflow(
            service_name="coze_workflow",
            parameters={"workflow_id": workflow_id},
            input_text="请帮我总结下今天的天气情况"
        )
        print("响应:", json.dumps(response, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"非流式工作流运行失败: {e}")
    
    # 流式工作流示例
    print("\n=== 流式工作流示例 ===")
    try:
        workflow_id = "your_workflow_id_here"  # 替换为你的Coze工作流ID
        full_response = client.stream_workflow(
            service_name="coze_workflow",
            parameters={"workflow_id": workflow_id},
            input_text="请帮我生成一个旅行计划",
            callback=print_chunk
        )
        print("\n完整响应:", full_response)
    except Exception as e:
        print(f"流式工作流运行失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
