# TTS音色数据库

本模块提供了一个用于管理TTS(文本转语音)音色的数据库解决方案，包括：

- 音色数据模型定义
- 数据库连接配置
- 火山引擎音色数据初始化脚本

## 数据模型结构

该方案设计了以下数据表：

1. `tts_platforms` - 语音合成平台
2. `tts_languages` - 支持的语言
3. `tts_voice_categories` - 音色分类
4. `tts_voices` - TTS音色信息
5. `voice_language_association` - 音色和语言的多对多关联表

## 如何使用

### 环境配置

首先配置数据库连接信息，在项目根目录的`.env`文件中添加：

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB_NAME=ai_tools
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 初始化数据库

运行以下命令初始化火山引擎音色数据：

```bash
python init_volcengine_voices.py
```

## 示例代码

```python
from sqlalchemy.orm import Session
from models import TTSVoice, TTSPlatform
from db_config import get_db

# 获取数据库会话
db = next(get_db())

# 查询火山引擎平台下的所有音色
platform = db.query(TTSPlatform).filter(TTSPlatform.code == "volcengine").first()
voices = db.query(TTSVoice).filter(TTSVoice.platform_id == platform.id).all()

# 打印音色信息
for voice in voices:
    print(f"音色ID: {voice.voice_id}, 名称: {voice.name}")
    print(f"支持语言: {', '.join([lang.name for lang in voice.languages])}")
    print("---")
```

## 扩展其他平台

如需添加其他平台的音色，只需参考`init_volcengine_voices.py`的实现方式，创建新的初始化脚本即可。

数据模型已经设计为可扩展的，支持多个平台、多种语言和不同分类的音色管理。
