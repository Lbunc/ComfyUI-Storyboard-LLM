# ComfyUI-Storyboard-LLM

🌐 **语言切换 / Language Switch**  
- [简体中文](README.md) | [English](README_EN.md)

A ComfyUI plugin that converts novel chapters into storyboard tables by calling DeepSeek API. Each storyboard shot contains static image prompts, dynamic video prompts, and dialogues.

## Features

- Convert novel chapter text into structured storyboard tables
- Each shot contains three parts:
  - Static image prompts (suitable for image generation)
  - Dynamic video prompts (suitable for video generation)
  - Dialogue text
- Support saving storyboard as JSON file
- Support custom prompt templates

## Node Preview

![Storyboard Generator Node](image/workflow.png)

## Installation

### Method 1: ComfyUI Manager Installation (Recommended)
1. Open ComfyUI Manager
2. Search for `Storyboard-LLM`
3. Click the `Install` button
4. Restart ComfyUI

### Method 2: Manual Installation via Git
1. Clone the repository to `custom_nodes` directory:
```bash
git clone https://github.com/Lbunc/ComfyUI-Storyboard-LLM.git
```
2. Install dependencies (if not already installed):
```bash
pip install -r requirements.txt
```
3. Restart ComfyUI

## Configuration

### Method 1: Configure via Web Settings (Recommended)
1. Open ComfyUI WebUI
2. Click the `Settings` button
3. Click on `StoryBoard` plugin settings
4. Enter your DeepSeek API key

### Method 2: Edit `settings.json` file:
- Open `custom_nodes/ComfyUI-Storyboard-LLM/settings.json`
- Edit the following content:

```json
{
  "api_key": "Your DeepSeek API Key",
  "base_url": "https://api.deepseek.com",
  "output_path": ""
}
```

- `api_key`: Required, your DeepSeek API key
- `base_url`: Optional, API base URL, defaults to `https://api.deepseek.com`
- `output_path`: Optional, JSON output path, leave empty to save in plugin directory

## Usage

### Method 1: Use Preset Workflow (Recommended)

1. Click the `Load` button in ComfyUI
2. Select `workflows/Storyboard-Generator-Workflow(DeepSeek).json`
3. Input your novel chapter text in the `Storyboard Generator (DeepSeek)` node
4. Run the workflow

### Method 2: Manual Setup

1. Find the `Storyboard Generator (DeepSeek)` node under the `StoryBoard` category in ComfyUI
2. Input your novel chapter text
3. Set whether to save JSON file
4. (Optional) Input custom prompt template
5. Run the workflow

## Node Inputs

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| chapter_text | STRING | Yes | Novel chapter content |
| save_json | BOOLEAN | Yes | Whether to save JSON file |
| custom_prompt | STRING | No | Custom prompt template |

## Node Outputs

| Output | Type | Description |
|--------|------|-------------|
| image_prompts | STRING | Static image prompts, grouped by shot number |
| video_prompts | STRING | Dynamic video prompts, grouped by shot number |
| dialogues | STRING | Dialogue text, grouped by shot number |

## Output Format Example

JSON output format:
```json
[
    {
        "静态": "Character description + action + scene + lighting + composition",
        "动态": "Character is doing something, environment changes accordingly",
        "台词": "Character dialogue or inner monologue"
    }
]
```

## Notes

- Make sure you have obtained a DeepSeek API key before use
- API calls incur costs, please control usage frequency appropriately
- It is recommended to input one chapter at a time (less than 3000 Chinese characters), longer texts may cause response truncation
- **Recommended to use `deepseek-v4-flash` model** for faster response speed, suitable for daily use; `deepseek-v4-pro` model has higher quality but slower response and may return incomplete JSON responses

## License

MIT License
