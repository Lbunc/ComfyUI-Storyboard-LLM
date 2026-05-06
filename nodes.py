# -*- coding: utf-8 -*-
"""
ComfyUI-Storyboard-LLM 插件 - 核心节点逻辑

本插件用于将小说章节转化为分镜表,通过调用 DeepSeek API 生成:
- 静态图像提示词(适用于图像生成)
- 动态视频提示词(适用于视频生成)
- 台词文本

使用说明:
1. 在 settings.json 中配置 API 密钥
2. 在 ComfyUI 中找到 storyboard 类别下的节点
3. 输入小说章节文本,运行工作流
"""

# 导入需要的模块
import json          # 用于处理 JSON 数据
import re           # 用于正则表达式匹配
import requests     # 用于发送 HTTP 请求
from typing import Tuple  # 用于类型提示
from pathlib import Path  # 用于文件路径操作
from datetime import datetime  # 用于生成时间戳

# 导入自定义模块
from .config import load_settings, save_settings  # 配置管理
from .prompt_template import format_prompt  # 提示词模板处理


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
    RETURN_TYPES = ("STRING", "STRING", "STRING")  # 三个输出端口
    RETURN_NAMES = ("image_prompts", "video_prompts", "dialogues")  # 输出端口名称
    FUNCTION = "generate_storyboard"  # 执行的核心方法名称
    CATEGORY = "storyboard"  # 节点在 ComfyUI 中的分类
    OUTPUT_NODE = True  # 标记为输出节点


    def generate_storyboard(self, chapter_text: str, save_json: bool = True, custom_prompt: str = "", model: str = "deepseek-v4-flash") -> Tuple[str, str, str]:
        """
        核心方法:生成故事板
        
        参数:
            chapter_text: str - 小说章节文本
            save_json: bool - 是否保存 JSON 文件
            custom_prompt: str - 自定义提示词模板
            model: str - 使用的模型名称
        
        返回值:
            Tuple[str, str, str] - (图像提示词, 视频提示词, 台词)
        """
        # 1. 加载配置(API 密钥,基础 URL,输出路径)
        settings = load_settings()
        api_key = settings.get("api_key", "")
        base_url = settings.get("base_url", "https://api.deepseek.com")
        output_path = settings.get("output_path", "")

        # 2. 验证 API 密钥是否已配置
        if not api_key:
            raise ValueError("请先在 settings.json 中配置DeepSeek API密钥!")

        # 3. 构建提示词(优先使用自定义模板,否则使用默认模板)
        if custom_prompt.strip():
            # 使用自定义模板(替换占位符)
            prompt = custom_prompt.replace("{chapter_content}", chapter_text)
        else:
            # 使用内置的默认模板
            prompt = format_prompt(chapter_text)

        # 4. 设置 HTTP 请求头(包含认证信息)
        headers = {
            "Content-Type": "application/json",  # 告诉服务器发送的是 JSON 格式
            "Authorization": f"Bearer {api_key}"  # API 认证令牌
        }

        # 5. 构建 API 请求参数
        payload = {
            "model": model,  # 使用的模型
            "messages": [
                # 系统消息:定义模型的角色
                {"role": "system", "content": "你是一位资深影视分镜师,擅长将文学性小说转化为可执行的视觉分镜脚本.请严格按照用户指定的格式输出JSON数据."},
                # 用户消息:包含实际的提示词
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,  # 创意程度(0-2,越高越随机)
            "max_tokens": 8192,  # 最大生成 token 数(8K输出)
            "response_format": {"type": "json_object"}  # 强制输出 JSON 格式
        }

        # 6. 发送 API 请求并处理响应
        try:
            # 发送 POST 请求到 DeepSeek API
            response = requests.post(
                f"{base_url}/chat/completions",  # API 端点
                headers=headers,  # 请求头
                json=payload,     # 请求体(JSON 格式)
                timeout=120       # 超时时间(2分钟)
            )
            
            # 如果状态码不是200,根据状态码提供具体的错误信息
            if response.status_code != 200:
                # 定义常见状态码对应的错误说明
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
                
                # 获取状态码对应的默认错误信息
                status_msg = status_messages.get(response.status_code, "未知错误")
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", str(error_data))
                except:
                    error_msg = response.text[:500]
                
                # 组合错误信息
                raise Exception(f"API请求失败 ({response.status_code} - {status_msg}): {error_msg}")
            
            # 正常响应时打印成功信息
            print("API请求成功")
            
            # 解析 JSON 响应
            result = response.json()
            
            # 检查响应结构是否正确
            if not result.get("choices") or len(result["choices"]) == 0:
                raise Exception(f"API响应中没有找到choices字段: {str(result)}")
            
            # 提取模型返回的内容
            llm_response = result["choices"][0]["message"].get("content", "")
            
            # 检查响应内容是否为空
            if not llm_response or not llm_response.strip():
                raise Exception(f"API返回内容为空!\n完整响应: {str(result)}")
        
        except requests.exceptions.RequestException as e:
            # 处理网络请求异常(如连接失败,超时等)
            raise Exception(f"网络请求失败: {str(e)}\n请检查网络连接或API地址是否正确")
        except (KeyError, IndexError) as e:
            # 处理响应解析异常(响应格式不符合预期)
            raise Exception(f"解析API响应失败: {str(e)}\n请检查API密钥是否正确")

        # 7. 解析模型返回的 JSON 数据
        storyboard_data = self.parse_json_response(llm_response)

        # 8. 保存 JSON 文件(如果启用)
        if save_json:
            self.save_json_file(storyboard_data, output_path)

        # 9. 提取三个输出:图像提示词,视频提示词,台词
        image_prompts, video_prompts, dialogues = self.extract_outputs(storyboard_data)

        # 10. 返回结果
        return (image_prompts, video_prompts, dialogues)


    def parse_json_response(self, response_text: str) -> list:
        """
        解析模型返回的 JSON 响应
        
        参数:
            response_text: str - 模型返回的原始文本
        
        返回值:
            list - 解析后的分镜数据列表
        """
        try:
            # 先尝试直接解析(因为启用了 JSON Output)
            return json.loads(response_text)
        except json.JSONDecodeError:
            # 如果直接解析失败,尝试提取完整的 JSON 数组
            # 找到第一个 [ 和最后一个 ] 的位置,提取完整的数组内容
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx+1]
            else:
                json_str = response_text
            
            # 清理可能的 markdown 代码块标记
            cleaned = re.sub(r'^```json\s*|\s*```$', '', json_str, flags=re.IGNORECASE)
            
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                # 如果还是解析失败,抛出详细错误信息
                raise Exception(f"解析JSON响应失败: {str(e)}\n响应内容: {response_text[:500]}")


    def save_json_file(self, data: list, output_path: str):
        """
        保存分镜数据到 JSON 文件
        
        参数:
            data: list - 分镜数据列表
            output_path: str - 输出路径(空则保存到插件目录)
        """
        if output_path:
            # 使用用户指定的路径
            output_file = Path(output_path) / f"storyboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            # 默认保存到插件目录,文件名包含时间戳
            output_file = Path(__file__).parent / f"storyboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 确保目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件(使用 UTF-8 编码支持中文)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


    def extract_outputs(self, data: list) -> Tuple[str, str, str]:
        """
        从分镜数据中提取三个输出
        
        参数:
            data: list - 分镜数据列表
        
        返回值:
            Tuple[str, str, str] - (图像提示词, 视频提示词, 台词)
        """
        image_prompts = []  # 静态图像提示词列表
        video_prompts = []  # 动态视频提示词列表
        dialogues = []      # 台词列表

        # 调试信息:打印总镜头数
        print(f"提取输出 - 总镜头数: {len(data)}")

        # 遍历每个分镜
        for i, item in enumerate(data):
            shot_num = i + 1  # 镜头编号(从1开始)
            
            # 获取字段值,同时支持中英文字段名(兼容模型返回格式不一致的问题)
            # 优先查找中文字段名,找不到再查找英文
            static = item.get("静态", "") or item.get("static", "") or "[无内容]"
            dynamic = item.get("动态", "") or item.get("dynamic", "") or "[无内容]"
            dialogue = item.get("台词", "") or item.get("dialogue", "") or "无"
            
            # 调试信息:检查是否有空内容
            if static == "[无内容]" or dynamic == "[无内容]":
                print(f"警告: 镜头{shot_num} 内容为空,原始数据: {item}")

            # 添加到对应列表,格式为 "[镜头N] 内容"
            image_prompts.append(f"[镜头{shot_num}] {static}")
            video_prompts.append(f"[镜头{shot_num}] {dynamic}")
            # 处理空台词的情况
            dialogues.append(f"[镜头{shot_num}] {dialogue}" if dialogue != "无" else f"[镜头{shot_num}] ")

        # 调试信息:打印每个输出列表的长度
        print(f"图像提示词数量: {len(image_prompts)}")
        print(f"视频提示词数量: {len(video_prompts)}")
        print(f"台词数量: {len(dialogues)}")

        # 将列表转换为字符串(每个镜头占一行)
        return ("\n".join(image_prompts), "\n".join(video_prompts), "\n".join(dialogues))


# 节点映射(ComfyUI 需要的注册信息)
NODE_CLASS_MAPPINGS = {
    "StoryboardNode": StoryboardNode  # 节点类名 -> 节点类
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "StoryboardNode": "Storyboard Generator (DeepSeek)"  # 在 UI 中显示的名称
}
