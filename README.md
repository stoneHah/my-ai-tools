# AI中台服务

这是一个基于FastAPI的AI中台服务，它提供统一的API接口访问各种AI服务，包括Coze、OpenAI等，支持流式响应。

## 功能特点

- 模块化、可扩展的架构设计
- 统一的API接口访问各种AI服务
- 插件式设计，易于集成新的AI服务提供商
- 支持流式和非流式响应模式
- 使用FastAPI构建高性能API接口

## 已支持的AI服务

- **Coze**: 支持Coze智能体的对话功能
- **Coze工作流**: 支持Coze工作流的访问
- 更多服务即将支持...

## 安装

1. 克隆此仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 复制配置文件并设置你的API令牌：`cp .env.example .env`
4. 编辑`.env`文件，填入你的API令牌

## 使用方法

### 启动API服务

```bash
python run_api.py
```

服务将在 http://localhost:8000 上运行，你可以访问 http://localhost:8000/docs 查看API文档。

### API端点

#### 1. 获取可用服务列表

```
GET /ai/services
```

可选查询参数：
- `service_type`: 服务类型过滤，如"chat"、"image"等

#### 2. 非流式聊天

```
POST /ai/chat
```

请求体示例：

```json
{
  "service_type": "chat",
  "service_name": "coze",
  "messages": [
    {"role": "user", "content": "你好，请介绍一下自己"}
  ],
  "parameters": {
    "bot_id": "your_bot_id_here"
  },
  "stream": false
}
```

#### 3. 流式聊天

```
POST /ai/chat/stream
```

请求体示例：

```json
{
  "service_type": "chat",
  "service_name": "coze",
  "messages": [
    {"role": "user", "content": "你好，请介绍一下自己"}
  ],
  "parameters": {
    "bot_id": "your_bot_id_here"
  },
  "stream": true
}
```

#### 4. 非流式工作流

```
POST /ai/workflow
```

请求体示例：

```json
{
  "service_type": "workflow",
  "service_name": "coze_workflow",
  "parameters": {
    "workflow_id": "your_workflow_id_here"
  },
  "stream": false
}
```

#### 5. 流式工作流

```
POST /ai/workflow/stream
```

请求体示例：

```json
{
  "service_type": "workflow",
  "service_name": "coze_workflow",
  "parameters": {
    "workflow_id": "your_workflow_id_here"
  },
  "stream": true
}
```

### 客户端示例

项目提供了Python客户端示例，位于`examples/ai_platform_client.py`。

```python
from examples.ai_platform_client import AIPlatformClient

# 创建客户端
client = AIPlatformClient()

# 获取可用服务列表
services = client.list_services()
print("可用服务列表:", services)

# 非流式聊天
response = client.chat(
    service_name="coze",
    messages=[{"role": "user", "content": "你好"}],
    parameters={"bot_id": "your_bot_id_here"}
)
print("响应:", response)

# 流式聊天
def handle_chunk(data, chunk_text, full_text):
    print(f"收到新块: {chunk_text}")

full_response = client.stream_chat(
    service_name="coze",
    messages=[{"role": "user", "content": "你好"}],
    parameters={"bot_id": "your_bot_id_here"},
    callback=handle_chunk
)
print("完整响应:", full_response)

# 非流式工作流
response = client.workflow(
    service_name="coze_workflow",
    parameters={"workflow_id": "your_workflow_id_here"}
)
print("响应:", response)

# 流式工作流
def handle_chunk(data, chunk_text, full_text):
    print(f"收到新块: {chunk_text}")

full_response = client.stream_workflow(
    service_name="coze_workflow",
    parameters={"workflow_id": "your_workflow_id_here"},
    callback=handle_chunk
)
print("完整响应:", full_response)
```

## 架构设计

### 核心组件

1. **AI服务抽象接口** (`ai_services/base.py`)
   - 定义所有AI服务必须实现的接口
   - 提供服务注册和发现机制

2. **服务实现** (`ai_services/*.py`)
   - 各种AI服务的具体实现
   - 实现抽象接口定义的方法

3. **API层** (`api/*.py`)
   - 提供统一的RESTful API接口
   - 处理请求路由和响应格式化

### 扩展新服务

要添加新的AI服务，只需：

1. 创建一个新的服务实现类，继承`AIServiceBase`
2. 实现必要的方法
3. 在服务启动时注册该服务

示例：

```python
from ai_services.base import AIServiceBase, AIServiceRegistry

class MyNewService(AIServiceBase):
    @property
    def service_name(self) -> str:
        return "my_service"
    
    @property
    def service_type(self) -> str:
        return "chat"
    
    async def chat_completion(self, messages, **kwargs):
        # 实现聊天功能
        pass
    
    async def stream_chat_completion(self, messages, **kwargs):
        # 实现流式聊天功能
        pass

# 注册服务
AIServiceRegistry.register(MyNewService())
```

## 环境变量

本项目使用以下环境变量：

- `COZE_API_TOKEN`: Coze API访问令牌
- `COZE_API_BASE`: Coze API基础URL（可选）
- `COZE_DEFAULT_BOT_ID`: 默认使用的Coze Bot ID（可选）
- `COZE_DEFAULT_WORKFLOW_ID`: 默认使用的Coze工作流ID（可选）

## 依赖

- FastAPI
- Uvicorn
- Pydantic
- Coze-py (Coze Python SDK)
- python-dotenv
