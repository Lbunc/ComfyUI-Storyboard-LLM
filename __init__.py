# -*- coding: utf-8 -*-
"""
ComfyUI-Storyboard-LLM 插件 - 入口文件

本文件是 ComfyUI 插件的入口点,负责:
1. 注册节点类到 ComfyUI 系统
2. 定义节点在 UI 中的显示名称
3. 注册 web 扩展和服务器路由
"""

import os

# 导入节点类和显示名称映射
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 注册 web 目录
WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

# 尝试注册服务器路由（如果 server 模块可用）
try:
    import server
    
    @server.PromptServer.instance.routes.post("/storyboard/settings")
    async def post_settings_handler(request):
        from .server import post_settings
        return await post_settings(request)
    
    @server.PromptServer.instance.routes.get("/storyboard/settings")
    async def get_settings_handler(request):
        from .server import get_settings
        return await get_settings(request)
    
    @server.PromptServer.instance.routes.post("/storyboard/settings/reset")
    async def reset_settings_handler(request):
        from .server import reset_settings
        return await reset_settings(request)
except Exception as e:
    print(f"Warning: Could not register storyboard server routes: {e}")

# 定义模块公开的接口
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
