---
name: elevenlabs
description: "ElevenLabs voice AI — text-to-speech, music generation, and sound effects. Use when generating voiceovers, creating audio content, building voice features, or when the user mentions ElevenLabs, TTS, voice generation, audio synthesis, AI voice, voiceover, speech, narration, sound effects, or music generation."
---

# ElevenLabs — Voice AI Platform

Generate speech, music, and sound effects via the ElevenLabs API. Supports 70+ languages, 22+ premium voices, and multiple models for different quality/latency tradeoffs.

## Prerequisites

- `ELEVENLABS_API_KEY` environment variable must be set (get it from ElevenLabs dashboard → API Keys)
- For JavaScript: use `@elevenlabs/elevenlabs-js` package only
- For Python: use `elevenlabs` package

## Models

| Model ID | Languages | Latency | Best For |
|----------|-----------|---------|----------|
| `eleven_v3` | 70+ | Standard | Highest quality, emotional range |
| `eleven_multilingual_v2` | 29 | Standard | High quality, long-form content |
| `eleven_flash_v2_5` | 32 | ~75ms | Ultra-low latency, real-time |
| `eleven_turbo_v2_5` | 32 | ~250ms | Balanced quality/speed |

**Default recommendation:** `eleven_multilingual_v2` for production voiceovers, `eleven_flash_v2_5` for real-time/interactive.

## Quick Start

### JavaScript/TypeScript

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { createWriteStream } from "fs";

const client = new ElevenLabsClient();
const audio = await client.textToSpeech.convert("JBFqnCBsd6RMkjVDRZzb", {
  text: "Hello, welcome to ElevenLabs!",
  modelId: "eleven_multilingual_v2",
});
audio.pipe(createWriteStream("output.mp3"));
```

### Python

```python
from elevenlabs import ElevenLabs

client = ElevenLabs()
audio = client.text_to_speech.convert(
    text="Hello, welcome to ElevenLabs!",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2"
)
with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
```

### cURL (batch scripting)

```bash
curl -X POST "https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}" \
  -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!", "model_id": "eleven_multilingual_v2"}' \
  --output output.mp3
```

## Popular Voice IDs

| ID | Name | Style |
|----|------|-------|
| `JBFqnCBsd6RMkjVDRZzb` | George | Male, narrative |
| `EXAVITQu4vr4xnSDxMaL` | Sarah | Female, soft |
| `onwK4e9ZLuTAKqWW03F9` | Daniel | Male, authoritative |
| `XB0fDUnXU5powFXDhCwa` | Charlotte | Female, conversational |

List all available voices:
```python
voices = client.voices.get_all()
for voice in voices.voices:
    print(f"{voice.voice_id}: {voice.name}")
```

## Voice Settings

Fine-tune voice output with these parameters:

| Parameter | Range | Effect |
|-----------|-------|--------|
| `stability` | 0.0–1.0 | Lower = more emotional variation, higher = steady delivery |
| `similarity_boost` | 0.0–1.0 | How closely to match original voice sample |
| `style` | 0.0–1.0 | Exaggerates voice style characteristics (v2+ models only) |
| `speed` | 0.25–4.0 | Playback speed (default 1.0) |
| `use_speaker_boost` | bool | Post-processing for clarity |

```python
from elevenlabs import VoiceSettings

audio = client.text_to_speech.convert(
    text="Customize my voice settings.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    voice_settings=VoiceSettings(
        stability=0.5,
        similarity_boost=0.75,
        style=0.5,
        speed=1.0,
        use_speaker_boost=True
    )
)
```

See [references/voice-settings.md](references/voice-settings.md) for detailed guidance.

## Language Enforcement

Force specific language pronunciation with ISO 639-1 codes:

```python
audio = client.text_to_speech.convert(
    text="Bonjour, comment allez-vous?",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    language_code="fr"
)
```

## Request Stitching (Long Audio)

When generating audio in multiple parts, use `previous_text`/`next_text` to avoid pops and tone shifts at boundaries:

```python
audio1 = client.text_to_speech.convert(
    text="This is the first part.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    next_text="And this continues the story."
)

audio2 = client.text_to_speech.convert(
    text="And this continues the story.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    previous_text="This is the first part."
)
```

## Output Formats

| Format | Description | Use case |
|--------|-------------|----------|
| `mp3_44100_128` | MP3 128kbps (default) | Web, apps |
| `mp3_44100_192` | MP3 192kbps (Creator+) | Higher quality |
| `pcm_44100` | Raw PCM 44.1kHz (Pro+) | CD quality, Remotion input |
| `wav_44100` | WAV uncompressed | Post-production |
| `opus_48000_64` | Opus 48kHz | Efficient streaming |

## Streaming

For real-time applications:

```python
audio_stream = client.text_to_speech.stream(
    text="This text will be streamed as audio.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_flash_v2_5"
)
for chunk in audio_stream:
    play_audio(chunk)
```

See [references/streaming.md](references/streaming.md) for WebSocket streaming.

## Batch Generation (Pipeline Pattern)

For generating multiple audio files from a script (voiceovers, courses, etc.):

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
import { writeFileSync } from "fs";

const client = new ElevenLabsClient();
const scenes = [
  { id: "intro", text: "Welcome to the show." },
  { id: "main", text: "Today we discuss AI." },
  { id: "outro", text: "Thanks for watching!" },
];

for (const scene of scenes) {
  const audio = await client.textToSpeech.convert("JBFqnCBsd6RMkjVDRZzb", {
    text: scene.text,
    modelId: "eleven_multilingual_v2",
  });
  // Collect chunks and write
  const chunks: Buffer[] = [];
  for await (const chunk of audio) chunks.push(Buffer.from(chunk));
  writeFileSync(`public/voiceover/${scene.id}.mp3`, Buffer.concat(chunks));
}
```

This pattern integrates directly with Remotion — see the `remotion` skill for the full ElevenLabs → Remotion pipeline.

## Text Normalization

Controls how numbers, dates, abbreviations are spoken:
- `"auto"` (default): Model decides
- `"on"`: Natural speech ("January fifteenth")
- `"off"`: Literal ("zero one slash one five")

## Tracking Costs

```python
response = client.text_to_speech.convert.with_raw_response(
    text="Hello!", voice_id="JBFqnCBsd6RMkjVDRZzb", model_id="eleven_multilingual_v2"
)
print(f"Characters used: {response.headers.get('x-character-count')}")
```

## Error Handling

| Code | Cause | Fix |
|------|-------|-----|
| 401 | Invalid API key | Check `ELEVENLABS_API_KEY` |
| 422 | Invalid parameters | Verify voice_id, model_id |
| 429 | Rate limit exceeded | Wait and retry |

## Music Generation

Generate original music from text prompts (up to 10 min):

```bash
# Via inference.sh CLI
infsh app run infsh/elevenlabs-music --input '{
  "prompt": "Upbeat electronic music with synths",
  "duration_seconds": 30
}'
```

## Sound Effects

Generate SFX from text descriptions:

```bash
# Via inference.sh CLI
infsh app run infsh/elevenlabs-sound-effects --input '{
  "prompt": "Dramatic thunder crack followed by rain",
  "duration_seconds": 5
}'
```

## References

- [Installation Guide](references/installation.md) — SDK setup for Python, JS, cURL
- [Streaming Audio](references/streaming.md) — WebSocket streaming patterns
- [Voice Settings](references/voice-settings.md) — Detailed parameter tuning guide
