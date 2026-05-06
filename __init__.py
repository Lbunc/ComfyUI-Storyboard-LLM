# -*- coding: utf-8 -*-
"""
ComfyUI-Storyboard-LLM 插件 - 入口文件

本文件是 ComfyUI 插件的入口点,负责:
1. 注册节点类到 ComfyUI 系统
2. 定义节点在 UI 中的显示名称
"""

# 导入节点类和显示名称映射
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 定义模块公开的接口
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
