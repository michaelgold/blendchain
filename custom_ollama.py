from typing import Any, Dict, List, Mapping, Optional
from langchain_community.llms.ollama import Ollama
from langchain_core.language_models.llms import LLMResult
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
import logging
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.agents import AgentAction, AgentFinish
from uuid import UUID

from tenacity import RetryCallState


logging.basicConfig(level=logging.INFO)


class CustomLLM(Ollama):
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        images: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        generations = []
        for prompt in prompts:
            # Apply preprocessing here
            # logging.log(logging.INFO, f"Original prompt: {prompt}")
            preprocessed_prompt = self.pre_process_input(prompt)
            # logging.log(logging.INFO, f"Preprocessed prompt: {preprocessed_prompt}")
            # run_manager.handlers.append(RemoveBackslashesCallback())
            # logging.log(logging.INFO, f"run_manager handlers: {run_manager.handlers}")

            final_chunk = super()._stream_with_aggregation(
                preprocessed_prompt,
                stop=stop,
                images=images,
                run_manager=run_manager,
                verbose=self.verbose,
                **kwargs,
            )
            logging.log(
                logging.INFO, f"final_chunk before post processing: {final_chunk.text}"
            )
            final_chunk.text = self.post_process_output(final_chunk.text)
            # logging.log(
            #     logging.INFO, f"final_chunk after post processing: {final_chunk.text}"
            # )
            generations.append([final_chunk])

        return LLMResult(generations=generations)

    def clean_text(self, text: str) -> str:
        return text.replace("\\_", "_").replace("\_", "_")

    def post_process_output(self, output: str):
        """Apply postprocessing to output here"""
        return self.clean_text(output)

    def pre_process_input(self, input: str):
        """Apply preprocessing to input here"""
        return self.clean_text(input)


class RemoveBackslashesCallback(BaseCallbackHandler):
    def clean_text(self, text: str) -> str:
        return text.replace("\\_", "_").replace("\_", "_")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        # Implement preprocessing logic here

        cleaned_input = self.clean_text(input_str)
        logging.log(logging.INFO, f"cleaned_output: {cleaned_input}")
        return cleaned_input

    def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        # Implement preprocessing logic here
        action.tool = self.clean_text(action.tool)
        action.tool_input = self.clean_text(action.tool_input)
        logging.log(logging.INFO, f"action.tool: {action.tool}")
        logging.log(logging.INFO, f"action.tool_input: {action.tool_input}")
        logging.log(logging.INFO, f"action.type: {action.type}")
        return super().on_agent_action(
            action, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_retry(
        self,
        retry_state: RetryCallState,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        logging.log(logging.INFO, f"retry_state: {retry_state}")
        return super().on_retry(
            retry_state, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        cleaned_output = self.clean_text(output)
        return super().on_tool_end(
            cleaned_output, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        logging.log(logging.INFO, f"tool error: {error}")
        return super().on_tool_error(
            error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        logging.log(logging.INFO, f"chain error: {error}")
        return super().on_chain_error(
            error, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )

    def on_text(
        self,
        text: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> Any:
        logging.log(logging.INFO, f"on text: {text}")
        return super().on_text(
            text, run_id=run_id, parent_run_id=parent_run_id, **kwargs
        )
