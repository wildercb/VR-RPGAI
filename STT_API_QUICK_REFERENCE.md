# STT API Quick Reference

## 🎯 Endpoint

```
POST http://localhost:4020/api/chat/transcribe
```

## 📝 Quick Examples

### cURL (Terminal)

```bash
# Transcribe an audio file
curl -X POST "http://localhost:4020/api/chat/transcribe" \
  -H "X-User-ID: test_user" \
  -F "audio=@recording.wav"

# Response:
# {"text": "Hello, how are you today?"}
```

### Python

```python
import requests

# Transcribe audio file
with open("recording.wav", "rb") as f:
    response = requests.post(
        "http://localhost:4020/api/chat/transcribe",
        headers={"X-User-ID": "test_user"},
        files={"audio": f}
    )

result = response.json()
print(f"Transcription: {result['text']}")
```

### JavaScript (Browser/Node)

```javascript
// Browser - from file input
const fileInput = document.getElementById('audioFile');
const formData = new FormData();
formData.append('audio', fileInput.files[0]);

const response = await fetch('http://localhost:4020/api/chat/transcribe', {
    method: 'POST',
    headers: {
        'X-User-ID': 'test_user'
    },
    body: formData
});

const result = await response.json();
console.log('Transcription:', result.text);

// Browser - from MediaRecorder
let mediaRecorder;
let audioChunks = [];

navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');

            const response = await fetch('http://localhost:4020/api/chat/transcribe', {
                method: 'POST',
                headers: { 'X-User-ID': 'test_user' },
                body: formData
            });

            const result = await response.json();
            console.log('Transcription:', result.text);
        };

        mediaRecorder.start();
    });

// Stop recording when ready
// mediaRecorder.stop();
```

## ⚙️ Parameters

### POST Request (Multipart Form Data)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `audio` | file | ✅ Yes | Audio file to transcribe |

### Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `X-User-ID` | string | ✅ Yes | User identifier |

## 🔊 Audio Format

**Supported Formats**: WAV, MP3, FLAC, OGG

**Recommended Settings**:
- **Format**: WAV (PCM)
- **Sample Rate**: 16000 Hz
- **Bit Depth**: 16-bit
- **Channels**: Mono
- **Max Duration**: 30 seconds for best performance

## 🚀 Response

**Success Response** (200 OK):
```json
{
  "text": "transcribed text here"
}
```

**Status Codes**:
- `200 OK` - Success, returns transcribed text
- `400 Bad Request` - Empty audio file or invalid format
- `500 Internal Server Error` - Transcription failed
- `503 Service Unavailable` - STT disabled or not initialized

## 💡 Tips

1. **Audio Quality**: Use clear audio with minimal background noise for best results

2. **File Size**: Keep audio files under 30 seconds for fast transcription

3. **Supported Formats**: WAV is recommended, but MP3, FLAC, and OGG are also supported

4. **Model Selection**: Change model in `docker-compose.yml` (line 54):
   ```yaml
   command: --model base-int8 --language en
   ```
   Available models:
   - `tiny` / `tiny-int8` - Fastest, least accurate (~40MB)
   - `base` / `base-int8` - Good balance (~75MB) - **recommended**
   - `small` - Better accuracy (~244MB)
   - `medium` - High accuracy (~769MB)
   - `large-v3` - Best accuracy (~1.5GB)

5. **Language**: Specify language in docker-compose.yml for better accuracy:
   ```yaml
   --language en  # English
   --language es  # Spanish
   --language fr  # French
   # ... etc
   ```

## 📚 Full Documentation

- **Unreal Integration**: `UNREAL_STT_INTEGRATION.md`
- **Voice Chat Flow**: `VOICE_CHAT_INTEGRATION.md`
- **Testing**: Use the UI at http://localhost:4020 and click "🎤 Record Voice"

## ✅ Testing

### Test in Browser UI

1. Go to http://localhost:4020
2. Create or select a character
3. Click "🎤 Record Voice" button
4. Speak your message
5. Click "⏹️ Stop Recording"
6. Watch the transcription appear and auto-send to character!

### Test via Command Line

```bash
# 1. Record audio (macOS example)
sox -d recording.wav rate 16000

# 2. Test transcription
curl -X POST "http://localhost:4020/api/chat/transcribe" \
  -H "X-User-ID: test_user" \
  -F "audio=@recording.wav"

# Should return: {"text": "your transcribed speech"}
```

## 🎮 Unreal Engine Integration

### Basic Example (C++)

```cpp
// Record audio in Unreal and save to file
// Then send to STT API

void USTTComponent::TranscribeAudio(const FString& AudioFilePath)
{
    // Read audio file
    TArray<uint8> AudioData;
    FFileHelper::LoadFileToArray(AudioData, *AudioFilePath);

    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(TEXT("http://localhost:4020/api/chat/transcribe"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("X-User-ID"), TEXT("test_user"));

    // Create multipart form data
    FString Boundary = FString::Printf(TEXT("----Boundary%d"), FMath::Rand());
    Request->SetHeader(TEXT("Content-Type"),
        FString::Printf(TEXT("multipart/form-data; boundary=%s"), *Boundary));

    // Build form data
    FString FormData;
    FormData += FString::Printf(TEXT("--%s\r\n"), *Boundary);
    FormData += TEXT("Content-Disposition: form-data; name=\"audio\"; filename=\"audio.wav\"\r\n");
    FormData += TEXT("Content-Type: audio/wav\r\n\r\n");

    TArray<uint8> RequestBody;
    RequestBody.Append((uint8*)TCHAR_TO_UTF8(*FormData), FormData.Len());
    RequestBody.Append(AudioData);

    FString EndBoundary = FString::Printf(TEXT("\r\n--%s--\r\n"), *Boundary);
    RequestBody.Append((uint8*)TCHAR_TO_UTF8(*EndBoundary), EndBoundary.Len());

    Request->SetContent(RequestBody);
    Request->OnProcessRequestComplete().BindUObject(this, &USTTComponent::OnTranscribeComplete);
    Request->ProcessRequest();
}

void USTTComponent::OnTranscribeComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful && Response.IsValid())
    {
        FString ResponseString = Response->GetContentAsString();

        // Parse JSON
        TSharedPtr<FJsonObject> JsonObject;
        TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

        if (FJsonSerializer::Deserialize(Reader, JsonObject))
        {
            FString TranscribedText = JsonObject->GetStringField(TEXT("text"));
            UE_LOG(LogTemp, Log, TEXT("Transcription: %s"), *TranscribedText);

            // Use transcribed text (e.g., send to character chat)
            OnTranscriptionComplete.Broadcast(TranscribedText);
        }
    }
}
```

See `UNREAL_STT_INTEGRATION.md` for complete integration guide with Blueprint examples.

## 🌟 Combined Voice Chat Flow

**Complete voice-to-voice conversation**:

1. User speaks → **STT** → Text
2. Text → **Character Chat API** → Response text
3. Response text → **TTS** → Audio
4. Play audio response

Example implementation: See `VOICE_CHAT_INTEGRATION.md`
