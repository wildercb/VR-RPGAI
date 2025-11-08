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

        this.init();
    }

    init() {
        // Event listeners
        document.getElementById('createCharacterBtn').addEventListener('click', () => this.createCharacter());
        document.getElementById('refreshCharactersBtn').addEventListener('click', () => this.loadCharacters());
        document.getElementById('sendMessageBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        document.getElementById('viewMemoriesBtn').addEventListener('click', () => this.viewMemories());
        document.getElementById('closeMemoryModal').addEventListener('click', () => this.closeMemoryModal());

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
        const listEl = document.getElementById('charactersList');
        listEl.innerHTML = '<div class="loading">Loading characters...</div>';

        try {
            const characters = await this.apiRequest('/api/characters');

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
        } catch (error) {
            listEl.innerHTML = `<div class="error">Failed to load characters: ${error.message}</div>`;
        }
    }

    selectCharacter(character) {
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
    }

    async sendMessage() {
        if (!this.currentCharacter) {
            this.showError('chatError', 'Please select a character first');
            return;
        }

        const input = document.getElementById('messageInput');
        const message = input.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addMessage('user', message);
        input.value = '';

        const btn = document.getElementById('sendMessageBtn');
        btn.disabled = true;
        btn.textContent = 'Thinking...';

        try {
            const response = await this.apiRequest(
                `/api/chat/${this.currentCharacter.id}`,
                'POST',
                { message }
            );

            this.conversationId = response.conversation_id;

            // Add assistant response
            this.addMessage('assistant', response.message);
        } catch (error) {
            this.showError('chatError', `Failed to send message: ${error.message}`);
            this.addMessage('assistant', '❌ Sorry, I encountered an error. Please try again.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Send';
            input.focus();
        }
    }

    addMessage(role, content) {
        const messagesEl = document.getElementById('chatMessages');

        const avatar = role === 'user'
            ? this.userId[0].toUpperCase()
            : this.currentCharacter.name[0];

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">${this.escapeHtml(content)}</div>
        `;

        messagesEl.appendChild(messageDiv);
        messagesEl.scrollTop = messagesEl.scrollHeight;
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
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rpgaiClient = new RPGAIClient();
});
