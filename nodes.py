import json
import re
import requests
from typing import Tuple
from pathlib import Path
from datetime import datetime
from .config import load_settings, save_settings
from .prompt_template import format_prompt

class StoryboardNode:
    @classmethod
    def INPUT_TYPES(cls):
        settings = load_settings()
        return {
            "required": {
                "chapter_text": ("STRING", {"multiline": True, "default": "", "tooltip": "输入小说章节内容"}),
                "save_json": ("BOOLEAN", {"default": True, "tooltip": "是否保存JSON文件"}),
            },
            "optional": {
                "output_path": ("STRING", {"multiline": False, "default": settings.get("output_path", ""), "tooltip": "JSON输出路径，留空则保存到插件目录"}),
                "base_url": ("STRING", {"multiline": False, "default": settings.get("base_url", "https://api.deepseek.com"), "tooltip": "API基础URL"}),
                "custom_prompt": ("STRING", {"multiline": True, "default": "", "tooltip": "自定义提示词模板，留空使用默认模板"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("image_prompts", "video_prompts", "dialogues")
    FUNCTION = "generate_storyboard"
    CATEGORY = "storyboard"
    OUTPUT_NODE = True

    def generate_storyboard(self, chapter_text: str, save_json: bool = True, output_path: str = "", base_url: str = "", custom_prompt: str = ""):
        settings = load_settings()
        api_key = settings.get("api_key", "")

        if not api_key:
            raise ValueError("请先在 settings.json 中配置DeepSeek API密钥！")

        if not base_url:
            base_url = settings.get("base_url", "https://api.deepseek.com")

        if output_path:
            settings["output_path"] = output_path
            save_settings(settings)

        if custom_prompt.strip():
            prompt = custom_prompt.format(chapter_content=chapter_text)
        else:
            prompt = format_prompt(chapter_text)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4096
        }

        try:
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            llm_response = result["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"解析API响应失败: {str(e)}")

        storyboard_data = self.parse_json_response(llm_response)

        if save_json:
            self.save_json_file(storyboard_data, output_path if output_path else settings.get("output_path", ""))

        image_prompts, video_prompts, dialogues = self.extract_outputs(storyboard_data)

        return (image_prompts, video_prompts, dialogues)

    def parse_json_response(self, response_text: str) -> list:
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        else:
            json_str = response_text

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            cleaned = re.sub(r'^```json\s*|\s*```$', '', json_str, flags=re.IGNORECASE)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                raise Exception(f"解析JSON响应失败: {str(e)}\n响应内容: {response_text[:500]}")

    def save_json_file(self, data: list, output_path: str):
        if output_path:
            output_file = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Path(__file__).parent / f"storyboard_{timestamp}.json"

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def extract_outputs(self, data: list) -> Tuple[str, str, str]:
        image_prompts = []
        video_prompts = []
        dialogues = []

        for i, item in enumerate(data):
            shot_num = i + 1
            static = item.get("静态", "")
            dynamic = item.get("动态", "")
            dialogue = item.get("台词", "")

            image_prompts.append(f"[镜头{shot_num}] {static}")
            video_prompts.append(f"[镜头{shot_num}] {dynamic}")
            dialogues.append(f"[镜头{shot_num}] {dialogue}" if dialogue and dialogue != "无" else f"[镜头{shot_num}] ")

        return ("\n".join(image_prompts), "\n".join(video_prompts), "\n".join(dialogues))


NODE_CLASS_MAPPINGS = {
    "StoryboardNode": StoryboardNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StoryboardNode": "Storyboard Generator (DeepSeek)"
}
