"""
任务服务集成测试
"""
import unittest
import os
import json
from datetime import datetime
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models.task import Task
from db.service.task_service import TaskService
# 使用正确的Base对象
from db.models.base import Base
# 导入所有模型以确保它们被注册到Base中
import db.models.task  # 确保Task模型被注册


class TestTaskServiceIntegration(unittest.TestCase):
    """任务服务集成测试，直接与数据库交互"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化，创建内存数据库"""
        # 使用SQLite内存数据库
        cls.engine = create_engine('sqlite:///:memory:')
        cls.SessionLocal = sessionmaker(bind=cls.engine)
        
        # 创建表结构
        Base.metadata.create_all(cls.engine)
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(cls.engine)
        tables = inspector.get_table_names()
        print(f"创建的表: {tables}")
        if 'tasks' not in tables:
            raise Exception("tasks表未创建成功")
    
    def setUp(self):
        """每个测试前准备，创建会话和服务实例"""
        self.db = self.SessionLocal()
        self.task_service = TaskService(self.db)
        
        # 清空任务表
        try:
            self.db.query(Task).delete()
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"清空任务表失败: {str(e)}")
            raise
    
    def tearDown(self):
        """每个测试后清理，关闭会话"""
        self.db.close()
    
    def test_create_and_get_task(self):
        """测试创建和获取任务"""
        # 创建任务
        task = self.task_service.create_task(
            service_type="test",
            service_name="test-service",
            status="pending",
            parameters={"param": "value"},
            task_specific_data={"data": "value"}
        )
        
        # 验证任务创建成功
        self.assertIsNotNone(task)
        self.assertEqual(task.service_type, "test")
        self.assertEqual(task.status, "pending")
        
        # 获取任务
        retrieved_task = self.task_service.get_task(task.task_id)
        
        # 验证获取成功
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.task_id, task.task_id)
    
    def test_update_and_get_task_with_refresh(self):
        """测试更新任务后使用刷新获取最新状态"""
        # 创建任务
        task = self.task_service.create_task(
            service_type="test",
            service_name="test-service",
            status="pending"
        )
        
        # 获取任务ID
        task_id = task.task_id
        
        # 创建第二个会话和服务实例，模拟不同请求
        db2 = self.SessionLocal()
        task_service2 = TaskService(db2)
        
        # 使用第一个服务实例获取任务
        task1 = self.task_service.get_task(task_id)
        self.assertEqual(task1.status, "pending")
        
        # 使用第二个服务实例更新任务
        updated_task = task_service2.update_task(
            task_id=task_id,
            status="completed",
            result={"output": "test result"}
        )
        
        # 使用第一个服务实例再次获取任务，但不刷新
        # 注意：由于SQLite的隔离级别，即使不刷新也可能看到最新数据
        # 这与生产环境中的MySQL等数据库行为可能不同
        task2 = self.task_service.get_task(task_id, refresh=False)
        
        # 记录状态，用于调试
        print(f"不刷新获取的状态: {task2.status}")
        
        # 使用第一个服务实例再次获取任务，并刷新
        task3 = self.task_service.get_task(task_id, refresh=True)
        
        # 验证刷新后获取到最新状态
        self.assertEqual(task3.status, "completed")
        self.assertEqual(task3.result, {"output": "test result"})
        
        # 关闭第二个会话
        db2.close()
    
    def test_update_and_get_task_with_direct_sql(self):
        """测试使用直接SQL更新后获取最新状态"""
        # 创建任务
        task = self.task_service.create_task(
            service_type="test",
            service_name="test-service",
            status="pending"
        )
        
        # 获取任务ID
        task_id = task.task_id
        
        # 使用服务获取任务
        task1 = self.task_service.get_task(task_id)
        self.assertEqual(task1.status, "pending")
        
        # 使用直接SQL更新任务状态，绕过SQLAlchemy
        result_json = json.dumps({"output": "direct sql"})
        self.db.execute(
            f"UPDATE tasks SET status = 'completed', result = '{result_json}' WHERE task_id = '{task_id}'"
        )
        self.db.commit()
        
        # 不刷新获取任务
        task2 = self.task_service.get_task(task_id, refresh=False)
        print(f"直接SQL更新后不刷新获取的状态: {task2.status}")
        
        # 刷新获取任务
        task3 = self.task_service.get_task(task_id, refresh=True)
        
        # 验证刷新后获取到最新状态
        self.assertEqual(task3.status, "completed")
        self.assertTrue("output" in task3.result)
        self.assertEqual(task3.result["output"], "direct sql")
    
    def test_list_tasks_with_refresh(self):
        """测试刷新后列出任务"""
        # 创建多个任务
        for i in range(3):
            self.task_service.create_task(
                service_type="test",
                service_name=f"service-{i}",
                status="pending"
            )
        
        # 列出任务
        tasks1 = self.task_service.list_tasks(service_type="test", status="pending")
        self.assertEqual(len(tasks1), 3)
        
        # 使用直接SQL更新所有任务状态
        self.db.execute("UPDATE tasks SET status = 'completed'")
        self.db.commit()
        
        # 不刷新列出任务
        tasks2 = self.task_service.list_tasks(service_type="test", status="pending", refresh=False)
        print(f"直接SQL更新后不刷新列出的任务数量: {len(tasks2)}")
        
        # 刷新后列出任务
        tasks3 = self.task_service.list_tasks(service_type="test", status="pending", refresh=True)
        
        # 验证刷新后列出的任务数量为0（因为所有任务都已完成）
        self.assertEqual(len(tasks3), 0)
        
        # 列出已完成的任务
        tasks4 = self.task_service.list_tasks(service_type="test", status="completed", refresh=True)
        self.assertEqual(len(tasks4), 3)


if __name__ == '__main__':
    unittest.main()
