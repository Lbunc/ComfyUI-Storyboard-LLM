# -*- coding: utf-8 -*-
"""
ComfyUI-Storyboard-LLM 插件 - 核心节点类

本文件实现了:
1. Storyboard 节点的 UI 定义
2. 与 DeepSeek API 的交互逻辑
3. 响应解析和输出处理
"""

# 导入标准库模块
import json          # 用于 JSON 数据的解析和序列化
import re           # 用于正则表达式处理
import requests     # 用于 HTTP 请求
from typing import Tuple  # 用于类型注解
from pathlib import Path  # 用于文件路径操作
from datetime import datetime  # 用于生成时间戳

# 导入自定义模块
from .config import load_settings       # 加载配置文件
from .prompt_template import format_prompt  # 格式化提示词模板


class StoryboardNode:
    """
    故事板生成节点类
    继承自 ComfyUI 的节点基类,实现小说转分镜表的核心功能
    """

    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点的输入参数(ComfyUI 节点必须实现的方法)
        
        返回值:
            dict: 包含 required(必填)和 optional(可选)参数的字典
        """
        # 加载配置文件中的设置
        settings = load_settings()
        
        return {
            "required": {
                # 小说章节文本输入
                "chapter_text": ("STRING", {"multiline": True, "default": "", "tooltip": "输入小说章节内容"}),
                # 是否保存 JSON 文件的开关
                "save_json": ("BOOLEAN", {"default": True, "tooltip": "是否保存JSON文件"}),
            },
            "optional": {
                # 自定义提示词模板
                "custom_prompt": ("STRING", {"multiline": True, "default": "", "tooltip": "自定义提示词模板,留空使用默认模板"}),
                # 模型选择(DeepSeek 提供的两种模型)
                "model": (["deepseek-v4-flash", "deepseek-v4-pro"], {"default": "deepseek-v4-flash", "tooltip": "选择使用的模型"}),
            },
        }

    # 定义节点的输出类型和名称
    RETURN_TYPES = ("STRING", "STRING", "STRING")  # 输出类型: 三个字符串
    RETURN_NAMES = ("image_prompts", "video_prompts", "dialogues")  # 输出名称
    FUNCTION = "generate_storyboard"  # 节点执行的方法名
    CATEGORY = "storyboard"  # 节点在 ComfyUI 菜单中的分类
    OUTPUT_NODE = True  # 标记为输出节点

    def generate_storyboard(self, chapter_text, save_json=True, custom_prompt="", model="deepseek-v4-flash"):
        """
        核心方法:生成故事板
        
        参数:
            chapter_text: str - 小说章节文本
            save_json: bool - 是否保存 JSON 文件
            custom_prompt: str - 自定义提示词模板
            model: str - 使用的模型名称
        
        返回值:
            tuple - (图像提示词, 视频提示词, 台词)
        """
        # 1. 加载配置(API 密钥,基础 URL,输出路径)
        settings = load_settings()
        api_key = settings.get("api_key", "")
        base_url = settings.get("base_url", "https://api.deepseek.com")
        output_path = settings.get("output_path", "")

        # 2. 验证 API 密钥是否已配置
        if not api_key:
            raise ValueError("请先在 settings.json 中配置 DeepSeek API 密钥!")

        # 3. 构建提示词(优先使用自定义模板,否则使用默认模板)
        if custom_prompt.strip():
            # 使用自定义模板(替换占位符)
            prompt = custom_prompt.replace("{chapter_content}", chapter_text)
        else:
            # 使用内置的默认模板
            prompt = format_prompt(chapter_text)

        # 4. 设置 HTTP 请求头(包含认证信息)
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key
        }

        # 5. 构建 API 请求参数
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一位资深影视分镜师,擅长将文学性小说转化为可执行的视觉分镜脚本.请严格按照用户指定的格式输出JSON数据."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 8192,
            "response_format": {"type": "json_object"}
        }

        # 6. 发送 API 请求并处理响应
        try:
            response = requests.post(
                base_url + "/chat/completions",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                status_messages = {
                    400: "请求参数错误,请检查输入格式",
                    401: "未授权访问,请检查API密钥是否正确",
                    403: "访问被禁止,可能API密钥无效或权限不足",
                    404: "API端点不存在,请检查base_url配置",
                    429: "请求过于频繁,请稍后重试或检查API配额",
                    500: "服务器内部错误,请稍后重试",
                    502: "网关错误,请稍后重试",
                    503: "服务暂时不可用,请稍后重试"
                }
                
                status_msg = status_messages.get(response.status_code, "未知错误")
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", str(error_data))
                except Exception:
                    error_msg = response.text[:500]
                
                raise Exception("API请求失败 (" + str(response.status_code) + " - " + status_msg + "): " + error_msg)
            
            print("API请求成功")
            
            # 解析 API 响应
            response_data = response.json()  # 将响应转为 JSON 对象
            model_response = response_data["choices"][0]["message"]["content"]  # 提取模型返回的内容
            storyboard_data = self._parse_response(model_response)  # 解析分镜数据
            
            # 如果需要保存 JSON 文件
            if save_json:
                self.save_json_file(storyboard_data, output_path)
            
            # 提取输出并返回
            return self._extract_outputs(storyboard_data, model)
            
        except requests.exceptions.Timeout:
            # 请求超时异常
            raise Exception("API请求超时,请稍后重试或检查网络连接")
        except requests.exceptions.RequestException as e:
            # 网络请求异常（如连接失败、DNS解析失败等）
            raise Exception("网络请求错误: " + str(e))
        except Exception as e:
            # 其他未知异常
            raise Exception("处理请求时出错: " + str(e))

    def _parse_response(self, response_text):
        """
        解析模型返回的 JSON 响应
        
        参数:
            response_text: str - 模型返回的原始响应文本
        
        返回值:
            list/dict - 解析后的分镜数据
        
        说明:
            该方法采用多层容错机制来处理模型可能返回的不规范响应:
            1. 首先尝试直接解析
            2. 如果失败,尝试提取 JSON 数组部分
            3. 移除可能存在的 markdown 代码块标记
            4. 尝试修复不完整的 JSON
        """
        try:
            # 第一层尝试: 直接解析 JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 第二层尝试: 提取 JSON 数组部分
            start_idx = response_text.find('[')  # 找到数组开始位置
            end_idx = response_text.rfind(']')   # 找到数组结束位置
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx+1]  # 提取数组部分
            else:
                json_str = response_text  # 如果找不到数组标记,使用原文本
            
            # 移除 markdown 代码块标记 (如 ```json 和 ```)
            cleaned = re.sub(r'^```json\s*|\s*```$', '', json_str, flags=re.IGNORECASE)
            
            try:
                # 第三层尝试: 解析清理后的 JSON
                return json.loads(cleaned)
            except json.JSONDecodeError:
                # 第四层尝试: 修复不完整的 JSON 后再解析
                fixed_json = self._fix_incomplete_json(cleaned)
                try:
                    return json.loads(fixed_json)
                except json.JSONDecodeError as e:
                    # 所有尝试都失败,抛出异常
                    raise Exception("解析JSON响应失败: " + str(e) + "\n响应内容: " + response_text[:500])
    
    def _fix_incomplete_json(self, json_str):
        """
        尝试修复不完整的 JSON 字符串
        
        参数:
            json_str: str - 待修复的 JSON 字符串
        
        返回值:
            str - 修复后的 JSON 字符串
        
        说明:
            该方法主要处理两种常见的 JSON 不完整情况:
            1. 字符串引号未闭合 (模型返回被截断)
            2. 数组缺少闭合括号 ]
        """
        # 修复一: 处理未闭合的字符串引号
        # 统计引号数量，如果是奇数，说明有未闭合的字符串
        quote_count = json_str.count('"')
        if quote_count % 2 != 0:
            # 找到最后一个未闭合的引号位置
            last_quote_idx = json_str.rfind('"')
            if last_quote_idx != -1:
                # 检查引号后面的内容，判断是否需要添加闭合引号
                remaining = json_str[last_quote_idx+1:].strip()
                # 如果后面没有内容或者只有数组/对象的闭合符，则需要添加引号
                if not remaining or remaining in [']', '}']:
                    json_str = json_str[:last_quote_idx+1] + '"' + json_str[last_quote_idx+1:]
        
        # 修复二: 确保 JSON 数组以 ] 结尾
        stripped = json_str.strip()
        if not stripped.endswith(']'):
            json_str += ']'
        
        return json_str

    def save_json_file(self, data, output_path):
        """
        保存分镜数据到 JSON 文件
        
        参数:
            data: list/dict - 分镜数据
            output_path: str - 输出目录路径(可为空)
        
        说明:
            如果未指定输出路径,则保存到插件所在目录
            文件名格式: storyboard_YYYYMMDD_HHMMSS.json
        """
        # 确定输出目录
        if not output_path:
            output_dir = Path(__file__).parent  # 使用插件目录
        else:
            output_dir = Path(output_path)  # 使用指定目录
        
        # 确保目录存在(递归创建)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成带时间戳的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "storyboard_" + timestamp + ".json"
        filepath = output_dir / filename
        
        # 写入 JSON 文件
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("分镜数据已保存到: " + str(filepath))

    def _extract_outputs(self, storyboard_data, model):
        """
        从分镜数据中提取输出信息
        
        参数:
            storyboard_data: list/dict - 解析后的分镜数据
            model: str - 使用的模型名称
        
        返回值:
            tuple - (图像提示词, 视频提示词, 台词)
        
        说明:
            该方法支持多种数据格式:
            1. 直接是镜头数组
            2. 包含 scenes/shots/storyboard 等字段的字典
            3. 单个镜头对象
            每个镜头支持多种字段名(中英文兼容)
        """
        # 初始化输出列表
        all_image_prompts = []  # 静态分镜提示词列表
        all_video_prompts = []  # 动态视频提示词列表
        all_dialogues = []      # 台词列表
        shot_items = []         # 镜头项目列表

        # 内部函数: 处理单个镜头项，提取三个字段
        def process_item(item):
            """
            从单个镜头项中提取数据
            
            参数:
                item: dict - 单个镜头的数据
            
            返回值:
                tuple - (图像提示词, 视频提示词, 台词)
            """
            # 支持多种字段名（中英文兼容）
            img = item.get("静态") or item.get("static") or item.get("image_prompts") or item.get("image_prompt") or item.get("images") or item.get("image") or ""
            vid = item.get("动态") or item.get("dynamic") or item.get("video_prompts") or item.get("video_prompt") or item.get("videos") or item.get("video") or ""
            dia = item.get("台词") or item.get("dialogues") or item.get("dialogue") or item.get("lines") or item.get("dialog") or ""
            return str(img) if img else "", str(vid) if vid else "", str(dia) if dia else ""

        # 判断数据格式并提取镜头列表
        if isinstance(storyboard_data, list):
            # 情况1: 直接是镜头数组
            shot_items = storyboard_data
        elif isinstance(storyboard_data, dict):
            # 情况2: 是包含镜头数组的字典
            for array_key in ["scenes", "shots", "shot_list", "storyboard", "items"]:
                if array_key in storyboard_data and isinstance(storyboard_data[array_key], list):
                    shot_items = storyboard_data[array_key]
                    break

            # 如果没找到镜头数组，尝试直接处理字典
            if not shot_items:
                img, vid, dia = process_item(storyboard_data)
                if img: all_image_prompts.append(img)
                if vid: all_video_prompts.append(vid)
                if dia: all_dialogues.append(dia)

        # 遍历镜头列表，提取数据并添加镜头号
        for idx, item in enumerate(shot_items, 1):
            if isinstance(item, dict):
                img, vid, dia = process_item(item)
                shot_label = "[镜头{}]".format(idx)  # 生成镜头号标签
                if img:
                    all_image_prompts.append(shot_label + " " + img)
                if vid:
                    all_video_prompts.append(shot_label + " " + vid)
                if dia:
                    all_dialogues.append(shot_label + " " + dia)

        # 将列表合并为字符串，用空行分隔
        image_result = "\n\n".join(all_image_prompts) if all_image_prompts else ""
        video_result = "\n\n".join(all_video_prompts) if all_video_prompts else ""
        dialogue_result = "\n\n".join(all_dialogues) if all_dialogues else ""

        # 如果所有输出都为空，将原始数据作为后备输出
        if not image_result and not video_result and not dialogue_result:
            fallback = json.dumps(storyboard_data, ensure_ascii=False, indent=2)
            image_result = fallback

        # 输出处理完成日志
        print("分镜数据提取完成，模型: {}, 共 {} 个镜头".format(model, len(shot_items) if shot_items else 1))

        return (image_result, video_result, dialogue_result)


NODE_CLASS_MAPPINGS = {
    "StoryboardNode": StoryboardNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StoryboardNode": "Storyboard Generator (DeepSeek)"
}