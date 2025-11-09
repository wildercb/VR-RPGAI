# 🔊 TTS UI Guide - Where to Find the Audio Button

## ✅ What You'll See NOW

After refreshing the page (Cmd+Shift+R), you will see **TWO ways** to test TTS:

### 1. **INSTANT TEST BUTTON** (Top of Page)

```
┌──────────────────────────────────────────────────────┐
│ 🎮 RPGAI Character Testing Interface  🔊 TTS Enabled│
│                                                      │
│ Create and interact with AI characters powered by   │
│ semantic memory. Character responses include voice   │
│ audio!                                               │
│                                                      │
│     [🔊 Test TTS Now]                               │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**THIS IS THE NEW BUTTON!** Click it to:
- Instantly hear TTS without creating a character
- Verify Piper TTS is working
- Hear: "Hello! Text to speech is working perfectly..."

### 2. **AUTOMATIC AUDIO ON CHARACTER RESPONSES**

After chatting with a character, you'll see:

```
┌────────────────────────────────────────────────┐
│ Chat Messages                                  │
├────────────────────────────────────────────────┤
│                                                │
│  You: Hello!                                   │
│                                                │
│  🧙 Wizard:                                    │
│  Greetings, traveler. I am Eldrin...          │
│                               [🔊 Play]        │
│                                                │
└────────────────────────────────────────────────┘
```

**The 🔊 Play button appears AFTER the character responds!**

## 🎯 Step-by-Step Testing

### Test 1: Quick TTS Test (No Character Needed!)

1. Go to http://localhost:4020
2. **Hard refresh**: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+F5` (Windows)
3. Look at the **top** of the page under the title
4. Click the green **"🔊 Test TTS Now"** button
5. Wait 2-5 seconds
6. **AUDIO PLAYS!** You'll hear: "Hello! Text to speech is working perfectly..."
7. See green checkmark: "✅ TTS is working! Audio should be playing now."

### Test 2: Character Chat with TTS

1. Create a character (left sidebar):
   - Concept: "A wise wizard"
   - Provider: ollama
   - Model: llama3.1
   - Click "Create Character"

2. Click on your character in the list

3. Type a message: "Tell me about yourself"

4. Press Enter

5. **Character responds with TEXT**

6. **🔊 Play button appears** next to the response

7. **Audio plays automatically!**

8. Click 🔊 Play anytime to replay

## 🎬 What Each Button Does

### Green Test Button (Top of Page)
- **Location**: Header section, below the subtitle
- **Purpose**: Test TTS instantly without needing a character
- **When to use**: First time setup, verify TTS is working
- **What it does**:
  - Calls Piper TTS directly
  - Generates sample audio
  - Plays it immediately
  - Shows success/error message

### 🔊 Play Button (On Character Messages)
- **Location**: Right side of each character response
- **Purpose**: Play/replay character's voice
- **When it appears**: AFTER character sends a response
- **What it does**:
  - Plays the cached TTS audio for that specific message
  - Can click multiple times to replay
  - Stops previous audio first

## 🔍 Troubleshooting "I Don't See the Button!"

### Problem: No Test Button at Top

**Check 1**: Hard refresh browser
```
Mac: Cmd + Shift + R
Windows: Ctrl + Shift + F5
```

**Check 2**: Clear browser cache completely
- Chrome: Settings → Privacy → Clear browsing data → Cached images and files

**Check 3**: Open in incognito/private window
- This forces fresh JavaScript load

### Problem: No 🔊 Play Button on Character Messages

**This is NORMAL before chatting!** The button only appears AFTER:
1. You create a character
2. You select the character
3. You send a message
4. Character responds

Then the 🔊 button will appear next to the response.

**If still missing after response**:
1. Check browser console (F12)
2. Look for `audio_file` in the response:
   ```javascript
   {
     "message": "...",
     "audio_file": "audio_cache/abc123.wav"  // <-- Should be here!
   }
   ```
3. If missing, check backend logs:
   ```bash
   docker-compose logs backend --tail 50 | grep -i tts
   ```

## 📸 Visual Reference

### Before Creating Character:
```
┌─────────────────────────────────────┐
│ 🔊 TTS Enabled                      │
│                                     │
│ [🔊 Test TTS Now] ← CLICK THIS!    │
│                                     │
│ ⚙️ Configuration                    │
│ API URL: http://localhost:4020      │
│ User ID: test_user                  │
│                                     │
│ ➕ Create Character                 │
│ ...                                 │
└─────────────────────────────────────┘
```

### After Character Responds:
```
┌─────────────────────────────────────┐
│ Chat with: Wizard 🧙                │
├─────────────────────────────────────┤
│ You:                                │
│ Hello!                              │
│                                     │
│ Wizard:                             │
│ Greetings, young traveler...        │
│ [🔊 Play] ← THIS BUTTON APPEARS!   │
│                                     │
│ You:                                │
│ Tell me more                        │
│                                     │
│ Wizard:                             │
│ In my long years, I have...         │
│ [🔊 Play] ← ANOTHER BUTTON HERE!   │
└─────────────────────────────────────┘
```

## ✨ Success Indicators

### When TTS is Working:

1. **Page Load**:
   - ✅ "🔊 TTS Enabled" badge visible
   - ✅ "🔊 Test TTS Now" button visible

2. **Click Test Button**:
   - ✅ Button changes to "⏳ Generating audio..."
   - ✅ After 2-5 seconds: Audio plays
   - ✅ Message: "✅ TTS is working!"

3. **Character Chat**:
   - ✅ Send message → Get response
   - ✅ 🔊 Play button appears
   - ✅ Audio plays automatically
   - ✅ Console shows: "Playing audio: /audio_cache/..."

4. **Browser Console** (F12):
   ```
   TTS test successful!
   Playing audio: /audio_cache/abc123.wav
   ```

5. **Audio Files Created**:
   ```bash
   ls /Users/wilder/dev/RPGAI/audio_cache/
   # Shows .wav files
   ```

## 🚨 Common Mistakes

### ❌ Mistake 1: Looking for button before chatting
- **Wrong**: Create character → Look for 🔊 button → "Where is it?"
- **Right**: Create character → Send message → Wait for response → See 🔊 button

### ❌ Mistake 2: Not refreshing browser
- **Wrong**: Update code → Reload page normally → Old JavaScript still cached
- **Right**: Update code → Hard refresh (Cmd+Shift+R) → New JavaScript loaded

### ❌ Mistake 3: Expecting button in character list
- **Wrong**: Character list → Click character → "Where's the audio button?"
- **Right**: Click character → Send message → Response appears → 🔊 button shows

## 🎉 Quick Verification Checklist

Run through this checklist:

- [ ] Open http://localhost:4020
- [ ] Hard refresh: `Cmd+Shift+R`
- [ ] See "🔊 TTS Enabled" badge at top
- [ ] See "🔊 Test TTS Now" button
- [ ] Click test button
- [ ] Hear audio: "Hello! Text to speech is working..."
- [ ] See success message
- [ ] Create a character
- [ ] Send message to character
- [ ] Character responds
- [ ] 🔊 Play button appears
- [ ] Audio plays automatically
- [ ] Click 🔊 Play button again → Audio replays

**If ALL checked: TTS IS FULLY WORKING!** 🎊

## 📞 Still Having Issues?

Try this complete reset:

```bash
cd /Users/wilder/dev/RPGAI
docker-compose restart backend piper
sleep 5
open http://localhost:4020
```

Then in the browser:
1. Open DevTools (F12)
2. Go to Application tab
3. Click "Clear storage"
4. Click "Clear site data"
5. Hard refresh (Cmd+Shift+R)
6. Click "🔊 Test TTS Now"

---

**TLDR**:
1. Refresh page: `Cmd+Shift+R`
2. Look at TOP of page
3. Click green **"🔊 Test TTS Now"** button
4. Audio plays instantly!
