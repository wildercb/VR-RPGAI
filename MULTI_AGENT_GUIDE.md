# Multi-Agent Auto-Response Guide

## New Feature: Character Auto-Response!

Characters can now **automatically respond** to conversations by analyzing what they "see" in the chat - no need to type messages as them!

---

## How It Works

When you click the **"💬 Respond"** button:

1. The selected character **reads the last 3 messages** in the conversation
2. They **automatically formulate a response** based on:
   - What was said
   - The current game context (weather, location, etc.)
   - Their personality and memories
   - Who they're responding to
3. Their response appears in the chat with their name

---

## How to Use (Step-by-Step)

### Example: Guard & Merchant Conversation

**1. Create Two Characters:**
- Character A: `A stern village guard who protects the gates`
- Character B: `A smooth-talking traveling merchant`

**2. Start with the Guard:**
- Click on "Guard" in the character list
- You'll see: "Hello! I'm [Guard]. How can I help you today?"

**3. You (Player) say something:**
- Type: `There's been a theft in the market`
- Send

**4. Guard responds:**
- Guard: "I'll investigate immediately. Has anyone suspicious been seen?"

**5. Make the Merchant respond:**
- Expand **"👥 Multi-Agent Chat"**
- In the dropdown, select: **"Merchant"**
- Click **"💬 Respond"**

**6. Merchant automatically responds!**
- The merchant reads the conversation
- Responds appropriately: "A theft? How unfortunate. I'm just a humble merchant passing through..."

**7. Continue the conversation:**
- Switch back to typing, or have the Guard respond next
- Characters remember the entire conversation!

---

## Advanced Example: Three-Way Conversation

**Characters:**
- Wizard (selected)
- Apprentice
- Village Elder

**Flow:**
1. **You to Wizard:** "Can you teach me fire magic?"
2. **Wizard responds:** "Fire magic is dangerous. You must be careful..."
3. **Select Apprentice → Click Respond:**
   - Apprentice: "Master, I've been practicing! Can I show you?"
4. **Select Village Elder → Click Respond:**
   - Elder: "Wizard, the village needs your help with the dragon!"
5. **Continue naturally** - all characters are aware of what's being said

---

## With Game Context

Set game context to make responses more realistic:

**Example:**
- **Location:** Village Square
- **Weather:** Raining
- **Time:** Night
- **Recent Event:** Dragon sighted nearby

**Conversation:**
1. **You:** "What should we do?"
2. **Guard (selected):** "We must prepare defenses!"
3. **Elder responds (auto):** "In this weather, at night? We should wait until dawn..."
4. **Wizard responds (auto):** "I sense dark magic... this dragon may not be natural."

All characters reference the context automatically!

---

## Key Features

### ✅ Context-Aware
- Characters see the recent messages
- They respond based on game state
- They maintain their personality

### ✅ Memory Persistent
- Characters remember who said what
- Future conversations reference past interactions
- Build complex relationships over time

### ✅ Natural Flow
- Mix player chat with character auto-responses
- Create realistic multi-NPC scenes
- Test complex game scenarios

---

## Use Cases

### 1. **Quest Design Testing**
Test how NPCs react to player choices:
```
Player: "I'll help find the missing villager"
Guard: "Thank you! Check the forest"
[Merchant responds]: "Be careful, there are wolves..."
[Healer responds]: "Bring them to me if injured"
```

### 2. **NPC Relationship Building**
Watch NPCs interact with each other:
```
[Blacksmith to Guard]: "I've finished your sword"
[Guard responds]: "Excellent timing, we need it for patrol"
[Mayor responds]: "How much do we owe you?"
```

### 3. **Dynamic Story Events**
Create emergent narratives:
```
Player: "The dragon attacked!"
[Guard responds]: "Sound the alarm!"
[Wizard responds]: "I'll cast a protection spell"
[Merchant responds]: "I'm fleeing to the next town!"
```

---

## Tips

1. **Select Different Characters** - The dropdown excludes the current character
2. **Use Game Context** - Weather, location, etc. affect responses
3. **Mix Manual & Auto** - Type messages yourself or let characters respond
4. **Watch Memories** - Click "View Memories" to see what they learned
5. **Build Scenarios** - Create complex multi-NPC situations

---

## API Usage (For Games)

In your game, trigger character responses programmatically:

```cpp
// Player talks to Guard
SendMessage(GuardCharacterID, "There's been a theft");

// Make Merchant automatically respond to Guard
TSharedPtr<FJsonObject> Request = MakeShareable(new FJsonObject);
Request->SetStringField(TEXT("character_id"), MerchantCharacterID);
Request->SetStringField(TEXT("message"), "Based on recent events, what do you say?");
Request->SetStringField(TEXT("from_character_id"), GuardCharacterID);

// Merchant responds based on conversation context
```

---

## Comparison: Old vs New

### Old Way (Manual)
```
You type: "Hello merchant"
[Manually select merchant from dropdown]
You type AS merchant: "Hello guard, I have goods"
[Switch back to guard]
You type AS guard: "Show me what you have"
```

### New Way (Auto-Response)
```
You type: "Hello merchant"
[Select merchant, click Respond]
Merchant automatically: "Hello! I have fine goods today"
[Select guard, click Respond]  
Guard automatically: "Show me your wares, merchant"
```

**Much more natural and faster!**

---

## Testing Checklist

- [ ] Create 2+ characters
- [ ] Have a conversation with one character
- [ ] Select another character from dropdown
- [ ] Click "💬 Respond"
- [ ] Verify character's response makes sense
- [ ] Set game context (weather, location)
- [ ] Click respond again, verify context is used
- [ ] Check "View Memories" - characters remember each other

---

## Start Testing Now!

```bash
cd /Users/wilder/dev/RPGAI
./start.sh
```

Open http://localhost:4020

Create characters and watch them interact!
