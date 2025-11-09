# Complete Voice Chat Integration Guide

## 🎯 Overview

This guide shows you how to create a **complete voice-to-voice conversation system** where players can speak to AI characters and hear spoken responses.

**Flow**:
1. 🎤 **Player speaks** → Microphone captures audio
2. 🔄 **STT (Whisper)** → Converts speech to text
3. 💬 **Character Chat API** → AI generates response text
4. 🔊 **TTS (Piper)** → Converts response to speech
5. 🎧 **Play Audio** → Player hears character's voice

---

## 📋 Prerequisites

### Services Running

Ensure all services are running:

```bash
docker-compose up -d
```

Verify:
```bash
docker-compose ps

# Should show all services "Up":
# - rpgai-backend
# - rpgai-whisper  (STT)
# - rpgai-piper    (TTS)
# - rpgai-postgres
# - rpgai-redis
# - rpgai-ollama (or external LLM)
```

### API Endpoints

- **STT**: `POST http://localhost:4020/api/chat/transcribe`
- **Chat**: `POST http://localhost:4020/api/chat/send`
- **TTS**: `GET http://localhost:4020/api/chat/synthesize?text=...`

---

## 🌐 Web Browser Implementation

### HTML + JavaScript

The RPGAI UI already includes full voice chat! Open http://localhost:4020 and:

1. Create or select a character
2. Click **"🎤 Record Voice"** button
3. Speak your message
4. Click **"⏹️ Stop Recording"**
5. Transcription appears → Auto-sends to character
6. Character response appears with **"🔊 Play"** button
7. Audio auto-plays!

**Implementation** ([static/app.js](static/app.js:679-804)):

```javascript
// 1. Record voice
async startRecording() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.mediaRecorder = new MediaRecorder(stream);
    this.audioChunks = [];

    this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            this.audioChunks.push(event.data);
        }
    };

    this.mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        await this.transcribeAudio(audioBlob);
    };

    this.mediaRecorder.start();
}

// 2. Transcribe speech to text
async transcribeAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    const response = await fetch(`${this.apiUrl}/api/chat/transcribe`, {
        method: 'POST',
        headers: { 'X-User-ID': this.userId },
        body: formData
    });

    const data = await response.json();
    const transcribedText = data.text;

    // Display and auto-send
    document.getElementById('messageInput').value = transcribedText;
    setTimeout(() => this.sendMessage(), 1000);
}

// 3. Send message and get TTS response
async sendMessage() {
    const response = await this.apiRequest('/api/chat/send', 'POST', {
        character_id: this.currentCharacter.id,
        message: message
    });

    // Add message with audio button
    this.addMessage('assistant', response.message, null, response.audio_file);

    // 4. Auto-play audio response
    if (response.audio_file) {
        this.playAudio(response.audio_file);
    }
}

playAudio(audioFile) {
    this.currentAudio = new Audio(`/${audioFile}`);
    this.currentAudio.play();
}
```

---

## 🎮 Unreal Engine Implementation

### Overview

Unreal implementation requires:
1. Audio capture (microphone)
2. HTTP requests for STT, Chat, TTS
3. Audio playback

### Full C++ Component

**VoiceChatComponent.h**:

```cpp
// VoiceChatComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Http.h"
#include "Sound/SoundWaveProcedural.h"
#include "VoiceChatComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTranscriptionComplete, FString, TranscribedText);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCharacterResponse, FString, ResponseText);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnVoiceResponseReady, USoundWave*, AudioClip);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class YOURPROJECT_API UVoiceChatComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UVoiceChatComponent();

    // Configuration
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice Chat")
    FString ServerURL = TEXT("http://localhost:4020");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice Chat")
    FString UserID = TEXT("test_user");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Voice Chat")
    FString CharacterID;

    // Audio capture
    UPROPERTY(BlueprintReadWrite, Category = "Voice Chat")
    bool bIsRecording = false;

    // Events
    UPROPERTY(BlueprintAssignable, Category = "Voice Chat")
    FOnTranscriptionComplete OnTranscriptionComplete;

    UPROPERTY(BlueprintAssignable, Category = "Voice Chat")
    FOnCharacterResponse OnCharacterResponse;

    UPROPERTY(BlueprintAssignable, Category = "Voice Chat")
    FOnVoiceResponseReady OnVoiceResponseReady;

    // Methods
    UFUNCTION(BlueprintCallable, Category = "Voice Chat")
    void StartRecording();

    UFUNCTION(BlueprintCallable, Category = "Voice Chat")
    void StopRecording();

    UFUNCTION(BlueprintCallable, Category = "Voice Chat")
    void SendVoiceMessage(const FString& AudioFilePath);

    UFUNCTION(BlueprintCallable, Category = "Voice Chat")
    void SendTextMessage(const FString& Message);

private:
    // HTTP callbacks
    void OnTranscribeComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess);
    void OnChatComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess);
    void OnTTSComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess);

    // Utilities
    USoundWaveProcedural* CreateSoundWaveFromWAV(const TArray<uint8>& WAVData);
    TArray<uint8> CreateMultipartFormData(const FString& FieldName, const FString& FileName,
                                          const TArray<uint8>& FileData, const FString& Boundary);

    // State
    FString CurrentTranscript;
    TArray<uint8> RecordedAudio;
};
```

**VoiceChatComponent.cpp**:

```cpp
// VoiceChatComponent.cpp
#include "VoiceChatComponent.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Json.h"
#include "JsonUtilities.h"
#include "Misc/FileHelper.h"

UVoiceChatComponent::UVoiceChatComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UVoiceChatComponent::StartRecording()
{
    bIsRecording = true;
    RecordedAudio.Empty();

    // TODO: Implement audio capture using Unreal's Voice Capture API
    // or platform-specific audio recording
    UE_LOG(LogTemp, Log, TEXT("Voice recording started"));
}

void UVoiceChatComponent::StopRecording()
{
    bIsRecording = false;
    UE_LOG(LogTemp, Log, TEXT("Voice recording stopped"));

    // TODO: Save recorded audio to temp file and call SendVoiceMessage()
}

void UVoiceChatComponent::SendVoiceMessage(const FString& AudioFilePath)
{
    // Read audio file
    TArray<uint8> AudioData;
    if (!FFileHelper::LoadFileToArray(AudioData, *AudioFilePath))
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to load audio file: %s"), *AudioFilePath);
        return;
    }

    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("%s/api/chat/transcribe"), *ServerURL));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("X-User-ID"), UserID);

    // Create multipart form data
    FString Boundary = FString::Printf(TEXT("----Boundary%d"), FMath::Rand());
    Request->SetHeader(TEXT("Content-Type"),
        FString::Printf(TEXT("multipart/form-data; boundary=%s"), *Boundary));

    TArray<uint8> RequestBody = CreateMultipartFormData(
        TEXT("audio"),
        FPaths::GetCleanFilename(AudioFilePath),
        AudioData,
        Boundary
    );

    Request->SetContent(RequestBody);
    Request->OnProcessRequestComplete().BindUObject(this, &UVoiceChatComponent::OnTranscribeComplete);
    Request->ProcessRequest();

    UE_LOG(LogTemp, Log, TEXT("Sending audio for transcription..."));
}

void UVoiceChatComponent::OnTranscribeComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess)
{
    if (!bSuccess || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("Transcription request failed"));
        return;
    }

    // Parse JSON response
    FString ResponseString = Response->GetContentAsString();
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        CurrentTranscript = JsonObject->GetStringField(TEXT("text"));
        UE_LOG(LogTemp, Log, TEXT("Transcription: %s"), *CurrentTranscript);

        // Broadcast event
        OnTranscriptionComplete.Broadcast(CurrentTranscript);

        // Auto-send to character
        SendTextMessage(CurrentTranscript);
    }
}

void UVoiceChatComponent::SendTextMessage(const FString& Message)
{
    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(FString::Printf(TEXT("%s/api/chat/send"), *ServerURL));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetHeader(TEXT("X-User-ID"), UserID);

    // Create JSON body
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
    JsonObject->SetStringField(TEXT("character_id"), CharacterID);
    JsonObject->SetStringField(TEXT("message"), Message);

    FString JsonString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    Request->SetContentAsString(JsonString);
    Request->OnProcessRequestComplete().BindUObject(this, &UVoiceChatComponent::OnChatComplete);
    Request->ProcessRequest();

    UE_LOG(LogTemp, Log, TEXT("Sending message to character..."));
}

void UVoiceChatComponent::OnChatComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess)
{
    if (!bSuccess || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("Chat request failed"));
        return;
    }

    // Parse JSON response
    FString ResponseString = Response->GetContentAsString();
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        FString ResponseText = JsonObject->GetStringField(TEXT("message"));
        UE_LOG(LogTemp, Log, TEXT("Character response: %s"), *ResponseText);

        // Broadcast event
        OnCharacterResponse.Broadcast(ResponseText);

        // Request TTS for response
        TSharedRef<IHttpRequest> TTSRequest = FHttpModule::Get().CreateRequest();
        FString EncodedText = FGenericPlatformHttp::UrlEncode(ResponseText);
        TTSRequest->SetURL(FString::Printf(TEXT("%s/api/chat/synthesize?text=%s"),
                                           *ServerURL, *EncodedText));
        TTSRequest->SetVerb(TEXT("GET"));
        TTSRequest->OnProcessRequestComplete().BindUObject(this, &UVoiceChatComponent::OnTTSComplete);
        TTSRequest->ProcessRequest();

        UE_LOG(LogTemp, Log, TEXT("Requesting TTS audio..."));
    }
}

void UVoiceChatComponent::OnTTSComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bSuccess)
{
    if (!bSuccess || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("TTS request failed"));
        return;
    }

    // Get WAV audio data
    TArray<uint8> WAVData = Response->GetContent();

    // Create sound wave
    USoundWaveProcedural* SoundWave = CreateSoundWaveFromWAV(WAVData);

    if (SoundWave)
    {
        UE_LOG(LogTemp, Log, TEXT("TTS audio ready, playing..."));

        // Broadcast event
        OnVoiceResponseReady.Broadcast(SoundWave);
    }
}

USoundWaveProcedural* UVoiceChatComponent::CreateSoundWaveFromWAV(const TArray<uint8>& WAVData)
{
    // Skip WAV header (44 bytes)
    if (WAVData.Num() < 44)
    {
        UE_LOG(LogTemp, Error, TEXT("Invalid WAV data"));
        return nullptr;
    }

    const uint8* AudioData = WAVData.GetData() + 44;
    int32 AudioDataSize = WAVData.Num() - 44;

    // Create procedural sound wave
    USoundWaveProcedural* SoundWave = NewObject<USoundWaveProcedural>();
    SoundWave->SetSampleRate(16000);
    SoundWave->NumChannels = 1;
    SoundWave->Duration = (float)AudioDataSize / (16000.0f * 2.0f); // 16-bit samples
    SoundWave->SoundGroup = SOUNDGROUP_Voice;

    // Queue audio data
    SoundWave->QueueAudio(AudioData, AudioDataSize);

    return SoundWave;
}

TArray<uint8> UVoiceChatComponent::CreateMultipartFormData(
    const FString& FieldName,
    const FString& FileName,
    const TArray<uint8>& FileData,
    const FString& Boundary)
{
    TArray<uint8> FormData;

    // Start boundary
    FString Header = FString::Printf(
        TEXT("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\nContent-Type: audio/wav\r\n\r\n"),
        *Boundary, *FieldName, *FileName
    );
    FormData.Append((uint8*)TCHAR_TO_UTF8(*Header), Header.Len());

    // File data
    FormData.Append(FileData);

    // End boundary
    FString Footer = FString::Printf(TEXT("\r\n--%s--\r\n"), *Boundary);
    FormData.Append((uint8*)TCHAR_TO_UTF8(*Footer), Footer.Len());

    return FormData;
}
```

### Blueprint Usage

1. **Add Component** to your player character or NPC
2. **Set Properties**:
   - Server URL: `http://localhost:4020`
   - Character ID: (get from UI or API)
   - User ID: `test_user`

3. **Wire Events**:
   - `OnTranscriptionComplete` → Display text in UI
   - `OnCharacterResponse` → Show character's text response
   - `OnVoiceResponseReady` → Play audio at character location

4. **Call Functions**:
   - `StartRecording()` when player presses voice button
   - `StopRecording()` when player releases button
   - `SendVoiceMessage(FilePath)` with recorded audio file

---

## 🧪 Testing

### 1. Test UI (Easiest)

```bash
# Open browser
open http://localhost:4020

# Or navigate to http://localhost:4020
```

1. Create character
2. Click "🎤 Record Voice"
3. Speak: "Hello, how are you?"
4. Click "⏹️ Stop"
5. Watch transcription → chat → audio response!

### 2. Test API Directly

```bash
# 1. Record audio (use any tool, e.g., sox on macOS)
sox -d test_recording.wav rate 16000

# 2. Transcribe
curl -X POST "http://localhost:4020/api/chat/transcribe" \
  -H "X-User-ID: test_user" \
  -F "audio=@test_recording.wav"

# Returns: {"text": "Hello, how are you?"}

# 3. Send to character (replace CHARACTER_ID)
curl -X POST "http://localhost:4020/api/chat/send" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{
    "character_id": "YOUR_CHARACTER_ID",
    "message": "Hello, how are you?"
  }'

# Returns: {"conversation_id": "...", "message": "I'\''m doing well...", "audio_file": "audio_cache/abc123.wav"}

# 4. Play audio response
curl "http://localhost:4020/audio_cache/abc123.wav" -o response.wav
afplay response.wav  # macOS
```

---

## 🎛️ Configuration

### Change STT Model (Accuracy vs Speed)

Edit `docker-compose.yml`:

```yaml
whisper:
  command: --model base-int8 --language en

# Options:
# - tiny-int8: Fastest, least accurate
# - base-int8: Good balance (default)
# - small: Better accuracy, slower
# - medium: High accuracy, much slower
# - large-v3: Best accuracy, very slow
```

### Change TTS Voice

Edit `docker-compose.yml`:

```yaml
piper:
  command: --voice en_US-lessac-medium

# See TTS_VOICE_CUSTOMIZATION.md for all voice options
```

### Restart Services

```bash
docker-compose restart whisper piper backend
```

---

## 🚀 Performance Tips

1. **STT Model Selection**:
   - VR/Real-time: Use `tiny-int8` (fastest)
   - Desktop: Use `base-int8` (balanced)
   - Non-real-time: Use `small` or `medium` (best quality)

2. **Audio Quality**:
   - Use 16kHz sample rate
   - Mono channel
   - 16-bit PCM WAV format
   - Minimize background noise

3. **Network**:
   - Run services locally for best latency
   - Use LAN instead of internet for multiplayer

4. **Caching**:
   - TTS responses are cached automatically
   - Same text = instant audio response

---

## 📚 Related Documentation

- **STT API**: `STT_API_QUICK_REFERENCE.md`
- **TTS API**: `TTS_API_QUICK_REFERENCE.md`
- **Unreal TTS**: `UNREAL_TTS_INTEGRATION.md`
- **Voice Customization**: `TTS_VOICE_CUSTOMIZATION.md`

---

## ✅ Checklist

- [ ] All services running (`docker-compose ps`)
- [ ] Whisper ready (`docker-compose logs whisper | grep Ready`)
- [ ] Piper ready (`docker-compose logs piper | grep Ready`)
- [ ] Character created (via UI at http://localhost:4020)
- [ ] Microphone access granted (browser/Unreal)
- [ ] Test voice recording in UI works
- [ ] Audio playback works

**You're ready for voice chat!** 🎉
