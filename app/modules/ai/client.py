from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from app.config import AZURE_AIPROJECT_ENDPOINT, AI_MODEL

_project_client = AIProjectClient(
    endpoint=AZURE_AIPROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)

_client = _project_client.get_openai_client()

MODEL = AI_MODEL

SYSTEM_PROMPT = """You are an expert SOP (Standard Operating Procedure) writer.
Your job is to analyze the provided document and extract a clear, structured SOP from it.

Always respond in this exact structure:

TITLE: <title of the SOP>

OVERVIEW: <one paragraph describing what this SOP covers and who it is for>

STEPS:
1. <Step Title>
   HOW: <detailed explanation of how to perform this step>

2. <Step Title>
   HOW: <detailed explanation of how to perform this step>

(continue for all steps)

Rules:
- Extract only what is in the document. Do not invent steps.
- If an image shows a UI or process, describe what it shows in the relevant step.
- Keep step titles short (5 words max).
- HOW sections should be clear enough for someone doing this for the first time."""


async def generate_sop(content_blocks: list) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_content(content_blocks)},
    ]

    response = _client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=4096,
    )

    raw_text = response.choices[0].message.content
    return _parse_sop(raw_text)


def _build_user_content(content_blocks: list) -> list:
    """Convert extractor blocks into OpenAI-compatible content parts."""
    parts = []
    for block in content_blocks:
        if block["type"] == "text":
            parts.append({"type": "text", "text": block["text"]})
        elif block["type"] == "image":
            src = block["source"]
            parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{src['media_type']};base64,{src['data']}"
                }
            })
        elif block["type"] == "document":
            # PDF sent as base64 — embed as image_url data URI
            src = block["source"]
            parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{src['media_type']};base64,{src['data']}"
                }
            })

    parts.append({"type": "text", "text": "Extract a structured SOP from the above document."})
    return parts


def _parse_sop(raw: str) -> dict:
    sop = {"title": "", "overview": "", "steps": []}
    current_step = None
    current_section = None

    for line in raw.splitlines():
        line = line.strip()

        if line.startswith("TITLE:"):
            sop["title"] = line.removeprefix("TITLE:").strip()

        elif line.startswith("OVERVIEW:"):
            sop["overview"] = line.removeprefix("OVERVIEW:").strip()
            current_section = "overview"

        elif line.startswith("STEPS:"):
            current_section = "steps"

        elif current_section == "overview" and line and not line[0].isdigit():
            sop["overview"] += " " + line

        elif current_section == "steps":
            if line and line[0].isdigit() and "." in line:
                if current_step:
                    sop["steps"].append(current_step)
                title = line.split(".", 1)[1].strip()
                current_step = {"title": title, "how": ""}

            elif line.startswith("HOW:") and current_step:
                current_step["how"] = line.removeprefix("HOW:").strip()

            elif current_step and line and not line.startswith("HOW:"):
                current_step["how"] += " " + line

    if current_step:
        sop["steps"].append(current_step)

    return sop
