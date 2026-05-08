
# -*- coding: utf-8 -*-
"""
ComfyUI-Storyboard-LLM 插件 - 后端服务器路由
"""

from aiohttp import web
from .config import load_settings, save_settings


async def get_settings(request):
    """获取设置的 API 端点"""
    settings = load_settings()
    return web.json_response(settings)


async def post_settings(request):
    """保存设置的 API 端点"""
    try:
        data = await request.json()
        save_settings(data)
        return web.json_response({"status": "success"})
    except Exception as e:
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def reset_settings(request):
    """重置设置的 API 端点"""
    from .config import DEFAULT_SETTINGS
    save_settings(DEFAULT_SETTINGS.copy())
    return web.json_response({"status": "success"})


def setup_routes():
    """设置路由"""
    routes = web.RouteTableDef()
    routes.get("/storyboard/settings")(get_settings)
    routes.post("/storyboard/settings")(post_settings)
    routes.post("/storyboard/settings/reset")(reset_settings)
    return routes

