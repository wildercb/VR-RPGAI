# TTS Voice Customization Guide

## Overview

Your RPGAI system uses **Piper TTS** for voice synthesis. This guide explains how to customize and change voices.

## Quick Start: Change the Voice

### Step 1: Choose a Voice

Browse available voices with audio samples:
- **Voice Samples**: https://rhasspy.github.io/piper-samples/
- **Voice Models**: https://huggingface.co/rhasspy/piper-voices

### Step 2: Update docker-compose.yml

Edit the `command` line in the piper service:

```yaml
piper:
  image: rhasspy/wyoming-piper:latest
  command: --voice en_US-danny-low  # Change this line
```

### Step 3: Restart Piper

```bash
docker-compose restart piper
```

That's it! All new TTS audio will use the new voice.

---

## Popular Voice Options

### American English Voices

**Female Voices:**
- `en_US-lessac-medium` (default - clear, professional)
- `en_US-amy-medium` (warm, friendly)
- `en_US-kristin-medium` (expressive)
- `en_US-kimberly-low` (soft, gentle)

**Male Voices:**
- `en_US-danny-low` (deep, clear)
- `en_US-joe-medium` (neutral, professional)
- `en_US-bryce-medium` (energetic)
- `en_US-ryan-medium` (smooth)

**Multi-Speaker:**
- `en_US-libritts_r-medium` (variety of speakers)
- `en_US-hfc_female-medium` (multiple female voices)
- `en_US-hfc_male-medium` (multiple male voices)

### British English Voices

- `en_GB-alan-medium` (British male)
- `en_GB-alba-medium` (British female)
- `en_GB-jenny_dioco-medium` (British female)
- `en_GB-northern_english_male-medium` (Northern English)
- `en_GB-southern_english_female-low` (Southern English)

### Quality Levels

- **low** - Fastest, smallest models (~10MB)
- **medium** - Good balance (~20MB) - **recommended**
- **high** - Best quality, larger models (~50MB+)

---

## Example: Switching to a Male Voice

Let's switch from the default female voice to a male voice:

### 1. Edit docker-compose.yml

```yaml
piper:
  image: rhasspy/wyoming-piper:latest
  container_name: rpgai-piper
  ports:
    - "10200:10200"
  volumes:
    - piper_data:/data
  command: --voice en_US-danny-low  # Changed to male voice
  restart: unless-stopped
```

### 2. Restart Piper

```bash
docker-compose restart piper
```

### 3. Test the New Voice

```bash
# Clear the audio cache to force regeneration
rm -rf audio_cache/*

# Test in the UI
# Go to http://localhost:4020
# Click "🔊 Test TTS Now" button
# You'll hear the new male voice!
```

---

## Advanced: Per-Character Voices (Future Enhancement)

Currently, Piper uses **one voice per server instance**. To have different voices per character, you would need to:

### Option 1: Multiple Piper Instances (Advanced)

Run multiple Piper containers on different ports:

```yaml
# docker-compose.yml
piper-male:
  image: rhasspy/wyoming-piper:latest
  container_name: rpgai-piper-male
  ports:
    - "10201:10200"
  volumes:
    - piper_male_data:/data
  command: --voice en_US-danny-low

piper-female:
  image: rhasspy/wyoming-piper:latest
  container_name: rpgai-piper-female
  ports:
    - "10202:10200"
  volumes:
    - piper_female_data:/data
  command: --voice en_US-amy-medium

volumes:
  piper_male_data:
  piper_female_data:
```

Then modify the backend to select the appropriate Piper instance based on character preferences.

### Option 2: Multi-Speaker Models (Current Solution)

Use a multi-speaker voice model like `en_US-libritts_r-medium` which contains multiple voice styles in one model. This is the simplest approach for voice variety.

---

## Voice Model Files

Piper downloads voice models on first use and caches them in the Docker volume.

### Model Location (inside container)
```
/data/voices/
```

### Model Files
Each voice consists of two files:
- `{voice}.onnx` - Neural network model
- `{voice}.onnx.json` - Model configuration

### Clearing Voice Cache

If you want to force re-download of voice models:

```bash
docker-compose down piper
docker volume rm rpgai_piper_data
docker-compose up -d piper
```

---

## Troubleshooting

### Voice Doesn't Change

**Problem**: Restarted Piper but still hearing the old voice.

**Solution**: Clear the audio cache:
```bash
rm -rf /Users/wilder/dev/RPGAI/audio_cache/*
```

The audio cache stores generated speech, so old audio will be reused until you clear it.

### Voice Download Fails

**Problem**: Piper can't download the voice model.

**Solution**: Check the logs:
```bash
docker-compose logs piper --tail 50
```

Make sure the voice name is correct. Check available voices at:
https://huggingface.co/rhasspy/piper-voices/tree/main

### Low Quality Voice

**Problem**: Voice sounds robotic or unclear.

**Solution**: Switch to a `medium` or `high` quality version:
```yaml
# Instead of:
command: --voice en_US-danny-low

# Use:
command: --voice en_US-danny-medium
```

---

## Voice Examples by Use Case

### For a Wise Wizard Character
```yaml
command: --voice en_GB-alan-medium
# Deep British male voice - perfect for wizards!
```

### For a Young Female NPC
```yaml
command: --voice en_US-amy-medium
# Warm, friendly female voice
```

### For a Gruff Guard
```yaml
command: --voice en_US-danny-low
# Deep male voice
```

### For a Merchant
```yaml
command: --voice en_US-joe-medium
# Neutral, professional voice
```

### For Variety (Multiple Characters)
```yaml
command: --voice en_US-libritts_r-medium
# Contains multiple speaker styles
```

---

## Testing Different Voices

### Quick Test Script

Create a test script to try different voices:

```bash
#!/bin/bash
# test_voices.sh

VOICES=(
  "en_US-lessac-medium"
  "en_US-danny-low"
  "en_US-amy-medium"
  "en_GB-alan-medium"
)

for voice in "${VOICES[@]}"; do
  echo "Testing voice: $voice"

  # Update docker-compose.yml
  sed -i '' "s/--voice .*/--voice $voice/" docker-compose.yml

  # Restart Piper
  docker-compose restart piper
  sleep 5

  # Clear cache
  rm -rf audio_cache/*

  # Test (open browser to test)
  echo "Voice ready: $voice"
  echo "Press Enter to test next voice..."
  read
done
```

---

## Performance Considerations

### Model Size vs Quality

| Quality | Size | Speed | Use Case |
|---------|------|-------|----------|
| low | ~10MB | Fastest | Mobile, real-time |
| medium | ~20MB | Fast | **Recommended** |
| high | ~50MB+ | Slower | Best quality |

### Recommended Settings

For most use cases, use **medium** quality:
- Good balance of quality and speed
- Fast enough for real-time chat
- Clear, natural-sounding voices

---

## Voice Resources

- **Voice Samples**: https://rhasspy.github.io/piper-samples/
- **Voice Models**: https://huggingface.co/rhasspy/piper-voices
- **Piper GitHub**: https://github.com/rhasspy/piper
- **Voice Quality Comparison**: https://github.com/rhasspy/piper/discussions/430

---

## Summary

**To change voices:**
1. Edit `docker-compose.yml` - change the `--voice` parameter
2. Run `docker-compose restart piper`
3. Clear audio cache: `rm -rf audio_cache/*`
4. Test in the UI with "🔊 Test TTS Now"

**Current voice**: `en_US-lessac-medium` (clear female voice)

**Try this next**: `en_US-danny-low` (deep male voice) or `en_GB-alan-medium` (British male)
