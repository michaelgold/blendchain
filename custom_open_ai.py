from dotenv import load_dotenv

load_dotenv()

from langchain_community.agent_toolkits.openapi.planner import (
    MAX_RESPONSE_LENGTH,
    RequestsDeleteToolWithParsing,
    RequestsGetToolWithParsing,
    RequestsPatchToolWithParsing,
    RequestsPostToolWithParsing,
    RequestsPutToolWithParsing,
    create_openapi_agent,
)

from langchain_openai import OpenAI

llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0.0)
