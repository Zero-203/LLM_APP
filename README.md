# 基于 Gradio 的聊天应用 (LLM_APP)

## 简介
这是一个基于 Gradio 的轻量聊天界面，使用兼容 OpenAI 的客户端与后端模型进行对话。主要文件：

- `LLM_APP.py` - Gradio UI 入口
- `chat_logic.py` - 聊天逻辑（消息构建、历史管理、模型选择）
- `streaming.py` - 流式接收实现（与 OpenAI 兼容的客户端交互）
- `providers.py` - 提供者（provider）配置映射

## 特性

- 支持多种 provider（可在 `providers.py` 中配置）
- 流式返回聊天内容
- 聊天历史管理（新建、删除、选择）

## 环境要求

- Python 3.8+
- 建议使用虚拟环境 (venv)

## 所需 Python 包

已在 `requirements.txt` 中列出，主要依赖：

- gradio
- openai

## 从 GitHub 克隆并运行（示例）

1. 克隆仓库

```bash
git clone <REPO_URL>
cd <REPO_DIR>
```

2. 创建并激活虚拟环境（Windows PowerShell 示例）

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

4. 启动应用

```bash
python LLM_APP.py
```

启动后，Gradio 将打印本地访问地址（例如 http://127.0.0.1:7860/）。脚本使用 demo.launch(share=True) 会同时创建一个公网临时链接。

## 使用说明

- 在界面中选择 Model（下拉）和 Provider（如果有多家支持），或直接输入 API Key（UI 右侧的 API Key 文本框）。
- 输入消息后点击 Send 开始对话。聊天以流式方式在界面中展示。

## Provider 与 API Key 配置

- `providers.py` 列出了示例 provider（AutoDL、DeepSeek、Aliyun），以及每个 provider 的 base_url、模型映射与认证方式。根据你使用的服务，修改该文件中的 `base_url`、`models` 或 `auth_name`。
- API Key 仅通过 UI 在运行时输入（右侧的 API Key 文本框）。

## 常见问题

- 无法连接/生成失败：检查 API Key、provider 的 base_url 与所选 model 是否匹配。
- 依赖安装失败：确认 Python 版本与 pip 源（在国内可配置镜像）。

## 开发与调试

- 入口：`LLM_APP.py`
- 逻辑：`chat_logic.py`
- 流式实现：`streaming.py`

## 许可

MIT License。