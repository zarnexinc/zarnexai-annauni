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
from pipecat.services.groq import GroqLLMService   # ✅ CORRECT IMPORT

from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


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

    llm = GroqLLMService(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.1-8b-instant",
        temperature=0.3,
        max_tokens=300,
        stream=True,
    )

    # ✅ FIXED messages structure
    messages = [
        {
            "role": "system",
            "content": """You are Zarnex Insurance Agent.
You speak to users on a phone call.
Everything you say is converted to speech.

VOICE RULES:
Speak in short clear sentences.
Do not speak punctuation symbols.
Do not read tags aloud.
Tags are for the system only.

GREETING AND INSURANCE TYPE:
Start in English.
Greet the user politely.
Explain that you help people find suitable insurance.
Ask which insurance they are looking for.

<options>
Life Insurance
Health Insurance
Vehicle Insurance
Home Insurance
Travel Insurance
</options>

STEP BY STEP QUESTIONS:
Ask only one question at a time.

SEARCH STEP:
After collecting all details say
I am now searching the web and finding the best policies for you

POLICY RESULT:

<policy_slider>
[
{
"id": "1",
"name": "LIC Tech Term",
"logo_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSVuvpbsJJKjHGbqqEOwDe3Ee9XbQ_zUTG4Yw&s",
"details": "Scraped Analysis High claim settlement ratio and trusted by families",
"premium": "Eight hundred fifty rupees per month",
"link": "https://www.licindia.in/"
}
]
</policy_slider>

If the user asks for a human reply with this tag only

<call_agent>9159747001</call_agent>

Talk only about insurance."""
        }
    ]

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