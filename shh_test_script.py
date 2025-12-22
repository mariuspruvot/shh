import asyncio

from shh.adapters.audio.processor import save_audio_to_wav
from shh.adapters.audio.recorder import AudioRecorder
from shh.adapters.llm.formatter import format_transcription
from shh.adapters.whisper.client import transcribe_audio
from shh.config.settings import Settings
from shh.core.styles import TranscriptionStyle


async def main() -> None:
    """Test the full pipeline: Record → Transcribe → Format."""
    print("🎤 Recording for 5 seconds... Speak now!")
    print("-" * 50)

    # Load settings
    settings = Settings.load_from_file() or Settings()
    if not settings.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found! Set SHH_OPENAI_API_KEY in .env")
        return

    # Step 1: Record audio
    async with AudioRecorder() as recorder:
        await asyncio.sleep(5)  # Record for 5 seconds
        audio_data = recorder.get_audio()

    try:
        # Step 2: Save to WAV
        audio_file_path = save_audio_to_wav(audio_data)

        # Step 3: Transcribe with Whisper
        print("\n📝 Transcribing with Whisper...")
        raw_transcription = await transcribe_audio(
            audio_file_path=audio_file_path, api_key=settings.openai_api_key
        )
        print(f"\n✅ Raw transcription:\n{raw_transcription}")

        # Step 4: Test formatting styles
        print("\n" + "=" * 50)
        print("🎨 Testing formatting styles...")
        print("=" * 50)

        # Test 1: Neutral (no formatting)
        print("\n1️⃣  NEUTRAL (no LLM call):")
        neutral = await format_transcription(
            raw_transcription,
            style=TranscriptionStyle.NEUTRAL,
            api_key=settings.openai_api_key,
        )
        print(f"   {neutral.text}")

        # Test 2: Casual style
        print("\n2️⃣  CASUAL:")
        casual = await format_transcription(
            raw_transcription,
            style=TranscriptionStyle.CASUAL,
            api_key=settings.openai_api_key,
        )
        print(f"   {casual.text}")

        # Test 3: Business style
        print("\n3️⃣  BUSINESS:")
        business = await format_transcription(
            raw_transcription,
            style=TranscriptionStyle.BUSINESS,
            api_key=settings.openai_api_key,
        )
        print(f"   {business.text}")

        # Test 4: Translation (casual + translate to English)
        print("\n4️⃣  CASUAL + TRANSLATE TO ENGLISH:")
        translated = await format_transcription(
            raw_transcription,
            style=TranscriptionStyle.CASUAL,
            api_key=settings.openai_api_key,
            target_language="English",
        )
        print(f"   {translated.text}")

        print("\n" + "=" * 50)
        print("✅ All tests complete!")
        print("=" * 50)

    finally:
        # Cleanup
        audio_file_path.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(main())
