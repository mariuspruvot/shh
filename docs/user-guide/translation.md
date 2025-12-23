# Translation

shh can transcribe audio in one language and translate it to another, all in a single command.

## Basic Usage

Use the `--translate` flag with your target language:

```bash
# Transcribe French audio and translate to English
shh --translate English

# Transcribe English audio and translate to Spanish
shh --translate Spanish
```

## Default Translation Language

Set a default translation language to avoid typing `--translate` every time:

```bash
# Set default translation language
shh config set default_translation_language English

# Now all recordings auto-translate to English
shh

# Override default when needed
shh --translate French
```

This is useful when you frequently translate to the same language.

## Supported Languages

You can translate to **any language supported by OpenAI's GPT models**. Common examples:

- English
- Spanish (Español)
- French (Français)
- German (Deutsch)
- Italian (Italiano)
- Portuguese (Português)
- Chinese (中文)
- Japanese (日本語)
- Korean (한국어)
- Arabic (العربية)
- Russian (Русский)
- Hindi (हिन्दी)

And many more. Just specify the language name in English.

## How It Works

1. **Whisper API** transcribes the audio (in original language)
2. **PydanticAI** translates the transcription to target language
3. Result appears in terminal and clipboard

!!! note "Language Detection"
    Whisper automatically detects the source language. You don't need to specify it - just provide the target language for translation.

## Combining with Styles

Translation works seamlessly with formatting styles:

```bash
# Casual translation
shh --style casual --translate French

# Business translation
shh --style business --translate English
```

The order of operations:

1. Transcribe (Whisper)
2. Translate (if `--translate` specified)
3. Format (if `--style` is not neutral)

This ensures natural phrasing in the target language.

## Examples

### Meeting Notes (French → English)

Record a French meeting and get English business-formatted notes:

```bash
shh --style business --translate English
```

### Voice Memo (English → Spanish)

Quick personal note translated to Spanish:

```bash
shh --style casual --translate Spanish
```

### Interview Transcription (Chinese → English)

Transcribe a Chinese interview to English:

```bash
shh --translate English
```

## Language Names

You can use various forms of language names:

```bash
# These all work
shh --translate English
shh --translate french
shh --translate Español
shh --translate 中文
```

The AI model understands common language names in multiple forms.

## Quality and Accuracy

### Whisper Transcription

Whisper supports 90+ languages with high accuracy. Some languages perform better than others:

- **Excellent**: English, Spanish, French, German, Italian, Portuguese
- **Good**: Chinese, Japanese, Korean, Russian, Arabic, Hindi
- **Varying**: Less common languages (quality depends on audio)

### Translation Quality

Translation uses OpenAI's `gpt-4o-mini`, which provides:

- Contextually aware translations
- Natural phrasing in target language
- Preservation of meaning and tone
- Handling of idioms and cultural context

## Best Practices

### Clear Audio

Translation quality depends on transcription accuracy. Ensure:

- Minimal background noise
- Clear pronunciation
- Good microphone placement

### Specify Style

Combining styles with translation produces better results:

```bash
# ✅ Good - clear intent
shh --style business --translate English

# ⚠️ Acceptable - but less polished
shh --translate English
```

### Review Output

AI translation is good but not perfect. Review important translations:

- Technical terms may need correction
- Cultural context might be lost
- Idioms may not translate directly

## Common Use Cases

### Multilingual Teams

Team members speak different languages:

```bash
# French speaker recording notes for English team
shh --style business --translate English
```

### Learning Languages

Practice speaking and get translations:

```bash
# Practice Spanish, get English translation to check understanding
shh --translate English
```

### Content Creation

Transcribe and translate interviews, podcasts, or videos:

```bash
# Transcribe Japanese podcast to English
shh --translate English
```

### Travel Notes

Quick voice notes while traveling, translated to your native language:

```bash
# Record in local language, translate to English
shh --translate English
```

## Technical Details

### API Calls

Translation requires **two** API calls:

1. Whisper API for transcription
2. GPT-4o-mini API for translation

**Cost**: Slightly higher than transcription alone, but still cost-effective with `gpt-4o-mini`.

### Language Detection

Whisper automatically detects the source language. If you need to know what language was detected, check the Whisper API response (not currently exposed in CLI, but available in the code).

### Privacy

Both Whisper and GPT API calls are processed by OpenAI. Audio and transcriptions are sent to OpenAI servers. Review [OpenAI's privacy policy](https://openai.com/policies/privacy-policy) if privacy is a concern.

## Troubleshooting

### Translation Not Working

If translation fails:

1. Check your API key has GPT access
2. Verify the language name is correct
3. Ensure you have sufficient API credits

### Poor Translation Quality

If translations are inaccurate:

- Check the source transcription for errors
- Use `--style` flag for better context
- Ensure clear audio quality
- Try rephrasing if speaking

### Wrong Language Detected

If Whisper detects the wrong source language:

- Speak more clearly
- Reduce background noise
- Ensure sufficient audio duration

## Next Steps

- [Formatting styles explained](styles.md)
- [Configuration options](configuration.md)
- [All commands reference](commands.md)
