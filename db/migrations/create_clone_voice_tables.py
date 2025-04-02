"""
u521bu5efau8bedu97f3u514bu9686u76f8u5173u7684u6570u636eu5e93u8868
"""
import sys
import os

# u6dfbu52a0u9879u76eeu6839u76eeu5f55u5230u7cfbu7edfu8defu5f84
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(root_dir)

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from db.config import DATABASE_URL, Base, engine


def create_tables():
    """u521bu5efau8bedu97f3u514bu9686u76f8u5173u7684u6570u636eu5e93u8868"""
    # u521bu5efau8868
    print(f"u6b63u5728u521bu5efau8bedu97f3u514bu9686u76f8u5173u7684u6570u636eu5e93u8868...")
    
    # u521bu5efau5143u6570u636e
    metadata = MetaData()
    
    # u624bu52a8u5b9au4e49u8868uff0cu907fu514du4f7fu7528u5916u952e
    tts_clone_voices = Table(
        'tts_clone_voices', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('voice_id', String(100), nullable=False, unique=True),
        Column('name', String(100), nullable=False),
        Column('description', Text, nullable=True),
        Column('user_id', String(100), nullable=False, index=True),
        Column('app_id', String(100), nullable=False, index=True),
        Column('platform_id', Integer, nullable=False),
        Column('original_sample_url', String(255), nullable=True),
        Column('is_streaming', Boolean, default=True),
        Column('is_active', Boolean, default=True),
        Column('created_at', DateTime),
        Column('updated_at', DateTime)
    )
    
    tts_clone_voice_languages = Table(
        'tts_clone_voice_languages', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('clone_voice_id', Integer, nullable=False),
        Column('language_id', Integer, nullable=False),
        Column('created_at', DateTime)
    )
    
    tts_clone_tasks = Table(
        'tts_clone_tasks', metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('task_id', String(100), nullable=False, unique=True),
        Column('user_id', String(100), nullable=False, index=True),
        Column('app_id', String(100), nullable=False, index=True),
        Column('sample_url', String(255), nullable=False),
        Column('voice_name', String(100), nullable=False),
        Column('status', String(20), nullable=False, default='pending'),
        Column('result_voice_id', String(100), nullable=True),
        Column('platform_id', Integer, nullable=False),
        Column('created_at', DateTime),
        Column('updated_at', DateTime)
    )
    
    # u5148u5c1du8bd5u5220u9664u8868uff08u5982u679cu5b58u5728uff09
    try:
        print("u5c1du8bd5u5220u9664u73b0u6709u8868...")
        tts_clone_voice_languages.drop(engine, checkfirst=True)
        tts_clone_voices.drop(engine, checkfirst=True)
        tts_clone_tasks.drop(engine, checkfirst=True)
        print("u5220u9664u5b8cu6210")
    except Exception as e:
        print(f"u5220u9664u8868u65f6u53d1u751fu5f02u5e38: {str(e)}")
    
    # u521bu5efau8868
    try:
        print("u5f00u59cbu521bu5efau8868...")
        tts_clone_voices.create(engine)
        print("u521bu5efau8868 tts_clone_voices u6210u529f")
        
        tts_clone_voice_languages.create(engine)
        print("u521bu5efau8868 tts_clone_voice_languages u6210u529f")
        
        tts_clone_tasks.create(engine)
        print("u521bu5efau8868 tts_clone_tasks u6210u529f")
        
        print("u6240u6709u8868u521bu5efau6210u529f")
    except Exception as e:
        print(f"u521bu5efau8868u65f6u53d1u751fu5f02u5e38: {str(e)}")


def drop_tables():
    """u5220u9664u8bedu97f3u514bu9686u76f8u5173u7684u6570u636eu5e93u8868"""
    # u5220u9664u8868
    print(f"u6b63u5728u5220u9664u8bedu97f3u514bu9686u76f8u5173u7684u6570u636eu5e93u8868...")
    
    # u521bu5efau5143u6570u636e
    metadata = MetaData()
    
    # u624bu52a8u5b9au4e49u8868
    tts_clone_voices = Table('tts_clone_voices', metadata, Column('id', Integer, primary_key=True))
    tts_clone_voice_languages = Table('tts_clone_voice_languages', metadata, Column('id', Integer, primary_key=True))
    tts_clone_tasks = Table('tts_clone_tasks', metadata, Column('id', Integer, primary_key=True))
    
    # u5220u9664u8868
    try:
        tts_clone_voice_languages.drop(engine, checkfirst=True)
        print("u5220u9664u8868 tts_clone_voice_languages u6210u529f")
        
        tts_clone_voices.drop(engine, checkfirst=True)
        print("u5220u9664u8868 tts_clone_voices u6210u529f")
        
        tts_clone_tasks.drop(engine, checkfirst=True)
        print("u5220u9664u8868 tts_clone_tasks u6210u529f")
        
        print("u6240u6709u8868u5220u9664u6210u529f")
    except Exception as e:
        print(f"u5220u9664u8868u65f6u53d1u751fu5f02u5e38: {str(e)}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="u8bedu97f3u514bu9686u6570u636eu5e93u8868u7ba1u7406")
    parser.add_argument('--action', type=str, choices=['create', 'drop'], default='create', help='u64cdu4f5cu7c7bu578b: create u6216 drop')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        create_tables()
    elif args.action == 'drop':
        drop_tables()
