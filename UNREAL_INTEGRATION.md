## Unreal Engine Integration Guide

Complete guide for integrating RPGAI characters into your Unreal Engine VR project.

## Table of Contents

1. [Quick Setup](#quick-setup)
2. [Blueprint Integration](#blueprint-integration)
3. [C++ Integration](#c-integration)
4. [Example Use Cases](#example-use-cases)
5. [Best Practices](#best-practices)

---

## Quick Setup

### 1. Start RPGAI Server

```bash
cd RPGAI
./start.sh
```

Server will be available at `http://localhost:8000`

### 2. Test from Unreal

In your Unreal project, you can use either:
- **VaRest Plugin** (recommended for blueprints)
- **Built-in HTTP Module** (C++)

---

## Blueprint Integration

### Method 1: Using VaRest Plugin

#### Install VaRest

1. Download VaRest from Unreal Marketplace (free)
2. Enable in your project plugins
3. Restart Unreal Editor

#### Create Character Blueprint

**Step 1: Create Character**

<img width="800" alt="Blueprint" src="https://via.placeholder.com/800x400?text=VaRest+Create+Character+Blueprint" />

```
Event BeginPlay
  ↓
Create VaRest Request
  ↓
Set URL: http://localhost:8000/api/characters
Set Verb: POST
Set Header: X-User-ID = {PlayerID}
Set Content Type: application/json
Set Request Object:
  {
    "prompt": "A friendly medieval blacksmith"
  }
  ↓
On Request Complete (Success)
  ↓
Get JSON Field: "id" → Save to Character ID variable
Get JSON Field: "name" → Display to player
```

**Step 2: Chat with Character**

```
On Player Input Text Entered
  ↓
Create VaRest Request
  ↓
Set URL: http://localhost:8000/api/chat/{CharacterID}
Set Verb: POST
Set Header: X-User-ID = {PlayerID}
Set Content Type: application/json
Set Request Object:
  {
    "message": {InputText}
  }
  ↓
On Request Complete (Success)
  ↓
Get JSON Field: "message" → Display in dialogue widget
Get JSON Field: "conversation_id" → Save for history
```

### Method 2: Using HTTP Module (Blueprint-Accessible)

#### Setup HTTP Module

1. In Project Settings → Modules, ensure `HTTP` module is enabled
2. Create a Blueprint Function Library for HTTP calls

#### Example Blueprint Function Library

Create new Blueprint Function Library: `BP_RPGAIHelpers`

**Function: Create AI Character**

Inputs:
- User ID (String)
- Character Prompt (String)
- Server URL (String) = "http://localhost:8000"

Outputs:
- Success (Boolean)
- Character ID (String)
- Character Name (String)

Logic:
```
1. Construct Request
   - URL: {ServerURL}/api/characters
   - Verb: POST
   - Headers: ["X-User-ID", {UserID}], ["Content-Type", "application/json"]
   - Body: {"prompt": "{CharacterPrompt}"}

2. Process Request (async)

3. On Complete:
   - Parse JSON
   - Extract "id" and "name"
   - Return results
```

**Function: Send Chat Message**

Inputs:
- User ID (String)
- Character ID (String)
- Message (String)
- Server URL (String)

Outputs:
- Success (Boolean)
- Response Message (String)
- Conversation ID (String)

---

## C++ Integration

### Setup HTTP Module

**YourProject.Build.cs:**

```cpp
PublicDependencyModuleNames.AddRange(new string[] {
    "Core",
    "CoreUObject",
    "Engine",
    "InputCore",
    "Http",           // Add this
    "Json",           // Add this
    "JsonUtilities"   // Add this
});
```

### Create Character Manager Component

**UCharacterAgentComponent.h:**

```cpp
#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Http.h"
#include "CharacterAgentComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnCharacterCreated, bool, bSuccess, FString, CharacterID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnMessageReceived, bool, bSuccess, FString, ResponseMessage);

UCLASS(ClassGroup=(Custom), meta=(BlueprintSpawnableComponent))
class YOURPROJECT_API UCharacterAgentComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UCharacterAgentComponent();

    // Configuration
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RPGAI")
    FString ServerURL = TEXT("http://localhost:8000");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "RPGAI")
    FString UserID = TEXT("player1");

    UPROPERTY(BlueprintReadOnly, Category = "RPGAI")
    FString CharacterID;

    UPROPERTY(BlueprintReadOnly, Category = "RPGAI")
    FString CharacterName;

    // Events
    UPROPERTY(BlueprintAssignable, Category = "RPGAI")
    FOnCharacterCreated OnCharacterCreated;

    UPROPERTY(BlueprintAssignable, Category = "RPGAI")
    FOnMessageReceived OnMessageReceived;

    // API Methods
    UFUNCTION(BlueprintCallable, Category = "RPGAI")
    void CreateCharacter(const FString& Prompt);

    UFUNCTION(BlueprintCallable, Category = "RPGAI")
    void SendMessage(const FString& Message);

    UFUNCTION(BlueprintCallable, Category = "RPGAI")
    void UploadDocument(const FString& Filename, const FString& Content);

private:
    void OnCreateCharacterResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    void OnSendMessageResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);
    void OnUploadDocumentResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful);

    TSharedRef<IHttpRequest> CreateRequest(const FString& Endpoint, const FString& Verb);
};
```

**UCharacterAgentComponent.cpp:**

```cpp
#include "CharacterAgentComponent.h"
#include "Json.h"
#include "JsonUtilities.h"

UCharacterAgentComponent::UCharacterAgentComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

TSharedRef<IHttpRequest> UCharacterAgentComponent::CreateRequest(const FString& Endpoint, const FString& Verb)
{
    TSharedRef<IHttpRequest> Request = FHttpModule::Get().CreateRequest();
    Request->SetURL(ServerURL + Endpoint);
    Request->SetVerb(Verb);
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetHeader(TEXT("X-User-ID"), UserID);
    return Request;
}

void UCharacterAgentComponent::CreateCharacter(const FString& Prompt)
{
    TSharedRef<IHttpRequest> Request = CreateRequest(TEXT("/api/characters"), TEXT("POST"));

    // Create JSON body
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField(TEXT("prompt"), Prompt);

    FString JsonBody;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonBody);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    Request->SetContentAsString(JsonBody);
    Request->OnProcessRequestComplete().BindUObject(this, &UCharacterAgentComponent::OnCreateCharacterResponse);
    Request->ProcessRequest();

    UE_LOG(LogTemp, Log, TEXT("Creating character: %s"), *Prompt);
}

void UCharacterAgentComponent::OnCreateCharacterResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to create character"));
        OnCharacterCreated.Broadcast(false, TEXT(""));
        return;
    }

    // Parse JSON response
    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());

    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        CharacterID = JsonObject->GetStringField(TEXT("id"));
        CharacterName = JsonObject->GetStringField(TEXT("name"));

        UE_LOG(LogTemp, Log, TEXT("Character created: %s (ID: %s)"), *CharacterName, *CharacterID);
        OnCharacterCreated.Broadcast(true, CharacterID);
    }
    else
    {
        OnCharacterCreated.Broadcast(false, TEXT(""));
    }
}

void UCharacterAgentComponent::SendMessage(const FString& Message)
{
    if (CharacterID.IsEmpty())
    {
        UE_LOG(LogTemp, Error, TEXT("No character ID set"));
        return;
    }

    TSharedRef<IHttpRequest> Request = CreateRequest(
        FString::Printf(TEXT("/api/chat/%s"), *CharacterID),
        TEXT("POST")
    );

    // Create JSON body
    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField(TEXT("message"), Message);

    FString JsonBody;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonBody);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    Request->SetContentAsString(JsonBody);
    Request->OnProcessRequestComplete().BindUObject(this, &UCharacterAgentComponent::OnSendMessageResponse);
    Request->ProcessRequest();

    UE_LOG(LogTemp, Log, TEXT("Sending message: %s"), *Message);
}

void UCharacterAgentComponent::OnSendMessageResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (!bWasSuccessful || !Response.IsValid())
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to send message"));
        OnMessageReceived.Broadcast(false, TEXT(""));
        return;
    }

    TSharedPtr<FJsonObject> JsonObject;
    TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Response->GetContentAsString());

    if (FJsonSerializer::Deserialize(Reader, JsonObject))
    {
        FString ResponseMessage = JsonObject->GetStringField(TEXT("message"));
        UE_LOG(LogTemp, Log, TEXT("Response: %s"), *ResponseMessage);
        OnMessageReceived.Broadcast(true, ResponseMessage);
    }
    else
    {
        OnMessageReceived.Broadcast(false, TEXT(""));
    }
}

void UCharacterAgentComponent::UploadDocument(const FString& Filename, const FString& Content)
{
    if (CharacterID.IsEmpty())
    {
        UE_LOG(LogTemp, Error, TEXT("No character ID set"));
        return;
    }

    TSharedRef<IHttpRequest> Request = CreateRequest(
        FString::Printf(TEXT("/api/documents/%s"), *CharacterID),
        TEXT("POST")
    );

    TSharedPtr<FJsonObject> JsonObject = MakeShareable(new FJsonObject());
    JsonObject->SetStringField(TEXT("filename"), Filename);
    JsonObject->SetStringField(TEXT("content"), Content);

    FString JsonBody;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonBody);
    FJsonSerializer::Serialize(JsonObject.ToSharedRef(), Writer);

    Request->SetContentAsString(JsonBody);
    Request->OnProcessRequestComplete().BindUObject(this, &UCharacterAgentComponent::OnUploadDocumentResponse);
    Request->ProcessRequest();
}

void UCharacterAgentComponent::OnUploadDocumentResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bWasSuccessful)
{
    if (bWasSuccessful)
    {
        UE_LOG(LogTemp, Log, TEXT("Document uploaded successfully"));
    }
}
```

### Usage in Blueprint or C++

**In Blueprint:**

1. Add `CharacterAgentComponent` to your NPC actor
2. Set `Server URL` and `User ID` in details panel
3. Bind to `OnCharacterCreated` and `OnMessageReceived` events
4. Call `Create Character` on BeginPlay with a prompt
5. Call `Send Message` when player interacts

**In C++:**

```cpp
// In your NPC actor
UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
UCharacterAgentComponent* CharacterAgent;

// In constructor
CharacterAgent = CreateDefaultSubobject<UCharacterAgentComponent>(TEXT("CharacterAgent"));

// On begin play
CharacterAgent->CreateCharacter(TEXT("A friendly shopkeeper who sells magical items"));

// On player interaction
CharacterAgent->SendMessage(PlayerInputText);
```

---

## Example Use Cases

### 1. VR Training Instructor

**Scenario:** Player learns CPR in VR

```cpp
// Create instructor character
CharacterAgent->CreateCharacter(
    TEXT("An experienced medical instructor who teaches CPR step-by-step with patience and clear instructions")
);

// Upload training manual
FString CPRGuide = LoadTextFile("Content/Training/CPR_Guide.txt");
CharacterAgent->UploadDocument(TEXT("CPR_Guide.txt"), CPRGuide);

// Player asks question
CharacterAgent->SendMessage(TEXT("How many chest compressions per minute?"));
// Response: "Good question! You should perform 100 to 120 chest compressions per minute..."
```

### 2. Dynamic Quest Giver

```cpp
// Create quest giver with game lore
CharacterAgent->CreateCharacter(
    TEXT("A mysterious cloaked figure who knows ancient secrets and gives cryptic but helpful quests")
);

// Upload lore documents
CharacterAgent->UploadDocument(TEXT("world_lore.txt"), GameLoreDatabase);
CharacterAgent->UploadDocument(TEXT("available_quests.json"), QuestData);

// Player interaction
CharacterAgent->SendMessage(TEXT("Tell me about the ancient ruins"));
// Character responds based on lore and available quests
```

### 3. Language Learning NPC

```cpp
// Spanish tutor
CharacterAgent->CreateCharacter(
    TEXT("A cheerful Spanish teacher who helps players learn conversational Spanish through natural dialogue")
);

CharacterAgent->UploadDocument(TEXT("spanish_vocabulary.txt"), VocabularyList);
CharacterAgent->UploadDocument(TEXT("common_phrases.txt"), PhrasesGuide);

// Player practices
CharacterAgent->SendMessage(TEXT("How do I say 'where is the bathroom' in Spanish?"));
```

### 4. Shop Keeper with Inventory

```cpp
// Create shopkeeper
CharacterAgent->CreateCharacter(
    TEXT("A friendly merchant who sells potions and remembers customer preferences")
);

// Upload shop inventory
FString InventoryJSON = GenerateShopInventoryJSON(); // From your game data
CharacterAgent->UploadDocument(TEXT("shop_inventory.json"), InventoryJSON);

// Customer interaction
CharacterAgent->SendMessage(TEXT("What health potions do you have?"));
// Shopkeeper responds with items from uploaded inventory
```

---

## Best Practices

### 1. Character Persistence

Save character IDs to player save data:

```cpp
UPROPERTY(SaveGame)
TMap<FString, FString> NPCCharacterIDs; // NPC Name → Character ID

// Save after creation
void OnCharacterCreated(bool bSuccess, FString CharacterID)
{
    if (bSuccess)
    {
        NPCCharacterIDs.Add(NPCName, CharacterID);
        SaveGame();
    }
}

// Load on game start
void InitializeNPC(const FString& NPCName)
{
    if (NPCCharacterIDs.Contains(NPCName))
    {
        CharacterAgent->CharacterID = NPCCharacterIDs[NPCName];
        // NPC is ready to chat
    }
    else
    {
        // Create new character
        CharacterAgent->CreateCharacter(GetNPCPrompt(NPCName));
    }
}
```

### 2. Error Handling

Always check for network errors:

```cpp
void OnMessageReceived(bool bSuccess, FString ResponseMessage)
{
    if (bSuccess)
    {
        // Display message in UI
        DialogueWidget->SetText(FText::FromString(ResponseMessage));
    }
    else
    {
        // Fallback to canned response
        DialogueWidget->SetText(FText::FromString("Sorry, I'm having trouble speaking right now."));
    }
}
```

### 3. Async Loading

Don't block game thread:

```cpp
// Bad: Blocking call
CharacterAgent->SendMessage(Message);
// Game freezes while waiting

// Good: Async with callback
CharacterAgent->OnMessageReceived.AddDynamic(this, &AMyNPC::HandleResponse);
CharacterAgent->SendMessage(Message);
// Game continues, response handled when ready
```

### 4. Rate Limiting

Prevent spam:

```cpp
float LastRequestTime = 0.f;
const float REQUEST_COOLDOWN = 1.0f; // 1 second

void SendChatMessage(const FString& Message)
{
    float CurrentTime = GetWorld()->GetTimeSeconds();
    if (CurrentTime - LastRequestTime < REQUEST_COOLDOWN)
    {
        UE_LOG(LogTemp, Warning, TEXT("Request too soon, please wait"));
        return;
    }

    LastRequestTime = CurrentTime;
    CharacterAgent->SendMessage(Message);
}
```

### 5. Document Updates

Update character knowledge at runtime:

```cpp
// When player discovers new lore
void OnPlayerDiscoveredLore(const FString& LoreName, const FString& LoreText)
{
    // Update quest giver's knowledge
    QuestGiverAgent->UploadDocument(
        FString::Printf(TEXT("lore_%s.txt"), *LoreName),
        LoreText
    );

    // Now quest giver can reference this lore in conversations
}
```

### 6. Multiple Character Sets

Create NPC teams:

```cpp
// Tavern NPCs
CreateCharacter("Bartender", "A chatty bartender who knows all the local gossip");
CreateCharacter("Mysterious Stranger", "A hooded figure with secrets to share");
CreateCharacter("Drunk Patron", "A jovial drunk who tells tall tales");

// Upload shared lore to all
for (auto& NPC : TavernNPCs)
{
    NPC->UploadDocument("tavern_rumors.txt", SharedRumors);
}
```

---

## Troubleshooting

### Character not responding?

```cpp
// Check health endpoint first
FString HealthURL = TEXT("http://localhost:8000/health");
// If unreachable, check:
// 1. Is Docker running?
// 2. Is RPGAI server started?
// 3. Is firewall blocking port 8000?
```

### Slow responses?

- Use Ollama with smaller models (phi3:mini) for faster responses
- Increase max_tokens limit if needed
- Consider caching common responses

### Character forgetting context?

- Check conversation history is being maintained
- Default is 20 messages - increase if needed
- Each user gets separate conversation per character

---

## Next Steps

- Add TTS integration for voice output
- Implement WebSocket for real-time streaming responses
- Add character emotion/animation hints
- Create character behavior trees based on AI responses

For more information, see main [README.md](README.md)
