from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sidekick_tools import playwright_tools, other_tools
from memory_manager import MemoryManager
import uuid
import asyncio
from datetime import datetime
import os 
import json  # Add if not already there

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    relevant_memories: Optional[str]  # Context from long-term memory


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class MemoryExtractionOutput(BaseModel):
    """Structured output for extracting facts from conversations."""
    facts_to_remember: List[str] = Field(
        description="List of important facts, preferences, or information worth remembering for future conversations"
    )
    conversation_summary: str = Field(
        description="Brief 1-sentence summary of what was discussed"
    )


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.memory_extractor_llm = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()  # Short-term conversation memory
        self.memory_manager = MemoryManager()  # Long-term memory (NEW!)
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()
        
        worker_llm = ChatOpenAI(
            model="deepseek-chat", 
            api_key=os.getenv("DEEPSEEK_API_KEY"), 
            base_url="https://api.deepseek.com"
        ) 
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        
        # FIX: Use JSON mode instead of structured output
        evaluator_llm = ChatOpenAI(
            model="deepseek-chat", 
            api_key=os.getenv("DEEPSEEK_API_KEY"), 
            base_url="https://api.deepseek.com",
            model_kwargs={"response_format": {"type": "json_object"}}  # Add this line
        )
        self.evaluator_llm_with_output = evaluator_llm  # Remove .with_structured_output()
        
        # Memory extraction LLM (also using JSON mode)
        memory_extractor = ChatOpenAI(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        self.memory_extractor_llm = memory_extractor
        
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        # Retrieve relevant memories for context
        user_message = state["messages"][-1].content if state["messages"] else ""
        memory_context = self.memory_manager.get_memory_context(user_message)
        
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
    You keep working on a task until either you have a question or clarification for the user, or the success criteria is met.
    You have many tools to help you, including tools to browse the internet, navigating and retrieving web pages.
    You have a tool to run python code, but note that you would need to include a print() statement if you wanted to receive output.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    {memory_context}

    This is the success criteria:
    {state["success_criteria"]}
    You should reply either with a question for the user about this assignment, or with your final response.
    If you have a question for the user, you need to reply by clearly stating your question. An example might be:

    Question: please clarify whether you want a summary or a detailed answer

    If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
    """

        if state.get("feedback_on_work"):
            system_message += f"""
    Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
    Here is the feedback on why this was rejected:
    {state["feedback_on_work"]}
    With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""

        # Add in the system message

        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)

        # Return updated state
        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        last_response = state["messages"][-1].content

        # Update system message to require JSON output
        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
    Assess the Assistant's last response based on the given criteria.

    **CRITICAL: You must respond with ONLY a valid JSON object in this exact format:**
    {
        "feedback": "your detailed feedback here",
        "success_criteria_met": true or false,
        "user_input_needed": true or false
    }

    Do not include any text before or after the JSON object."""

        user_message = f"""You are evaluating a conversation between the User and Assistant.

    The entire conversation:
    {self.format_conversation(state["messages"])}

    Success criteria:
    {state["success_criteria"]}

    Assistant's final response:
    {last_response}

    Evaluate if the success criteria is met and if more user input is needed.

    **Remember: Respond with ONLY valid JSON in the format specified above.**
    """
        
        if state["feedback_on_work"]:
            user_message += f"\n\nPrevious feedback: {state['feedback_on_work']}\n"
            user_message += "If the Assistant is repeating mistakes, indicate user input is needed."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        # Get response and parse JSON manually
        response = self.evaluator_llm_with_output.invoke(evaluator_messages)
    
        # Parse JSON
        import json
        try:
            eval_result = json.loads(response.content)
            feedback = eval_result["feedback"]
            success_criteria_met = eval_result["success_criteria_met"]
            user_input_needed = eval_result["user_input_needed"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Error parsing evaluator response: {e}")
            print(f"Response was: {response.content}")
            # Fallback
            feedback = "Evaluation error - please try again"
            success_criteria_met = False
            user_input_needed = True

        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback: {feedback}",
                }
            ],
            "feedback_on_work": feedback,
            "success_criteria_met": success_criteria_met,
            "user_input_needed": user_input_needed,
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "memory_extractor"  # Extract memories before ending
        else:
            return "worker"
    
    def memory_extractor(self, state: State) -> Dict[str, Any]:
        """
        Extract and store important facts from the conversation.
        
        This runs at the end of each successful interaction to build
        long-term memory about the user and their preferences.
        """
        system_message = """You are a memory extraction system. Analyze the conversation and extract important facts worth remembering.

Extract things like:
- User preferences (e.g., "prefers Python over JavaScript")
- Important information about the user (e.g., "studies at IU", "works on AI projects")
- Specific instructions or patterns (e.g., "always wants detailed explanations")
- Project-specific information (e.g., "working on a Sidekick project")
- Tools or technologies the user uses
- Communication style preferences

Do NOT extract:
- Temporary information (e.g., "today's weather")
- One-time tasks (e.g., "send email about meeting")
- Obvious general knowledge

**You must respond with ONLY valid JSON in this exact format:**
{
    "facts_to_remember": ["fact 1", "fact 2", ...],
    "conversation_summary": "Brief 1-sentence summary"
}
"""
        
        # Format the conversation for analysis
        conversation = self.format_conversation(state["messages"])
        
        user_message = f"""Analyze this conversation and extract important facts:

{conversation}

Remember: Respond with ONLY valid JSON in the format specified above."""
        
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ]
        
        try:
            # Get extraction
            response = self.memory_extractor_llm.invoke(messages)
            result = json.loads(response.content)
            
            facts = result.get("facts_to_remember", [])
            summary = result.get("conversation_summary", "Conversation")
            
            # Store facts in long-term memory
            if facts:
                self.memory_manager.store_conversation_facts(summary, facts)
                print(f"💾 Stored {len(facts)} new memories!")
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Memory extraction error: {e}")
        
        # Don't modify state, just pass through
        return {}

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_node("memory_extractor", self.memory_extractor)

        # Add edges
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, 
            {"worker": "worker", "memory_extractor": "memory_extractor"}
        )
        # After extracting memories, end the conversation
        graph_builder.add_edge("memory_extractor", END)
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep_streaming(self, message, success_criteria, history):
        """
        Run a task with streaming updates for real-time feedback.
        Yields status updates as the agent works through the workflow.
        """
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "relevant_memories": None,
        }
        
        # Add user message to history immediately
        user = {"role": "user", "content": message}
        current_history = history + [user]
        
        # Initialize streaming response
        streaming_message = {"role": "assistant", "content": ""}
        assistant_content = ""
        last_status = ""
        
        # Stream through the graph
        async for event in self.graph.astream(state, config=config):
            # Extract node name and data
            for node_name, node_data in event.items():
                status_message = ""
                
                if node_name == "worker":
                    # Worker is thinking/responding
                    if "messages" in node_data and node_data["messages"]:
                        last_msg = node_data["messages"][-1]
                        
                        # Check if making tool calls
                        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                            tool_names = [tc.get('name', 'unknown') for tc in last_msg.tool_calls]
                            status_message = f"🔧 Using tools: {', '.join(tool_names)}..."
                        elif hasattr(last_msg, 'content') and last_msg.content and not hasattr(last_msg, 'tool_calls'):
                            # Worker has produced a response
                            if isinstance(last_msg, AIMessage):
                                assistant_content = last_msg.content
                                status_message = f"{assistant_content}\n\n⏳ Processing..."
                            else:
                                status_message = "🤔 Analyzing task..."
                        else:
                            status_message = "🤔 Thinking..."
                
                elif node_name == "tools":
                    # Tools are executing
                    status_message = "⚙️ Executing actions..."
                
                elif node_name == "evaluator":
                    # Evaluating results
                    if assistant_content:
                        status_message = f"{assistant_content}\n\n✅ Reviewing results..."
                    else:
                        status_message = "✅ Evaluating work..."
                
                elif node_name == "memory_extractor":
                    # Storing memories (final step)
                    if assistant_content:
                        status_message = f"{assistant_content}\n\n💾 Saving to memory..."
                    else:
                        status_message = "💾 Saving to memory..."
                
                # Only yield if status changed (avoid duplicate updates)
                if status_message and status_message != last_status:
                    streaming_message["content"] = status_message
                    last_status = status_message
                    yield current_history + [streaming_message]
        
        # Get final clean result (without status indicators)
        if assistant_content:
            streaming_message["content"] = assistant_content
        else:
            # Fallback: try to get from final state
            final_state = await self.graph.aget_state(config)
            if final_state.values.get("messages"):
                # Find the actual assistant response (not evaluator feedback)
                for msg in reversed(final_state.values["messages"]):
                    if hasattr(msg, 'content') and msg.content:
                        content = msg.content
                        if not content.startswith("Evaluator Feedback"):
                            if isinstance(msg, AIMessage):
                                assistant_content = content
                                break
                streaming_message["content"] = assistant_content if assistant_content else "Task completed."
        
        # Final yield with clean response (no status indicators)
        yield current_history + [streaming_message]
    
    async def run_superstep(self, message, success_criteria, history):
        """Legacy non-streaming method - kept for compatibility"""
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "relevant_memories": None,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        # feedback is internal only - don't show to user
        # feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply]  # Only show user's message and assistant's reply

    def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
