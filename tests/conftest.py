"""
pytest配置文件
用于设置测试环境
"""
import os
import sys
from pathlib import Path

import logging
logging.basicConfig(level=logging.INFO)

# 将项目根目录添加到Python路径中
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
