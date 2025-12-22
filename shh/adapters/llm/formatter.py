from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from shh.core.styles import TranscriptionStyle
from shh.utils.exceptions import FormattingError
from shh.utils.logger import logger


class FormattedTranscription(BaseModel):
    """Structured output from LLM formatting."""

    text: str = Field(..., description="The formatted transcription text.")


# System prompts for each formatting style
STYLE_PROMPTS = {
    TranscriptionStyle.CASUAL: """
You are a helpful assistant that formats voice transcriptions in a casual, conversational style.

Your task:
- Automatically detect the language of the input text
- Preserve the original language UNLESS a target language is specified
- Remove filler words (um, uh, like, you know, euh, ben, etc.)
- Fix grammar naturally without being overly formal
- Keep the friendly, conversational tone
- Use contractions where appropriate in the target language
- Keep it readable and natural

If a target language is specified:
- Translate the text to that language while applying the casual style
- Ensure the translation sounds natural in the target language

Do NOT add information that wasn't in the original transcription.
Just clean it up and make it flow naturally.
""".strip(),
    TranscriptionStyle.BUSINESS: """
You are a professional editor that formats voice transcriptions for business communication.

Your task:
- Automatically detect the language of the input text
- Preserve the original language UNLESS a target language is specified
- Remove all filler words and false starts
- Use formal, professional language
- Organize into clear paragraphs where appropriate
- Use complete sentences with proper grammar
- Avoid contractions in formal contexts
- Maintain a professional, polished tone

If a target language is specified:
- Translate the text to that language while maintaining business formality
- Use professional terminology appropriate for the target language

Do NOT add information that wasn't in the original transcription.
Focus on clarity and professionalism.
""".strip(),
}


async def format_transcription(
    text: str,
    style: TranscriptionStyle = TranscriptionStyle.NEUTRAL,
    api_key: str = "",
    target_language: str | None = None,
) -> FormattedTranscription:
    """
    Format the transcription text using an AI agent based on the specified style.

    Args:
        text: Raw transcription text from Whisper
        style: Formatting style to apply (neutral, casual, business)
        api_key: OpenAI API key for LLM calls
        target_language: Optional language to translate to (e.g., "English", "French", "Spanish")

    Returns:
        FormattedTranscription with styled and optionally translated text
    """

    # Handle neutral style - no LLM call needed
    if style == TranscriptionStyle.NEUTRAL and not target_language:
        return FormattedTranscription(text=text)

    # For neutral style with translation, use casual prompt
    system_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS[TranscriptionStyle.CASUAL])

    # Build the user prompt
    user_prompt = f"Format this transcription: {text}"
    if target_language:
        user_prompt = f"Format this transcription and translate it to {target_language}: {text}"

    # Create OpenAI model with API key
    model = OpenAIChatModel("gpt-4o-mini", provider=OpenAIProvider(api_key=api_key))

    # Create PydanticAI agent
    agent: Agent[None, FormattedTranscription] = Agent(
        model,
        output_type=FormattedTranscription,
        system_prompt=system_prompt,
    )

    try:
        result = await agent.run(user_prompt)
        return result.output
    except Exception as e:
        logger.error(f"Formatting failed: {e}")
        raise FormattingError(f"Failed to format transcription: {e}") from e
