import asyncio
import os
import sys

# Add the root directory to sys.path to import browser_use
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from browser_use import Agent, ChatGoogle

load_dotenv()

# You can set GOOGLE_APPLICATION_CREDENTIALS in your .env file
# or pass the path directly to ChatGoogle
service_account_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service-account.json')
project_id = os.getenv('GOOGLE_CLOUD_PROJECT') # Optional, will be read from JSON if not provided
location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')

async def run_search():
    # Initialize ChatGoogle with Vertex AI and service account JSON
    llm = ChatGoogle(
        model='gemini-2.0-flash',
        vertexai=True,
        project=project_id,
        location=location,
        service_account_json=service_account_json
    )
    
    agent = Agent(
        llm=llm,
        task='What is the latest version of browser-use?',
    )

    await agent.run()

if __name__ == '__main__':
    asyncio.run(run_search())
