"""
测试 CozeWorkflowService 的 run_workflow 方法
"""
import os
import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
sys.path.append(str(Path(__file__).parent.parent))

# 现在可以正确导入模块
from ai_services.coze_workflow import CozeWorkflowService

# 加载环境变量
load_dotenv()

async def test_run_workflow():
    """测试运行工作流"""
    # 从环境变量获取配置
    api_token = os.getenv("COZE_API_TOKEN")
    api_base = os.getenv("COZE_API_BASE")
    workflow_id = "7484855620220125223"
    
    if not api_token or not workflow_id:
        print("请确保设置了 COZE_API_TOKEN 和 COZE_DEFAULT_WORKFLOW_ID 环境变量")
        return
    
    # 创建服务实例
    service = CozeWorkflowService(
        api_token=api_token,
        api_base=api_base,
        workflow_id=workflow_id
    )
    
    # 准备输入参数
    input_params = {
        "input": "3.87 J@I.iP 09/17 rRk:/ 是真爱还是骗婚？藏在老实人皮囊下的爱情...细思极恐！ # 一剪到底 # 影视解说 # 电影推荐 # 一口气看完系列 # 我的观影报告  https://v.douyin.com/pzu9j2wCt5A/ 复制此链接，打开Dou音搜索，直接观看视频！"
    }
    
    try:
        # 调用工作流
        print(f"正在运行工作流 {workflow_id}...")
        result = await service.run_workflow(
            workflow_id=workflow_id,
            input_params=input_params
        )
        
        # 打印结果
        print(f"\n工作流运行结果: {type(result).__name__}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"运行工作流时出错: {e}")

async def test_stream_workflow():
    """测试流式运行工作流"""
    # 从环境变量获取配置
    api_token = os.getenv("COZE_API_TOKEN")
    api_base = os.getenv("COZE_API_BASE")
    workflow_id = os.getenv("COZE_DEFAULT_WORKFLOW_ID")
    
    if not api_token or not workflow_id:
        print("请确保设置了 COZE_API_TOKEN 和 COZE_DEFAULT_WORKFLOW_ID 环境变量")
        return
    
    # 创建服务实例
    service = CozeWorkflowService(
        api_token=api_token,
        api_base=api_base,
        workflow_id=workflow_id
    )
    
    # 准备输入参数
    input_params = {
        "input": "请详细介绍一下Python的异步编程"
    }
    
    try:
        # 调用流式工作流
        print(f"正在流式运行工作流 {workflow_id}...")
        full_content = ""
        
        async for chunk in service.stream_workflow(
            workflow_id=workflow_id,
            input_params=input_params
        ):
            if "delta" in chunk:
                print(chunk["delta"], end="", flush=True)
                full_content += chunk["delta"]
        
        print("\n\n流式工作流完成")
        
    except Exception as e:
        print(f"流式运行工作流时出错: {e}")

if __name__ == "__main__":
    # 运行测试
    print("=== 测试 CozeWorkflowService ===")
    
    # 选择要运行的测试
    test_type = input("选择测试类型 (1: 普通运行, 2: 流式运行, 3: 全部): ")
    
    if test_type == "1":
        asyncio.run(test_run_workflow())
    elif test_type == "2":
        asyncio.run(test_stream_workflow())
    elif test_type == "3":
        asyncio.run(test_run_workflow())
        print("\n" + "-" * 50 + "\n")
        asyncio.run(test_stream_workflow())
    else:
        print("无效的选择")