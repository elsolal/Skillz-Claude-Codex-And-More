---
name: remotion
description: "Remotion — video creation in React. Best practices, rendering, animations, audio sync, and ElevenLabs voiceover pipeline. Use when creating videos programmatically, building motion graphics, animating React components to video, working with Remotion compositions, or when the user mentions Remotion, video generation, motion design, animation to video, React video, programmatic video, voiceover sync."
---

# Remotion — Video Creation in React

Create programmatic videos with React components. This skill covers best practices, rendering, and the full ElevenLabs → Remotion voiceover pipeline.

## Rule Files (Load on Demand)

Read individual rule files for detailed explanations and code examples. Load them based on what you're building:

### Core Concepts
- [rules/compositions.md](rules/compositions.md) — Compositions, stills, folders, default props, dynamic metadata
- [rules/animations.md](rules/animations.md) — Fundamental animation patterns (useCurrentFrame, interpolate)
- [rules/timing.md](rules/timing.md) — Interpolation curves: linear, easing, spring animations
- [rules/sequencing.md](rules/sequencing.md) — Delay, trim, limit duration of items
- [rules/transitions.md](rules/transitions.md) — Scene transition patterns
- [rules/parameters.md](rules/parameters.md) — Make videos parametrizable with Zod schemas
- [rules/calculate-metadata.md](rules/calculate-metadata.md) — Dynamically set composition duration, dimensions, props

### Visual Elements
- [rules/text-animations.md](rules/text-animations.md) — Typography and text animation patterns
- [rules/images.md](rules/images.md) — Embedding images with the Img component
- [rules/videos.md](rules/videos.md) — Embedding videos: trimming, volume, speed, looping
- [rules/gifs.md](rules/gifs.md) — GIFs synchronized with timeline
- [rules/charts.md](rules/charts.md) — Bar, pie, line, stock chart patterns
- [rules/maps.md](rules/maps.md) — Mapbox maps with animation
- [rules/lottie.md](rules/lottie.md) — Lottie animations in Remotion
- [rules/3d.md](rules/3d.md) — 3D content with Three.js / React Three Fiber
- [rules/light-leaks.md](rules/light-leaks.md) — Light leak overlay effects

### Audio & Voice
- [rules/audio.md](rules/audio.md) — Audio: importing, trimming, volume, speed, pitch
- [rules/voiceover.md](rules/voiceover.md) — **ElevenLabs TTS → Remotion pipeline** (key file for voice sync)
- [rules/audio-visualization.md](rules/audio-visualization.md) — Spectrum bars, waveforms, bass-reactive effects
- [rules/sfx.md](rules/sfx.md) — Sound effects in Remotion
- [rules/subtitles.md](rules/subtitles.md) — Captions and subtitle rendering
- [rules/display-captions.md](rules/display-captions.md) — Displaying caption overlays
- [rules/import-srt-captions.md](rules/import-srt-captions.md) — Importing SRT caption files
- [rules/transcribe-captions.md](rules/transcribe-captions.md) — Transcribing audio to captions

### Assets & Fonts
- [rules/assets.md](rules/assets.md) — Importing images, videos, audio, fonts
- [rules/fonts.md](rules/fonts.md) — Google Fonts and local fonts
- [rules/tailwind.md](rules/tailwind.md) — TailwindCSS in Remotion

### Media Processing
- [rules/ffmpeg.md](rules/ffmpeg.md) — FFmpeg for trimming, silence detection
- [rules/trimming.md](rules/trimming.md) — Cutting beginning/end of animations
- [rules/transparent-videos.md](rules/transparent-videos.md) — Rendering with transparency
- [rules/extract-frames.md](rules/extract-frames.md) — Extract frames from videos
- [rules/get-audio-duration.md](rules/get-audio-duration.md) — Get audio duration in seconds
- [rules/get-video-duration.md](rules/get-video-duration.md) — Get video duration in seconds
- [rules/get-video-dimensions.md](rules/get-video-dimensions.md) — Get video width/height
- [rules/can-decode.md](rules/can-decode.md) — Check if a video can be decoded
- [rules/measuring-dom-nodes.md](rules/measuring-dom-nodes.md) — Measure DOM element dimensions
- [rules/measuring-text.md](rules/measuring-text.md) — Measure text dimensions, fit text to containers

## ElevenLabs → Remotion Pipeline

The most common workflow: generate voice audio with ElevenLabs, then sync it with Remotion visuals.

### Step 1: Generate Audio (see `elevenlabs` skill)

```typescript
// generate-voiceover.ts
const response = await fetch(
  `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
  {
    method: "POST",
    headers: {
      "xi-api-key": process.env.ELEVENLABS_API_KEY!,
      "Content-Type": "application/json",
      Accept: "audio/mpeg",
    },
    body: JSON.stringify({
      text: "Welcome to the show.",
      model_id: "eleven_multilingual_v2",
      voice_settings: { stability: 0.5, similarity_boost: 0.75, style: 0.3 },
    }),
  }
);
const audioBuffer = Buffer.from(await response.arrayBuffer());
writeFileSync("public/voiceover/scene-01.mp3", audioBuffer);
```

### Step 2: Dynamic Duration with calculateMetadata

```tsx
import { CalculateMetadataFunction, staticFile } from "remotion";
import { getAudioDuration } from "./get-audio-duration";

const FPS = 30;
const SCENE_FILES = [
  "voiceover/scene-01-intro.mp3",
  "voiceover/scene-02-main.mp3",
  "voiceover/scene-03-outro.mp3",
];

export const calculateMetadata: CalculateMetadataFunction<Props> = async () => {
  const durations = await Promise.all(
    SCENE_FILES.map((file) => getAudioDuration(staticFile(file)))
  );
  const totalFrames = durations.reduce((sum, d) => sum + d * FPS, 0);
  return { durationInFrames: Math.ceil(totalFrames) };
};
```

### Step 3: Render

```bash
npx remotion render src/index.ts MyComposition out/video.mp4
```

For details, load [rules/voiceover.md](rules/voiceover.md).

## Cloud Rendering (inference.sh)

Render videos without local setup via inference.sh CLI:

```bash
infsh app run infsh/remotion-render --input '{
  "code": "import { useCurrentFrame, AbsoluteFill, interpolate } from \"remotion\"; export default function Main() { const frame = useCurrentFrame(); const opacity = interpolate(frame, [0, 30], [0, 1]); return <AbsoluteFill style={{backgroundColor: \"#1a1a2e\", display: \"flex\", justifyContent: \"center\", alignItems: \"center\"}}><h1 style={{color: \"#eee\", fontSize: 80, opacity}}>Hello</h1></AbsoluteFill>; }",
  "duration_seconds": 3,
  "fps": 30,
  "width": 1920,
  "height": 1080
}'
```

### Input Schema

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | React/TSX component (must export default) |
| `composition_id` | string | No | Composition ID to render |
| `props` | object | No | Props passed to the component |
| `width` | number | No | Video width (default 1920) |
| `height` | number | No | Video height (default 1080) |
| `fps` | number | No | Frames per second (default 30) |
| `duration_seconds` | number | No | Duration in seconds |
| `codec` | string | No | Output codec |

### Available Imports in Cloud Rendering

```tsx
import {
  useCurrentFrame, useVideoConfig,
  spring, interpolate,
  AbsoluteFill, Sequence, Audio, Video, Img
} from "remotion";
import React, { useState, useEffect } from "react";
```

## Key Patterns

### Basic Animation

```tsx
import { useCurrentFrame, interpolate, AbsoluteFill } from "remotion";

export const MyComp: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1]);
  const translateY = interpolate(frame, [0, 30], [50, 0]);

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <h1 style={{ opacity, transform: `translateY(${translateY}px)` }}>
        Hello World
      </h1>
    </AbsoluteFill>
  );
};
```

### Spring Animation

```tsx
import { useCurrentFrame, useVideoConfig, spring } from "remotion";

const frame = useCurrentFrame();
const { fps } = useVideoConfig();
const scale = spring({ frame, fps, config: { damping: 10, stiffness: 100 } });
```

### Sequencing Scenes

```tsx
import { Sequence } from "remotion";

<Sequence from={0} durationInFrames={90}>
  <IntroScene />
</Sequence>
<Sequence from={90} durationInFrames={150}>
  <MainScene />
</Sequence>
<Sequence from={240}>
  <OutroScene />
</Sequence>
```

## Project Setup

```bash
npx create-video@latest my-video
cd my-video
npm start              # Preview in browser
npx remotion render src/index.ts MyComp out/video.mp4
```

## Related Skills

- **elevenlabs** — Voice generation for the audio pipeline
- **figma-implement-design** — Turn Figma mockups into Remotion components
