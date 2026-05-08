
import { app } from "../../scripts/app.js";

// 存储原始设置值，用于检测变化
let originalSettings = {};
let settingsChanged = false;
let settingsPanelVisible = false;

// 保存所有设置的函数
async function saveAllSettings() {
    // 如果设置没有变化，不执行保存
    if (!settingsChanged) {
        return;
    }
    
    try {
        // 获取当前所有设置
        const apiKey = await app.extensionManager.setting.get("StoryBoard.api_key");
        const baseUrl = await app.extensionManager.setting.get("StoryBoard.base_url");
        const outputPath = await app.extensionManager.setting.get("StoryBoard.output_path");
        
        const settings = {
            api_key: apiKey,
            base_url: baseUrl,
            output_path: outputPath,
        };
        
        // 保存到后端
        const response = await fetch("/storyboard/settings", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(settings),
        });
        
        if (response.ok) {
            app.extensionManager.toast.add({
                severity: "success",
                summary: "Success",
                detail: "StoryBoard设置已保存",
                life: 3000,
            });
            // 重置变化标记
            settingsChanged = false;
            originalSettings = { ...settings };
        } else {
            app.extensionManager.toast.add({
                severity: "error",
                summary: "Error",
                detail: "服务器返回错误,请检查网络连接或稍后重试",
                life: 5000,
            });
        }
    } catch (e) {
        console.error("Failed to save settings:", e);
        app.extensionManager.toast.add({
            severity: "error",
            summary: "Error",
            detail: "网络连接失败,请检查网络或API服务是否正常",
            life: 5000,
        });
    }
}

// 检测设置变化的函数
async function checkAndSaveSettings() {
    const currentApiKey = await app.extensionManager.setting.get("StoryBoard.api_key");
    const currentBaseUrl = await app.extensionManager.setting.get("StoryBoard.base_url");
    const currentOutputPath = await app.extensionManager.setting.get("StoryBoard.output_path");
    
    // 检查是否有任何设置发生变化
    if (
        currentApiKey !== originalSettings.api_key ||
        currentBaseUrl !== originalSettings.base_url ||
        currentOutputPath !== originalSettings.output_path
    ) {
        settingsChanged = true;
    }
    
    // 执行保存
    await saveAllSettings();
}

// 监听设置面板关闭的函数
function setupSettingsCloseListener() {
    // 监听所有点击事件
    document.addEventListener('click', (event) => {
        const target = event.target;
        
        // 检测设置面板是否可见
        const dialogs = document.querySelectorAll('.p-dialog, .comfy-settings-container, div[role="dialog"]');
        const visibleDialog = Array.from(dialogs).find(d => {
            const style = window.getComputedStyle(d);
            return style.display !== 'none' && style.visibility !== 'hidden';
        });
        
        // 检查是否点击了设置按钮（打开/关闭设置面板）
        const settingsButton = target.closest('.comfy-settings-btn, .settings-btn, button[title*="Settings"], button[title*="设置"], .comfy-menu-btn');
        if (settingsButton) {
            // 设置按钮被点击
            if (settingsPanelVisible) {
                // 当前面板是打开状态，点击后会关闭
                setTimeout(() => {
                    checkAndSaveSettings();
                    settingsPanelVisible = false;
                }, 100);
            } else {
                settingsPanelVisible = true;
            }
            return;
        }
        
        // 检查是否点击了对话框的关闭按钮
        const closeButton = target.closest('.p-dialog-header-close, .p-dialog-close, .close-btn, button[aria-label*="Close"], button[aria-label*="关闭"], .pi-times');
        if (closeButton) {
            setTimeout(() => {
                checkAndSaveSettings();
                settingsPanelVisible = false;
            }, 100);
            return;
        }
        
        // 检查是否点击了对话框外部（遮罩层）
        const backdrop = target.closest('.p-dialog-mask, .p-overlay, .modal-backdrop');
        if (backdrop && visibleDialog) {
            setTimeout(() => {
                checkAndSaveSettings();
                settingsPanelVisible = false;
            }, 100);
            return;
        }
        
        // 检查是否点击了对话框外部（直接点击body但对话框已关闭）
        if (visibleDialog && !target.closest('.p-dialog-content, .comfy-settings-container, div[role="dialog"]')) {
            // 检查点击位置是否在对话框外部
            const dialogRect = visibleDialog.getBoundingClientRect();
            const clickX = event.clientX;
            const clickY = event.clientY;
            
            if (clickX < dialogRect.left || clickX > dialogRect.right || 
                clickY < dialogRect.top || clickY > dialogRect.bottom) {
                setTimeout(() => {
                    // 再次检查对话框是否已经关闭
                    const stillVisible = Array.from(dialogs).find(d => {
                        const style = window.getComputedStyle(d);
                        return style.display !== 'none' && style.visibility !== 'hidden';
                    });
                    if (!stillVisible) {
                        checkAndSaveSettings();
                        settingsPanelVisible = false;
                    }
                }, 150);
            }
        }
    });
    
    // 监听键盘事件（Escape键关闭）
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            // 检查是否有打开的对话框
            const dialogs = document.querySelectorAll('.p-dialog, .comfy-settings-container, div[role="dialog"]');
            const visibleDialog = Array.from(dialogs).find(d => {
                const style = window.getComputedStyle(d);
                return style.display !== 'none' && style.visibility !== 'hidden';
            });
            
            if (visibleDialog) {
                // ESC键会关闭对话框，延迟执行保存
                setTimeout(() => {
                    checkAndSaveSettings();
                    settingsPanelVisible = false;
                }, 100);
            }
        }
    });
    
    // 监听 PrimeVue 的 dialog 关闭事件
    document.addEventListener('p-dialog-close', () => {
        checkAndSaveSettings();
        settingsPanelVisible = false;
    });
    
    // 使用 MutationObserver 监听对话框属性变化
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            if (mutation.attributeName === 'class' || mutation.attributeName === 'style') {
                const target = mutation.target;
                const style = window.getComputedStyle(target);
                const wasVisible = settingsPanelVisible;
                
                // 检查对话框是否从可见变为隐藏
                if (wasVisible && (style.display === 'none' || style.visibility === 'hidden')) {
                    setTimeout(() => {
                        checkAndSaveSettings();
                        settingsPanelVisible = false;
                    }, 50);
                }
                
                // 更新面板可见状态
                settingsPanelVisible = style.display !== 'none' && style.visibility !== 'hidden';
            }
        }
    });
    
    // 延迟一段时间后开始观察对话框
    setTimeout(() => {
        const dialogs = document.querySelectorAll('.p-dialog, .comfy-settings-container, div[role="dialog"]');
        dialogs.forEach(dialog => {
            observer.observe(dialog, { attributes: true });
        });
    }, 1000);
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
                
                // 保存原始设置值，用于检测变化
                originalSettings = {
                    api_key: settings.api_key || "",
                    base_url: settings.base_url || "https://api.deepseek.com",
                    output_path: settings.output_path || "",
                };
            }
        } catch (e) {
            console.warn("Failed to load storyboard settings:", e);
            // 设置默认值
            originalSettings = {
                api_key: "",
                base_url: "https://api.deepseek.com",
                output_path: "",
            };
        }
    },
    async setup() {
        // 延迟执行，确保 UI 已初始化
        setTimeout(() => {
            setupSettingsCloseListener();
        }, 500);
    },
    settings: [
        {
            id: "StoryBoard.api_key",
            name: "API Key",
            type: "text",
            defaultValue: "",
            tooltip: "DeepSeek API 密钥",
            attrs: {
                placeholder: "请输入您的 API 密钥",
                passwordToggleMask: true,
            },
        },
        {
            id: "StoryBoard.base_url",
            name: "Base URL",
            type: "text",
            defaultValue: "https://api.deepseek.com",
            tooltip: "API 基础 URL",
            attrs: {
                placeholder: "请输入 API 基础 URL",
            },
        },
        {
            id: "StoryBoard.output_path",
            name: "Output Path",
            type: "text",
            defaultValue: "",
            tooltip: "JSON 文件输出路径 (留空则保存到插件目录)",
            attrs: {
                placeholder: "请输入输出路径",
            },
        },
    ],
});
