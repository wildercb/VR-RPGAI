# TTS API Quick Reference

## 🎯 Endpoint

```
GET/POST http://localhost:4020/api/chat/synthesize
```

## 📝 Quick Examples

### cURL (Terminal)
```bash
# GET request
curl "http://localhost:4020/api/chat/synthesize?text=Hello%20world" -o speech.wav

# POST request
curl -X POST "http://localhost:4020/api/chat/synthesize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  -o speech.wav
```

### Unity C# (One-Liner)
```csharp
// Add to coroutine:
using (var www = UnityWebRequestMultimedia.GetAudioClip(
    "http://localhost:4020/api/chat/synthesize?text=" + UnityWebRequest.EscapeURL("Hello!"),
    AudioType.WAV))
{
    yield return www.SendWebRequest();
    AudioClip clip = DownloadHandlerAudioClip.GetContent(www);
    GetComponent<AudioSource>().PlayOneShot(clip);
}
```

### Python
```python
import requests

response = requests.get(
    "http://localhost:4020/api/chat/synthesize",
    params={"text": "Hello world"}
)

with open("speech.wav", "wb") as f:
    f.write(response.content)
```

### JavaScript (Browser/Node)
```javascript
// Browser
fetch("http://localhost:4020/api/chat/synthesize?text=Hello")
  .then(r => r.blob())
  .then(blob => {
    const audio = new Audio(URL.createObjectURL(blob));
    audio.play();
  });

// Node.js
const response = await fetch("http://localhost:4020/api/chat/synthesize?text=Hello");
const buffer = await response.arrayBuffer();
fs.writeFileSync("speech.wav", Buffer.from(buffer));
```

## ⚙️ Parameters

### GET Request
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `text` | string | ✅ Yes | Text to synthesize |

### POST Request
```json
{
  "text": "Your text here",     // Required
  "voice": "en_US-danny-low"    // Optional (future feature)
}
```

## 🔊 Audio Format

- **Format**: WAV (PCM)
- **Sample Rate**: 16000 Hz
- **Bit Depth**: 16-bit
- **Channels**: Mono
- **Voice**: en_US-lessac-medium (configurable)

## 🚀 Response

- **Content-Type**: `audio/wav`
- **Status Codes**:
  - `200 OK` - Success, returns WAV file
  - `400 Bad Request` - Missing or empty text
  - `500 Internal Server Error` - TTS generation failed
  - `503 Service Unavailable` - TTS disabled

## 💡 Tips

1. **URL Encoding**: Always escape special characters in text
   - Space → `%20`
   - `!` → `%21`
   - Use `UnityWebRequest.EscapeURL()` in Unity

2. **Caching**: Same text returns cached audio (instant!)

3. **Max Length**: No hard limit, but keep under 500 chars for best performance

4. **Voice**: Change in `docker-compose.yml` (line 42):
   ```yaml
   command: --voice en_US-danny-low
   ```

## 📚 Full Documentation

- **Unity Guide**: `UNITY_TTS_INTEGRATION.md`
- **Voice Customization**: `TTS_VOICE_CUSTOMIZATION.md`
- **Testing**: `TTS_UI_GUIDE.md`
- **API Docs**: http://localhost:4020/docs

## ✅ Testing

```bash
# Test endpoint is working
curl "http://localhost:4020/api/chat/synthesize?text=test" -o test.wav && file test.wav

# Should output: "RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 16000 Hz"
```

## 🎮 Unity Quick Start

```csharp
public class TTS : MonoBehaviour
{
    IEnumerator Start()
    {
        string url = "http://localhost:4020/api/chat/synthesize?text=" +
                     UnityWebRequest.EscapeURL("Hello from Unity!");

        using (var www = UnityWebRequestMultimedia.GetAudioClip(url, AudioType.WAV))
        {
            yield return www.SendWebRequest();

            if (www.result == UnityWebRequest.Result.Success)
            {
                AudioClip clip = DownloadHandlerAudioClip.GetContent(www);
                GetComponent<AudioSource>().PlayOneShot(clip);
            }
        }
    }
}
```

**That's it! TTS in 10 lines of code.** 🎉
