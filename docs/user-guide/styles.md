# Formatting Styles

## Available Styles

### Neutral

Raw Whisper output, no AI formatting.

```bash
shh --style neutral
```

**Example:**
> Um, so like, I think we should probably update the database schema, you know, to improve performance and stuff.

### Casual

Removes filler words, conversational tone.

```bash
shh --style casual
```

**Example:**
> I think we should update the database schema to improve performance.

### Business

Professional, polished output.

```bash
shh --style business
```

**Example:**
> I recommend updating the database schema to improve performance and data integrity. This will provide measurable benefits to system efficiency.

## Comparison

| Feature | Neutral | Casual | Business |
|---------|---------|--------|----------|
| Filler words | Kept | Removed | Removed |
| Tone | Verbatim | Conversational | Professional |
| Structure | Original | Light cleanup | Polished |
| API calls | 1 (Whisper) | 2 (Whisper + GPT) | 2 (Whisper + GPT) |

## With Translation

Styles work with translation - formatting applied after translation:

```bash
shh --style casual --translate French
shh --style business --translate English
```

## Set Default

```bash
shh config set default_style casual
```
