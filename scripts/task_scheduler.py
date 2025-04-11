"""
任务调度器，用于定期检查任务状态
"""
import os
import time
import asyncio
import logging
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from db.config import get_db
from db.service.task_service import TaskService
from ai_services.video.registry import VideoServiceRegistry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class TaskScheduler:
    """任务调度器，用于定期检查任务状态"""
    
    def __init__(self, interval: int = 60):
        """
        初始化任务调度器
        
        Args:
            interval: 检查间隔，单位为秒，默认60秒
        """
        self.interval = interval
        self.running = False
        self.task_service = TaskService(next(get_db()))
        
    async def check_video_tasks(self):
        """检查视频生成任务状态"""
        try:
            # 获取所有未完成的视频任务
            pending_tasks = self.task_service.list_tasks(
                service_type="video",
                status=["pending", "running"],
                limit=100
            )
            
            if not pending_tasks:
                logger.info("没有待处理的视频任务")
                return
            
            logger.info(f"发现 {len(pending_tasks)} 个待处理的视频任务")
            
            # 检查每个任务的状态
            for task in pending_tasks:
                try:
                    # 获取服务实例
                    service = VideoServiceRegistry.get_service(task.service_name)
                    if not service:
                        logger.warning(f"找不到服务 '{task.service_name}'，跳过任务 '{task.task_id}'")
                        continue
                    
                    # 获取任务结果
                    logger.info(f"正在检查任务 '{task.task_id}' 的状态")
                    result = await service.get_video_task_result(task_id=task.task_id)
                    
                    # 任务状态已经在服务实现中更新到数据库
                    logger.info(f"任务 '{task.task_id}' 的状态为 '{result['status']}'")
                    
                except Exception as e:
                    logger.error(f"检查任务 '{task.task_id}' 状态时出错: {str(e)}", exc_info=True)
            
        except Exception as e:
            logger.error(f"检查视频任务状态时出错: {str(e)}", exc_info=True)
    
    async def run_once(self):
        """运行一次任务检查"""
        logger.info("开始检查任务状态")
        
        # 检查视频任务
        await self.check_video_tasks()
        
        # 未来可以添加其他类型的任务检查
        
        logger.info("任务状态检查完成")
    
    async def run(self):
        """运行任务调度器"""
        self.running = True
        
        while self.running:
            await self.run_once()
            
            # 等待下一次检查
            logger.info(f"等待 {self.interval} 秒后进行下一次检查")
            await asyncio.sleep(self.interval)
    
    def start(self):
        """启动任务调度器"""
        # 创建事件循环
        loop = asyncio.new_event_loop()
        
        # 在新线程中运行事件循环
        def run_loop():
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run())
        
        # 启动线程
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
        
        logger.info(f"任务调度器已启动，检查间隔为 {self.interval} 秒")
        
        return thread
    
    def stop(self):
        """停止任务调度器"""
        self.running = False
        logger.info("任务调度器已停止")


# 如果直接运行此脚本，则启动任务调度器
if __name__ == "__main__":
    scheduler = TaskScheduler(interval=30)  # 设置为30秒检查一次
    thread = scheduler.start()
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # 捕获Ctrl+C
        scheduler.stop()
        logger.info("程序已退出")
