# Formatting Styles

shh can format your transcriptions using AI to match different contexts. Choose a style based on how you plan to use the transcription.

## Available Styles

### Neutral

**Best for:** Accuracy, raw data, archival

Neutral style returns the transcription exactly as Whisper outputs it, with no AI formatting applied. This is the fastest option and preserves the original phrasing.

**When to use:**

- You need verbatim transcriptions
- You'll edit the text yourself
- You want to minimize API costs (no GPT call)
- Accuracy matters more than readability

**Example:**

```bash
shh --style neutral
```

**Input (spoken):**
> Um, so like, I think we should probably update the database schema, you know, to improve performance and stuff.

**Output:**
> Um, so like, I think we should probably update the database schema, you know, to improve performance and stuff.

---

### Casual

**Best for:** Quick notes, personal use, conversational context

Casual style removes filler words and smooths out the transcription while maintaining a conversational tone. It's like how you'd text a colleague.

**When to use:**

- Taking quick notes or voice memos
- Internal team communication
- Personal documentation
- You want readability without formality

**Example:**

```bash
shh --style casual
```

**Input (spoken):**
> Um, so like, I think we should probably update the database schema, you know, to improve performance and stuff.

**Output:**
> I think we should update the database schema to improve performance.

**What it does:**

- Removes filler words (um, uh, like, you know)
- Fixes minor grammatical issues
- Maintains conversational tone
- Keeps it concise but friendly

---

### Business

**Best for:** Professional documentation, formal communication, presentations

Business style transforms your transcription into polished, professional text suitable for formal contexts. It adds structure and clarity.

**When to use:**

- Meeting minutes or reports
- Documentation for stakeholders
- Professional emails or messages
- Presentations or proposals

**Example:**

```bash
shh --style business
```

**Input (spoken):**
> Um, so like, I think we should probably update the database schema, you know, to improve performance and stuff.

**Output:**
> I recommend updating the database schema to improve performance and data integrity. This will provide measurable benefits to system efficiency.

**What it does:**

- Removes all filler words
- Restructures sentences for clarity
- Uses professional vocabulary
- Adds context and structure
- May expand on ideas for completeness

---

## Setting a Default Style

If you always use the same style, set it as your default:

```bash
# Set casual as default
shh config set default_style casual

# Now 'shh' automatically uses casual formatting
shh
```

Override the default anytime with the `--style` flag:

```bash
# Even with casual as default, use business for this recording
shh --style business
```

## Style Comparison

| Feature | Neutral | Casual | Business |
|---------|---------|--------|----------|
| Filler words | Kept | Removed | Removed |
| Tone | Verbatim | Conversational | Professional |
| Structure | Original | Light cleanup | Polished |
| Speed | Fastest | Fast | Slower |
| API calls | 1 (Whisper) | 2 (Whisper + GPT) | 2 (Whisper + GPT) |
| Cost | Lowest | Medium | Medium |

## Combined with Translation

Styles work seamlessly with translation:

```bash
# Casual French transcription
shh --style casual --translate French

# Business English transcription from French audio
shh --style business --translate English
```

The formatting is applied **after** translation, ensuring natural phrasing in the target language.

## Technical Details

### How It Works

1. **Neutral**: Whisper API only → Direct output
2. **Casual/Business**: Whisper API → PydanticAI agent → Formatted output

### AI Model

Formatting uses OpenAI's `gpt-4o-mini` model for cost-effective, high-quality results. This is separate from the Whisper API call.

### Prompts

The formatting agent receives context about the desired style and applies transformations accordingly. Prompts are optimized for:

- Preserving meaning and intent
- Removing only true filler words (not meaningful pauses)
- Maintaining speaker's voice in casual mode
- Professional polish in business mode

### Privacy

Both Whisper and GPT API calls are processed by OpenAI. If privacy is a concern:

- Use `--style neutral` (Whisper only)
- Consider self-hosted alternatives
- Review [OpenAI's privacy policy](https://openai.com/policies/privacy-policy)

## Best Practices

### For Voice Memos

Use **casual** style - it cleans up your thoughts without over-formalizing them.

```bash
shh config set default_style casual
```

### For Meetings

Use **business** style - creates professional documentation ready to share.

```bash
shh --style business
```

### For Transcription Archives

Use **neutral** style - preserves exact phrasing for future reference.

```bash
shh --style neutral
```

### Cost Optimization

If you're watching API costs:

- Use `neutral` for drafts, then manually edit
- Use `casual/business` only for final versions
- Set `neutral` as default, override when needed

## Next Steps

- [Translation guide](translation.md)
- [Configuration options](configuration.md)
- [All commands reference](commands.md)
