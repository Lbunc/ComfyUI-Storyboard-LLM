
import { app } from "../../scripts/app.js";

// 保存设置的函数
async function saveSetting(key, value) {
    try {
        // 先获取当前所有设置
        const response = await fetch("/storyboard/settings");
        let currentSettings = {};
        if (response.ok) {
            currentSettings = await response.json();
        }
        
        // 更新指定的设置
        currentSettings[key] = value;
        
        // 保存到后端
        const saveResponse = await fetch("/storyboard/settings", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(currentSettings),
        });
        
        if (saveResponse.ok) {
            app.extensionManager.toast.add({
                severity: "success",
                summary: "Success",
                detail: `${key} 已保存`,
                life: 3000,
            });
        } else {
            app.extensionManager.toast.add({
                severity: "error",
                summary: "Error",
                detail: "保存失败",
                life: 5000,
            });
        }
    } catch (e) {
        console.error("Failed to save setting:", e);
        app.extensionManager.toast.add({
            severity: "error",
            summary: "Error",
            detail: "保存时发生错误",
            life: 5000,
        });
    }
}

app.registerExtension({
    name: "Storyboard Settings",
    async init() {
        try {
            // 从后端加载设置
            const response = await fetch("/storyboard/settings");
            if (response.ok) {
                const settings = await response.json();
                
                // 将后端设置应用到 ComfyUI 设置中
                if (settings.api_key !== undefined) {
                    await app.extensionManager.setting.set("storyboard.api_key", settings.api_key);
                }
                if (settings.base_url !== undefined) {
                    await app.extensionManager.setting.set("storyboard.base_url", settings.base_url);
                }
                if (settings.output_path !== undefined) {
                    await app.extensionManager.setting.set("storyboard.output_path", settings.output_path);
                }
            }
        } catch (e) {
            console.warn("Failed to load storyboard settings:", e);
        }
    },
    settings: [
        {
            id: "storyboard.api_key",
            name: "API Key",
            type: "text",
            defaultValue: "",
            tooltip: "DeepSeek API 密钥",
            attrs: {
                placeholder: "请输入您的 API 密钥",
                passwordToggleMask: true,
            },
            onChange: async (newVal) => {
                await saveSetting("api_key", newVal);
            },
        },
        {
            id: "storyboard.base_url",
            name: "Base URL",
            type: "text",
            defaultValue: "https://api.deepseek.com",
            tooltip: "API 基础 URL",
            attrs: {
                placeholder: "请输入 API 基础 URL",
            },
            onChange: async (newVal) => {
                await saveSetting("base_url", newVal);
            },
        },
        {
            id: "storyboard.output_path",
            name: "Output Path",
            type: "text",
            defaultValue: "",
            tooltip: "JSON 文件输出路径 (留空则保存到插件目录)",
            attrs: {
                placeholder: "请输入输出路径",
            },
            onChange: async (newVal) => {
                await saveSetting("output_path", newVal);
            },
        },
    ],
});
