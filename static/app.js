// RPGAI Character Testing Interface

class RPGAIClient {
    constructor() {
        this.apiUrl = document.getElementById('apiUrl').value;
        this.userId = document.getElementById('userId').value;
        this.currentCharacter = null;
        this.conversationId = null;
        this.providers = [];
        this.ollamaModels = [];
        this.openrouterModels = [];
        this.allCharacters = [];  // Store all characters for multi-agent
        this.currentAudio = null;  // Currently playing audio

        // Voice recording
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;

        this.init();
    }

    init() {
        // Event listeners
        document.getElementById('createCharacterBtn').addEventListener('click', () => this.createCharacter());
        document.getElementById('refreshCharactersBtn').addEventListener('click', () => this.loadCharacters());
        document.getElementById('sendMessageBtn').addEventListener('click', () => {
            const fromCharId = document.getElementById('fromCharacterSelect')?.value || null;
            this.sendMessage(fromCharId);
        });
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const fromCharId = document.getElementById('fromCharacterSelect')?.value || null;
                this.sendMessage(fromCharId);
            }
        });
        document.getElementById('viewMemoriesBtn').addEventListener('click', () => this.viewMemories());
        document.getElementById('closeMemoryModal').addEventListener('click', () => this.closeMemoryModal());
        document.getElementById('characterRespondBtn').addEventListener('click', () => this.makeCharacterRespond());
        document.getElementById('testTTSBtn').addEventListener('click', () => this.testTTS());
        document.getElementById('voiceRecordBtn').addEventListener('click', () => this.toggleVoiceRecording());

        // Provider change handler
        document.getElementById('llmProvider').addEventListener('change', (e) => {
            this.loadModelsForProvider(e.target.value);
        });

        // Update API URL and User ID on change
        document.getElementById('apiUrl').addEventListener('change', (e) => {
            this.apiUrl = e.target.value;
        });
        document.getElementById('userId').addEventListener('change', (e) => {
            this.userId = e.target.value;
        });

        // Load providers and characters on start
        this.loadProviders();
        this.loadCharacters();
    }

    async apiRequest(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
            'X-User-ID': this.userId
        };

        const options = {
            method,
            headers
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${this.apiUrl}${endpoint}`, options);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'API request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    showError(elementId, message) {
        const el = document.getElementById(elementId);
        el.innerHTML = `<div class="error">${message}</div>`;
        setTimeout(() => el.innerHTML = '', 5000);
    }

    showSuccess(elementId, message) {
        const el = document.getElementById(elementId);
        el.innerHTML = `<div class="success">${message}</div>`;
        setTimeout(() => el.innerHTML = '', 3000);
    }

    async loadProviders() {
        try {
            const data = await this.apiRequest('/api/models/providers');
            this.providers = data.providers;

            const providerSelect = document.getElementById('llmProvider');
            providerSelect.innerHTML = this.providers
                .filter(p => p.status === 'available' || p.status === 'configured')
                .map(p => `<option value="${p.name}">${p.name} (${p.type})</option>`)
                .join('');

            // Load models for the first available provider
            if (providerSelect.options.length > 0) {
                const firstProvider = providerSelect.value;
                await this.loadModelsForProvider(firstProvider);
            } else {
                providerSelect.innerHTML = '<option value="">No providers available</option>';
                document.getElementById('llmModel').innerHTML = '<option value="">No providers configured</option>';
            }
        } catch (error) {
            console.error('Failed to load providers:', error);
            document.getElementById('llmProvider').innerHTML = '<option value="">Failed to load providers</option>';
        }
    }

    async loadModelsForProvider(provider) {
        const modelSelect = document.getElementById('llmModel');
        modelSelect.innerHTML = '<option value="">Loading models...</option>';

        try {
            if (provider === 'ollama') {
                const data = await this.apiRequest('/api/models/ollama');
                this.ollamaModels = data.models;

                if (this.ollamaModels.length === 0) {
                    modelSelect.innerHTML = '<option value="">No Ollama models installed</option>';
                    return;
                }

                modelSelect.innerHTML = this.ollamaModels.map(m =>
                    `<option value="${m.name}">${m.name}</option>`
                ).join('');
            } else if (provider === 'openrouter') {
                const data = await this.apiRequest('/api/models/openrouter');
                this.openrouterModels = data.models;

                modelSelect.innerHTML = this.openrouterModels.map(m =>
                    `<option value="${m.name}">${m.description} (${m.pricing})</option>`
                ).join('');
            }
        } catch (error) {
            console.error('Failed to load models:', error);
            modelSelect.innerHTML = '<option value="">Failed to load models</option>';
        }
    }

    async createCharacter() {
        const prompt = document.getElementById('characterPrompt').value.trim();
        const llmProvider = document.getElementById('llmProvider').value;
        const llmModel = document.getElementById('llmModel').value;

        if (!prompt) {
            this.showError('createError', 'Please enter a character concept');
            return;
        }

        if (!llmProvider || !llmModel) {
            this.showError('createError', 'Please select a provider and model');
            return;
        }

        const btn = document.getElementById('createCharacterBtn');
        btn.disabled = true;
        btn.textContent = 'Creating...';

        try {
            const requestBody = {
                prompt,
                llm_provider: llmProvider,
                llm_model: llmModel
            };

            const character = await this.apiRequest('/api/characters', 'POST', requestBody);

            this.showSuccess('createError', `Character "${character.name}" created!`);
            document.getElementById('characterPrompt').value = '';

            await this.loadCharacters();
            this.selectCharacter(character);
        } catch (error) {
            this.showError('createError', `Failed to create character: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Create Character';
        }
    }

    async loadCharacters() {
        console.log('loadCharacters() called');
        const listEl = document.getElementById('charactersList');
        listEl.innerHTML = '<div class="loading">Loading characters...</div>';

        try {
            const characters = await this.apiRequest('/api/characters');
            console.log('Loaded characters:', characters.length, characters.map(c => c.name));
            this.allCharacters = characters;  // Store for later use

            if (characters.length === 0) {
                listEl.innerHTML = '<div class="loading">No characters yet. Create one above!</div>';
                return;
            }

            listEl.innerHTML = characters.map(char => `
                <div class="character-item" data-id="${char.id}">
                    <h3>${char.name}</h3>
                    <p>${char.personality_summary || char.creation_prompt.substring(0, 60) + '...'}</p>
                    <p style="font-size: 11px; margin-top: 5px; opacity: 0.7;">
                        ${char.llm_provider || 'default'} / ${char.llm_model || 'default'}
                    </p>
                </div>
            `).join('');

            // Add click handlers
            document.querySelectorAll('.character-item').forEach(item => {
                item.addEventListener('click', () => {
                    const charId = item.dataset.id;
                    const character = characters.find(c => c.id === charId);
                    this.selectCharacter(character);
                });
            });

            // Update multi-agent character selector
            this.updateCharacterSelector(characters);
        } catch (error) {
            listEl.innerHTML = `<div class="error">Failed to load characters: ${error.message}</div>`;
        }
    }

    updateCharacterSelector(characters) {
        if (!characters || characters.length === 0) {
            console.warn('updateCharacterSelector: No characters provided');
            return;
        }

        console.log('updateCharacterSelector called with:', {
            charactersCount: characters.length,
            characterNames: characters.map(c => c.name),
            currentCharacter: this.currentCharacter?.name
        });

        const select = document.getElementById('fromCharacterSelect');
        if (!select) {
            console.warn('fromCharacterSelect element not found!');
        } else {
            // Keep "Player (You)" option and add all characters
            select.innerHTML = '<option value="">-- Player (You) --</option>' +
                characters.map(char =>
                    `<option value="${char.id}">${char.name}</option>`
                ).join('');
            console.log('fromCharacterSelect updated with', select.options.length, 'options');
        }

        // Also update the responding character selector
        const respondSelect = document.getElementById('respondingCharacterSelect');
        if (!respondSelect) {
            console.error('respondingCharacterSelect element not found!');
            return;
        }

        const currentCharId = this.currentCharacter?.id;

        // If no character is selected, show all characters
        // If a character is selected, exclude it from the list
        const availableCharacters = currentCharId
            ? characters.filter(char => char.id !== currentCharId)
            : characters;

        console.log('Updating respondingCharacterSelect:', {
            totalCharacters: characters.length,
            currentCharacterId: currentCharId,
            availableCharactersCount: availableCharacters.length,
            availableCharacterNames: availableCharacters.map(c => c.name)
        });

        const optionsHtml = '<option value="">-- Select Character --</option>' +
            availableCharacters
                .map(char => `<option value="${char.id}">${char.name}</option>`)
                .join('');

        console.log('Generated HTML for dropdown (first 200 chars):', optionsHtml.substring(0, 200));

        respondSelect.innerHTML = optionsHtml;

        console.log('respondingCharacterSelect now has', respondSelect.options.length, 'options:',
            Array.from(respondSelect.options).map(o => o.text));
    }

    selectCharacter(character) {
        console.log('selectCharacter() called with:', character.name);
        this.currentCharacter = character;
        this.conversationId = null;

        // Update UI
        document.querySelectorAll('.character-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.id === character.id) {
                item.classList.add('active');
            }
        });

        document.getElementById('chatTitle').textContent = character.name;
        const subtitle = character.personality_summary || character.creation_prompt;
        const modelInfo = `${character.llm_provider || 'default'} / ${character.llm_model || 'default'}`;
        document.getElementById('chatSubtitle').textContent = `${subtitle} • Model: ${modelInfo}`;
        document.getElementById('viewMemoriesBtn').style.display = 'block';

        // Clear chat and enable input
        document.getElementById('chatMessages').innerHTML = `
            <div class="message assistant">
                <div class="message-avatar">${character.name[0]}</div>
                <div class="message-content">
                    Hello! I'm ${character.name}. How can I help you today?
                </div>
            </div>
        `;

        document.getElementById('messageInput').disabled = false;
        document.getElementById('sendMessageBtn').disabled = false;
        document.getElementById('messageInput').focus();

        // Update the responding character selector to exclude current character
        console.log('Calling updateCharacterSelector from selectCharacter, allCharacters:', this.allCharacters.length);
        this.updateCharacterSelector(this.allCharacters);  // Use cached characters instead of reloading
    }

    async sendMessage(fromCharacterId = null) {
        if (!this.currentCharacter) {
            this.showError('chatError', 'Please select a character first');
            return;
        }

        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message, fromCharacterId);
        input.value = '';

        const btn = document.getElementById('sendMessageBtn');
        btn.disabled = true;
        btn.textContent = 'Thinking...';

        try {
            // Build game context from UI inputs
            const context = this.buildGameContext();

            const requestBody = {
                character_id: this.currentCharacter.id,
                message
            };

            if (context) {
                requestBody.context = context;
            }

            if (fromCharacterId) {
                requestBody.from_character_id = fromCharacterId;
            }

            const response = await this.apiRequest(
                '/api/chat/send',
                'POST',
                requestBody
            );

            this.conversationId = response.conversation_id;

            // Add assistant response
            this.addMessage('assistant', response.message, null, response.audio_file);

            // Play audio if available
            if (response.audio_file) {
                this.playAudio(response.audio_file);
            }
        } catch (error) {
            this.showError('chatError', `Failed to send message: ${error.message}`);
            this.addMessage('assistant', '❌ Sorry, I encountered an error. Please try again.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Send';
            input.focus();
        }
    }

    async makeCharacterRespond() {
        const respondingCharSelect = document.getElementById('respondingCharacterSelect');
        const respondingCharId = respondingCharSelect?.value;

        console.log('makeCharacterRespond called:', {
            respondingCharId,
            currentCharacter: this.currentCharacter?.name,
            allCharactersCount: this.allCharacters.length
        });

        if (!respondingCharId) {
            this.showError('chatError', 'Please select a character to respond');
            return;
        }

        if (!this.currentCharacter) {
            this.showError('chatError', 'No active conversation to respond to');
            return;
        }

        const btn = document.getElementById('characterRespondBtn');
        btn.disabled = true;
        btn.textContent = 'Thinking...';

        try {
            // Get the selected character's details from stored characters
            const respondingChar = this.allCharacters.find(c => c.id === respondingCharId);

            if (!respondingChar) {
                throw new Error('Character not found. Please refresh the character list.');
            }

            // Get recent messages to build context
            const messagesEl = document.getElementById('chatMessages');
            const recentMessages = Array.from(messagesEl.querySelectorAll('.message'))
                .slice(-3)  // Last 3 messages
                .map(msg => {
                    const content = msg.querySelector('.message-content').textContent;
                    return content;
                })
                .join('\n');

            // Build the automatic response message
            const autoMessage = `Based on the recent conversation: "${recentMessages}", what is your response?`;

            // Build context
            const context = this.buildGameContext();

            const requestBody = {
                character_id: respondingCharId,
                message: autoMessage,
                from_character_id: this.currentCharacter.id  // Responding to current character
            };

            if (context) {
                requestBody.context = context;
            }

            const response = await this.apiRequest(
                '/api/chat/send',
                'POST',
                requestBody
            );

            // Add the responding character's message to chat
            this.addCharacterMessage(respondingChar.name, response.message, response.audio_file);

            // Play audio if available
            if (response.audio_file) {
                this.playAudio(response.audio_file);
            }

        } catch (error) {
            this.showError('chatError', `Failed to get character response: ${error.message}`);
        } finally {
            btn.disabled = false;
            btn.textContent = '💬 Respond';
        }
    }

    addCharacterMessage(characterName, content, audioFile = null) {
        const messagesEl = document.getElementById('chatMessages');

        let audioButton = '';
        if (audioFile) {
            audioButton = `
                <button
                    onclick="window.rpgaiClient.playAudio('${audioFile}')"
                    style="margin-left: 10px; padding: 4px 8px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
                    title="Play audio">
                    🔊 Play
                </button>
            `;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';
        messageDiv.innerHTML = `
            <div class="message-avatar">${characterName[0]}</div>
            <div class="message-content">
                <strong style="color: #764ba2; font-size: 12px;">${characterName}:</strong><br>
                ${this.escapeHtml(content)}
                ${audioButton}
            </div>
        `;

        messagesEl.appendChild(messageDiv);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    buildGameContext() {
        const location = document.getElementById('gameLocation')?.value;
        const weather = document.getElementById('gameWeather')?.value;
        const timeOfDay = document.getElementById('gameTime')?.value;
        const playerHealth = document.getElementById('playerHealth')?.value;
        const npcHealth = document.getElementById('npcHealth')?.value;
        const recentEvent = document.getElementById('recentEvent')?.value;
        const npcMood = document.getElementById('npcMood')?.value;

        // Only include non-empty values
        const context = {};
        if (location) context.location = location;
        if (weather) context.weather = weather;
        if (timeOfDay) context.time_of_day = timeOfDay;
        if (playerHealth) context.player_health = parseInt(playerHealth);
        if (npcHealth) context.npc_health = parseInt(npcHealth);
        if (recentEvent) context.recent_event = recentEvent;
        if (npcMood) context.npc_mood = npcMood;

        return Object.keys(context).length > 0 ? context : null;
    }

    addMessage(role, content, characterName = null, audioFile = null) {
        const messagesEl = document.getElementById('chatMessages');

        const avatar = role === 'user'
            ? this.userId[0].toUpperCase()
            : (characterName ? characterName[0] : this.currentCharacter.name[0]);

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        let audioButton = '';
        if (audioFile && role === 'assistant') {
            audioButton = `
                <button
                    onclick="window.rpgaiClient.playAudio('${audioFile}')"
                    style="margin-left: 10px; padding: 4px 8px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;"
                    title="Play audio">
                    🔊 Play
                </button>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                ${characterName ? `<strong style="color: #764ba2; font-size: 12px;">${characterName}:</strong><br>` : ''}
                ${this.escapeHtml(content)}
                ${audioButton}
            </div>
        `;

        messagesEl.appendChild(messageDiv);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    playAudio(audioFile) {
        if (!audioFile) return;

        // Stop any currently playing audio
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio = null;
        }

        // Create and play new audio
        const audioUrl = `/${audioFile}`;
        console.log('Playing audio:', audioUrl);

        this.currentAudio = new Audio(audioUrl);
        this.currentAudio.play().catch(error => {
            console.error('Audio playback failed:', error);
            this.showError('chatError', 'Failed to play audio');
        });
    }

    async testTTS() {
        const btn = document.getElementById('testTTSBtn');
        const resultEl = document.getElementById('ttsTestResult');

        btn.disabled = true;
        btn.textContent = '⏳ Generating audio...';
        resultEl.textContent = '';

        try {
            // Call backend TTS test endpoint
            const response = await fetch(`${this.apiUrl}/api/chat/test-tts`);

            if (!response.ok) {
                throw new Error('TTS service unavailable');
            }

            const audioBlob = await response.blob();
            const audioUrl = URL.createObjectURL(audioBlob);

            // Play the audio
            if (this.currentAudio) {
                this.currentAudio.pause();
            }

            this.currentAudio = new Audio(audioUrl);
            await this.currentAudio.play();

            resultEl.textContent = '✅ TTS is working! Audio should be playing now.';
            resultEl.style.color = '#10b981';
            btn.textContent = '🔊 Test TTS Now';

            console.log('TTS test successful!');

        } catch (error) {
            console.error('TTS test failed:', error);
            resultEl.textContent = '❌ TTS test failed. Check console for details.';
            resultEl.style.color = '#ef4444';
            btn.textContent = '🔊 Test TTS Now';
        } finally {
            btn.disabled = false;
        }
    }

    async viewMemories() {
        if (!this.currentCharacter) return;

        const modal = document.getElementById('memoryModal');
        const content = document.getElementById('memoriesContent');

        modal.classList.add('active');
        content.innerHTML = '<div class="loading">Loading memories...</div>';

        try {
            const data = await this.apiRequest(`/api/chat/${this.currentCharacter.id}/memories`);

            if (!data.enabled) {
                content.innerHTML = '<p>Memory system is disabled.</p>';
                return;
            }

            if (data.memories.length === 0) {
                content.innerHTML = '<p>No memories yet. Have a conversation to create some!</p>';
                return;
            }

            content.innerHTML = `
                <p style="margin-bottom: 15px; color: #666;">
                    Total memories: ${data.total_memories}
                </p>
                ${data.memories.map(mem => `
                    <div class="memory-item">
                        <div class="memory-item-content">${this.escapeHtml(mem.content)}</div>
                        <div class="memory-item-meta">
                            ${mem.created_at ? new Date(mem.created_at).toLocaleString() : 'Unknown time'}
                        </div>
                    </div>
                `).join('')}
            `;
        } catch (error) {
            content.innerHTML = `<div class="error">Failed to load memories: ${error.message}</div>`;
        }
    }

    closeMemoryModal() {
        document.getElementById('memoryModal').classList.remove('active');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async toggleVoiceRecording() {
        if (this.isRecording) {
            // Stop recording
            this.stopRecording();
        } else {
            // Start recording
            await this.startRecording();
        }
    }

    async startRecording() {
        const btn = document.getElementById('voiceRecordBtn');
        const statusEl = document.getElementById('voiceRecordStatus');

        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // Create MediaRecorder
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = async () => {
                // Create audio blob from recorded chunks
                // MediaRecorder typically produces webm or ogg
                const mimeType = this.mediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(this.audioChunks, { type: mimeType });

                console.log('Recorded audio:', { type: mimeType, size: audioBlob.size });

                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop());

                // Transcribe the audio
                await this.transcribeAudio(audioBlob);

                // Reset state
                this.audioChunks = [];
                this.isRecording = false;
                btn.textContent = '🎤 Record Voice';
                btn.style.background = '#667eea';
                statusEl.textContent = '';
            };

            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;

            btn.textContent = '⏹️ Stop Recording';
            btn.style.background = '#ef4444';
            statusEl.textContent = '🔴 Recording... Click to stop';
            statusEl.style.color = '#ef4444';

            console.log('Voice recording started');

        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError('chatError', 'Failed to access microphone. Please grant permission.');
            btn.textContent = '🎤 Record Voice';
            statusEl.textContent = '❌ Microphone access denied';
            statusEl.style.color = '#ef4444';
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
            console.log('Voice recording stopped');
        }
    }

    async transcribeAudio(audioBlob) {
        const statusEl = document.getElementById('voiceRecordStatus');

        try {
            statusEl.textContent = '⏳ Transcribing...';
            statusEl.style.color = '#f59e0b';

            // Determine file extension based on mime type
            const mimeType = audioBlob.type;
            let filename = 'recording.webm';  // Default
            if (mimeType.includes('wav')) filename = 'recording.wav';
            else if (mimeType.includes('ogg')) filename = 'recording.ogg';
            else if (mimeType.includes('mp4')) filename = 'recording.mp4';

            // Create FormData and append audio file
            const formData = new FormData();
            formData.append('audio', audioBlob, filename);

            console.log('Sending transcribe request:', { filename, type: mimeType, size: audioBlob.size });

            // Send to transcription endpoint
            const response = await fetch(`${this.apiUrl}/api/chat/transcribe`, {
                method: 'POST',
                headers: {
                    'X-User-ID': this.userId
                },
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Transcription failed');
            }

            const data = await response.json();
            const transcribedText = data.text;

            console.log('Transcription successful:', transcribedText);

            // Display transcription in chat
            this.addMessage('user', `🎤 ${transcribedText}`, null);

            // Put transcribed text in message input
            document.getElementById('messageInput').value = transcribedText;

            statusEl.textContent = `✅ Transcribed: "${transcribedText}"`;
            statusEl.style.color = '#10b981';

            // Auto-send if character is selected
            if (this.currentCharacter) {
                // Auto-send after 1 second
                setTimeout(() => {
                    this.sendMessage();
                }, 1000);
            }

        } catch (error) {
            console.error('Transcription failed:', error);
            statusEl.textContent = `❌ Transcription failed: ${error.message}`;
            statusEl.style.color = '#ef4444';
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rpgaiClient = new RPGAIClient();
});
