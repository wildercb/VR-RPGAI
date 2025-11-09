# Interactive AI Character Room Demo

A 3D interactive demo showcasing RPGAI's voice-enabled AI characters in a customizable environment built with Three.js.

## Features

### 🎨 Room Customization
- **Change floor color** - Select any color for the floor
- **Change wall color** - Customize wall colors
- **Adjust lighting** - Choose from Bright, Normal, Dim, or Dark
- **Add furniture** - Place chairs, tables, and plants around the room

### 🤖 AI Character Interaction
- **Select characters** - Choose from your existing AI characters
- **Create new characters** - Generate new characters with custom prompts
- **Watch them move** - Characters autonomously wander around the room
- **3D visualization** - Fully rendered 3D character models with name tags

### 💬 Communication
- **Text chat** - Type messages to interact with characters
- **Voice input** - Record voice messages using your microphone
- **Voice responses** - Characters speak back using TTS (text-to-speech)
- **Animated responses** - Characters animate while speaking

### 🎮 Game Context
- The demo automatically sends game context (location, furniture count) to characters
- Characters are aware of their environment and can reference it in conversations

## How to Use

### 1. Start the Services

Make sure all services are running:

```bash
docker-compose up -d
```

### 2. Access the Demo

Open your browser and navigate to:

```
http://localhost:4020/demo-room.html
```

### 3. Interact with the Demo

1. **Click "Start Demo"** to enter the interactive room
2. **Select a character** from the left panel (or create a new one)
3. **Customize the room** using the controls on the right
4. **Chat with the character** using text or voice input at the bottom

## Controls

### Character Panel (Left)
- **Character List** - Click a character to select them
- **Refresh Characters** - Reload the character list
- **Create New Character** - Generate a new AI character

### Room Panel (Right)
- **Floor Color** - Color picker for floor
- **Wall Color** - Color picker for walls
- **Lighting** - Dropdown to adjust ambient lighting
- **Add Furniture** - Buttons to add chairs, tables, and plants
- **Reset Room** - Remove all furniture and reset colors

### Chat Panel (Bottom)
- **Text Input** - Type your message and press Enter or click Send
- **Voice Button** - Click to start recording, click again to stop and send
- **Chat History** - See the conversation history

## Features Demonstrated

This demo showcases:

1. **Character Management API** (`GET /api/characters`, `POST /api/characters`)
2. **Chat API** (`POST /api/chat/{character_id}`)
3. **Voice Recognition** (`POST /api/chat/transcribe`)
4. **Text-to-Speech** (automatic audio generation)
5. **Semantic Memory** (characters remember conversation context)
6. **Game Context Integration** (characters receive environment information)

## Technical Details

### Frontend
- **Three.js** - 3D rendering engine
- **Vanilla JavaScript** - No framework dependencies
- **Web Audio API** - Audio playback
- **MediaRecorder API** - Voice recording

### Backend Integration
- **RESTful API** - All interactions via RPGAI API
- **Multipart uploads** - Voice recordings sent as form data
- **JSON responses** - All data in JSON format
- **Real-time updates** - Dynamic character loading

### 3D Scene
- **Perspective camera** - 75° field of view
- **Directional lighting** - Realistic shadows
- **Ambient lighting** - Adjustable brightness
- **Fog effect** - Depth perception
- **Shadow mapping** - PCF soft shadows

### Character AI
- **Autonomous movement** - Characters wander randomly
- **Smooth rotation** - Characters face their movement direction
- **Speech animation** - Bounce effect during TTS playback
- **Name tags** - Dynamic canvas-based labels

## Browser Requirements

- **Modern browser** with WebGL support (Chrome, Firefox, Safari, Edge)
- **Microphone access** for voice input (optional)
- **Audio playback** capability

## Troubleshooting

### "No characters yet. Create one!"
- You haven't created any characters yet
- Click "Create New Character" to make one

### Voice button not working
- Grant microphone permissions in your browser
- Check browser console for errors
- Ensure HTTPS or localhost (mic requires secure context)

### Character not speaking
- Check that TTS is enabled in your `.env` file
- Verify Piper service is running: `docker-compose ps piper`
- Check audio is not muted in browser

### Character not visible
- Make sure you've selected a character from the left panel
- Check browser console for errors
- Refresh the page

## Extension Ideas

Want to extend this demo? Consider adding:

- **Multiple characters** in the room at once
- **Character appearance customization** (colors, sizes, accessories)
- **More furniture types** (bookshelves, windows, doors)
- **Room layouts** (different room shapes and sizes)
- **Character emotions** (facial expressions, gestures)
- **Background music** and sound effects
- **Save/load room configurations**
- **Multiplayer mode** (multiple users in same room)
- **VR support** (WebXR integration)
- **Mobile controls** (touch gestures for camera)

## API Endpoints Used

- `GET /api/characters` - Load all characters
- `POST /api/characters` - Create new character
- `POST /api/chat/{character_id}` - Send message to character
- `POST /api/chat/transcribe` - Transcribe voice to text
- `GET /audio_cache/{filename}` - Stream TTS audio

## Files

- **demo-room.html** - Main HTML interface
- **demo-room.js** - Three.js scene and API logic

## License

Part of the RPGAI project - see main README for details.
