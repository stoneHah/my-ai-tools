"""
火山引擎视频生成服务集成测试
使用实际的火山引擎API环境进行测试
"""
import os
import uuid
import asyncio
import time
from pathlib import Path
import urllib.parse

import pytest
from dotenv import load_dotenv

from ai_services.video.volcengine_video import VolcengineVideoService
from db.service.task_service import TaskService
from db.config import get_db
from ai_services.storage.registry import register_all_storage_services

# 加载环境变量
load_dotenv()

# 注册所有存储服务
register_all_storage_services()

# 测试图片URL
TEST_IMAGE_URL = "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"

# 跳过标记
skip_if_no_api_key = pytest.mark.skipif(
    not os.environ.get("ARK_API_KEY"),
    reason="需要设置ARK_API_KEY环境变量"
)


@pytest.fixture
def video_service():
    """创建视频服务实例"""
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        pytest.skip("需要设置ARK_API_KEY环境变量")
    
    # 创建任务服务实例
    task_service = TaskService(next(get_db()))
    
    # 创建视频服务实例
    service = VolcengineVideoService(api_key=api_key, task_service=task_service)
    return service


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_create_image_to_video_task(video_service):
    """测试创建图生视频任务"""
    # 创建任务
    task_dict = await video_service.create_image_to_video_task(
        prompt="女孩抱着狐狸，女孩睁开眼，温柔地看向镜头",
        image_url=TEST_IMAGE_URL,
        ratio="16:9",
        duration=5
    )
    
    # 验证任务创建成功
    assert task_dict is not None
    assert "task_id" in task_dict
    assert task_dict["status"] == "pending"
    assert "created_at" in task_dict
    assert task_dict["prompt"] == "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头"
    assert task_dict["image_url"] == TEST_IMAGE_URL
    assert task_dict["ratio"] == "16:9"
    assert task_dict["duration"] == 5
    
    # 返回任务ID，用于后续测试
    return task_dict["task_id"]


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_get_video_task_result(video_service):
    """测试获取视频生成任务结果"""
    # 先创建任务
    # task_id = await test_create_image_to_video_task(video_service)
    task_id = "f8983585-85bb-4a3f-a4c5-558968fbb5fa"
    
    # 获取任务结果
    result = await video_service.get_video_task_result(task_id=task_id)
    
    # 验证任务结果
    assert result is not None
    assert "task_id" in result
    assert result["task_id"] == task_id
    assert "status" in result
    
    # 由于任务可能需要时间处理，这里只验证基本结构
    # 任务状态可能是pending、running、completed、failed
    assert result["status"] in ["pending", "running", "completed", "failed"]


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_wait_for_video_task_completion(video_service):
    """测试等待视频生成任务完成"""
    # 先创建任务
    task_id = await test_create_image_to_video_task(video_service)
    
    # 等待任务完成，最多等待5分钟
    max_wait_time = 300  # 5分钟
    wait_interval = 10   # 每10秒检查一次
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        # 获取任务结果
        result = await video_service.get_video_task_result(task_id=task_id)
        
        # 如果任务已完成或失败，退出循环
        if result["status"] in ["completed", "failed"]:
            break
        
        # 等待一段时间后再次检查
        await asyncio.sleep(wait_interval)
    
    # 验证任务已处理（完成或失败）
    assert result["status"] in ["completed", "failed"]
    
    # 如果任务完成，验证视频URL
    if result["status"] == "completed":
        assert "videos" in result
        assert len(result["videos"]) > 0
        assert result["videos"][0].startswith("http")
    # 如果任务失败，验证错误信息
    elif result["status"] == "failed":
        assert "error" in result
        assert result["error"] is not None


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_create_image_to_video_task_without_task_service():
    """测试不使用任务服务创建图生视频任务"""
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        pytest.skip("需要设置ARK_API_KEY环境变量")
    
    # 创建不带任务服务的视频服务实例
    service = VolcengineVideoService(api_key=api_key, task_service=None)
    
    # 创建任务
    task_dict = await service.create_image_to_video_task(
        prompt="女孩抱着狐狸，特写镜头",
        image_url=TEST_IMAGE_URL,
        ratio="1:1",
        duration=3
    )
    
    # 验证任务创建成功
    assert task_dict is not None
    assert "task_id" in task_dict
    assert task_dict["status"] == "pending"
    
    # 获取任务结果
    result = await service.get_video_task_result(task_id=task_dict["task_id"])
    
    # 验证任务结果
    assert result is not None
    assert "task_id" in result
    assert result["task_id"] == task_dict["task_id"]
    assert "status" in result
