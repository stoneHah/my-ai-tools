"""
火山引擎视频生成服务单元测试
使用模拟对象进行测试
"""
import os
import uuid
import asyncio
from unittest.mock import patch, MagicMock

import pytest
from dotenv import load_dotenv

from ai_services.video.volcengine_video import VolcengineVideoService

# 加载环境变量
load_dotenv()


@pytest.fixture
def mock_ark_client():
    """模拟Ark客户端"""
    mock_client = MagicMock()
    mock_client.content_generation = MagicMock()
    mock_client.content_generation.tasks = MagicMock()
    
    # 模拟创建任务
    mock_create_result = MagicMock()
    mock_create_result.id = "mock-task-id-123"
    mock_client.content_generation.tasks.create = MagicMock(return_value=mock_create_result)
    
    # 模拟获取任务结果
    mock_get_result = MagicMock()
    mock_get_result.status = "succeeded"
    mock_get_result.outputs = [
        {
            "type": "video",
            "video": {
                "url": "https://example.com/test-video.mp4"
            }
        }
    ]
    mock_client.content_generation.tasks.get = MagicMock(return_value=mock_get_result)
    
    return mock_client


@pytest.fixture
def mock_task_service():
    """模拟任务服务"""
    mock_service = MagicMock()
    mock_service.create_task = MagicMock(return_value="mock-db-task-id")
    mock_service.update_task = MagicMock()
    mock_service.get_task = MagicMock()
    
    return mock_service


@pytest.mark.asyncio
async def test_create_image_to_video_task(mock_ark_client, mock_task_service):
    """测试创建图生视频任务"""
    with patch('ai_services.video.volcengine_video.Ark', return_value=mock_ark_client):
        service = VolcengineVideoService(api_key="mock-api-key", task_service=mock_task_service)
        
        # 创建任务
        task_dict = await service.create_image_to_video_task(
            prompt="测试提示词",
            image_url="https://example.com/test.jpg",
            ratio="16:9",
            duration=5
        )
        
        # 验证任务创建成功
        assert task_dict is not None
        assert "task_id" in task_dict
        assert "volcengine_task_id" in task_dict
        assert task_dict["volcengine_task_id"] == "mock-task-id-123"
        assert task_dict["status"] == "pending"
        
        # 验证调用了Ark客户端的create方法
        mock_ark_client.content_generation.tasks.create.assert_called_once()
        
        # 验证调用了任务服务的create_task方法
        mock_task_service.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_get_video_task_result(mock_ark_client, mock_task_service):
    """测试获取视频生成任务结果"""
    # 设置模拟任务
    mock_task = MagicMock()
    mock_task.task_specific_data = {"volcengine_task_id": "mock-task-id-123"}
    mock_task_service.get_task.return_value = mock_task
    
    with patch('ai_services.video.volcengine_video.Ark', return_value=mock_ark_client):
        service = VolcengineVideoService(api_key="mock-api-key", task_service=mock_task_service)
        
        # 获取任务结果
        result = await service.get_video_task_result(task_id="mock-db-task-id")
        
        # 验证任务结果
        assert result is not None
        assert "task_id" in result
        assert result["task_id"] == "mock-db-task-id"
        assert "status" in result
        assert result["status"] == "completed"
        assert "videos" in result
        assert len(result["videos"]) == 1
        assert result["videos"][0] == "https://example.com/test-video.mp4"
        
        # 验证调用了Ark客户端的get方法
        mock_ark_client.content_generation.tasks.get.assert_called_once_with(task_id="mock-task-id-123")
        
        # 验证调用了任务服务的update_task方法
        mock_task_service.update_task.assert_called_once()


@pytest.mark.asyncio
async def test_get_video_task_result_failed(mock_ark_client, mock_task_service):
    """测试获取失败的视频生成任务结果"""
    # 设置模拟任务
    mock_task = MagicMock()
    mock_task.task_specific_data = {"volcengine_task_id": "mock-task-id-123"}
    mock_task_service.get_task.return_value = mock_task
    
    # 设置模拟失败结果
    mock_get_result = MagicMock()
    mock_get_result.status = "failed"
    mock_get_result.failure_reason = "测试失败原因"
    mock_get_result.outputs = None
    mock_ark_client.content_generation.tasks.get = MagicMock(return_value=mock_get_result)
    
    with patch('ai_services.video.volcengine_video.Ark', return_value=mock_ark_client):
        service = VolcengineVideoService(api_key="mock-api-key", task_service=mock_task_service)
        
        # 获取任务结果
        result = await service.get_video_task_result(task_id="mock-db-task-id")
        
        # 验证任务结果
        assert result is not None
        assert "task_id" in result
        assert result["task_id"] == "mock-db-task-id"
        assert "status" in result
        assert result["status"] == "failed"
        assert "error" in result
        assert result["error"] == "测试失败原因"
        
        # 验证调用了任务服务的update_task方法，更新为失败状态
        mock_task_service.update_task.assert_called_once_with(
            task_id="mock-db-task-id",
            status="failed",
            error_message="测试失败原因"
        )
