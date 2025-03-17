"""
API模型定义模块
包含请求和响应的数据模型
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Message(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色，如system、user、assistant")
    content: str = Field(..., description="消息内容")
    
class ChatRequest(BaseModel):
    """通用聊天请求模型"""
    service_type: str = Field("chat", description="服务类型")
    service_name: str = Field(..., description="服务名称，如coze、openai等")
    messages: List[Dict[str, Any]] = Field(..., description="消息列表")
    stream: bool = Field(True, description="是否使用流式响应")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="服务特定的参数，如bot_id等")
    
class ChatResponse(BaseModel):
    """聊天响应模型（非流式）"""
    id: str
    choices: List[Dict[str, Any]]
    created: int
    
class StreamChatResponse(BaseModel):
    """流式聊天响应的每个块"""
    id: str
    choices: List[Dict[str, Any]]
    created: int

class ServiceInfo(BaseModel):
    """服务信息模型"""
    service_type: str
    service_name: str
    
class ServicesListResponse(BaseModel):
    """服务列表响应模型"""
    services: Dict[str, List[str]] = Field(..., description="按类型分组的服务列表")
