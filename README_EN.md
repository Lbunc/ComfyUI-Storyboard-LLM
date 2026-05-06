# ComfyUI-Storyboard-LLM

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

1. Copy the `ComfyUI-Storyboard-LLM` folder to ComfyUI's `custom_nodes` directory
2. Install dependencies (if not already installed):
```bash
pip install -r requirements.txt
```
3. Restart ComfyUI

## Configuration

Edit the `settings.json` file:

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

1. Find the `Storyboard Generator (DeepSeek)` node under the `storyboard` category in ComfyUI
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
        "static": "Character description + action + scene + lighting + composition",
        "dynamic": "Character is doing something, environment changes accordingly",
        "dialogue": "Character dialogue or inner monologue"
    }
]
```

## License

MIT License

## Notes

- Make sure you have obtained a DeepSeek API key before use
- API calls incur costs, please control usage frequency appropriately
- It is recommended to input one chapter at a time (less than 3000 Chinese characters), longer texts may cause response truncation
