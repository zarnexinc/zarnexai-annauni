#
# Copyright (c) 2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import os
import sys
from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import parse_telephony_websocket
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.services.sarvam.tts import SarvamTTSService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")

from tools.gmail import send_gmail
from pipecat.frames.frames import FunctionCallResultFrame

async def run_bot(transport: BaseTransport, handle_sigint: bool):

    stt = SarvamSTTService(
        api_key=os.getenv("SARVAM_API_KEY"),
        model="saarika:v2.5",
    )

    tts = SarvamTTSService(
        api_key=os.getenv("SARVAM_API_KEY"),
        model="bulbul:v2",
        voice_id="manisha",
    )

    tools = [
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email via Gmail to the specified recipient with the given subject and body.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "The recipient's email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "The subject of the email"
                        },
                        "body": {
                            "type": "string",
                            "description": "The body content of the email"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            }
        }
    ]

    llm = GroqLLMService(
        api_key=os.getenv("GROQ_API_KEY"),
        model="mixtral-8x7b-32768",
        temperature=0.3,
        max_tokens=300,
        stream=True,
        tools=tools,
    )

    # ✅ FIXED messages structure
    messages = [
        {"role": "system", "content": "You are a mail sender. When the user requests to send mail, ask for the recipient's email address, subject, and body. Then confirm the details with the user. After confirmation, use the send_email tool to send the email."},


    ]

    @llm.event_handler("on_function_call")
    async def on_function_call(llm, function_call):
        if function_call.name == "send_email":
            args = function_call.arguments
            access_token = os.getenv("GMAIL_ACCESS_TOKEN")
            if not access_token:
                await llm.push_frame(FunctionCallResultFrame(result="Error: Gmail access token not configured."))
                return
            try:
                send_gmail(access_token, args["to"], args["subject"], args["body"])
                await llm.push_frame(FunctionCallResultFrame(result="Email sent successfully!"))
            except Exception as e:
                await llm.push_frame(FunctionCallResultFrame(result=f"Failed to send email: {str(e)}"))

    context = LLMContext(messages)

    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Starting outbound call conversation")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Outbound call ended")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""

    try:
        transport_type, call_data = await parse_telephony_websocket(
            runner_args.websocket
        )
    except ValueError as e:
        logger.error(f"Failed to parse telephony WebSocket: {e}")
        return

    logger.info(f"Auto-detected transport: {transport_type}")

    body_data = call_data.get("body", {})
    to_number = body_data.get("to_number")
    from_number = body_data.get("from_number")

    logger.info(f"Call metadata - To: {to_number}, From: {from_number}")

    serializer = TwilioFrameSerializer(
        stream_sid=call_data["stream_id"],
        call_sid=call_data["call_id"],
        account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
        auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
    )

    transport = FastAPIWebsocketTransport(
        websocket=runner_args.websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            serializer=serializer,
        ),
    )

    await run_bot(transport, runner_args.handle_sigint)