# Translation

## Basic Usage

```bash
shh --translate English       # Transcribe and translate to English
shh --translate Spanish
```

## Set Default

```bash
shh config set default_translation_language English
shh                          # Auto-translates to English
shh --translate French       # Override default
```

## Supported Languages

English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, Russian, Hindi, and many more.

## With Formatting

```bash
shh --style casual --translate French
shh --style business --translate English
```

Order: Transcribe → Translate → Format
