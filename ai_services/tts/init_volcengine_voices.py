"""
初始化火山引擎音色数据库脚本
"""
import re
import sys
import os
import logging
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 从本地配置导入，不使用全局配置
from db.config import Base, engine, SessionLocal
from models import TTSPlatform, TTSVoiceCategory, TTSLanguage, TTSVoice

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_tables():
    """创建数据库表"""
    logger.info("开始创建数据库表...")
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")

def init_platform_data(db: Session):
    """初始化平台数据"""
    logger.info("开始初始化平台数据...")
    
    # 检查是否已存在
    volcengine = db.query(TTSPlatform).filter(TTSPlatform.code == "volcengine").first()
    if not volcengine:
        volcengine = TTSPlatform(
            name="火山引擎",
            code="volcengine",
            description="火山引擎提供的语音合成服务",
            api_base_url="https://api.volcengine.com/tts"
        )
        db.add(volcengine)
        db.commit()
        db.refresh(volcengine)
        logger.info(f"平台 '{volcengine.name}' 添加成功")
    else:
        logger.info(f"平台 '{volcengine.name}' 已存在，跳过")
    
    return volcengine

def init_language_data(db: Session):
    """初始化语言数据"""
    logger.info("开始初始化语言数据...")
    
    languages = [
        {"name": "中文", "code": "zh"},
        {"name": "美式英语", "code": "en-US"}
    ]
    
    result = {}
    for lang_data in languages:
        lang = db.query(TTSLanguage).filter(TTSLanguage.code == lang_data["code"]).first()
        if not lang:
            lang = TTSLanguage(**lang_data)
            db.add(lang)
            db.commit()
            db.refresh(lang)
            logger.info(f"语言 '{lang.name}' 添加成功")
        else:
            logger.info(f"语言 '{lang.name}' 已存在，跳过")
        
        result[lang.code] = lang
    
    return result

def init_categories_data(db: Session):
    """初始化音色分类数据"""
    logger.info("开始初始化音色分类数据...")
    
    categories = [
        {"name": "通用音色", "description": "通用场景的音色"},
        {"name": "视频配音", "description": "适合视频制作和配音的音色"},
        {"name": "有声阅读", "description": "适合有声书和阅读内容的音色"}
    ]
    
    result = {}
    for cat_data in categories:
        category = db.query(TTSVoiceCategory).filter(TTSVoiceCategory.name == cat_data["name"]).first()
        if not category:
            category = TTSVoiceCategory(**cat_data)
            db.add(category)
            db.commit()
            db.refresh(category)
            logger.info(f"分类 '{category.name}' 添加成功")
        else:
            logger.info(f"分类 '{category.name}' 已存在，跳过")
        
        result[category.name] = category
    
    return result

def parse_voice_data():
    """解析火山引擎音色数据"""
    # 火山引擎音色数据
    volcengine_voices_raw = """
ICL_zh_female_aomanjiaosheng_tob 中文 潇洒随性
ICL_zh_male_xiaosasuixing_tob 中文 腹黑公子
ICL_zh_male_fuheigongzi_tob 中文 诡异神秘
ICL_zh_male_guiyishenmi_tob 中文 儒雅才俊
ICL_zh_male_ruyacaijun_tob 中文 病娇白莲
ICL_zh_male_bingjiaobailian_tob 中文 正直青年
ICL_zh_male_zhengzhiqingnian_tob 中文 娇憨女王
ICL_zh_female_jiaohannvwang_tob 中文 病娇萌妹
ICL_zh_female_bingjiaomengmei_tob 中文 青涩小生
ICL_zh_male_qingsenaigou_tob 中文 纯真学弟
ICL_zh_male_chunzhenxuedi_tob 中文 暖心学姐
ICL_zh_female_nuanxinxuejie_tob 中文 可爱女生
ICL_zh_female_keainvsheng_tob 中文 成熟姐姐
ICL_zh_female_chengshujiejie_tob 中文 病娇姐姐
ICL_zh_female_bingjiaojiejie_tob 中文 优柔帮主
ICL_zh_male_youroubangzhu_tob 中文 优柔公子
ICL_zh_male_yourougongzi_tob 中文 妩媚御姐
ICL_zh_female_wumeiyujie_tob 中文 调皮公主
ICL_zh_female_tiaopigongzhu_tob 中文 傲娇女友
ICL_zh_female_aojiaonvyou_tob 中文 贴心男友
ICL_zh_male_tiexinnanyou_tob 中文 少年将军
ICL_zh_male_shaonianjiangjun_tob 中文 贴心女友
ICL_zh_female_tiexinnvyou_tob 中文 病娇哥哥
ICL_zh_male_bingjiaogege_tob 中文 学霸男同桌
ICL_zh_male_xuebanantongzhuo_tob 中文 幽默叔叔
ICL_zh_male_youmoshushu_tob 中文 性感御姐
ICL_zh_female_xingganyujie_tob 中文 假小子
ICL_zh_female_jiaxiaozi_tob 中文 冷峻上司
ICL_zh_male_lengjunshangsi_tob 中文 温柔男同桌
ICL_zh_male_wenrounantongzhuo_tob 中文 病娇弟弟
ICL_zh_male_bingjiaodidi_tob 中文 幽默大爷
ICL_zh_male_youmodaye_tob 中文 傲慢少爷
ICL_zh_male_aomanshaoye_tob 中文 神秘法师
ICL_zh_male_shenmifashi_tob 中文 视频配音 和蔼奶奶
ICL_zh_female_heainainai_tob 中文 邻居阿姨
ICL_zh_female_linjuayi_tob 中文 温柔小雅
zh_female_wenrouxiaoya_moon_bigtts 中文 天才童声
zh_male_tiancaitongsheng_mars_bigtts 中文 猴哥
zh_male_sunwukong_mars_bigtts 中文 熊二
zh_male_xionger_mars_bigtts 中文 佩奇猪
zh_female_peiqi_mars_bigtts 中文 武则天
zh_female_wuzetian_mars_bigtts 中文 顾姐
zh_female_gujie_mars_bigtts 中文 樱桃丸子
zh_female_yingtaowanzi_mars_bigtts 中文 广告解说
zh_male_chunhui_mars_bigtts 中文 少儿故事
zh_female_shaoergushi_mars_bigtts 中文 四郎
zh_male_silang_mars_bigtts 中文 磁性解说男声/Morgan
zh_male_jieshuonansheng_mars_bigtts 中文、美式英语 鸡汤妹妹/Hope
zh_female_jitangmeimei_mars_bigtts 中文、美式英语 贴心女声/Candy
zh_female_tiexinnvsheng_mars_bigtts 中文、美式英语 俏皮女声
zh_female_qiaopinvsheng_mars_bigtts 中文 萌丫头/Cutey
zh_female_mengyatou_mars_bigtts 中文、美式英语 懒音绵宝
zh_male_lanxiaoyang_mars_bigtts 中文 亮嗓萌仔
zh_male_dongmanhaimian_mars_bigtts 中文 有声阅读 悬疑解说
zh_male_changtianyi_mars_bigtts 中文 儒雅青年
zh_male_ruyaqingnian_mars_bigtts 中文 霸气青叔
zh_male_baqiqingshu_mars_bigtts 中文 擎苍
zh_male_qingcang_mars_bigtts 中文 活力小哥
zh_male_yangguangqingnian_mars_bigtts 中文 古风少御
zh_female_gufengshaoyu_mars_bigtts 中文 温柔淑女
zh_female_wenroushunv_mars_bigtts 中文 反卷青年
zh_male_fanjuanqingnian_mars_bigtts 中文
    """
    
    voices_data = []
    
    # 定义正则表达式模式
    pattern = r'([A-Za-z0-9_]+)\s+([^\\]+?)\s+([^\\]+?)(?:\s+([^\\]+?))?$'
    
    # 当前分类
    current_category = "通用音色"
    
    for line in volcengine_voices_raw.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # 检查是否是分类行
        if '视频配音' in line and len(line.split()) == 2:
            current_category = "视频配音"
            continue
        elif '有声阅读' in line and len(line.split()) == 2:
            current_category = "有声阅读"
            continue
        
        # 解析音色数据行
        match = re.match(pattern, line)
        if match:
            voice_id = match.group(1)
            
            # 处理特殊情况，有些行包含分类信息
            if match.group(2) == "中文" and '视频配音' in match.group(3):
                languages = ["zh"]
                name = match.group(4)
                category = "视频配音"
            elif match.group(2) == "中文" and '有声阅读' in match.group(3):
                languages = ["zh"]
                name = match.group(4)
                category = "有声阅读"
            elif "中文、美式英语" in match.group(2):
                languages = ["zh", "en-US"]
                name = match.group(3)
                category = current_category
            else:
                languages = [lang.strip() for lang in match.group(2).split('、')]
                languages = ["zh" if lang == "中文" else "en-US" if lang == "美式英语" else lang for lang in languages]
                name = match.group(3)
                category = current_category
            
            # 解析性别
            gender = None
            if "female" in voice_id:
                gender = "female"
            elif "male" in voice_id:
                gender = "male"
            
            # 检查是否支持流式调用
            is_streaming = True
            if name in ["病弱少女", "活泼女孩", "和蔼奶奶", "邻居阿姨"]:
                is_streaming = False
            
            voices_data.append({
                "voice_id": voice_id,
                "name": name,
                "gender": gender,
                "languages": languages,
                "category": category,
                "is_streaming": is_streaming
            })
    
    return voices_data

def init_voices_data(db: Session, platform: TTSPlatform, languages: dict, categories: dict):
    """初始化音色数据"""
    logger.info("开始初始化音色数据...")
    
    voices_data = parse_voice_data()
    
    for voice_data in voices_data:
        # 检查音色是否已存在
        existing_voice = db.query(TTSVoice).filter(TTSVoice.voice_id == voice_data["voice_id"]).first()
        if existing_voice:
            logger.info(f"音色 '{voice_data['name']}' 已存在，跳过")
            continue
        
        # 创建新音色
        voice = TTSVoice(
            voice_id=voice_data["voice_id"],
            name=voice_data["name"],
            gender=voice_data["gender"],
            description=f"火山引擎{voice_data['name']}音色",
            platform_id=platform.id,
            category_id=categories[voice_data["category"]].id,
            is_streaming=voice_data["is_streaming"]
        )
        
        # 添加语言关联
        for lang_code in voice_data["languages"]:
            if lang_code in languages:
                voice.languages.append(languages[lang_code])
        
        db.add(voice)
        logger.info(f"音色 '{voice.name}' 添加成功")
    
    db.commit()

def main():
    """主函数"""
    db = None
    try:
        # 创建数据库表
        create_tables()
        
        # 获取数据库会话
        db = SessionLocal()
        
        # 初始化基础数据
        platform = init_platform_data(db)
        languages = init_language_data(db)
        categories = init_categories_data(db)
        
        # 初始化音色数据
        init_voices_data(db, platform, languages, categories)
        
        logger.info("数据初始化完成")
    except Exception as e:
        logger.error(f"初始化过程出错: {e}")
    finally:
        if db is not None:
            db.close()

if __name__ == "__main__":
    main()
