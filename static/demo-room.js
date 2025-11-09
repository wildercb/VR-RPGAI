// Interactive AI Character Room Demo
// Uses Three.js for 3D rendering and RPGAI API for character interaction
console.log('🎮 Demo Room JS Loading - Version 4 (FIXED) 🎮');

const API_URL = window.location.origin;
// Use a consistent user ID for the demo so characters persist
const USER_ID = 'test_user';

// Three.js scene setup
let scene, camera, renderer, room;
let characters = []; // Array of character objects: { id, data, mesh, position, target, rotation, isTalking }
let selectedCharacterId = null;
let furniture = [];
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];

// Character spawn positions (circular arrangement)
const SPAWN_POSITIONS = [
    { x: 0, z: 2 },
    { x: 2, z: 0 },
    { x: 0, z: -2 },
    { x: -2, z: 0 },
    { x: 1.5, z: 1.5 },
    { x: 1.5, z: -1.5 },
    { x: -1.5, z: -1.5 },
    { x: -1.5, z: 1.5 }
];

function startDemo() {
    console.log('Starting demo...');

    // Check if Three.js is loaded
    if (typeof THREE === 'undefined') {
        alert('Three.js failed to load. Please refresh the page.');
        return;
    }

    document.getElementById('instructions').classList.add('hidden');
    document.getElementById('character-panel').style.display = 'block';
    document.getElementById('room-panel').style.display = 'block';
    document.getElementById('chat-panel').style.display = 'block';

    initThreeJS();
    loadCharacters();
    setupEventListeners();
    animate();

    console.log('Demo initialized. Scene:', scene);
}

function initThreeJS() {
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x87CEEB);
    scene.fog = new THREE.Fog(0x87CEEB, 10, 50);

    // Camera
    camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    camera.position.set(0, 5, 8);
    camera.lookAt(0, 0, 0);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    document.getElementById('canvas-container').appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 5);
    dirLight.castShadow = true;
    dirLight.shadow.camera.left = -10;
    dirLight.shadow.camera.right = 10;
    dirLight.shadow.camera.top = 10;
    dirLight.shadow.camera.bottom = -10;
    scene.add(dirLight);

    // Create room
    createRoom();

    // Window resize handler
    window.addEventListener('resize', onWindowResize, false);
}

function createRoom() {
    room = new THREE.Group();

    // Floor
    const floorGeometry = new THREE.PlaneGeometry(12, 12);
    const floorMaterial = new THREE.MeshStandardMaterial({
        color: 0x8B7355,
        roughness: 0.8,
        metalness: 0.2
    });
    const floor = new THREE.Mesh(floorGeometry, floorMaterial);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    floor.name = 'floor';
    room.add(floor);

    // Walls
    const wallMaterial = new THREE.MeshStandardMaterial({
        color: 0xF5DEB3,
        roughness: 0.9,
        side: THREE.DoubleSide
    });

    // Back wall
    const backWallGeometry = new THREE.PlaneGeometry(12, 4);
    const backWall = new THREE.Mesh(backWallGeometry, wallMaterial);
    backWall.position.set(0, 2, -6);
    backWall.receiveShadow = true;
    backWall.name = 'backWall';
    room.add(backWall);

    // Left wall
    const leftWall = new THREE.Mesh(backWallGeometry, wallMaterial);
    leftWall.position.set(-6, 2, 0);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.receiveShadow = true;
    leftWall.name = 'leftWall';
    room.add(leftWall);

    // Right wall
    const rightWall = new THREE.Mesh(backWallGeometry, wallMaterial);
    rightWall.position.set(6, 2, 0);
    rightWall.rotation.y = -Math.PI / 2;
    rightWall.receiveShadow = true;
    rightWall.name = 'rightWall';
    room.add(rightWall);

    scene.add(room);
}

function createCharacterMesh(characterData, position) {
    console.log('Creating mesh for character:', characterData.name, 'at position:', position);

    // Generate unique color from character ID (hash to hue)
    const hue = (parseInt(characterData.id.substring(0, 8), 16) % 360);
    const bodyColor = new THREE.Color(`hsl(${hue}, 70%, 50%)`);

    const characterGroup = new THREE.Group();

    // Body (use cylinder instead of capsule for compatibility)
    const bodyGeometry = new THREE.CylinderGeometry(0.3, 0.3, 1.2, 16);
    const bodyMaterial = new THREE.MeshStandardMaterial({ color: bodyColor });
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
    body.position.y = 1;
    body.castShadow = true;
    body.name = 'body';
    characterGroup.add(body);

    // Head
    const headGeometry = new THREE.SphereGeometry(0.35, 16, 16);
    const headMaterial = new THREE.MeshStandardMaterial({ color: 0xFFDBAC });
    const head = new THREE.Mesh(headGeometry, headMaterial);
    head.position.y = 2;
    head.castShadow = true;
    head.name = 'head';
    characterGroup.add(head);

    // Eyes
    const eyeGeometry = new THREE.SphereGeometry(0.08, 8, 8);
    const eyeMaterial = new THREE.MeshStandardMaterial({ color: 0x000000 });
    const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    leftEye.position.set(-0.12, 2.1, 0.3);
    characterGroup.add(leftEye);

    const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEye.position.set(0.12, 2.1, 0.3);
    characterGroup.add(rightEye);

    // Speech ring indicator (shows when character is talking)
    const ringGeometry = new THREE.RingGeometry(0.5, 0.6, 32);
    const ringMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ff00,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0
    });
    const speechRing = new THREE.Mesh(ringGeometry, ringMaterial);
    speechRing.rotation.x = -Math.PI / 2;
    speechRing.position.y = 0.05;
    speechRing.name = 'speechRing';
    characterGroup.add(speechRing);

    // Name tag
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.fillRect(0, 0, 256, 64);
    ctx.fillStyle = 'black';
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(characterData.name, 128, 42);

    const nameTexture = new THREE.CanvasTexture(canvas);
    const nameMaterial = new THREE.MeshBasicMaterial({ map: nameTexture, transparent: true });
    const nameGeometry = new THREE.PlaneGeometry(1.5, 0.4);
    const nameTag = new THREE.Mesh(nameGeometry, nameMaterial);
    nameTag.position.y = 2.8;
    nameTag.name = 'nameTag';
    characterGroup.add(nameTag);

    characterGroup.position.set(position.x, 0, position.z);

    console.log('Character mesh created successfully');
    return characterGroup;
}

function addFurniture(type) {
    let furnitureItem;

    switch (type) {
        case 'chair':
            furnitureItem = createChair();
            break;
        case 'table':
            furnitureItem = createTable();
            break;
        case 'plant':
            furnitureItem = createPlant();
            break;
    }

    // Random position in room
    const x = (Math.random() - 0.5) * 8;
    const z = (Math.random() - 0.5) * 8;
    furnitureItem.position.set(x, 0, z);

    furniture.push(furnitureItem);
    scene.add(furnitureItem);
}

function createChair() {
    const chairGroup = new THREE.Group();

    // Seat
    const seatGeometry = new THREE.BoxGeometry(0.8, 0.1, 0.8);
    const woodMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
    const seat = new THREE.Mesh(seatGeometry, woodMaterial);
    seat.position.y = 0.5;
    seat.castShadow = true;
    chairGroup.add(seat);

    // Backrest
    const backrestGeometry = new THREE.BoxGeometry(0.8, 0.8, 0.1);
    const backrest = new THREE.Mesh(backrestGeometry, woodMaterial);
    backrest.position.set(0, 0.9, -0.35);
    backrest.castShadow = true;
    chairGroup.add(backrest);

    // Legs
    const legGeometry = new THREE.CylinderGeometry(0.05, 0.05, 0.5);
    const positions = [
        [-0.3, 0.25, -0.3],
        [0.3, 0.25, -0.3],
        [-0.3, 0.25, 0.3],
        [0.3, 0.25, 0.3]
    ];

    positions.forEach(pos => {
        const leg = new THREE.Mesh(legGeometry, woodMaterial);
        leg.position.set(...pos);
        leg.castShadow = true;
        chairGroup.add(leg);
    });

    return chairGroup;
}

function createTable() {
    const tableGroup = new THREE.Group();

    // Top
    const topGeometry = new THREE.BoxGeometry(2, 0.1, 1.2);
    const woodMaterial = new THREE.MeshStandardMaterial({ color: 0xA0522D });
    const top = new THREE.Mesh(topGeometry, woodMaterial);
    top.position.y = 0.8;
    top.castShadow = true;
    tableGroup.add(top);

    // Legs
    const legGeometry = new THREE.CylinderGeometry(0.08, 0.08, 0.8);
    const positions = [
        [-0.9, 0.4, -0.5],
        [0.9, 0.4, -0.5],
        [-0.9, 0.4, 0.5],
        [0.9, 0.4, 0.5]
    ];

    positions.forEach(pos => {
        const leg = new THREE.Mesh(legGeometry, woodMaterial);
        leg.position.set(...pos);
        leg.castShadow = true;
        tableGroup.add(leg);
    });

    return tableGroup;
}

function createPlant() {
    const plantGroup = new THREE.Group();

    // Pot
    const potGeometry = new THREE.CylinderGeometry(0.2, 0.15, 0.3, 8);
    const potMaterial = new THREE.MeshStandardMaterial({ color: 0xB8860B });
    const pot = new THREE.Mesh(potGeometry, potMaterial);
    pot.position.y = 0.15;
    pot.castShadow = true;
    plantGroup.add(pot);

    // Plant (simple sphere cluster)
    const leafMaterial = new THREE.MeshStandardMaterial({ color: 0x228B22 });
    for (let i = 0; i < 5; i++) {
        const leafGeometry = new THREE.SphereGeometry(0.15 + Math.random() * 0.1, 8, 8);
        const leaf = new THREE.Mesh(leafGeometry, leafMaterial);
        leaf.position.set(
            (Math.random() - 0.5) * 0.3,
            0.4 + Math.random() * 0.3,
            (Math.random() - 0.5) * 0.3
        );
        leaf.castShadow = true;
        plantGroup.add(leaf);
    }

    return plantGroup;
}

function setupEventListeners() {
    // Floor color
    document.getElementById('floor-color').addEventListener('change', (e) => {
        const floor = room.children.find(child => child.name === 'floor');
        if (floor) {
            floor.material.color.set(e.target.value);
        }
    });

    // Wall color
    document.getElementById('wall-color').addEventListener('change', (e) => {
        const walls = room.children.filter(child => child.name && child.name.includes('Wall'));
        walls.forEach(wall => {
            wall.material.color.set(e.target.value);
        });
    });

    // Lighting
    document.getElementById('lighting').addEventListener('change', (e) => {
        const ambientLight = scene.children.find(child => child.isAmbientLight);
        const intensities = {
            'bright': 0.9,
            'normal': 0.6,
            'dim': 0.4,
            'dark': 0.2
        };
        if (ambientLight) {
            ambientLight.intensity = intensities[e.target.value];
        }
    });
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function animate() {
    requestAnimationFrame(animate);

    // Update all characters
    characters.forEach(char => {
        // Move towards target
        const dx = char.target.x - char.position.x;
        const dz = char.target.z - char.position.z;
        const distance = Math.sqrt(dx * dx + dz * dz);

        if (distance > 0.1) {
            // Move towards target
            const speed = 0.02;
            char.position.x += dx * speed;
            char.position.z += dz * speed;

            // Rotate to face movement direction
            char.rotation = Math.atan2(dx, dz);

            // Update mesh
            char.mesh.position.set(char.position.x, 0, char.position.z);
            char.mesh.rotation.y = char.rotation;
        } else if (Math.random() < 0.01) {
            // Pick new random target
            char.target.x = (Math.random() - 0.5) * 8;
            char.target.z = (Math.random() - 0.5) * 8;
        }

        // Animate speech ring if talking
        if (char.isTalking) {
            const speechRing = char.mesh.getObjectByName('speechRing');
            if (speechRing) {
                speechRing.material.opacity = 0.5 + Math.sin(Date.now() * 0.005) * 0.3;
                speechRing.rotation.z += 0.02;
            }

            // Animate head bobbing while talking
            const head = char.mesh.getObjectByName('head');
            if (head) {
                head.position.y = 2 + Math.sin(Date.now() * 0.01) * 0.05;
            }
        }

        // Make name tag always face camera
        const nameTag = char.mesh.getObjectByName('nameTag');
        if (nameTag) {
            nameTag.rotation.y = -char.mesh.rotation.y;
        }
    });

    renderer.render(scene, camera);
}

// === CHARACTER MANAGEMENT ===

// Store characters globally so click handler can access them
let loadedCharacters = [];

async function loadCharacters() {
    showStatus('Loading characters...');
    try {
        const response = await fetch(`${API_URL}/api/characters/`, {
            headers: {
                'X-User-ID': USER_ID
            }
        });

        if (!response.ok) {
            throw new Error('Failed to load characters');
        }

        const characterList = await response.json();
        console.log('Loaded characters:', characterList.length);

        // Store globally
        loadedCharacters = characterList;

        const listEl = document.getElementById('character-list');
        listEl.innerHTML = '';

        if (characterList.length === 0) {
            listEl.innerHTML = '<div style="padding: 10px; color: #666; text-align: center;">No characters yet. Create one!</div>';
            hideStatus();
            return;
        }

        // Build HTML with onclick attributes
        characterList.forEach((char, index) => {
            const item = document.createElement('div');
            item.className = 'character-item';
            item.dataset.characterId = char.id;
            item.dataset.characterIndex = index;
            item.style.cursor = 'pointer';
            item.innerHTML = `
                <div class="character-name">${char.name}</div>
                <div class="character-prompt">${char.creation_prompt.substring(0, 60)}...</div>
            `;

            console.log('Added character to list:', char.name);
            listEl.appendChild(item);
        });

        // Use event delegation - attach ONE listener to the parent
        listEl.onclick = function(e) {
            console.log('🖱️ LIST CLICKED!');
            const item = e.target.closest('.character-item');
            if (item) {
                const index = parseInt(item.dataset.characterIndex);
                const char = loadedCharacters[index];
                console.log('Character clicked:', char.name);
                console.log('Character data:', char);
                selectCharacter(char);
            } else {
                console.log('Clicked element:', e.target);
            }
        };

        hideStatus();
    } catch (error) {
        console.error('Error loading characters:', error);
        showStatus('Failed to load characters', 'error');
    }
}

function selectCharacter(charData) {
    console.log('=== SELECT CHARACTER START ===');
    console.log('Character data:', charData);
    console.log('Current characters in room:', characters.length);

    // Update UI - highlight selected character in list
    document.querySelectorAll('.character-item').forEach(item => {
        item.classList.remove('selected');
        if (item.dataset.characterId === charData.id) {
            item.classList.add('selected');
        }
    });

    // Check if character already exists in the room
    const existingChar = characters.find(c => c.id === charData.id);
    if (existingChar) {
        console.log('Character already in room, switching chat focus');
        selectedCharacterId = charData.id;
        enableChatControls(charData.name);
        showStatus(`Now chatting with ${charData.name}`);
        highlightCharacter(charData.id);
        console.log('=== SELECT CHARACTER END (existing) ===');
        return;
    }

    // Check if we can add more characters (max 8)
    if (characters.length >= SPAWN_POSITIONS.length) {
        console.log('Room is full!');
        showStatus('Room is full! (max 8 characters)', 'error');
        console.log('=== SELECT CHARACTER END (full) ===');
        return;
    }

    selectedCharacterId = charData.id;
    console.log('Selected character ID:', selectedCharacterId);

    // Get next available spawn position
    const position = SPAWN_POSITIONS[characters.length];
    console.log('Spawn position:', position);

    // Create new character mesh
    const mesh = createCharacterMesh(charData, position);
    if (!mesh) {
        console.error('Failed to create character mesh!');
        showStatus('Error creating character!', 'error');
        return;
    }

    scene.add(mesh);
    console.log('Added mesh to scene');

    // Add to characters array
    const newChar = {
        id: charData.id,
        data: charData,
        mesh: mesh,
        position: { x: position.x, z: position.z },
        target: { x: position.x, z: position.z },
        rotation: 0,
        isTalking: false
    };
    characters.push(newChar);

    console.log('Character added to characters array. Total:', characters.length);
    console.log('Characters array:', characters);

    addChatMessage('system', `${charData.name} has entered the room!`);
    showStatus(`${charData.name} added to room!`);
    enableChatControls(charData.name);

    console.log('=== SELECT CHARACTER END (new) ===');
}

// CRITICAL FIX: Simplified chat enabling function with direct DOM manipulation
function enableChatControls(characterName) {
    console.log('>>> ENABLING CHAT CONTROLS FOR:', characterName);

    // Get elements by ID - most direct way possible
    const chatInput = document.getElementById('chat-input');
    const voiceBtn = document.getElementById('voice-btn');
    const sendButtons = document.querySelectorAll('#chat-input-container button');
    const activeChar = document.getElementById('active-character');
    const activeCharName = document.getElementById('active-character-name');
    const interactBtn = document.getElementById('interact-btn');

    console.log('Elements found:');
    console.log('- chatInput:', chatInput);
    console.log('- voiceBtn:', voiceBtn);
    console.log('- sendButtons:', sendButtons.length);
    console.log('- activeChar:', activeChar);
    console.log('- activeCharName:', activeCharName);

    // FORCE enable with removeAttribute for maximum compatibility
    if (chatInput) {
        chatInput.removeAttribute('disabled');
        chatInput.disabled = false;
        chatInput.placeholder = `Talk to ${characterName}...`;
        console.log('✓ Chat input enabled, disabled attr:', chatInput.disabled);
    } else {
        console.error('✗ Chat input NOT FOUND');
    }

    if (voiceBtn) {
        voiceBtn.removeAttribute('disabled');
        voiceBtn.disabled = false;
        console.log('✓ Voice button enabled, disabled attr:', voiceBtn.disabled);
    } else {
        console.error('✗ Voice button NOT FOUND');
    }

    // Enable ALL buttons in chat container
    sendButtons.forEach((btn, idx) => {
        btn.removeAttribute('disabled');
        btn.disabled = false;
        console.log(`✓ Button ${idx} enabled, disabled attr:`, btn.disabled);
    });

    if (activeChar && activeCharName) {
        activeChar.style.display = 'block';
        activeCharName.textContent = characterName;
        console.log('✓ Active character display updated');
    }

    // Enable interact button if 2+ characters
    if (interactBtn && characters.length >= 2) {
        interactBtn.removeAttribute('disabled');
        interactBtn.disabled = false;
        console.log('✓ Interact button enabled (2+ characters)');
    }

    console.log('>>> CHAT CONTROLS ENABLE COMPLETE');
}

function highlightCharacter(characterId) {
    // Flash the character briefly
    const char = characters.find(c => c.id === characterId);
    if (char) {
        const body = char.mesh.getObjectByName('body');
        if (body) {
            const originalColor = body.material.color.clone();
            body.material.color.set(0xFFFF00); // Yellow flash
            setTimeout(() => {
                body.material.color.copy(originalColor);
            }, 300);
        }
    }
}

function clearRoom() {
    if (characters.length === 0) {
        showStatus('Room is already empty');
        return;
    }

    if (!confirm(`Remove all ${characters.length} characters from the room?`)) {
        return;
    }

    // Remove all character meshes from scene
    characters.forEach(char => {
        scene.remove(char.mesh);
    });

    // Clear characters array
    characters = [];
    selectedCharacterId = null;

    // Disable chat controls
    disableChatControls();

    // Clear chat
    document.getElementById('chat-messages').innerHTML = '';

    // Clear selection
    document.querySelectorAll('.character-item').forEach(item => {
        item.classList.remove('selected');
    });

    showStatus('Room cleared!');
}

function disableChatControls() {
    const chatInput = document.getElementById('chat-input');
    const voiceBtn = document.getElementById('voice-btn');
    const sendButtons = document.querySelectorAll('#chat-input-container button');
    const activeChar = document.getElementById('active-character');

    if (chatInput) {
        chatInput.disabled = true;
        chatInput.placeholder = 'Select a character to chat...';
    }

    if (voiceBtn) {
        voiceBtn.disabled = true;
    }

    sendButtons.forEach(btn => {
        btn.disabled = true;
    });

    if (activeChar) {
        activeChar.style.display = 'none';
    }
}

function createNewCharacter() {
    // Show modal
    const modal = document.getElementById('create-modal');
    modal.style.display = 'flex';

    // Clear previous value
    document.getElementById('new-char-prompt').value = '';
}

function closeCreateModal() {
    document.getElementById('create-modal').style.display = 'none';
}

async function confirmCreateCharacter() {
    const prompt = document.getElementById('new-char-prompt').value.trim();

    if (!prompt) {
        alert('Please describe your character concept');
        return;
    }

    closeCreateModal();
    showStatus('AI is generating your character...');

    try {
        const response = await fetch(`${API_URL}/api/characters/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': USER_ID
            },
            body: JSON.stringify({
                prompt: prompt,
                llm_model: 'granite4:micro'
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('API Error:', errorData);
            throw new Error('Failed to create character');
        }

        const newChar = await response.json();
        showStatus(`✨ Created ${newChar.name}!`);

        // Reload character list
        await loadCharacters();

        // Auto-select the new character after list reloads
        setTimeout(() => {
            const charToSelect = loadedCharacters.find(c => c.id === newChar.id);
            if (charToSelect) {
                selectCharacter(charToSelect);
            }
        }, 500);
    } catch (error) {
        console.error('Error creating character:', error);
        showStatus('Failed to create character - check console for details', 'error');
    }
}

function resetRoom() {
    // Remove all furniture
    furniture.forEach(item => {
        scene.remove(item);
    });
    furniture = [];

    // Reset colors
    document.getElementById('floor-color').value = '#8B7355';
    document.getElementById('wall-color').value = '#F5DEB3';
    document.getElementById('lighting').value = 'normal';

    // Apply default colors
    const floor = room.children.find(child => child.name === 'floor');
    if (floor) {
        floor.material.color.set(0x8B7355);
    }

    const walls = room.children.filter(child => child.name && child.name.includes('Wall'));
    walls.forEach(wall => {
        wall.material.color.set(0xF5DEB3);
    });

    const ambientLight = scene.children.find(child => child.isAmbientLight);
    if (ambientLight) {
        ambientLight.intensity = 0.6;
    }

    showStatus('Room reset!');
}

// === CHAT FUNCTIONS ===

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message || !selectedCharacterId) {
        return;
    }

    const selectedChar = characters.find(c => c.id === selectedCharacterId);
    if (!selectedChar) {
        showStatus('Please select a character first', 'error');
        return;
    }

    // Add user message to chat
    addChatMessage('user', message);
    input.value = '';

    // Show typing indicator
    showStatus(`${selectedChar.data.name} is thinking...`);

    try {
        // Build game context
        const gameContext = {
            location: 'Interactive Demo Room',
            furniture_count: furniture.length,
            other_characters: characters.filter(c => c.id !== selectedCharacterId).map(c => c.data.name)
        };

        const response = await fetch(`${API_URL}/api/chat/${selectedCharacterId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': USER_ID
            },
            body: JSON.stringify({
                message: message,
                game_context: gameContext
            })
        });

        if (!response.ok) {
            throw new Error('Chat request failed');
        }

        const data = await response.json();
        console.log('Chat API response:', data);

        // Add character response to chat (API returns 'message' field)
        const responseText = data.message || data.response || 'No response';
        console.log('Response text:', responseText);
        addChatMessage('character', responseText, selectedChar.data.name);

        // Play TTS audio if available (API returns 'audio_file' field)
        if (data.audio_file) {
            // Ensure proper URL formatting (add / if not present)
            const audioPath = data.audio_file.startsWith('/') ? data.audio_file : `/${data.audio_file}`;
            const audioUrl = `${API_URL}${audioPath}`;
            console.log('Playing audio from:', audioUrl);
            playCharacterAudio(selectedChar, audioUrl);
        }

        hideStatus();
    } catch (error) {
        console.error('Error sending message:', error);
        showStatus('Failed to send message', 'error');
    }
}

async function toggleVoiceInput() {
    const voiceBtn = document.getElementById('voice-btn');

    if (!isRecording) {
        // Start recording
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener('stop', async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                await transcribeAudio(audioBlob);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            });

            mediaRecorder.start();
            isRecording = true;
            voiceBtn.classList.add('recording');
            voiceBtn.textContent = '⏹️ Stop';
            showStatus('Recording...');
        } catch (error) {
            console.error('Error accessing microphone:', error);
            showStatus('Microphone access denied', 'error');
        }
    } else {
        // Stop recording
        mediaRecorder.stop();
        isRecording = false;
        voiceBtn.classList.remove('recording');
        voiceBtn.textContent = '🎤 Voice';
        showStatus('Processing voice...');
    }
}

async function transcribeAudio(audioBlob) {
    try {
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');

        const response = await fetch(`${API_URL}/api/chat/transcribe`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Transcription failed');
        }

        const data = await response.json();

        // Put transcribed text in input and send
        const input = document.getElementById('chat-input');
        input.value = data.text;
        await sendMessage();

        hideStatus();
    } catch (error) {
        console.error('Error transcribing audio:', error);
        showStatus('Failed to transcribe audio', 'error');
    }
}

function playCharacterAudio(character, audioUrl) {
    console.log('Playing audio for character:', character.data.name, 'URL:', audioUrl);

    // Set character as talking
    character.isTalking = true;

    // Show speech ring
    const speechRing = character.mesh.getObjectByName('speechRing');
    if (speechRing) {
        speechRing.material.opacity = 0.7;
    }

    // Play audio
    const audio = new Audio(audioUrl);

    audio.onended = () => {
        console.log('Audio playback ended for:', character.data.name);
        character.isTalking = false;
        if (speechRing) {
            speechRing.material.opacity = 0;
        }
    };

    audio.onerror = (e) => {
        console.error('Audio playback error:', e);
        character.isTalking = false;
        if (speechRing) {
            speechRing.material.opacity = 0;
        }
    };

    audio.play().catch(err => {
        console.error('Failed to play audio:', err);
        character.isTalking = false;
        if (speechRing) {
            speechRing.material.opacity = 0;
        }
    });
}

function addChatMessage(type, text, characterName = null) {
    const messagesEl = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    if (type === 'character' && characterName) {
        messageDiv.innerHTML = `
            <div class="message-sender">${characterName}</div>
            <div>${text}</div>
        `;
    } else if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-sender">You</div>
            <div>${text}</div>
        `;
    } else {
        messageDiv.textContent = text;
    }

    messagesEl.appendChild(messageDiv);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// === UI HELPERS ===

function showStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.className = 'show';
    if (type === 'error') {
        statusEl.style.background = 'rgba(220, 53, 69, 0.9)';
    } else {
        statusEl.style.background = 'rgba(0, 0, 0, 0.8)';
    }
}

function hideStatus() {
    const statusEl = document.getElementById('status');
    statusEl.classList.remove('show');
}

// === CHARACTER INTERACTION ===

async function makeCharactersInteract() {
    if (characters.length < 2) {
        showStatus('Need at least 2 characters in the room to interact', 'error');
        return;
    }

    // Pick two random characters
    const char1 = characters[Math.floor(Math.random() * characters.length)];
    let char2 = characters[Math.floor(Math.random() * characters.length)];

    // Make sure they're different
    while (char2.id === char1.id && characters.length > 1) {
        char2 = characters[Math.floor(Math.random() * characters.length)];
    }

    showStatus(`${char1.data.name} is talking to ${char2.data.name}...`);

    try {
        // Generate a random conversation starter
        const topics = [
            "What do you think about this place?",
            "Tell me about yourself.",
            "What's on your mind?",
            "How are you feeling today?",
            "What's the most interesting thing you've learned recently?"
        ];
        const topic = topics[Math.floor(Math.random() * topics.length)];

        // Character 1 asks the question
        const gameContext = {
            location: 'Interactive Demo Room',
            furniture_count: furniture.length,
            other_characters: characters.filter(c => c.id !== char1.id).map(c => c.data.name),
            speaking_to: char2.data.name
        };

        const response1 = await fetch(`${API_URL}/api/chat/${char1.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': USER_ID
            },
            body: JSON.stringify({
                message: `You are talking to ${char2.data.name}. ${topic}`,
                game_context: gameContext
            })
        });

        if (!response1.ok) throw new Error('Character 1 response failed');

        const data1 = await response1.json();
        const message1 = data1.message || 'No response';

        addChatMessage('character', message1, char1.data.name);

        // Play audio for character 1
        if (data1.audio_file) {
            const audioPath = data1.audio_file.startsWith('/') ? data1.audio_file : `/${data1.audio_file}`;
            const audioUrl = `${API_URL}${audioPath}`;
            playCharacterAudio(char1, audioUrl);

            // Wait for audio to finish before character 2 responds
            await new Promise(resolve => setTimeout(resolve, 2000));
        }

        // Character 2 responds
        showStatus(`${char2.data.name} is responding...`);

        const gameContext2 = {
            location: 'Interactive Demo Room',
            furniture_count: furniture.length,
            other_characters: characters.filter(c => c.id !== char2.id).map(c => c.data.name),
            speaking_to: char1.data.name
        };

        const response2 = await fetch(`${API_URL}/api/chat/${char2.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': USER_ID
            },
            body: JSON.stringify({
                message: `${char1.data.name} just said to you: "${message1}". Respond to them.`,
                game_context: gameContext2
            })
        });

        if (!response2.ok) throw new Error('Character 2 response failed');

        const data2 = await response2.json();
        const message2 = data2.message || 'No response';

        addChatMessage('character', message2, char2.data.name);

        // Play audio for character 2
        if (data2.audio_file) {
            const audioPath = data2.audio_file.startsWith('/') ? data2.audio_file : `/${data2.audio_file}`;
            const audioUrl = `${API_URL}${audioPath}`;
            playCharacterAudio(char2, audioUrl);
        }

        hideStatus();
    } catch (error) {
        console.error('Error making characters interact:', error);
        showStatus('Failed to make characters interact', 'error');
    }
}
