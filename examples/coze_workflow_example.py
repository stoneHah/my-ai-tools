"""
Coze工作流使用示例
演示如何通过AI中台服务调用Coze工作流
"""
import json
import asyncio
import sseclient
import requests
from typing import Dict, Any, Optional

class WorkflowClient:
    """Coze工作流客户端"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        """
        初始化客户端
        
        Args:
            api_url: API服务的URL
        """
        self.api_url = api_url
    
    def run_workflow(self, 
                   workflow_id: str, 
                   input_text: str) -> Dict[str, Any]:
        """
        运行工作流（非流式）
        
        Args:
            workflow_id: 工作流ID
            input_text: 输入文本
            
        Returns:
            工作流运行结果
        """
        url = f"{self.api_url}/ai/chat"
        response = requests.post(
            url,
            json={
                "service_type": "workflow",
                "service_name": "coze_workflow",
                "messages": [
                    {"role": "user", "content": input_text}
                ],
                "parameters": {
                    "workflow_id": workflow_id
                },
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()
    
    def stream_workflow(self, 
                      workflow_id: str, 
                      input_text: str, 
                      callback=None) -> str:
        """
        流式运行工作流
        
        Args:
            workflow_id: 工作流ID
            input_text: 输入文本
            callback: 处理每个响应块的回调函数
            
        Returns:
            完整响应文本
        """
        url = f"{self.api_url}/ai/chat/stream"
        response = requests.post(
            url,
            json={
                "service_type": "workflow",
                "service_name": "coze_workflow",
                "messages": [
                    {"role": "user", "content": input_text}
                ],
                "parameters": {
                    "workflow_id": workflow_id
                },
                "stream": True
            },
            stream=True
        )
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

# 使用示例
async def main():
    client = WorkflowClient()
    workflow_id = "your_workflow_id_here"  # 替换为你的Coze工作流ID
    
    # 非流式示例
    print("=== 非流式工作流运行示例 ===")
    try:
        response = client.run_workflow(
            workflow_id=workflow_id,
            input_text="请帮我总结下今天的天气情况"
        )
        print("响应:", json.dumps(response, indent=2, ensure_ascii=False))
        
        # 提取输出
        output = ""
        for choice in response.get("choices", []):
            message = choice.get("message", {})
            output += message.get("content", "")
        
        print("\n工作流输出:", output)
    except Exception as e:
        print(f"非流式工作流运行失败: {e}")
    
    # 流式示例
    print("\n=== 流式工作流运行示例 ===")
    
    def print_chunk(data, chunk_text, full_text):
        """处理每个接收到的数据块"""
        print(f"接收到新块: {chunk_text}")
    
    try:
        full_response = client.stream_workflow(
            workflow_id=workflow_id,
            input_text="请帮我生成一个旅行计划",
            callback=print_chunk
        )
        print("\n完整响应:", full_response)
    except Exception as e:
        print(f"流式工作流运行失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
