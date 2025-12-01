from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain_core.tools import Tool, StructuredTool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from mathgrader.tools import get_grading_tools



load_dotenv(override=True)
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"
serper = GoogleSerperAPIWrapper()
sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

async def playwright_tools():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        # Add timeout:
        timeout=60000  # 60 seconds instead of 30
    )
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright

def push(text: str):
    """Send a push notification to the user"""
    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def send_email(subject: str, body: str):
    """Send an email from alshaerahmed8003@gmail.com to ahmealsh@iu.edu. 
    Args:
        subject: The email subject line
        body: The email body content
    """
    try:
        message = Mail(
            from_email='alshaerahmed8003@gmail.com',
            to_emails='ahmealsh@iu.edu',
            subject=subject,
            html_content=body
        )
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        return f"Email sent successfully! Status code: {response.status_code}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def other_tools():
    push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    
    email_tool = StructuredTool.from_function(
        func=send_email,
        name="send_email",
        description="Use this tool to send an email from alshaerahmed8003@gmail.com to ahmealsh@iu.edu. Requires two arguments: subject (string) and body (string)."
    )
    
    file_tools = get_file_tools()

    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    grading_tools = get_grading_tools()
    
    return file_tools + [push_tool, email_tool, tool_search,  wiki_tool] + grading_tools

