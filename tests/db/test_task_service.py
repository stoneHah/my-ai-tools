"""
测试任务服务层
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
from sqlalchemy.orm import Session

from db.service.task_service import TaskService
from db.models.task import Task


class TestTaskService(unittest.TestCase):
    """测试任务服务"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟数据库会话
        self.mock_db = Mock(spec=Session)
        
        # 创建任务服务实例
        self.task_service = TaskService(self.mock_db)
        
        # 创建模拟任务对象
        self.mock_task = Mock(spec=Task)
        self.mock_task.task_id = "test-task-id"
        self.mock_task.service_type = "test-service-type"
        self.mock_task.service_name = "test-service-name"
        self.mock_task.status = "pending"
        self.mock_task.parameters = {"param": "value"}
        self.mock_task.result = None
        self.mock_task.error_message = None
        self.mock_task.task_specific_data = {"specific": "data"}
        self.mock_task.created_at = datetime.now()
        self.mock_task.completed_at = None
    
    def test_refresh_session(self):
        """测试刷新数据库会话"""
        # 调用刷新会话方法
        self.task_service.refresh_session()
        
        # 验证是否调用了expire_all方法
        self.mock_db.expire_all.assert_called_once()
    
    @patch('db.dao.task_dao.TaskDAO.get_task_by_id')
    def test_get_task_with_refresh(self, mock_get_task_by_id):
        """测试获取任务并刷新会话"""
        # 设置模拟返回值
        mock_get_task_by_id.return_value = self.mock_task
        
        # 调用get_task方法，启用刷新
        task = self.task_service.get_task("test-task-id", refresh=True)
        
        # 验证是否调用了expire_all方法
        self.mock_db.expire_all.assert_called_once()
        
        # 验证是否调用了refresh方法
        self.mock_db.refresh.assert_called_once_with(self.mock_task)
        
        # 验证返回的任务是否正确
        self.assertEqual(task, self.mock_task)
    
    @patch('db.dao.task_dao.TaskDAO.get_task_by_id')
    def test_get_task_without_refresh(self, mock_get_task_by_id):
        """测试获取任务但不刷新会话"""
        # 设置模拟返回值
        mock_get_task_by_id.return_value = self.mock_task
        
        # 调用get_task方法，禁用刷新
        task = self.task_service.get_task("test-task-id", refresh=False)
        
        # 验证没有调用expire_all方法
        self.mock_db.expire_all.assert_not_called()
        
        # 验证没有调用refresh方法
        self.mock_db.refresh.assert_not_called()
        
        # 验证返回的任务是否正确
        self.assertEqual(task, self.mock_task)
    
    @patch('db.dao.task_dao.TaskDAO.list_tasks')
    def test_list_tasks_with_refresh(self, mock_list_tasks):
        """测试列出任务并刷新会话"""
        # 设置模拟返回值
        mock_list_tasks.return_value = [self.mock_task]
        
        # 调用list_tasks方法，启用刷新
        tasks = self.task_service.list_tasks(
            service_type="test-service-type",
            status="pending",
            refresh=True
        )
        
        # 验证是否调用了expire_all方法
        self.mock_db.expire_all.assert_called_once()
        
        # 验证返回的任务列表是否正确
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], self.mock_task)
    
    @patch('db.dao.task_dao.TaskDAO.list_tasks')
    def test_list_tasks_without_refresh(self, mock_list_tasks):
        """测试列出任务但不刷新会话"""
        # 设置模拟返回值
        mock_list_tasks.return_value = [self.mock_task]
        
        # 调用list_tasks方法，禁用刷新
        tasks = self.task_service.list_tasks(
            service_type="test-service-type",
            status="pending",
            refresh=False
        )
        
        # 验证没有调用expire_all方法
        self.mock_db.expire_all.assert_not_called()
        
        # 验证返回的任务列表是否正确
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], self.mock_task)
    
    def test_simulate_cache_issue(self):
        """模拟缓存问题场景"""
        # 创建模拟任务
        original_task = Mock(spec=Task)
        original_task.task_id = "test-task-id"
        original_task.status = "pending"
        
        updated_task = Mock(spec=Task)
        updated_task.task_id = "test-task-id"
        updated_task.status = "completed"
        
        # 模拟TaskDAO.get_task_by_id方法
        # 第一次调用返回pending状态的任务
        # 第二次调用返回completed状态的任务
        with patch('db.dao.task_dao.TaskDAO.get_task_by_id', side_effect=[original_task, updated_task]):
            # 第一次获取任务，不刷新
            task1 = self.task_service.get_task("test-task-id", refresh=False)
            self.assertEqual(task1.status, "pending")
            
            # 第二次获取任务，启用刷新
            task2 = self.task_service.get_task("test-task-id", refresh=True)
            self.assertEqual(task2.status, "completed")
            
            # 验证刷新方法被调用
            self.mock_db.expire_all.assert_called_once()
            self.mock_db.refresh.assert_called_once_with(updated_task)
    
    @patch('db.dao.task_dao.TaskDAO.get_task_by_id')
    @patch('db.dao.task_dao.TaskDAO.update_task')
    def test_query_update_query_with_refresh(self, mock_update_task, mock_get_task_by_id):
        """测试先查询任务，然后修改任务状态，再次查询任务（启用刷新）"""
        # 创建初始任务和更新后的任务
        initial_task = Mock(spec=Task)
        initial_task.task_id = "test-task-id"
        initial_task.status = "pending"
        initial_task.result = None
        
        updated_task = Mock(spec=Task)
        updated_task.task_id = "test-task-id"
        updated_task.status = "completed"
        updated_task.result = {"output": "test result"}
        
        # 设置模拟返回值
        mock_get_task_by_id.side_effect = [initial_task, updated_task]
        mock_update_task.return_value = updated_task
        
        # 第一次查询任务
        task1 = self.task_service.get_task("test-task-id", refresh=True)
        self.assertEqual(task1.status, "pending")
        self.assertIsNone(task1.result)
        
        # 更新任务状态
        updated = self.task_service.update_task(
            task_id="test-task-id",
            status="completed",
            result={"output": "test result"}
        )
        self.assertEqual(updated.status, "completed")
        
        # 重置模拟对象的调用记录
        self.mock_db.expire_all.reset_mock()
        self.mock_db.refresh.reset_mock()
        
        # 第二次查询任务，启用刷新
        task2 = self.task_service.get_task("test-task-id", refresh=True)
        
        # 验证任务状态已更新
        self.assertEqual(task2.status, "completed")
        self.assertEqual(task2.result, {"output": "test result"})
        
        # 验证刷新方法被调用
        self.mock_db.expire_all.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(updated_task)
    
    @patch('db.dao.task_dao.TaskDAO.get_task_by_id')
    @patch('db.dao.task_dao.TaskDAO.update_task')
    def test_query_update_query_without_refresh(self, mock_update_task, mock_get_task_by_id):
        """测试先查询任务，然后修改任务状态，再次查询任务（不启用刷新）"""
        # 创建初始任务和更新后的任务
        initial_task = Mock(spec=Task)
        initial_task.task_id = "test-task-id"
        initial_task.status = "pending"
        initial_task.result = None
        
        # 注意：即使不刷新，第二次查询也会返回更新后的任务
        # 这是因为模拟对象的行为，而不是真实的SQLAlchemy缓存行为
        # 在真实场景中，不刷新可能会返回缓存的旧数据
        updated_task = Mock(spec=Task)
        updated_task.task_id = "test-task-id"
        updated_task.status = "completed"
        updated_task.result = {"output": "test result"}
        
        # 设置模拟返回值
        mock_get_task_by_id.side_effect = [initial_task, updated_task]
        mock_update_task.return_value = updated_task
        
        # 第一次查询任务
        task1 = self.task_service.get_task("test-task-id", refresh=False)
        self.assertEqual(task1.status, "pending")
        self.assertIsNone(task1.result)
        
        # 更新任务状态
        updated = self.task_service.update_task(
            task_id="test-task-id",
            status="completed",
            result={"output": "test result"}
        )
        self.assertEqual(updated.status, "completed")
        
        # 重置模拟对象的调用记录
        self.mock_db.expire_all.reset_mock()
        self.mock_db.refresh.reset_mock()
        
        # 第二次查询任务，不启用刷新
        task2 = self.task_service.get_task("test-task-id", refresh=False)
        
        # 验证任务状态
        # 注意：在模拟测试中，即使不刷新也会返回更新后的任务
        # 这与真实的SQLAlchemy缓存行为不同
        self.assertEqual(task2.status, "completed")
        
        # 验证没有调用刷新方法
        self.mock_db.expire_all.assert_not_called()
        self.mock_db.refresh.assert_not_called()


if __name__ == '__main__':
    unittest.main()
