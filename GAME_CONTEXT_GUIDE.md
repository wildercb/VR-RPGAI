# Game Context & Multi-Agent Communication Guide

## New Features Added

### 1. **Game Context Integration** ✅
Characters now respond to real-time game state like location, weather, health, events, and more!

### 2. **Multi-Agent Communication** ✅
Characters can now talk to each other! NPCs remember conversations with other NPCs.

---

## How to Test (Web UI)

### Test 1: Game Context - Weather & Location

1. **Open** http://localhost:4020
2. **Create a character**: `A tavern keeper in a fantasy world`
3. **Expand "🎮 Game Context"**
4. **Set:**
   - Location: `Dark Tavern`
   - Weather: `Stormy`
   - Time of Day: `Night`
5. **Send message**: `How's business today?`

**Expected**: Character mentions the storm, night time, and how it affects the tavern.

---

### Test 2: Game Context - Health & Mood

1. **Create character**: `A healer who cares about the injured`
2. **Set context:**
   - Player Health: `30`
   - NPC Mood: `worried`
   - Recent Event: `player_attacked_by_wolves`
3. **Send message**: `Can you help me?`

**Expected**: Character reacts urgently to low health, mentions wolves, shows concern.

---

### Test 3: Multi-Agent Chat (Character-to-Character)

1. **Create TWO characters:**
   - Character A: `A wise wizard mentor`
   - Character B: `An eager young apprentice`

2. **Select Character A (Wizard)** from the character list
3. **Expand "👥 Multi-Agent Chat"**
4. **Select "eager young apprentice"** from the dropdown
5. **Send message**: `Master, I have a question about fire magic`
6. **Watch** the wizard respond to the apprentice!

7. **Now switch:** Select Character B (Apprentice)
8. **Select "wizard mentor"** in the multi-agent dropdown  
9. **Send**: `Thank you for the lesson!`

**Expected**: Both characters remember their conversation with each other!

---

### Test 4: Complex Scenario (All Features)

**Create a scene:**
- Character 1: `A village guard who protects the gates`
- Character 2: `A suspicious merchant`

**Scenario:**
1. **Select Guard**
2. **Set context:**
   - Location: `Village Gate`
   - Time: `Night`
   - Recent Event: `theft_reported_in_market`
   - NPC Mood: `alert`
3. **Send as Merchant** (multi-agent): `Good evening, guard. May I enter?`
4. **Watch** the guard respond suspiciously due to the theft event!

---

## API Testing (For Unreal/Game Integration)

### Endpoint: `POST /api/chat/send`

**Example 1: Player chat with game context**
```bash
curl -X POST http://localhost:4020/api/chat/send \
  -H "Content-Type: application/json" \
  -H "X-User-ID: player_1" \
  -d '{
    "character_id": "YOUR_CHARACTER_ID",
    "message": "What do you think about the storm?",
    "context": {
      "location": "Marketplace",
      "weather": "stormy",
      "time_of_day": "evening",
      "player_health": 85,
      "npc_mood": "nervous",
      "recent_event": "lightning_struck_nearby"
    }
  }'
```

**Example 2: NPC-to-NPC conversation**
```bash
# Merchant talking to Guard
curl -X POST http://localhost:4020/api/chat/send \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_player" \
  -d '{
    "character_id": "GUARD_CHARACTER_ID",
    "message": "I have goods to sell",
    "from_character_id": "MERCHANT_CHARACTER_ID",
    "context": {
      "location": "Town Gate",
      "time_of_day": "morning"
    }
  }'
```

---

## Context Fields Reference

All fields are optional:

```json
{
  "location": "string",           // Where the interaction happens
  "weather": "string",            // sunny, raining, stormy, snowing, foggy
  "time_of_day": "string",        // dawn, morning, noon, afternoon, evening, night, midnight
  "player_health": 0-100,         // Player's health percentage
  "player_reputation": -100 to 100, // How NPCs view the player
  "npc_health": 0-100,            // NPC's current health
  "npc_mood": "string",           // happy, sad, angry, fearful, neutral, excited
  "recent_event": "string",       // player_attacked_guard, theft_occurred, dragon_spotted, etc.
  "nearby_npcs": ["name1", "name2"], // Other NPCs in the scene
  "custom_data": {                // Any game-specific data
    "quest_status": "active",
    "inventory_gold": 250
  }
}
```

---

## Unreal Integration Example

**C++ Usage:**
```cpp
// In your NPC Blueprint/C++ class
void ANPCCharacter::SendMessageToNPC(const FString& Message)
{
    // Build context from game state
    TSharedPtr<FJsonObject> Context = MakeShareable(new FJsonObject);
    Context->SetStringField(TEXT("location"), GetCurrentLocationName());
    Context->SetStringField(TEXT("weather"), GetWeatherSystem()->GetCurrentWeather());
    Context->SetStringField(TEXT("time_of_day"), GetTimeOfDay());
    Context->SetNumberField(TEXT("npc_health"), CurrentHealth);
    
    // Check if player recently attacked anyone
    if (bPlayerAttackedRecently)
    {
        Context->SetStringField(TEXT("recent_event"), TEXT("player_hostile"));
    }
    
    // Build request
    TSharedPtr<FJsonObject> RequestBody = MakeShareable(new FJsonObject);
    RequestBody->SetStringField(TEXT("character_id"), CharacterID);
    RequestBody->SetStringField(TEXT("message"), Message);
    RequestBody->SetObjectField(TEXT("context"), Context);
    
    // Send to API
    CharacterAIComponent->SendRequest(RequestBody);
}
```

---

## Benefits for Your Game

### 1. **Dynamic Reactions**
NPCs respond differently based on:
- Time of day (shopkeeper closes at night)
- Weather (guards complain about rain)
- Health (healers notice injuries)
- Recent events (NPCs react to player actions)

### 2. **Living World**
NPCs talk to each other:
- Guards warn merchants about threats
- Shopkeepers gossip with customers  
- Quest givers coordinate with companions

### 3. **Memory Across Interactions**
- Guard remembers merchant was suspicious
- Healer remembers player was injured
- Characters build relationships over time

---

## Testing Checklist

- [ ] Game context: Weather affects dialogue
- [ ] Game context: Location mentioned in responses
- [ ] Game context: Low health triggers concern
- [ ] Game context: Recent events acknowledged
- [ ] Multi-agent: Character A talks to Character B
- [ ] Multi-agent: Character B remembers conversation with A
- [ ] Multi-agent: Memories persist across sessions
- [ ] Combined: Context + multi-agent together

---

## Next Steps

1. ✅ Test features in Web UI
2. ✅ Try API with curl
3. ⬜ Integrate with Unreal/Unity game
4. ⬜ Add more context fields as needed
5. ⬜ Build behavior trees based on responses

**Your system now meets the Aethereal challenge requirements for:**
- ✅ Dynamic AI Dialogues
- ✅ Character Memory (Mem0 semantic memory)
- ✅ In-Game Context Integration
- ✅ Multi-Agent Communication

**Still to add:**
- ⬜ Visual/Facial animations
- ⬜ Behavioral actions (attack, flee, etc.)
- ⬜ Voice integration (TTS is ready, needs testing)
