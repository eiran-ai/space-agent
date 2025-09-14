import os
from pathlib import Path
import json
from typing import List
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from openai import OpenAI
from .utils.prompt import ClientMessage, convert_to_openai_messages
from .utils.tools import get_current_weather
from .module.detect import router as detect_router, init_detect


load_dotenv(".env.local")

app = FastAPI()

# Load system prompt from project root desc.md
SYSTEM_PROMPT = """
This system is a smart assistant for satellite and drone images.
It doesn’t just detect objects (roads, farms, buildings, etc.), it can also compare current images with past ones using geo-metadata to align them. This lets people see how things are changing over time.

The interface is simple, like a map app:

Left: tools and project files

Middle: the map or image with detected objects

Right: AI chat that explains results in plain language

Bottom: analytics (counts, trends, changes)

Why it’s useful

Automates image analysis → saves time

Tracks changes over time (not just “what’s there now”)

Shows results visually on a map with coordinates

Explains findings in numbers + plain language

Main Use Cases

Urban planning – monitor city growth

Agriculture – track farmland, crops, deforestation

Disaster response – compare “before vs after” damage

Security monitoring – detect new construction or unusual changes

AI Answering Rules

Keep answers concise and in plain language.

Stay on topic → Only answer questions about satellite images, space, or drones. Ignore unrelated questions.

If data is missing (e.g., no counts or classes available), clearly say so and suggest running detection again.

Always try to provide useful insight, even with limited data.

No raw URLs or machine-style IDs — always use human-friendly descriptions.
"""

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


class Request(BaseModel):
    messages: List[ClientMessage]


available_tools = {
    "get_current_weather": get_current_weather,
}

def do_stream(messages: List[ChatCompletionMessageParam]):
    stream = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True,
        tools=[{
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather at a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "The latitude of the location",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "The longitude of the location",
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
        }]
    )

    return stream

def stream_text(messages: List[ChatCompletionMessageParam], protocol: str = 'data'):
    draft_tool_calls = []
    draft_tool_calls_index = -1

    stream = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True,
        tools=[{
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather at a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "The latitude of the location",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "The longitude of the location",
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
        }]
    )

    for chunk in stream:
        for choice in chunk.choices:
            if choice.finish_reason == "stop":
                continue

            elif choice.finish_reason == "tool_calls":
                for tool_call in draft_tool_calls:
                    yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                        id=tool_call["id"],
                        name=tool_call["name"],
                        args=tool_call["arguments"])

                for tool_call in draft_tool_calls:
                    tool_result = available_tools[tool_call["name"]](
                        **json.loads(tool_call["arguments"]))

                    yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                        id=tool_call["id"],
                        name=tool_call["name"],
                        args=tool_call["arguments"],
                        result=json.dumps(tool_result))

            elif choice.delta.tool_calls:
                for tool_call in choice.delta.tool_calls:
                    id = tool_call.id
                    name = tool_call.function.name
                    arguments = tool_call.function.arguments

                    if (id is not None):
                        draft_tool_calls_index += 1
                        draft_tool_calls.append(
                            {"id": id, "name": name, "arguments": ""})

                    else:
                        draft_tool_calls[draft_tool_calls_index]["arguments"] += arguments

            else:
                yield '0:{text}\n'.format(text=json.dumps(choice.delta.content))

        if chunk.choices == []:
            usage = chunk.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens

            yield 'e:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}},"isContinued":false}}\n'.format(
                reason="tool-calls" if len(
                    draft_tool_calls) > 0 else "stop",
                prompt=prompt_tokens,
                completion=completion_tokens
            )



@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.post("/api/chat")
async def handle_chat_data(request: Request, protocol: str = Query('data')):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)

    # Prepend hidden system prompt context if available
    if SYSTEM_PROMPT:
        openai_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *openai_messages,
        ]

    response = StreamingResponse(stream_text(openai_messages, protocol))
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    return response

# Include detection router under /api and initialize on startup
app.include_router(detect_router, prefix="/api")

@app.on_event("startup")
async def _init_modules():
    init_detect(app)
