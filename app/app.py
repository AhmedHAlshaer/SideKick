import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    """
    Process message with streaming support.
    Shows real-time updates as the agent works.
    """
    # Validate input
    if not message or not message.strip():
        yield history, sidekick, message, success_criteria
        return
    
    # Stream updates to the UI
    async for updated_history in sidekick.run_superstep_streaming(message, success_criteria, history):
        yield updated_history, sidekick, "", ""  # Clear input fields as we stream  


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(
    title="Sidekick", 
    theme=gr.themes.Soft(
        primary_hue="slate",
        secondary_hue="zinc",
        neutral_hue="slate",
        font=["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"]
    ),
    css="""
    /* Responsive Notion/ChatGPT inspired styling */
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
        padding: 0 1rem !important;
    }
    
    /* Main header */
    .main-header {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    
    .main-header h1 {
        font-size: 2rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        color: #6b7280;
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* Chat area - responsive height */
    .chatbot {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
        height: 600px !important;
    }
    
    /* Input area */
    .input-group {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-top: 1rem;
    }
    
    textarea, input {
        border: none !important;
        box-shadow: none !important;
        font-size: 1rem !important;
    }
    
    textarea:focus, input:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    
    /* Buttons */
    .primary-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.2s !important;
        font-size: 1rem !important;
    }
    
    .primary-btn:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    .secondary-btn {
        background: #f3f4f6 !important;
        border: none !important;
        border-radius: 8px !important;
        color: #6b7280 !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
        font-size: 1rem !important;
    }
    
    .secondary-btn:hover {
        background: #e5e7eb !important;
    }
    
    /* Remove default gradio styling */
    .contain {
        gap: 0 !important;
    }
    
    /* Mobile responsive - under 768px */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 0 0.5rem !important;
        }
        
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .main-header p {
            font-size: 0.875rem;
        }
        
        .main-header {
            padding: 1rem 0 1rem 0;
            margin-bottom: 1rem;
        }
        
        .chatbot {
            height: 400px !important;
        }
        
        .input-group {
            padding: 0.75rem;
        }
        
        textarea, input {
            font-size: 0.95rem !important;
        }
        
        .primary-btn, .secondary-btn {
            padding: 0.625rem 1rem !important;
            font-size: 0.95rem !important;
        }
    }
    
    /* Tablet responsive - 768px to 1024px */
    @media (min-width: 768px) and (max-width: 1024px) {
        .gradio-container {
            max-width: 900px !important;
        }
        
        .chatbot {
            height: 500px !important;
        }
    }
    
    /* Desktop - over 1024px */
    @media (min-width: 1024px) {
        .gradio-container {
            max-width: 1200px !important;
        }
    }
    """
) as ui:
    # Header
    gr.HTML("""
        <div class="main-header">
            <h1>Sidekick</h1>
            <p>Your intelligent AI assistant</p>
        </div>
    """)
    
    sidekick = gr.State(delete_callback=free_resources)

    # Chat area
    chatbot = gr.Chatbot(
        type="messages",
        height=600,
        show_label=False,
        avatar_images=None,
        bubble_full_width=False,
        show_copy_button=True,
        elem_classes="chatbot",
        scale=1
    )
    
    # Input area
    with gr.Group(elem_classes="input-group"):
        message = gr.Textbox(
            show_label=False, 
            placeholder="Ask me anything...",
            container=False,
            lines=2,
            max_lines=6,
            autofocus=True
        )
        
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, 
                placeholder="Success criteria (optional)",
                container=False,
                scale=4
            )
            reset_button = gr.Button("Reset", elem_classes="secondary-btn", scale=1)
            go_button = gr.Button("Send", elem_classes="primary-btn", scale=1)

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick, message, success_criteria]
    )
    success_criteria.submit(
        process_message, [sidekick, message, success_criteria, chatbot], 
        [chatbot, sidekick, message, success_criteria]  # Add message here!
    )
    go_button.click(
        process_message, [sidekick, message, success_criteria, chatbot], 
        [chatbot, sidekick, message, success_criteria]  # Add message here!
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])


ui.launch(inbrowser=True)
