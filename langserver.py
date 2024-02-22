from contextlib import asynccontextmanager
from langserve import add_routes
from langchain.requests import RequestsWrapper
from langchain_core.language_models import BaseLanguageModel


# from langchain_community.agent_toolkits.openapi import planner

import custom_planner as planner
from langchain_community.agent_toolkits.openapi.spec import reduce_openapi_spec
from typing import Any, Dict, List, Mapping, Optional

# from langchain.llms import ollama as Ollama
from langchain_community.llms.ollama import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from pydantic import PrivateAttr
import logging

logging.basicConfig(level=logging.INFO)
from langchain_core.prompts import BasePromptTemplate, PromptTemplate


import json
import requests

# from langchain_community.agent_toolkits.openapi.base import  create_openapi_agent, OpenAPIToolkit
import ollama
from fastapi import FastAPI
from langchain import runnables  # Import Runnable from LangChain
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from custom_ollama import CustomLLM, RemoveBackslashesCallback, model_name

# from langchain_core.language_models.llms import ollama as Ollama
from langchain_community.llms.ollama import Ollama

from langchain_core.language_models.llms import LLMResult


def ensure_model_is_available(model_name):
    """
    Ensures that a model is available by checking if it exists and pulling it if necessary.

    Args:
        model_name (str): The name of the model to check and pull if necessary.

    Raises:
        ollama.ResponseError: If there is an error while checking or pulling the model.
    """
    try:
        # Attempt to show the model details
        ollama.show(model_name)
    except ollama.ResponseError as e:
        if e.status_code == 404:
            # If the model is not found, pull it
            print(f"Model {model_name} not found. Pulling the model...")
            ollama.pull(model_name)
        else:
            # If there's another error, raise it
            raise (f"Error pulling model {model_name}")


requests_wrapper = RequestsWrapper()

# Initialize the OpenAPI toolkit with your OpenAPI spec
openapi_toolkit = None
openapi_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    openapi_spec_url = "http://localhost:8000/openapi.json"
    response = requests.get(openapi_spec_url)
    openapi_spec = response.json()  # Parse the JSON response into a Python dictionary
    openapi_spec["servers"] = [{"url": "http://localhost:8000"}]
    reduced_openapi_spec = reduce_openapi_spec(openapi_spec)

    requests_wrapper = RequestsWrapper()

    # model_name = "wizardcoder:7b-python"
    # model_name = "deepseek-coder:6.7b"
    # model_name = "llama2:13b-text"

    ensure_model_is_available(model_name)
    llm = CustomLLM(model=model_name, verbose=True)

    agent_executor_kwargs = {
        "handle_parsing_errors": True,
        "callbacks": [RemoveBackslashesCallback()],
    }

    def _get_default_llm_chain(prompt: BasePromptTemplate) -> Any:
        from langchain.chains.llm import LLMChain

        logging.log(logging.INFO, f"in _get_default_llm_chain prompt: {prompt}")

        return LLMChain(
            llm=Ollama(model=model_name),
            prompt=prompt,
        )

    # monkey patch the openapi agent planner to use our custom llm chain
    # planner._get_default_llm_chain = _get_default_llm_chain

    openapi_agent: AgentExecutor = planner.create_openapi_agent(
        reduced_openapi_spec,
        requests_wrapper,
        llm,
        agent_executor_kwargs=agent_executor_kwargs,
    )

    openapi_agent.callbacks = [RemoveBackslashesCallback()]
    openapi_agent.verbose = True

    openapi_agent.handle_parsing_errors = True

    add_routes(app, openapi_agent, path="/api_interaction")

    yield


app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="Spin up a simple api server using Langchain's Runnable interfaces",
    lifespan=lifespan,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
