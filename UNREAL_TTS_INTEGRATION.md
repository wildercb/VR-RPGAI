# Unreal Engine TTS Integration Guide

## Overview

Your RPGAI backend provides a **simple, Unreal-friendly TTS API** that converts text to speech and returns WAV audio files.

## API Endpoint

### Base URL
```
http://localhost:4020/api/chat/synthesize
```

### Supported Methods
- **GET** - Simple query parameter (recommended for Unreal)
- **POST** - JSON body (for advanced use)

---

## Quick Start (Unreal C++)

### Method 1: HTTP GET Request (Blueprint-Compatible)

#### C++ Header (TTSComponent.h)
```cpp
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Http.h"
#include "Sound/SoundWaveProcedural.h"
#include "TTSComponent.generated.h"

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class YOURPROJECT_API UTTSComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UTTSComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "TTS")
    FString ServerURL = TEXT("http://localhost:4020");

    UPROPERTY(BlueprintReadOnly, Category = "TTS")
    UAudioComponent* AudioComponent;

    // Synthesize and play text
    UFUNCTION(BlueprintCallable, Category = "TTS")
    void SpeakText(const FString& Text);

    // Check if currently speaking
    UFUNCTION(BlueprintPure, Category = "TTS")
    bool IsSpeaking() const;

protected:
    virtual void BeginPlay() override;

private:
    void OnTTSRequestComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    USoundWaveProcedural* CreateSoundWaveFromWAVData(const TArray<uint8>& WAVData);
};
```

#### C++ Implementation (TTSComponent.cpp)
```cpp
#include "TTSComponent.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Components/AudioComponent.h"

UTTSComponent::UTTSComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UTTSComponent::BeginPlay()
{
    Super::BeginPlay();

    // Create audio component
    AudioComponent = NewObject<UAudioComponent>(GetOwner());
    AudioComponent->RegisterComponent();
}

void UTTSComponent::SpeakText(const FString& Text)
{
    if (Text.IsEmpty())
    {
        UE_LOG(LogTemp, Warning, TEXT("TTS: Empty text provided"));
        return;
    }

    // URL encode the text
    FString EncodedText = FGenericPlatformHttp::UrlEncode(Text);
    FString URL = FString::Printf(TEXT("%s/api/chat/synthesize?text=%s"), *ServerURL, *EncodedText);

    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(URL);
    Request->SetVerb(TEXT("GET"));
    Request->OnProcessRequestComplete().BindUObject(this, &UTTSComponent::OnTTSRequestComplete);

    UE_LOG(LogTemp, Log, TEXT("TTS Request: %s"), *URL);
    Request->ProcessRequest();
}

void UTTSComponent::OnTTSRequestComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("TTS Request Failed"));
        return;
    }

    if (Response->GetResponseCode() != 200)
    {
        UE_LOG(LogTemp, Error, TEXT("TTS Error: HTTP %d"), Response->GetResponseCode());
        return;
    }

    // Get WAV data
    TArray<uint8> WAVData = Response->GetContent();
    UE_LOG(LogTemp, Log, TEXT("TTS: Received %d bytes"), WAVData.Num());

    // Create sound wave from WAV data
    USoundWaveProcedural* SoundWave = CreateSoundWaveFromWAVData(WAVData);

    if (SoundWave && AudioComponent)
    {
        AudioComponent->SetSound(SoundWave);
        AudioComponent->Play();
        UE_LOG(LogTemp, Log, TEXT("TTS: Playing audio"));
    }
}

USoundWaveProcedural* UTTSComponent::CreateSoundWaveFromWAVData(const TArray<uint8>& WAVData)
{
    // Parse WAV header (simplified - assumes 16kHz, 16-bit, mono from Piper)
    if (WAVData.Num() < 44)
    {
        UE_LOG(LogTemp, Error, TEXT("TTS: Invalid WAV data (too small)"));
        return nullptr;
    }

    // Create procedural sound wave
    USoundWaveProcedural* SoundWave = NewObject<USoundWaveProcedural>();
    SoundWave->SetSampleRate(16000);
    SoundWave->NumChannels = 1;
    SoundWave->Duration = INDEFINITELY_LOOPING_DURATION;
    SoundWave->SoundGroup = SOUNDGROUP_Default;
    SoundWave->bLooping = false;

    // Skip WAV header (44 bytes) and queue audio data
    const int32 HeaderSize = 44;
    const uint8* AudioData = WAVData.GetData() + HeaderSize;
    const int32 AudioDataSize = WAVData.Num() - HeaderSize;

    SoundWave->QueueAudio(AudioData, AudioDataSize);

    return SoundWave;
}

bool UTTSComponent::IsSpeaking() const
{
    return AudioComponent && AudioComponent->IsPlaying();
}
```

---

## Blueprint Integration

### Blueprint-Only Solution (No C++ Required!)

#### 1. Create Blueprint Function Library

Create a new Blueprint Function Library called `TTS_FunctionLibrary`:

**Function: Speak Text**

Nodes:
1. **Make URL**: `http://localhost:4020/api/chat/synthesize?text=` + (URL Encode Text)
2. **HTTP Request** (from VaRest plugin or built-in HTTP)
3. **On Success**: Import WAV → Create Sound Wave → Play Audio

#### 2. Using VaRest Plugin (Recommended)

```
1. Install VaRest plugin from Marketplace (FREE)
2. Create Blueprint:

[Event BeginPlay]
  ↓
[Construct Json Request] → Set URL: "http://localhost:4020/api/chat/synthesize?text=Hello"
  ↓
[Process Request]
  ↓
[On Request Complete]
  ↓
[Get Response Content as Bytes]
  ↓
[Import Sound Wave from Bytes]
  ↓
[Play Sound 2D]
```

---

## Complete NPC Dialogue System (C++)

### NPCCharacter.h
```cpp
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "TTSComponent.h"
#include "NPCCharacter.generated.h"

UCLASS()
class YOURPROJECT_API ANPCCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ANPCCharacter();

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "TTS")
    UTTSComponent* TTSComponent;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Dialogue")
    TArray<FString> DialogueLines;

    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    void StartConversation();

    UFUNCTION(BlueprintCallable, Category = "Dialogue")
    void SayNextLine();

protected:
    virtual void BeginPlay() override;

private:
    int32 CurrentLineIndex = 0;
    FTimerHandle DialogueTimerHandle;

    void CheckIfFinishedSpeaking();
};
```

### NPCCharacter.cpp
```cpp
#include "NPCCharacter.h"
#include "TimerManager.h"

ANPCCharacter::ANPCCharacter()
{
    PrimaryActorTick.bCanEverTick = false;

    // Create TTS component
    TTSComponent = CreateDefaultSubobject<UTTSComponent>(TEXT("TTSComponent"));
}

void ANPCCharacter::BeginPlay()
{
    Super::BeginPlay();

    // Example dialogue
    DialogueLines = {
        TEXT("Greetings, traveler!"),
        TEXT("What brings you to our village?"),
        TEXT("The wizard lives in the tower to the north."),
        TEXT("May your journey be safe!")
    };
}

void ANPCCharacter::StartConversation()
{
    CurrentLineIndex = 0;
    SayNextLine();
}

void ANPCCharacter::SayNextLine()
{
    if (CurrentLineIndex < DialogueLines.Num())
    {
        FString Line = DialogueLines[CurrentLineIndex];
        CurrentLineIndex++;

        // Speak the line
        TTSComponent->SpeakText(Line);

        UE_LOG(LogTemp, Log, TEXT("NPC says: %s"), *Line);

        // Wait for audio to finish, then say next line
        GetWorld()->GetTimerManager().SetTimer(
            DialogueTimerHandle,
            this,
            &ANPCCharacter::CheckIfFinishedSpeaking,
            0.1f,
            true
        );
    }
    else
    {
        UE_LOG(LogTemp, Log, TEXT("Conversation finished"));
    }
}

void ANPCCharacter::CheckIfFinishedSpeaking()
{
    if (!TTSComponent->IsSpeaking())
    {
        GetWorld()->GetTimerManager().ClearTimer(DialogueTimerHandle);

        // Wait a moment, then say next line
        FTimerHandle PauseTimerHandle;
        GetWorld()->GetTimerManager().SetTimer(
            PauseTimerHandle,
            this,
            &ANPCCharacter::SayNextLine,
            0.5f,
            false
        );
    }
}
```

---

## Blueprint Example

### Simple TTS Blueprint

**For Blueprint-only projects:**

1. **Create Actor Component** called `BP_TTSComponent`

2. **Add Custom Event**: `Speak Text`
   - Input: Text (String)

3. **Blueprint Logic**:
```
[Speak Text Event]
  ↓
[Append Strings]
  - "http://localhost:4020/api/chat/synthesize?text="
  - [URL Encode] Text Input
  ↓
[HTTP Request Node] (VaRest or native)
  - URL: Constructed URL
  - Method: GET
  ↓
[On Success]
  ↓
[Get Response Content]
  ↓
[Create Sound Wave from WAV]
  ↓
[Spawn Sound 2D]
  - Sound: Sound Wave
  - Volume: 1.0
  - Pitch: 1.0
```

---

## Advanced: RPGAI Character Integration

### Integrate with Character Chat System

```cpp
// CharacterChatComponent.h
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Http.h"
#include "TTSComponent.h"
#include "CharacterChatComponent.generated.h"

USTRUCT(BlueprintType)
struct FChatResponse
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly)
    FString ConversationId;

    UPROPERTY(BlueprintReadOnly)
    FString Message;

    UPROPERTY(BlueprintReadOnly)
    FString AudioFile;
};

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class YOURPROJECT_API UCharacterChatComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCharacterChatComponent();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RPGAI")
    FString ServerURL = TEXT("http://localhost:4020");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RPGAI")
    FString CharacterId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RPGAI")
    FString UserId = TEXT("player1");

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "TTS")
    UTTSComponent* TTSComponent;

    // Send message to RPGAI character
    UFUNCTION(BlueprintCallable, Category = "RPGAI")
    void SendMessage(const FString& Message);

protected:
    virtual void BeginPlay() override;

private:
    void OnChatRequestComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    void PlayAudioFromURL(const FString& AudioURL);
};
```

```cpp
// CharacterChatComponent.cpp
#include "CharacterChatComponent.h"
#include "HttpModule.h"
#include "Json.h"
#include "JsonUtilities.h"

UCharacterChatComponent::UCharacterChatComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void UCharacterChatComponent::BeginPlay()
{
    Super::BeginPlay();

    TTSComponent = NewObject<UTTSComponent>(this);
    TTSComponent->RegisterComponent();
}

void UCharacterChatComponent::SendMessage(const FString& Message)
{
    // Build JSON request
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject);
    JsonObject->SetStringField(TEXT("character_id"), CharacterId);
    JsonObject->SetStringField(TEXT("message"), Message);

    FString JsonString;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    // Create HTTP request
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(ServerURL + TEXT("/api/chat/send"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetHeader(TEXT("X-User-ID"), UserId);
    Request->SetContentAsString(JsonString);
    Request->OnProcessRequestComplete().BindUObject(this, &UCharacterChatComponent::OnChatRequestComplete);

    UE_LOG(LogTemp, Log, TEXT("Sending message: %s"), *Message);
    Request->ProcessRequest();
}

void UCharacterChatComponent::OnChatRequestComplete(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("Chat request failed"));
        return;
    }

    // Parse JSON response
    FString ResponseString = Response->GetContentAsString();
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(ResponseString);

    if (FJsonSerializer::Deserialize(Reader, JsonObject) && JsonObject.IsValid())
    {
        FString Message = JsonObject->GetStringField(TEXT("message"));
        FString AudioFile = JsonObject->GetStringField(TEXT("audio_file"));

        UE_LOG(LogTemp, Log, TEXT("Character says: %s"), *Message);

        // Play TTS audio
        if (!AudioFile.IsEmpty())
        {
            FString AudioURL = ServerURL + TEXT("/") + AudioFile;
            PlayAudioFromURL(AudioURL);
        }
    }
}

void UCharacterChatComponent::PlayAudioFromURL(const FString& AudioURL)
{
    // Download and play audio
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(AudioURL);
    Request->SetVerb(TEXT("GET"));
    Request->OnProcessRequestComplete().BindLambda(
        [this](FHttpRequestPtr Req, FHttpResponsePtr Resp, bool bSuccess)
        {
            if (bSuccess && Resp.IsValid())
            {
                TArray<uint8> WAVData = Resp->GetContent();
                // Use TTSComponent's CreateSoundWaveFromWAVData method
                // Or implement similar WAV parsing here
                UE_LOG(LogTemp, Log, TEXT("Playing character audio"));
            }
        }
    );
    Request->ProcessRequest();
}
```

---

## Using HTTP Request Node (Blueprint)

### For Blueprint Developers:

1. **Add HTTP Request Node**:
   - Right-click → Add Node → "Send HTTP Request"
   - Or use VaRest plugin for easier JSON handling

2. **Configure Request**:
   - **URL**: `http://localhost:4020/api/chat/synthesize?text=Hello`
   - **Method**: GET
   - **Connect**: On Success → Parse Response → Play Sound

3. **Parse WAV Response**:
   - Use "Get Response Content as Bytes"
   - Import to Sound Wave
   - Play with "Play Sound 2D"

---

## Performance Tips

### 1. Pre-cache Common Phrases

```cpp
void AGameMode::PreloadCommonPhrases()
{
    TArray<FString> CommonPhrases = {
        TEXT("Hello"),
        TEXT("Goodbye"),
        TEXT("Thank you"),
        TEXT("Follow me")
    };

    for (const FString& Phrase : CommonPhrases)
    {
        // Request each phrase to cache on server
        TTSComponent->SpeakText(Phrase);
    }
}
```

### 2. Dialogue Queue System

```cpp
// Queue multiple lines
TArray<FString> DialogueQueue;

void ProcessDialogueQueue()
{
    if (DialogueQueue.Num() > 0 && !TTSComponent->IsSpeaking())
    {
        FString NextLine = DialogueQueue[0];
        DialogueQueue.RemoveAt(0);
        TTSComponent->SpeakText(NextLine);
    }
}
```

---

## Audio Format

- **Format**: WAV (PCM)
- **Sample Rate**: 16000 Hz
- **Bit Depth**: 16-bit
- **Channels**: Mono (1 channel)
- **Voice**: Configurable (see TTS_VOICE_CUSTOMIZATION.md)

---

## Troubleshooting

### Issue: "Connection refused"

**Solution:** Ensure RPGAI backend is running:
```bash
docker-compose ps
```

### Issue: Audio not playing

**Solution:**
1. Check Audio Component is valid
2. Verify HTTP request succeeded (check logs)
3. Test URL in browser: `http://localhost:4020/api/chat/synthesize?text=test`

### Issue: CORS errors

**Solution:** Add your Unreal server URL to `.env`:
```
CORS_ORIGINS=["http://localhost:3000", "http://yourunrealserver.com"]
```

---

## Complete Blueprint Example

**BP_NPCWithTTS**:

```
[Event BeginPlay]
  ↓
[Create TTS Component]
  ↓
[Add to Actor]

[Custom Event: Say Line]
  Input: Line (String)
  ↓
[Construct URL]
  - Base: "http://localhost:4020/api/chat/synthesize?text="
  - Append: [URL Encode] Line
  ↓
[VaRest Request]
  - URL: Constructed URL
  - Method: GET
  ↓
[On Request Complete]
  ↓
[Get Response as Bytes]
  ↓
[Create Sound Wave]
  ↓
[Play Sound 2D]
  - Sound: Created Wave
  - Volume: 1.0
```

---

## Next Steps

1. **Install VaRest Plugin** (optional but recommended for Blueprint)
   - Unreal Marketplace → Search "VaRest"
   - Free plugin for HTTP/JSON

2. **Change Voice**: Edit `docker-compose.yml`
   - See `TTS_VOICE_CUSTOMIZATION.md`

3. **Production Setup**:
   - Update CORS origins
   - Consider dedicated server
   - Add authentication for public APIs

**Your TTS API is ready for Unreal Engine integration!** 🎮🎙️
