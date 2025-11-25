"""
Prompt templates for video transcript summarization.

Usage:
    from prompts import SUMMARY_PROMPT, SummaryResponse

    prompt = SUMMARY_PROMPT.format(transcript=transcript_text)
    response = client.messages.create(...)
    summary = SummaryResponse.model_validate_json(response.content[0].text)
"""

from textwrap import dedent

from pydantic import BaseModel

# --------------------------------------------------------------------------
# Response Models
# --------------------------------------------------------------------------


class Concept(BaseModel):
    term: str
    definition: str


class SummaryResponse(BaseModel):
    """Structured summary response from Claude."""

    headline: str
    key_points: list[str]
    concepts: list[Concept]
    narrative: list[str]  # List of paragraphs


# --------------------------------------------------------------------------
# System Prompt
# --------------------------------------------------------------------------

SUMMARY_SYSTEM_PROMPT = dedent("""\
    You are an expert at distilling video content into clear, structured summaries.
    You extract the core thesis, key insights, and important terminology while
    preserving the logical flow of the original content. You write in clear,
    direct prose without filler or redundancy.""")


# --------------------------------------------------------------------------
# Summary Prompt Template
# --------------------------------------------------------------------------

SUMMARY_PROMPT = dedent("""\
    Analyze this video transcript and produce a structured summary.

    Return a JSON object with exactly these fields:

    {{
      "headline": "One sentence capturing the core thesis or main argument (max 200 chars)",

      "key_points": [
        "3-5 key takeaways, each one sentence, capturing actionable insights or important claims"
      ],

      "concepts": [
        {{"term": "Important Term", "definition": "Brief explanation (1-2 sentences)"}}
      ],

      "narrative": [
        "First paragraph: Context and main argument",
        "Second paragraph: Supporting evidence or elaboration",
        "Third paragraph: Conclusions or implications"
      ]
    }}

    Guidelines:
    - headline: The single most important point. If someone reads nothing else, this is it.
    - key_points:
        - Concrete takeaways, not vague observations.
        - "X does Y because Z" not "The video discusses X"
    - concepts:
        - Only include terms that are central to understanding the content.
        - Skip obvious terms.
    - narrative:
        - 2-4 paragraphs that flow naturally.
        - Capture the arc of the argument, not a list of topics.

    Return ONLY the JSON object, no markdown code blocks or other text.

    Transcript:
    {transcript}""")


# --------------------------------------------------------------------------
# Alternative Templates (for future use)
# --------------------------------------------------------------------------

SOCRATIC_SYSTEM_PROMPT = dedent("""\
    You transform educational content into engaging Socratic dialogues between
    TEACHER and STUDENT. The teacher synthesizes and explains with clarity and
    appropriate analogies. The student asks questions a viewer might have and
    occasionally summarizes understanding to reinforce key points.""")

SOCRATIC_PROMPT = dedent("""\
    Transform this transcript into a Socratic dialogue between TEACHER and STUDENT.

    Format each turn as:
    TEACHER: [dialogue]
    STUDENT: [dialogue]

    Guidelines:
    - TEACHER explains concepts, uses analogies, asks probing questions
    - STUDENT asks clarifying questions, voices likely confusions, summarizes understanding
    - Preserve all substantive information from the source
    - Each turn should be 2-4 sentences (optimized for text-to-speech)
    - End with a synthesis that reinforces main takeaways
    - Aim for 15-25 exchanges total

    Transcript:
    {transcript}""")


BULLET_SUMMARY_PROMPT = dedent("""\
    Create a concise bullet-point summary of this transcript.

    Return a JSON object:
    {{
      "title": "Descriptive title for the content",
      "bullets": [
        "Key point 1",
        "Key point 2"
      ],
      "one_liner": "Single sentence summary"
    }}

    Keep bullets to 8-12 items max. Each bullet should be self-contained.
    Return ONLY the JSON object.

    Transcript:
    {transcript}""")
