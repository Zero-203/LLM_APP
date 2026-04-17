import sys
import codecs
import gradio as gr

from providers import MODULES
from chat_logic import (
    respond,
    on_history_select,
    delete_history,
    create_new_conversation,
    on_model_change,
)


def build_ui():
    with gr.Blocks() as demo:
        gr.Markdown("# 基于Gradio的聊天应用")

        history_store = gr.State({})
        selected_history = gr.State([])
        current_history_title = gr.State("")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## 历史对话")
                history_dropdown = gr.Dropdown(label="选择历史对话", interactive=True)
                with gr.Row():
                    delete_btn = gr.Button("删除对话")
                create_btn = gr.Button("新建对话")

            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="聊天记录", buttons=[["copy","copy_all"]])
                with gr.Row():
                    model_dropdown = gr.Dropdown(
                        choices=MODULES,
                        value=None,
                        label="Model"
                    )
                    provider_dropdown = gr.Dropdown(
                        choices=[],
                        value=None,
                        label="Provider (自动或手动选择)"
                    )
                    api_key_text = gr.Textbox(
                        label="API Key",
                        placeholder="输入 API Key",
                        type="password"
                    )
                call_info = gr.Textbox(label="调用信息", interactive=False)
                with gr.Row():
                    msg = gr.Textbox(show_label=False, placeholder="Type a message and press Enter", lines=3)
                    send_btn = gr.Button("Send", scale=0)

        # Events binding
        history_dropdown.change(
            on_history_select,
            inputs=[history_dropdown, history_store, chatbot, current_history_title, model_dropdown, provider_dropdown, api_key_text],
            outputs=[selected_history, chatbot, current_history_title, history_store, history_dropdown, model_dropdown, provider_dropdown, api_key_text, call_info]
        )

        delete_btn.click(
            delete_history,
            inputs=[history_dropdown, history_store],
            outputs=[chatbot, selected_history, history_store, history_dropdown, current_history_title]
        )

        create_btn.click(
            create_new_conversation,
            inputs=[chatbot, current_history_title, history_store, model_dropdown, provider_dropdown, api_key_text],
            outputs=[chatbot, selected_history, history_store, history_dropdown, current_history_title]
        )

        model_dropdown.change(
            on_model_change,
            inputs=[model_dropdown],
            outputs=[provider_dropdown, call_info]
        )

        send_btn.click(
            respond,
            inputs=[model_dropdown, provider_dropdown, api_key_text, selected_history, msg],
            outputs=[chatbot, msg, selected_history]
        )

    return demo


def main():
    demo = build_ui()
    demo.launch(share=True)


if __name__ == "__main__":
    main()
