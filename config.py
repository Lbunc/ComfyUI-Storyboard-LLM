# -*- coding: utf-8 -*-
"""
ComfyUI-Storyboard-LLM 插件 - 配置管理模块

本模块负责:
1. 加载插件配置(API 密钥,基础 URL,输出路径等)
2. 保存配置到 settings.json 文件
3. 提供默认配置值

配置文件位置:插件目录下的 settings.json
"""

import json  # 用于处理 JSON 格式的配置文件
from pathlib import Path  # 用于处理文件路径


# 配置文件路径(相对于本文件的 settings.json)
SETTINGS_FILE = Path(__file__).parent / "settings.json"

# 默认配置值
DEFAULT_SETTINGS = {
    "api_key": "",  # DeepSeek API 密钥(用户需要填写)
    "base_url": "https://api.deepseek.com",  # API 基础 URL
    "output_path": ""  # JSON 文件输出路径(空则保存到插件目录)
}


def load_settings():
    """
    加载配置文件
    
    逻辑:
    1. 检查 settings.json 是否存在
    2. 如果存在,读取并解析 JSON
    3. 将读取的配置与默认配置合并(读取的配置优先级更高)
    4. 如果文件不存在或读取失败,返回默认配置
    
    返回值:
        dict: 包含配置项的字典
    """
    if SETTINGS_FILE.exists():
        try:
            # 文件存在,尝试读取
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # 合并配置:用户配置覆盖默认配置
                return {**DEFAULT_SETTINGS, **settings}
        except Exception:
            # 读取失败(如 JSON 格式错误),返回默认配置
            pass
    # 文件不存在或读取失败,返回默认配置的副本
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """
    保存配置到文件
    
    参数:
        settings: dict - 要保存的配置字典
    
    逻辑:
    1. 确保配置文件所在目录存在
    2. 将配置写入 settings.json 文件(使用 UTF-8 编码)
    3. 使用缩进格式化 JSON,便于阅读
    4. ensure_ascii=False 保证中文字符正常显示
    """
    # 确保目录存在(如果不存在则创建)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入配置文件
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
