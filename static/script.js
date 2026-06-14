import * as THREE from 'three';

// --- GAME STATE ---
const STATE = {
    START: 0,
    PLAYING: 1,
    CRASHED: 2,
    PAUSED: 3
};

let gameState = STATE.START;
let gameSpeed = 0;
const BASE_SPEED = 70; // Units per second
const MAX_SPEED = 180;
let speedRamp = 1.2; // Increase speed per second
let elapsedPlayTime = 0;
let score = 0;
let distanceSurvived = 0;
let highScore = parseInt(localStorage.getItem('roadcaster_highscore') || '0');
let highScoreBeatenThisRun = false;
let comboCount = 0;
let comboTimer = 0;
const COMBO_DURATION = 4.0; // Seconds to maintain combo

// Event Tracking
let recentEvents = [];
const EVENT_PRIORITY = {
    'crash': 6,
    'combo_milestone': 5,
    'multi_overtake': 4,
    'recovery': 3.5,
    'traffic_weave': 3.5,
    'near_miss': 3,
    'overtake': 2,
    'clean_streak': 1,
    'speed_milestone': 0.5
};

// Queue system for commentary
let lastCommentaryTime = 0;
const COMMENTARY_INTERVAL = 1000; // 1.0 seconds minimum between lines
let pendingEvent = null;
let activeCommentaryMode = 'sports';
let activeCommentaryVoice = 'Jasper';
let serverTtsEnabled = false;
let isSpeaking = false;

// Audio variables
let audioCtx = null;
let currentAudioSource = null;
let masterVolume = 0.7;
let currentTtsRequestId = 0;

// --- THREE.JS GRAPHICS ---
let container, renderer, scene, camera;
let roadSegments = [];
const SEGMENT_LENGTH = 40;
const SEGMENT_COUNT = 7;
let roadsideElements = [];
let speedLines = [];
const MAX_SPEED_LINES = 30;

// Lighting
let dirLight, ambientLight, hemLight;

// Vehicles
let playerVehicle = null;
let trafficVehicles = [];
const MAX_TRAFFIC = 15;
let nextVehicleId = 1;
let trafficSpawnTimer = 0;
let trafficSpawnInterval = 1.8; // Spawn every 1.8s base, ramps down with difficulty

// Player Lane switching
let currentLane = 1; // 0 = Left (-3.5), 1 = Center (0), 2 = Right (3.5)
const LANE_POSITIONS = [-3.5, 0, 3.5];
let targetX = 0;
let isLaneTransitioning = false;
let laneChangeTime = 0.0;
const LANE_CHANGE_DURATION = 0.22; // Quick, snappy turns
let prevLaneX = 0;

// Keyboard Input
const keys = {
    left: false,
    right: false,
    boost: false
};

// Camera shake
let cameraShake = {
    intensity: 0,
    duration: 0,
    elapsed: 0
};

// Particle System for Crash
let particles = [];

// Cleanup tracking of events per vehicle to prevent duplicate triggers
const processedNearMisses = new Set();
const processedOvertakes = new Set();

// FIFA-style action-oriented play-by-play variables
let actionQueue = [];
let speedHistory = [];
let lastSpeedSurgeTime = 0;

// Weaving tracking
let laneChangeCount = 0;
let laneChangeTimer = 0;

// Clean streak tracking
let timeSinceLastExcitingEvent = 0;
let cleanStreakIntervalCount = 0; // Trigger every 15s of clean driving

// DOM Elements
const dom = {
    hud: document.getElementById('hud'),
    hudScore: document.getElementById('hud-score'),
    hudSpeed: document.getElementById('hud-speed'),
    hudDistance: document.getElementById('hud-distance'),
    hudHighscore: document.getElementById('hud-highscore'),
    comboBadge: document.getElementById('combo-badge'),
    hudCombo: document.getElementById('hud-combo'),
    broadcastPanel: document.getElementById('broadcast-panel'),
    commentaryText: document.getElementById('commentary-text'),
    avatar: document.getElementById('commentator-avatar'),
    avatarName: document.getElementById('commentator-name'),
    avatarRole: document.getElementById('commentator-role'),
    volumeSlider: document.getElementById('volume-slider'),
    modeTabs: document.querySelectorAll('.mode-tab'),
    setupModeCards: document.querySelectorAll('.setup-mode-card'),
    startOverlay: document.getElementById('start-overlay'),
    gameoverOverlay: document.getElementById('gameover-overlay'),
    startBtn: document.getElementById('start-btn'),
    restartBtn: document.getElementById('restart-btn'),
    ttsLabel: document.getElementById('tts-type-label'),
    voiceSelect: document.getElementById('voice-select'),
    voiceBtns: document.querySelectorAll('.voice-btn'),
    
    // Debug panel elements
    debugTtsStatus: document.getElementById('debug-tts-status'),
    debugEventType: document.getElementById('debug-event-type'),
    debugMetaSpeed: document.getElementById('debug-meta-speed'),
    debugMetaCombo: document.getElementById('debug-meta-combo'),
    debugMetaVehicle: document.getElementById('debug-meta-vehicle'),
    debugMetaDist: document.getElementById('debug-meta-dist'),
    debugContextTags: document.getElementById('debug-context-tags'),
    debugMetricMomentum: document.getElementById('debug-metric-momentum'),
    debugMetricPool: document.getElementById('debug-metric-pool'),
    debugMetricVoice: document.getElementById('debug-metric-voice'),
    debugJsonDisplay: document.getElementById('debug-json-display'),
    debugPanel: document.getElementById('debug-panel'),
    toggleDebugBtn: document.getElementById('toggle-debug-btn')
};

// --- INITIALIZATION ---
function init() {
    setupDomListeners();
    checkBackendStatus();
    initThree();
    createEnvironment();
    createPlayer();
    
    // Start Animation Loop
    let lastTime = performance.now();
    function animate(currentTime) {
        requestAnimationFrame(animate);
        
        let dt = (currentTime - lastTime) / 1000.0;
        if (dt > 0.1) dt = 0.1; // Cap dt to prevent massive jumps when tab loses focus
        lastTime = currentTime;
        
        update(dt);
        render();
    }
    requestAnimationFrame(animate);
}

// Check Backend Status (TTS Check)
async function checkBackendStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        if (data.tts_enabled) {
            serverTtsEnabled = true;
            dom.ttsLabel.textContent = "Local TTS";
            dom.ttsLabel.className = "tts-badge local-tts";
            dom.debugTtsStatus.textContent = "ONLINE (15M Nano)";
            dom.debugTtsStatus.className = "status-val success";
        } else {
            fallbackToWebSpeech("Backend disabled");
        }
    } catch (e) {
        console.error("Backend status check failed, using Web Speech API fallback:", e);
        fallbackToWebSpeech("Server unreachable");
    }
}

function fallbackToWebSpeech(reason) {
    serverTtsEnabled = false;
    dom.ttsLabel.textContent = "Browser TTS";
    dom.ttsLabel.className = "tts-badge web-tts";
    dom.debugTtsStatus.textContent = `FALLBACK (${reason})`;
    dom.debugTtsStatus.className = "status-val warning";
}

// Setup Event Listeners
function setupDomListeners() {
    // Mode selectors
    dom.modeTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            dom.modeTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeCommentaryMode = tab.dataset.mode;
            
            // Sync default voice for mode
            activeCommentaryVoice = MODE_DEFAULT_VOICES[activeCommentaryMode];
            if (dom.voiceSelect) {
                dom.voiceSelect.value = activeCommentaryVoice;
            }
            dom.voiceBtns.forEach(btn => {
                if (btn.dataset.voice === activeCommentaryVoice) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            updateCasterCharacter(activeCommentaryVoice);
        });
    });

    dom.setupModeCards.forEach(card => {
        card.addEventListener('click', () => {
            dom.setupModeCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            activeCommentaryMode = card.dataset.mode;
            
            // Sync with bottom panel
            dom.modeTabs.forEach(t => {
                if (t.dataset.mode === activeCommentaryMode) {
                    t.classList.add('active');
                } else {
                    t.classList.remove('active');
                }
            });
            
            // Sync default voice for mode
            activeCommentaryVoice = MODE_DEFAULT_VOICES[activeCommentaryMode];
            if (dom.voiceSelect) {
                dom.voiceSelect.value = activeCommentaryVoice;
            }
            dom.voiceBtns.forEach(btn => {
                if (btn.dataset.voice === activeCommentaryVoice) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            updateCasterCharacter(activeCommentaryVoice);
        });
    });

    // Voice dropdown selector in bottom HUD panel
    if (dom.voiceSelect) {
        dom.voiceSelect.addEventListener('change', (e) => {
            activeCommentaryVoice = e.target.value;
            updateCasterCharacter(activeCommentaryVoice);
            
            // Sync start screen voice buttons
            dom.voiceBtns.forEach(btn => {
                if (btn.dataset.voice === activeCommentaryVoice) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
        });
    }

    // Voice buttons selector in start overlay
    dom.voiceBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            dom.voiceBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeCommentaryVoice = btn.dataset.voice;
            
            // Automatically select and sync caster mode based on voice
            const char = VOICE_CHARACTERS[activeCommentaryVoice];
            if (char) {
                activeCommentaryMode = char.style;
                // Update bottom mode selector tabs
                dom.modeTabs.forEach(t => {
                    if (t.dataset.mode === activeCommentaryMode) {
                        t.classList.add('active');
                    } else {
                        t.classList.remove('active');
                    }
                });
                // Update start overlay mode cards
                dom.setupModeCards.forEach(c => {
                    if (c.dataset.mode === activeCommentaryMode) {
                        c.classList.add('active');
                    } else {
                        c.classList.remove('active');
                    }
                });
            }
            
            // Sync with bottom panel voice dropdown
            if (dom.voiceSelect) {
                dom.voiceSelect.value = activeCommentaryVoice;
            }
            updateCasterCharacter(activeCommentaryVoice);
        });
    });

    // Start Buttons
    dom.startBtn.addEventListener('click', startGame);
    dom.restartBtn.addEventListener('click', restartGame);
    
    // Keyboard Controls
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    
    // Volume Control
    dom.volumeSlider.addEventListener('input', (e) => {
        masterVolume = e.target.value / 100.0;
    });

    // Collapsible Debug Panel
    dom.toggleDebugBtn.addEventListener('click', () => {
        dom.debugPanel.classList.toggle('collapsed');
        dom.toggleDebugBtn.textContent = dom.debugPanel.classList.contains('collapsed') ? 'Expand' : 'Collapse';
    });

    // Window Resize
    window.addEventListener('resize', onWindowResize);
}

const VOICE_CHARACTERS = {
    'Jasper': { avatar: '🎙️', name: 'JASPER', role: 'Lead Caster', style: 'sports' },
    'Bruno': { avatar: '🏎️', name: 'BRUNO', role: 'F1 Caster', style: 'sports' },
    'Leo': { avatar: '⚽', name: 'LEO', role: 'FIFA Caster', style: 'sports' },
    'Hugo': { avatar: '🎬', name: 'HUGO', role: 'Dramatic Caster', style: 'narrator' },
    'Bella': { avatar: '📻', name: 'BELLA', role: 'Radio Host', style: 'sports' },
    'Luna': { avatar: '🌙', name: 'LUNA', role: 'Ambient Narrator', style: 'narrator' },
    'Rosie': { avatar: '🎭', name: 'ROSIE', role: 'Drama Queen', style: 'savage' },
    'Kiki': { avatar: '💀', name: 'KIKI', role: 'Toxic Caster', style: 'savage' }
};

const MODE_DEFAULT_VOICES = {
    'sports': 'Jasper',
    'narrator': 'Hugo',
    'savage': 'Kiki'
};

function updateCasterCharacter(voice) {
    const char = VOICE_CHARACTERS[voice] || VOICE_CHARACTERS['Jasper'];
    dom.avatar.textContent = char.avatar;
    dom.avatarName.textContent = char.name;
    dom.avatarRole.textContent = char.role;
    
    // Set border accent color based on voice style
    const panel = dom.broadcastPanel;
    if (char.style === 'sports') {
        panel.style.borderLeftColor = 'var(--accent-cyan)';
    } else if (char.style === 'narrator') {
        panel.style.borderLeftColor = 'var(--accent-orange)';
    } else if (char.style === 'savage') {
        panel.style.borderLeftColor = 'var(--accent-pink)';
    }
}

// Initialize Web Audio Context on first interaction
function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

// --- THREE.JS GRAPHICS SETUP ---
function initThree() {
    container = document.getElementById('canvas-container');
    
    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xa0d2f0); // Beautiful day sky blue
    scene.fog = new THREE.FogExp2(0xa0d2f0, 0.0055); // Softer fog for daytime horizon
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    container.appendChild(renderer.domElement);
    
    // Camera
    camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    // Position camera behind and above Z=0 where the player resides
    camera.position.set(0, 4.5, 9.5);
    camera.lookAt(0, 1.0, -15);
    
    // Lighting
    ambientLight = new THREE.AmbientLight(0xffffff, 0.65); // Bright day ambient fill
    scene.add(ambientLight);
    
    hemLight = new THREE.HemisphereLight(0x87ceeb, 0x556b2f, 0.45); // Sky blue to grass olive
    scene.add(hemLight);
    
    dirLight = new THREE.DirectionalLight(0xfffaf0, 2.5); // Bright warm yellow sun
    dirLight.position.set(20, 40, 20);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 100;
    const d = 15;
    dirLight.shadow.camera.left = -d;
    dirLight.shadow.camera.right = d;
    dirLight.shadow.camera.top = d;
    dirLight.shadow.camera.bottom = -d;
    scene.add(dirLight);
}

// Create Endless Road and Environment
function createEnvironment() {
    // Ground plane
    const groundGeo = new THREE.PlaneGeometry(1000, 1000);
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x2e6f40, roughness: 0.9 }); // Green grass/earth
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.05;
    ground.receiveShadow = true;
    scene.add(ground);
    
    // Road Segments
    for (let i = 0; i < SEGMENT_COUNT; i++) {
        createRoadSegment(i * -SEGMENT_LENGTH);
    }
    
    // Concrete Side Barriers
    for (let i = 0; i < SEGMENT_COUNT * 2; i++) {
        const side = i % 2 === 0 ? 1 : -1;
        const segIdx = Math.floor(i / 2);
        createSideBarrier(segIdx * -SEGMENT_LENGTH, side);
    }
    
    // Lampposts (spaced out every ~20 units on left/right sides)
    for (let i = 0; i < SEGMENT_COUNT * 2; i++) {
        const side = i % 2 === 0 ? 1 : -1;
        const z = Math.floor(i / 2) * -SEGMENT_LENGTH - (side > 0 ? 0 : SEGMENT_LENGTH/2);
        createLamppost(z, side * 7);
    }
    
    // Background distant mountains/horizon silhouettes
    createHorizonSilhouettes();
}

function createRoadSegment(z) {
    const roadGroup = new THREE.Group();
    roadGroup.position.set(0, 0, z);
    
    // Asphalt Slab (width 12 units = 3 lanes of 3.5 units plus shoulders)
    const asphaltGeo = new THREE.PlaneGeometry(13, SEGMENT_LENGTH);
    const asphaltMat = new THREE.MeshStandardMaterial({ 
        color: 0x2c2c35, // Lighter grey asphalt for daytime
        roughness: 0.7, 
        metalness: 0.1
    });
    const asphalt = new THREE.Mesh(asphaltGeo, asphaltMat);
    asphalt.rotation.x = -Math.PI / 2;
    asphalt.receiveShadow = true;
    roadGroup.add(asphalt);
    
    // Road shoulder lines (Solid White)
    const lineMat = new THREE.MeshBasicMaterial({ color: 0xcccccc });
    
    const leftBorder = new THREE.Mesh(new THREE.PlaneGeometry(0.15, SEGMENT_LENGTH), lineMat);
    leftBorder.rotation.x = -Math.PI / 2;
    leftBorder.position.set(-6, 0.01, 0);
    roadGroup.add(leftBorder);
    
    const rightBorder = leftBorder.clone();
    rightBorder.position.set(6, 0.01, 0);
    roadGroup.add(rightBorder);
    
    // Dashed Lane Markings (White dashes separating lanes)
    const dashLength = 3;
    const dashGap = 4;
    const numDashes = Math.ceil(SEGMENT_LENGTH / (dashLength + dashGap));
    
    for (let d = 0; d < numDashes; d++) {
        const dashZ = -SEGMENT_LENGTH/2 + (d * (dashLength + dashGap)) + dashLength/2;
        
        // Left lane markings
        const leftDash = new THREE.Mesh(new THREE.PlaneGeometry(0.1, dashLength), lineMat);
        leftDash.rotation.x = -Math.PI / 2;
        leftDash.position.set(-1.75, 0.01, dashZ);
        roadGroup.add(leftDash);
        
        // Right lane markings
        const rightDash = leftDash.clone();
        rightDash.position.set(1.75, 0.01, dashZ);
        roadGroup.add(rightDash);
    }
    
    scene.add(roadGroup);
    roadSegments.push(roadGroup);
}

function createSideBarrier(z, side) {
    // Concrete blocks
    const barrierGeo = new THREE.BoxGeometry(0.6, 0.8, SEGMENT_LENGTH);
    const barrierMat = new THREE.MeshStandardMaterial({ color: 0x242436, roughness: 0.9 });
    const barrier = new THREE.Mesh(barrierGeo, barrierMat);
    barrier.position.set(side * 6.5, 0.4, z);
    barrier.receiveShadow = true;
    barrier.castShadow = true;
    
    // Store metadata for scrolling
    barrier.userData = { side, type: 'barrier' };
    scene.add(barrier);
    roadsideElements.push(barrier);
}

function createLamppost(z, x) {
    const lamppost = new THREE.Group();
    lamppost.position.set(x, 0, z);
    
    // Pole
    const poleGeo = new THREE.CylinderGeometry(0.08, 0.12, 6, 8);
    const poleMat = new THREE.MeshStandardMaterial({ color: 0x1a1a2e, metalness: 0.8, roughness: 0.2 });
    const pole = new THREE.Mesh(poleGeo, poleMat);
    pole.position.y = 3;
    pole.castShadow = true;
    lamppost.add(pole);
    
    // Arm
    const armGeo = new THREE.BoxGeometry(1.5, 0.1, 0.1);
    const arm = new THREE.Mesh(armGeo, poleMat);
    // Point arm towards the road
    const dir = x > 0 ? -1 : 1;
    arm.position.set(dir * 0.7, 6, 0);
    lamppost.add(arm);
    
    // Light bulb/Fixture
    const bulbGeo = new THREE.SphereGeometry(0.2, 8, 8);
    const bulbMat = new THREE.MeshBasicMaterial({ color: 0xcccccc }); // off grey bulb during day
    const bulb = new THREE.Mesh(bulbGeo, bulbMat);
    bulb.position.set(dir * 1.45, 5.85, 0);
    lamppost.add(bulb);
    
    // Light cone (Invisible during day)
    const coneGeo = new THREE.CylinderGeometry(0.1, 5, 6, 16, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
        color: 0xffd966,
        transparent: true,
        opacity: 0.0, // turned off
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
        depthWrite: false
    });
    const cone = new THREE.Mesh(coneGeo, coneMat);
    cone.position.set(dir * 1.45, 2.9, 0);
    lamppost.add(cone);
    
    // PointLight (turned off during day)
    const light = new THREE.PointLight(0xffe699, 0.0, 12, 1.5); // 0 intensity
    light.position.set(dir * 1.45, 5.5, 0);
    light.castShadow = false;
    lamppost.add(light);
    
    lamppost.userData = { initialX: x, type: 'lamppost' };
    scene.add(lamppost);
    roadsideElements.push(lamppost);
}

function createHorizonSilhouettes() {
    // Simple buildings/mountains at the far back to scroll slowly (parallax)
    const numBuildings = 30;
    const buildingGroup = new THREE.Group();
    buildingGroup.position.set(0, 0, -250);
    
    for (let i = 0; i < numBuildings; i++) {
        const w = 15 + Math.random() * 30;
        const h = 20 + Math.random() * 60;
        const d = 15 + Math.random() * 20;
        
        const buildingGeo = new THREE.BoxGeometry(w, h, d);
        const buildingMat = new THREE.MeshBasicMaterial({ 
            color: 0x010103, // pure black/dark purple silhouette
            fog: true 
        });
        
        const b = new THREE.Mesh(buildingGeo, buildingMat);
        
        // Randomly position left or right of center road
        const side = Math.random() > 0.5 ? 1 : -1;
        const x = side * (30 + Math.random() * 150);
        b.position.set(x, h/2 - 5, Math.random() * -100);
        buildingGroup.add(b);
    }
    
    scene.add(buildingGroup);
    
    // Parallax update function
    STATE.horizonGroup = buildingGroup;
}

// Procedural Vehicles
function createPlayer() {
    playerVehicle = new THREE.Group();
    playerVehicle.position.set(0, 0.35, 0); // Positioned at Z = 0
    
    // Main Body (Glossy sports car red)
    const bodyGeo = new THREE.BoxGeometry(1.6, 0.45, 3.8);
    const bodyMat = new THREE.MeshStandardMaterial({ 
        color: 0xd80000, // Sleek chrome/red
        roughness: 0.05, 
        metalness: 1.0 
    });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.castShadow = true;
    body.receiveShadow = true;
    playerVehicle.add(body);
    
    // Cockpit
    const cockpitGeo = new THREE.BoxGeometry(1.3, 0.4, 1.8);
    const cockpitMat = new THREE.MeshStandardMaterial({ 
        color: 0x050508, // Very dark tinted glass
        roughness: 0.05, 
        metalness: 0.95 
    });
    const cockpit = new THREE.Mesh(cockpitGeo, cockpitMat);
    cockpit.position.set(0, 0.4, -0.2);
    cockpit.castShadow = true;
    playerVehicle.add(cockpit);
    
    // Windshield (cyan tinted glass at front)
    const shieldGeo = new THREE.BoxGeometry(1.25, 0.45, 0.02);
    const shieldMat = new THREE.MeshStandardMaterial({
        color: 0x00f0ff,
        transparent: true,
        opacity: 0.4,
        roughness: 0.1,
        metalness: 0.9
    });
    const shield = new THREE.Mesh(shieldGeo, shieldMat);
    shield.position.set(0, 0.4, -1.05);
    shield.rotation.x = -Math.PI / 6; // Angled aerodynamic windshield
    playerVehicle.add(shield);
    
    // Double Racing Stripes (Contrast neon cyan)
    const stripeGeo = new THREE.BoxGeometry(0.12, 0.01, 3.8);
    const stripeMat = new THREE.MeshStandardMaterial({ color: 0x00f0ff, roughness: 0.1 });
    
    const stripeL = new THREE.Mesh(stripeGeo, stripeMat);
    stripeL.position.set(-0.15, 0.23, 0);
    playerVehicle.add(stripeL);
    
    const stripeR = stripeL.clone();
    stripeR.position.x = 0.15;
    playerVehicle.add(stripeR);
    
    // Sporty Side Mirrors
    const mirrorMat = new THREE.MeshStandardMaterial({ color: 0xd80000, roughness: 0.1 });
    const mirrorGlassMat = new THREE.MeshStandardMaterial({ color: 0xffffff, metalness: 1.0, roughness: 0.05 });
    
    // Left Side Mirror
    const mirrorLGroup = new THREE.Group();
    mirrorLGroup.position.set(-0.85, 0.4, -0.5);
    const stemL = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.05, 0.05), mirrorMat);
    stemL.position.set(-0.06, 0, 0);
    mirrorLGroup.add(stemL);
    const bodyL = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.1, 0.08), mirrorMat);
    bodyL.position.set(-0.15, 0, 0);
    mirrorLGroup.add(bodyL);
    const glassL = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.08), mirrorGlassMat);
    glassL.position.set(-0.19, 0, 0.041);
    mirrorLGroup.add(glassL);
    playerVehicle.add(mirrorLGroup);
    
    // Right Side Mirror
    const mirrorRGroup = new THREE.Group();
    mirrorRGroup.position.set(0.85, 0.4, -0.5);
    const stemR = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.05, 0.05), mirrorMat);
    stemR.position.set(0.06, 0, 0);
    mirrorRGroup.add(stemR);
    const bodyR = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.1, 0.08), mirrorMat);
    bodyR.position.set(0.15, 0, 0);
    mirrorRGroup.add(bodyR);
    const glassR = new THREE.Mesh(new THREE.PlaneGeometry(0.16, 0.08), mirrorGlassMat);
    glassR.position.set(0.19, 0, 0.041);
    mirrorRGroup.add(glassR);
    playerVehicle.add(mirrorRGroup);
    
    // Spoiler
    const spoilerWingGeo = new THREE.BoxGeometry(1.8, 0.06, 0.4);
    const spoilerMat = new THREE.MeshStandardMaterial({ color: 0xd80000, roughness: 0.2 });
    const wing = new THREE.Mesh(spoilerWingGeo, spoilerMat);
    wing.position.set(0, 0.5, 1.7);
    wing.castShadow = true;
    playerVehicle.add(wing);
    
    const spoilerSupportGeo = new THREE.BoxGeometry(0.1, 0.3, 0.2);
    const supportL = new THREE.Mesh(spoilerSupportGeo, spoilerMat);
    supportL.position.set(-0.7, 0.3, 1.7);
    playerVehicle.add(supportL);
    
    const supportR = supportL.clone();
    supportR.position.x = 0.7;
    playerVehicle.add(supportR);
    
    // Headlights (Glowing Cyan emissive boxes)
    const headMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const headlightL = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.1, 0.05), headMat);
    headlightL.position.set(-0.6, 0.05, -1.91);
    playerVehicle.add(headlightL);
    
    const headlightR = headlightL.clone();
    headlightR.position.x = 0.6;
    playerVehicle.add(headlightR);
    
    // Front headlights SpotLight to project on the road (reduced for day)
    const headSpot = new THREE.SpotLight(0x00ffff, 0.5, 20, Math.PI/6, 0.5, 1);
    headSpot.position.set(0, 0.1, -1.9);
    headSpot.target.position.set(0, -0.5, -15);
    playerVehicle.add(headSpot);
    playerVehicle.add(headSpot.target);
    
    // Underglow Cyan PointLight
    const underglow = new THREE.PointLight(0x00ffff, 1.5, 4, 1.5);
    underglow.position.set(0, -0.2, 0);
    playerVehicle.add(underglow);
    
    // Taillights (Glowing Red emissive boxes)
    const tailMat = new THREE.MeshBasicMaterial({ color: 0xff0044 });
    const taillightL = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.1, 0.05), tailMat);
    taillightL.position.set(-0.6, 0.1, 1.91);
    playerVehicle.add(taillightL);
    
    const taillightR = taillightL.clone();
    taillightR.position.x = 0.6;
    playerVehicle.add(taillightR);
    
    // Chrome Exhaust Pipes
    const exhaustMat = new THREE.MeshStandardMaterial({ color: 0xaaaaaa, metalness: 0.9, roughness: 0.1 });
    const pipeL = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.5, 8), exhaustMat);
    pipeL.rotation.x = Math.PI / 2;
    pipeL.position.set(-0.5, -0.15, 1.9);
    playerVehicle.add(pipeL);
    const pipeR = pipeL.clone();
    pipeR.position.x = 0.5;
    playerVehicle.add(pipeR);
    
    // Wheels (Dark grey cylinders with shiny chrome rims)
    const wheelGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.3, 16);
    wheelGeo.rotateZ(Math.PI / 2);
    const wheelMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.8 });
    const rimGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.32, 12);
    rimGeo.rotateZ(Math.PI / 2);
    const rimMat = new THREE.MeshStandardMaterial({ color: 0xe5e4e2, metalness: 1.0, roughness: 0.05 });
    
    const wheels = [];
    const positions = [
        [-0.85, -0.05, -1.1], // Front Left
        [0.85, -0.05, -1.1],  // Front Right
        [-0.85, -0.05, 1.1],  // Rear Left
        [0.85, -0.05, 1.1]   // Rear Right
    ];
    
    positions.forEach(pos => {
        const w = new THREE.Mesh(wheelGeo, wheelMat);
        w.position.set(pos[0], pos[1], pos[2]);
        w.castShadow = true;
        
        // Add rim as child to wheel so it rotates with it!
        const rim = new THREE.Mesh(rimGeo, rimMat);
        w.add(rim);
        
        playerVehicle.add(w);
        wheels.push(w);
    });
    
    playerVehicle.userData = { wheels };
    scene.add(playerVehicle);
}

// Procedural Traffic Generator
function spawnTrafficVehicle() {
    // Determine lane to spawn in
    const occupiedLanes = new Set();
    trafficVehicles.forEach(v => {
        if (v.position.z < -180) { // Spawning safety buffer
            occupiedLanes.add(v.userData.lane);
        }
    });
    
    const freeLanes = [0, 1, 2].filter(l => !occupiedLanes.has(l));
    if (freeLanes.length === 0) return; // All lanes occupied at spawn point
    
    const lane = freeLanes[Math.floor(Math.random() * freeLanes.length)];
    
    // Determine vehicle type
    const rand = Math.random();
    let type = 'car';
    if (rand > 0.8) type = 'truck';
    else if (rand > 0.65) type = 'bus';
    
    // Instantiate vehicle mesh
    const vMesh = createTrafficMesh(type);
    vMesh.position.set(LANE_POSITIONS[lane], vMesh.userData.heightOffset, -220); // Spawns far ahead
    
    // Speed: Traffic moves slower than player
    // relative difference dictates speed of approaching vehicles
    const randomSpeed = 20 + Math.random() * 20; // 20 - 40 units/sec
    vMesh.userData.speed = randomSpeed;
    vMesh.userData.lane = lane;
    vMesh.userData.id = nextVehicleId++;
    vMesh.userData.type = type;
    
    scene.add(vMesh);
    trafficVehicles.push(vMesh);
}

function createTrafficMesh(type) {
    const group = new THREE.Group();
    
    // Pick a random nice color palette
    const colors = [
        0xcc0033, 0x1f75fe, 0xffa700, 0x00a86b, 0x7c4700,
        0x5f5f5f, 0x1c1c1c, 0xe5e4e2, 0x0070ff, 0x8b0000
    ];
    const randColor = colors[Math.floor(Math.random() * colors.length)];
    
    let hOffset = 0.35;
    
    if (type === 'car') {
        hOffset = 0.35;
        
        // Body
        const bodyGeo = new THREE.BoxGeometry(1.5, 0.45, 3.4);
        const bodyMat = new THREE.MeshStandardMaterial({ color: randColor, roughness: 0.2, metalness: 0.1 });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.castShadow = true;
        body.receiveShadow = true;
        group.add(body);
        
        // Cabin
        const cabinGeo = new THREE.BoxGeometry(1.25, 0.4, 1.7);
        const cabinMat = new THREE.MeshStandardMaterial({ color: 0x0a0a0f, roughness: 0.1 });
        const cabin = new THREE.Mesh(cabinGeo, cabinMat);
        cabin.position.set(0, 0.4, -0.1);
        cabin.castShadow = true;
        group.add(cabin);
        
        // Headlights (warm white)
        const headlightGeo = new THREE.BoxGeometry(0.2, 0.1, 0.05);
        const headlightMat = new THREE.MeshBasicMaterial({ color: 0xffffee });
        
        const hlL = new THREE.Mesh(headlightGeo, headlightMat);
        hlL.position.set(-0.55, 0.05, -1.71);
        group.add(hlL);
        
        const hlR = hlL.clone();
        hlR.position.x = 0.55;
        group.add(hlR);
        
        // Taillights
        const tlGeo = new THREE.BoxGeometry(0.25, 0.1, 0.05);
        const tlMat = new THREE.MeshBasicMaterial({ color: 0x990000 });
        const tlL = new THREE.Mesh(tlGeo, tlMat);
        tlL.position.set(-0.55, 0.1, 1.71);
        group.add(tlL);
        
        const tlR = tlL.clone();
        tlR.position.x = 0.55;
        group.add(tlR);
        
    } else if (type === 'bus') {
        hOffset = 0.75;
        
        // Bus body (large rectangular block)
        const busColor = Math.random() > 0.5 ? 0xccaa00 : 0x0044bb; // school bus yellow or transit blue
        const busGeo = new THREE.BoxGeometry(1.8, 1.5, 7.5);
        const busMat = new THREE.MeshStandardMaterial({ color: busColor, roughness: 0.4 });
        const body = new THREE.Mesh(busGeo, busMat);
        body.position.set(0, 0.4, 0);
        body.castShadow = true;
        body.receiveShadow = true;
        group.add(body);
        
        // Windows (dark horizontal strip on sides)
        const winGeoL = new THREE.PlaneGeometry(7.0, 0.35);
        const winMat = new THREE.MeshBasicMaterial({ color: 0x111122, side: THREE.DoubleSide });
        const winL = new THREE.Mesh(winGeoL, winMat);
        winL.position.set(-0.91, 0.6, 0);
        winL.rotation.y = Math.PI / 2;
        group.add(winL);
        
        const winR = winL.clone();
        winR.position.x = 0.91;
        winR.rotation.y = -Math.PI / 2;
        group.add(winR);
        
        // Front windscreen
        const screenGeo = new THREE.PlaneGeometry(1.6, 0.55);
        const screen = new THREE.Mesh(screenGeo, winMat);
        screen.position.set(0, 0.6, -3.76);
        group.add(screen);
        
        // Headlights
        const hl = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.15, 0.05), new THREE.MeshBasicMaterial({ color: 0xffffdd }));
        hl.position.set(-0.65, -0.1, -3.76);
        group.add(hl);
        
        const hlR = hl.clone();
        hlR.position.x = 0.65;
        group.add(hlR);
        
        // Taillights
        const tl = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.15, 0.05), new THREE.MeshBasicMaterial({ color: 0xaa0000 }));
        tl.position.set(-0.65, -0.1, 3.76);
        group.add(tl);
        
        const tlR = tl.clone();
        tlR.position.x = 0.65;
        group.add(tlR);
        
    } else if (type === 'truck') {
        hOffset = 0.75;
        
        // Cabin front
        const cabinColor = randColor;
        const cabGeo = new THREE.BoxGeometry(1.7, 1.4, 2.0);
        const cabMat = new THREE.MeshStandardMaterial({ color: cabinColor, roughness: 0.3 });
        const cab = new THREE.Mesh(cabGeo, cabMat);
        cab.position.set(0, 0.3, -2.4);
        cab.castShadow = true;
        group.add(cab);
        
        // Windshield
        const windMat = new THREE.MeshBasicMaterial({ color: 0x0a0a0f });
        const screen = new THREE.Mesh(new THREE.PlaneGeometry(1.5, 0.45), windMat);
        screen.position.set(0, 0.6, -3.41);
        group.add(screen);
        
        // Cargo Container Box
        const cargoGeo = new THREE.BoxGeometry(1.8, 1.7, 6.0);
        const cargoMat = new THREE.MeshStandardMaterial({ color: 0xdddddd, roughness: 0.7 }); // grey cargo trailer
        const cargo = new THREE.Mesh(cargoGeo, cargoMat);
        cargo.position.set(0, 0.45, 1.5);
        cargo.castShadow = true;
        cargo.receiveShadow = true;
        group.add(cargo);
        
        // Headlights
        const hl = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.15, 0.05), new THREE.MeshBasicMaterial({ color: 0xffffee }));
        hl.position.set(-0.6, -0.15, -3.41);
        group.add(hl);
        
        const hlR = hl.clone();
        hlR.position.x = 0.6;
        group.add(hlR);
        
        // Taillights
        const tl = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.15, 0.05), new THREE.MeshBasicMaterial({ color: 0x990000 }));
        tl.position.set(-0.6, -0.3, 4.51);
        group.add(tl);
        
        const tlR = tl.clone();
        tlR.position.x = 0.6;
        group.add(tlR);
    }
    
    // Add wheels
    const wheelGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.3, 12);
    wheelGeo.rotateZ(Math.PI / 2);
    const wheelMat = new THREE.MeshStandardMaterial({ color: 0x151515, roughness: 0.85 });
    
    const wheels = [];
    const wZPositions = type === 'car' ? [-1.0, 1.0] : (type === 'bus' ? [-2.2, 2.2] : [-2.4, 0.8, 3.2]);
    const wXDist = type === 'car' ? 0.8 : 0.9;
    
    wZPositions.forEach(zPos => {
        const wL = new THREE.Mesh(wheelGeo, wheelMat);
        wL.position.set(-wXDist, -hOffset + 0.35, zPos);
        wL.castShadow = true;
        group.add(wL);
        wheels.push(wL);
        
        const wR = new THREE.Mesh(wheelGeo, wheelMat);
        wR.position.set(wXDist, -hOffset + 0.35, zPos);
        wR.castShadow = true;
        group.add(wR);
        wheels.push(wR);
    });
    
    group.userData = { wheels, heightOffset: hOffset };
    return group;
}

// Speed Lines for High Speed Effect
function createSpeedLine() {
    const lineGeo = new THREE.BoxGeometry(0.04, 0.04, 8 + Math.random() * 8);
    const lineMat = new THREE.MeshBasicMaterial({ 
        color: 0xffffff,
        transparent: true,
        opacity: 0.25,
        depthWrite: false
    });
    const line = new THREE.Mesh(lineGeo, lineMat);
    
    // Position randomly along road shoulders, far ahead
    const side = Math.random() > 0.5 ? 1 : -1;
    const x = side * (6 + Math.random() * 4);
    const y = 0.2 + Math.random() * 3.5;
    const z = -200 - Math.random() * 100;
    
    line.position.set(x, y, z);
    scene.add(line);
    speedLines.push(line);
}

// Particle System Burst for Crashes - Advanced Graphics
function createExplosion(pos) {
    const count = 150; // High particle count
    const pGeo = new THREE.BoxGeometry(0.15, 0.15, 0.15);
    const smokeGeo = new THREE.BoxGeometry(0.3, 0.3, 0.3);
    
    // Spawns multiple categories of particles: Sparks, metal debris, and rising smoke
    for (let i = 0; i < count; i++) {
        let color, size, mat, p;
        const rand = Math.random();
        
        if (rand > 0.6) {
            // Bright orange/yellow flame sparks
            color = Math.random() > 0.5 ? 0xffaa00 : 0xff3300;
            mat = new THREE.MeshBasicMaterial({ color });
            p = new THREE.Mesh(pGeo, mat);
            p.userData = {
                type: 'spark',
                velocity: new THREE.Vector3(
                    (Math.random() - 0.5) * 16,
                    Math.random() * 12 + 4,
                    (Math.random() - 0.5) * 16
                ),
                gravity: 12,
                decay: 0.95 + Math.random() * 0.04
            };
        } else if (rand > 0.3) {
            // Silver/metallic car fragments
            color = Math.random() > 0.5 ? 0x888888 : 0x333333;
            mat = new THREE.MeshStandardMaterial({ color, metalness: 0.8, roughness: 0.2 });
            p = new THREE.Mesh(pGeo, mat);
            p.userData = {
                type: 'debris',
                velocity: new THREE.Vector3(
                    (Math.random() - 0.5) * 14,
                    Math.random() * 10 + 3,
                    (Math.random() - 0.5) * 14
                ),
                gravity: 18,
                decay: 0.98
            };
        } else {
            // Rising dark smoke particles
            color = 0x222222;
            mat = new THREE.MeshBasicMaterial({ 
                color, 
                transparent: true, 
                opacity: 0.6 
            });
            p = new THREE.Mesh(smokeGeo, mat);
            p.userData = {
                type: 'smoke',
                velocity: new THREE.Vector3(
                    (Math.random() - 0.5) * 6,
                    Math.random() * 6 + 2,
                    (Math.random() - 0.5) * 6
                ),
                gravity: -2, // rise upward slightly
                decay: 0.92
            };
        }
        
        p.position.copy(pos);
        scene.add(p);
        particles.push(p);
    }
    
    // Add point light at explosion center
    const expLight = new THREE.PointLight(0xff5500, 8, 15);
    expLight.position.copy(pos);
    scene.add(expLight);
    
    // Animate point light decay
    const decayInterval = setInterval(() => {
        if (gameState !== STATE.PLAYING) {
            expLight.intensity *= 0.9;
            if (expLight.intensity < 0.1) {
                scene.remove(expLight);
                clearInterval(decayInterval);
            }
        } else {
            scene.remove(expLight);
            clearInterval(decayInterval);
        }
    }, 50);
}

// --- CONTROLS INPUT ---
function handleKeyDown(e) {
    if (gameState !== STATE.PLAYING) return;
    
    initAudio(); // Activate audio context on keypress
    
    if (e.key === 'a' || e.key === 'ArrowLeft') {
        if (!keys.left) {
            keys.left = true;
            changeLane(-1);
        }
    } else if (e.key === 'd' || e.key === 'ArrowRight') {
        if (!keys.right) {
            keys.right = true;
            changeLane(1);
        }
    } else if (e.key === ' ' || e.key === 'ArrowUp') {
        if (!keys.boost) {
            keys.boost = true;
            actionQueue.push({
                event: 'boost_start',
                speed: Math.round(gameSpeed * 1.8),
                timestamp: elapsedPlayTime
            });
        }
    } else if (e.key === 'Escape') {
        // Pause/unpause toggle can go here if needed
    }
}

function handleKeyUp(e) {
    if (e.key === 'a' || e.key === 'ArrowLeft') {
        keys.left = false;
    } else if (e.key === 'd' || e.key === 'ArrowRight') {
        keys.right = false;
    } else if (e.key === ' ' || e.key === 'ArrowUp') {
        if (keys.boost) {
            keys.boost = false;
            actionQueue.push({
                event: 'boost_end',
                speed: Math.round(gameSpeed * 1.8),
                timestamp: elapsedPlayTime
            });
        }
    }
}

function changeLane(direction) {
    const prevLane = currentLane;
    currentLane = Math.max(0, Math.min(2, currentLane + direction));
    
    if (prevLane !== currentLane) {
        prevLaneX = playerVehicle.position.x;
        targetX = LANE_POSITIONS[currentLane];
        isLaneTransitioning = true;
        laneChangeTime = 0.0;
        
        // Log lane change action
        const actionEvent = direction < 0 ? 'swerve_left' : 'swerve_right';
        actionQueue.push({
            event: actionEvent,
            direction: direction < 0 ? 'left' : 'right',
            from_lane: prevLane,
            to_lane: currentLane,
            timestamp: elapsedPlayTime
        });

        // Track weaves
        laneChangeCount++;
        laneChangeTimer = 4.0; // Weave window
        if (laneChangeCount >= 3) {
            triggerGameplayEvent('traffic_weave', 'car');
            actionQueue.push({
                event: 'rapid_weave',
                count: laneChangeCount,
                timestamp: elapsedPlayTime
            });
            laneChangeCount = 0;
        }
    }
}

// --- GAME LOGIC UPDATE LOOP ---
function update(dt) {
    if (gameState === STATE.PLAYING) {
        elapsedPlayTime += dt;
        timeSinceLastExcitingEvent += dt;
        
        // Clean streak timer checks (every 12 seconds of quiet driving)
        if (timeSinceLastExcitingEvent > 12.0) {
            timeSinceLastExcitingEvent = 0;
            triggerGameplayEvent('clean_streak', 'car');
        }
        
        // Speed scaling (Difficulty ramp)
        let targetSpeed = BASE_SPEED + (elapsedPlayTime * speedRamp);
        if (keys.boost) {
            targetSpeed += 25; // boost gives instant extra velocity
        }
        targetSpeed = Math.min(MAX_SPEED, targetSpeed);
        
        // Lerp speed to make acceleration feel smooth
        gameSpeed = THREE.MathUtils.lerp(gameSpeed, targetSpeed, 0.08);
        
        // Track speed history for speed surges (increases by 30+ km/h in 2 seconds)
        const currentSpeedKmh = gameSpeed * 1.8;
        speedHistory.push({ time: elapsedPlayTime, speed: currentSpeedKmh });
        speedHistory = speedHistory.filter(sh => elapsedPlayTime - sh.time <= 2.0);
        if (speedHistory.length > 0) {
            const oldSpeed = speedHistory[0].speed;
            const speedDiff = currentSpeedKmh - oldSpeed;
            if (speedDiff >= 30.0 && (elapsedPlayTime - lastSpeedSurgeTime > 3.0)) {
                lastSpeedSurgeTime = elapsedPlayTime;
                actionQueue.push({
                    event: 'speed_surge',
                    from_speed: Math.round(oldSpeed),
                    to_speed: Math.round(currentSpeedKmh),
                    timestamp: elapsedPlayTime
                });
            }
        }
        
        // Score: Base points for distance traveled
        score += gameSpeed * dt * 0.2;
        distanceSurvived += gameSpeed * dt * 0.1;
        
        // Live high score crossed check
        if (score > highScore && highScore > 0 && !highScoreBeatenThisRun) {
            highScoreBeatenThisRun = true;
            triggerGameplayEvent('high_score', 'car');
        }
        
        // Update DOM elements
        dom.hudScore.textContent = Math.round(score).toLocaleString('en-US', { minimumIntegerDigits: 6, useGrouping: false });
        
        dom.hudSpeed.textContent = Math.round(currentSpeedKmh); // convert to km/h scale
        dom.hudDistance.textContent = Math.round(distanceSurvived);
        
        // Update speedometer progress gauge
        const maxSpeedKmh = MAX_SPEED * 1.8;
        const progressPercent = Math.min(1.0, currentSpeedKmh / maxSpeedKmh);
        const dashoffset = 190 - (progressPercent * 190);
        const speedProgressElement = document.getElementById('speedometer-progress');
        if (speedProgressElement) {
            speedProgressElement.style.strokeDashoffset = dashoffset;
        }
        
        // Combo decay timer
        if (comboCount > 0) {
            comboTimer -= dt;
            if (comboTimer <= 0) {
                comboCount = 0;
                dom.comboBadge.classList.add('hidden');
            }
        }
        
        // Camera Shake effect damping
        if (cameraShake.duration > 0) {
            cameraShake.elapsed += dt;
            if (cameraShake.elapsed >= cameraShake.duration) {
                cameraShake.duration = 0;
                cameraShake.intensity = 0;
            }
        }
        
        // Weaving timer decay
        if (laneChangeTimer > 0) {
            laneChangeTimer -= dt;
            if (laneChangeTimer <= 0) {
                laneChangeCount = 0;
            }
        }
        
        // Update Player lane shifting lerp
        if (isLaneTransitioning) {
            laneChangeTime += dt;
            const t = Math.min(1.0, laneChangeTime / LANE_CHANGE_DURATION);
            
            // Cubic ease out lane change transition
            const easeOut = 1 - Math.pow(1 - t, 3);
            playerVehicle.position.x = THREE.MathUtils.lerp(prevLaneX, targetX, easeOut);
            
            // Lean rotation effect
            const leanIntensity = 0.16;
            const deltaX = targetX - prevLaneX;
            playerVehicle.rotation.z = -deltaX * leanIntensity * Math.sin(t * Math.PI);
            playerVehicle.rotation.y = -deltaX * 0.05 * Math.sin(t * Math.PI);
            
            if (t >= 1.0) {
                playerVehicle.position.x = targetX;
                playerVehicle.rotation.z = 0;
                playerVehicle.rotation.y = 0;
                isLaneTransitioning = false;
            }
        }
        
        // Rotate Player Wheels
        if (playerVehicle.userData.wheels) {
            playerVehicle.userData.wheels.forEach(w => {
                w.rotation.x -= (gameSpeed * 0.15) * dt;
            });
        }
        
        // Scroll Road Segments
        roadSegments.forEach(seg => {
            seg.position.z += gameSpeed * dt;
            
            // If segment passed behind camera, recycle it to the front
            if (seg.position.z > 30) {
                // Find the segment furthest ahead
                let minZ = 0;
                roadSegments.forEach(s => {
                    if (s.position.z < minZ) minZ = s.position.z;
                });
                seg.position.z = minZ - SEGMENT_LENGTH;
            }
        });
        
        // Scroll Roadside Barriers and Lampposts
        roadsideElements.forEach(elem => {
            elem.position.z += gameSpeed * dt;
            
            // Recycle roadside elements
            if (elem.position.z > 30) {
                let minZ = 0;
                roadsideElements.forEach(e => {
                    if (e.position.z < minZ) minZ = e.position.z;
                });
                elem.position.z = minZ - SEGMENT_LENGTH / 2;
                
                // Keep lamp on the correct side
                if (elem.userData.type === 'lamppost') {
                    elem.position.x = elem.userData.initialX;
                }
            }
        });
        
        // Horizon Silhouette parallax scrolling (moves 10x slower)
        if (STATE.horizonGroup) {
            STATE.horizonGroup.position.z += gameSpeed * dt * 0.15;
            if (STATE.horizonGroup.position.z > -100) {
                STATE.horizonGroup.position.z = -280;
            }
        }
        
        // Update & Scroll Speed Lines
        updateSpeedLines(dt);
        
        // Traffic Spawning
        trafficSpawnTimer += dt;
        // Increase spawn speed with time (more cars)
        const currentInterval = Math.max(0.75, trafficSpawnInterval - (elapsedPlayTime * 0.012));
        if (trafficSpawnTimer >= currentInterval) {
            trafficSpawnTimer = 0;
            spawnTrafficVehicle();
        }
        
        // Update Traffic Vehicles
        updateTrafficVehicles(dt);
        
        // Collisions & Near Miss Checks
        checkCollisions();
        
        // Process narrative tick
        processNarrativeTick();
    }
    
    // Update active particles (even if crashed, to watch fragments fall)
    updateParticles(dt);
}

function updateSpeedLines(dt) {
    // Spawn new speed lines depending on velocity
    const numLinesNeeded = Math.min(MAX_SPEED_LINES, Math.floor((gameSpeed / MAX_SPEED) * MAX_SPEED_LINES));
    while (speedLines.length < numLinesNeeded) {
        createSpeedLine();
    }
    
    for (let i = speedLines.length - 1; i >= 0; i--) {
        const line = speedLines[i];
        line.position.z += (gameSpeed * 1.5) * dt; // speed lines fly past faster than traffic
        
        // Recycle if behind camera
        if (line.position.z > 20) {
            scene.remove(line);
            speedLines.splice(i, 1);
        }
    }
}

function updateTrafficVehicles(dt) {
    for (let i = trafficVehicles.length - 1; i >= 0; i--) {
        const tv = trafficVehicles[i];
        
        // Moves relative to road speed
        tv.position.z += (gameSpeed - tv.userData.speed) * dt;
        
        // Rotate wheels
        if (tv.userData.wheels) {
            tv.userData.wheels.forEach(w => {
                w.rotation.x -= (tv.userData.speed * 0.15) * dt;
            });
        }
        
        // Recycle vehicle once it goes past the player/camera
        if (tv.position.z > 25) {
            scene.remove(tv);
            processedNearMisses.delete(tv.userData.id);
            processedOvertakes.delete(tv.userData.id);
            trafficVehicles.splice(i, 1);
        }
    }
}

// Particle System updates
function updateParticles(dt) {
    for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        const ud = p.userData;
        
        // Apply gravity and update position
        ud.velocity.y -= ud.gravity * dt;
        p.position.addScaledVector(ud.velocity, dt);
        
        // Spin the particles for realistic debris motion
        p.rotation.x += ud.velocity.y * dt * 0.5;
        p.rotation.y += ud.velocity.x * dt * 0.5;
        
        // Shrink sparks / fade smoke
        if (ud.type === 'spark') {
            p.scale.multiplyScalar(ud.decay);
            if (p.scale.x < 0.05) {
                scene.remove(p);
                particles.splice(i, 1);
                continue;
            }
        } else if (ud.type === 'smoke') {
            if (p.material) {
                p.material.opacity *= ud.decay;
                p.scale.multiplyScalar(1.02); // expand slightly as it diffuses
                if (p.material.opacity < 0.05) {
                    scene.remove(p);
                    particles.splice(i, 1);
                    continue;
                }
            }
        }
        
        // Recycle/remove once below ground level
        if (p.position.y < -0.2) {
            scene.remove(p);
            particles.splice(i, 1);
        }
    }
}

// --- COLLISION & NEAR-MISS DETECTION ---
function checkCollisions() {
    if (gameState !== STATE.PLAYING) return;
    
    // Build player bounding box (narrowed slightly for fair gameplay)
    const playerBox = new THREE.Box3();
    const playerMin = new THREE.Vector3(-0.7, -0.1, -1.75);
    const playerMax = new THREE.Vector3(0.7, 0.8, 1.75);
    playerBox.set(playerMin.add(playerVehicle.position), playerMax.add(playerVehicle.position));
    
    // Near Miss zone box (expanded player box)
    const nearMissBox = playerBox.clone();
    nearMissBox.expandByVector(new THREE.Vector3(0.75, 0, 0.4)); // check sideways proximity
    
    trafficVehicles.forEach(tv => {
        const tvId = tv.userData.id;
        
        // Build traffic bounding box
        const tvBox = new THREE.Box3();
        let tvMin, tvMax;
        
        if (tv.userData.type === 'car') {
            tvMin = new THREE.Vector3(-0.7, -0.1, -1.6);
            tvMax = new THREE.Vector3(0.7, 0.8, 1.6);
        } else if (tv.userData.type === 'bus') {
            tvMin = new THREE.Vector3(-0.9, -0.1, -3.7);
            tvMax = new THREE.Vector3(0.9, 1.6, 3.7);
        } else { // Truck
            tvMin = new THREE.Vector3(-0.9, -0.1, -4.5);
            tvMax = new THREE.Vector3(0.9, 1.8, 4.5);
        }
        
        tvBox.set(tvMin.add(tv.position), tvMax.add(tv.position));
        
        // 1. Check CRASH
        if (playerBox.intersectsBox(tvBox)) {
            triggerCrash(tv);
            return;
        }
        
        // 2. Check NEAR MISS (only if not already near missed or overtaken)
        if (nearMissBox.intersectsBox(tvBox) && !processedNearMisses.has(tvId) && !processedOvertakes.has(tvId)) {
            // Ensure they are close in Z depth to avoid triggering near miss on distant cars
            const zDist = Math.abs(playerVehicle.position.z - tv.position.z);
            // Z depth must be inside overlap length
            if (zDist < 3.2) {
                processedNearMisses.add(tvId);
                triggerNearMiss(tv);
            }
        }
        
        // 3. Check OVERTAKE
        // When traffic Z passes player Z (since player is Z=0, when traffic goes positive, it is overtaken)
        if (tv.position.z > 0.5 && !processedOvertakes.has(tvId)) {
            processedOvertakes.add(tvId);
            triggerOvertake(tv);
        }
    });
}

function triggerNearMiss(tv) {
    timeSinceLastExcitingEvent = 0;
    
    // Visual indicators
    triggerCameraShake(0.25, 0.15);
    flashScreen('near-miss');
    
    // Increments combo
    comboCount++;
    comboTimer = COMBO_DURATION;
    
    dom.comboBadge.classList.remove('hidden');
    dom.hudCombo.textContent = `x${comboCount}`;
    
    // Score bonus
    const bonus = 25 * comboCount;
    score += bonus;
    
    // Sideways proximity check for Extreme Near Miss
    const xDist = Math.abs(playerVehicle.position.x - tv.position.x);
    const isExtreme = xDist < 1.35; // Sideways overlap proximity threshold
    
    // Determine the type of dodge action
    let isSqueeze = false;
    for (let tv2 of trafficVehicles) {
        if (tv2.userData.id !== tv.userData.id) {
            const zDist2 = Math.abs(playerVehicle.position.z - tv2.position.z);
            const xDist2 = Math.abs(playerVehicle.position.x - tv2.position.x);
            if (zDist2 < 4.0 && xDist2 < 4.0) {
                const playerX = playerVehicle.position.x;
                if ((tv.position.x - playerX) * (tv2.position.x - playerX) < 0) {
                    isSqueeze = true;
                    break;
                }
            }
        }
    }

    if (isSqueeze) {
        actionQueue.push({
            event: 'squeeze_through',
            vehicle_type: tv.userData.type,
            gap: parseFloat(xDist.toFixed(2)),
            timestamp: elapsedPlayTime
        });
    } else {
        const side = playerVehicle.position.x < tv.position.x ? 'left' : 'right';
        actionQueue.push({
            event: `dodge_${side}`,
            vehicle_type: tv.userData.type,
            gap_distance: parseFloat(xDist.toFixed(2)),
            timestamp: elapsedPlayTime
        });
    }

    if (isExtreme) {
        actionQueue.push({
            event: 'close_call',
            vehicle_type: tv.userData.type,
            distance: parseFloat(xDist.toFixed(2)),
            timestamp: elapsedPlayTime
        });
    }

    // Check milestones
    if (comboCount % 5 === 0) {
        triggerGameplayEvent('combo_milestone', tv.userData.type);
    } else {
        // Recovery check: did we have a near miss right after another very recently?
        const wasRecovery = recentEvents.length > 0 && (recentEvents[recentEvents.length - 1] === 'near_miss' || recentEvents[recentEvents.length - 1] === 'extreme_near_miss');
        if (wasRecovery) {
            triggerGameplayEvent('recovery', tv.userData.type);
        } else {
            if (isExtreme) {
                triggerGameplayEvent('extreme_near_miss', tv.userData.type);
            } else {
                triggerGameplayEvent('near_miss', tv.userData.type);
            }
        }
    }
}

function triggerOvertake(tv) {
    // If it was already a near miss, don't double count as basic overtake
    if (processedNearMisses.has(tv.userData.id)) {
        return;
    }
    
    // Add score
    score += 10;
    
    // Track rapid passes
    const timeNow = performance.now();
    
    // Track action
    const side = playerVehicle.position.x < tv.position.x ? 'left' : 'right';
    actionQueue.push({
        event: `overtake_${side}`,
        vehicle_type: tv.userData.type,
        timestamp: elapsedPlayTime
    });

    // Check if we did a multi overtake (overtaking multiple vehicles within 2.0s)
    if (!triggerOvertake.recentOvertakes) triggerOvertake.recentOvertakes = [];
    triggerOvertake.recentOvertakes.push(timeNow);
    // Filter overtakes within last 2 seconds
    triggerOvertake.recentOvertakes = triggerOvertake.recentOvertakes.filter(t => timeNow - t < 2000);
    
    if (triggerOvertake.recentOvertakes.length >= 3) {
        triggerGameplayEvent('multi_overtake', tv.userData.type);
        triggerOvertake.recentOvertakes = [];
    } else {
        triggerGameplayEvent('overtake', tv.userData.type);
    }
}

function triggerCrash(tv) {
    gameState = STATE.CRASHED;
    gameSpeed = 0;
    
    triggerCameraShake(0.8, 0.5);
    flashScreen('crash');
    createExplosion(playerVehicle.position);
    
    // Hide headlights spot light
    playerVehicle.children.forEach(c => {
        if (c.isSpotLight) c.intensity = 0;
    });
    
    // Set high score
    const isNewHighScore = score > highScore;
    if (isNewHighScore) {
        highScore = Math.round(score);
        localStorage.setItem('roadcaster_highscore', highScore);
        dom.hudHighscore.textContent = highScore.toLocaleString();
    }
    
    // Instantly show the game over overlay and restart button!
    showGameOverScreen(null);
    
    // Dispatch crash event immediately (bypassing normal queue interval)
    triggerGameplayEvent('crash', tv.userData.type);
}

// Camera FX
function triggerCameraShake(intensity, duration) {
    cameraShake.intensity = intensity;
    cameraShake.duration = duration;
    cameraShake.elapsed = 0.0;
}

function flashScreen(type) {
    const flashDiv = document.createElement('div');
    flashDiv.style.position = 'absolute';
    flashDiv.style.top = '0';
    flashDiv.style.left = '0';
    flashDiv.style.width = '100%';
    flashDiv.style.height = '100%';
    flashDiv.style.zIndex = '99';
    flashDiv.style.pointerEvents = 'none';
    flashDiv.style.transition = 'opacity 0.1s ease-out';
    flashDiv.style.opacity = '0.7';
    
    if (type === 'crash') {
        flashDiv.style.backgroundColor = '#ff0033';
        flashDiv.style.transition = 'opacity 0.8s ease-out';
    } else {
        flashDiv.style.backgroundColor = '#ffffff';
    }
    
    document.body.appendChild(flashDiv);
    
    // Request animation frame to guarantee render
    requestAnimationFrame(() => {
        flashDiv.style.opacity = '0';
        setTimeout(() => {
            flashDiv.remove();
        }, type === 'crash' ? 800 : 150);
    });
}

// --- NARRATIVE BUFFER & COMMENTARY LAYER ---
// --- NARRATIVE BUFFER & COMMENTARY LAYER ---
const narrativeBuffer = {
    events: [],
    tickInterval: 3500,    // Evaluate narrative state every 3.5 seconds (broadcaster summary!)
    lastTickTime: 0
};

function triggerGameplayEvent(eventType, vehicleType) {
    const ev = {
        event: eventType,
        speed: Math.round(gameSpeed * 1.8),
        combo: comboCount,
        vehicle_type: vehicleType,
        total_score: Math.round(score),
        distance_survived: Math.round(distanceSurvived),
        is_high_score: score >= highScore,
        recent_events: [...recentEvents],
        timestamp: elapsedPlayTime
    };
    
    // Maintain rolling list of 5 recent events
    recentEvents.push(eventType);
    if (recentEvents.length > 5) recentEvents.shift();
    
    // Critical bypass events (Crash & Game Start) play immediately, interrupting current audio
    const isCritical = (eventType === 'crash' || eventType === 'game_start');
    
    if (isCritical) {
        stopAudio(); // cancel active TTS immediately
        sendNarrativeRequest([ev], true); // dispatch instantly
        return;
    }
    
    // Otherwise buffer normally
    narrativeBuffer.events.push(ev);
}

function processNarrativeTick() {
    if (gameState !== STATE.PLAYING) return;
    
    // Prevent overlapping commentary: do not send ticks while caster is speaking
    if (isSpeaking) return;
    
    const timeNow = performance.now();
    if (narrativeBuffer.lastTickTime === 0) {
        narrativeBuffer.lastTickTime = timeNow;
        return;
    }
    
    if (timeNow - narrativeBuffer.lastTickTime >= narrativeBuffer.tickInterval) {
        narrativeBuffer.lastTickTime = timeNow;
        
        // Accumulate and send when we have events or periodically to evaluate control/cruising streak
        if (narrativeBuffer.events.length === 0) {
            if (timeNow - processNarrativeTick.lastEmptyTickTime < 4000) {
                return;
            }
            processNarrativeTick.lastEmptyTickTime = timeNow;
        }
        
        const batch = [...narrativeBuffer.events];
        narrativeBuffer.events = [];
        
        sendNarrativeRequest(batch);
    }
}
processNarrativeTick.lastEmptyTickTime = 0;

async function sendNarrativeRequest(batch, isCritical = false) {
    const payload = {
        events: batch,
        actions: [...actionQueue],
        current_time: elapsedPlayTime,
        current_speed: Math.round(gameSpeed * 1.8),
        current_combo: comboCount,
        critical: isCritical
    };
    actionQueue = [];
    
    const displayEv = batch.length > 0 ? batch[batch.length - 1] : {
        event: 'cruising',
        speed: Math.round(gameSpeed * 1.8),
        combo: comboCount,
        vehicle_type: 'car',
        total_score: Math.round(score),
        distance_survived: Math.round(distanceSurvived)
    };
    updateDebugEventPanel(displayEv);
    dom.debugJsonDisplay.textContent = JSON.stringify(payload, null, 2);
    
    try {
        const response = await fetch(`/api/narrative?mode=${activeCommentaryMode}&voice=${activeCommentaryVoice}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        // Skip speaking if server requested, unless it is a critical bypass event
        if (data.skip && !isCritical) {
            return;
        }
        
        if (data.error) {
            console.error("Narrative server error:", data.error);
            return;
        }
        
        // Render commentary subtitles with typewriter and persistence
        renderCommentaryText(data.commentary);
        updateDebugPipeline(data);
        
        if (data.narrative_state) {
            dom.debugEventType.textContent = data.narrative_state;
        }
        
        // Trigger gameplay over overlay update if crash event returns
        if (isCritical && batch.some(e => e.event === 'crash')) {
            showGameOverScreen(data.commentary);
        }
        
        playNarratorVoice(data.commentary, data.voice);
        
    } catch (err) {
        console.error("Narrative request failed:", err);
        if (batch.length > 0) {
            const fallbackText = getLocalFallbackText(batch[batch.length - 1]);
            renderCommentaryText(fallbackText);
            playNarratorVoice(fallbackText, 'Jasper');
            if (isCritical && batch.some(e => e.event === 'crash')) {
                showGameOverScreen(fallbackText);
            }
        }
    }
}

// Local fallback dictionary
function getLocalFallbackText(ev) {
    if (ev.event === 'crash') return "And that is a massive crash. The run is over.";
    if (ev.event === 'extreme_near_miss') return "Centimeters away! That was incredibly close.";
    if (ev.event === 'near_miss') return "Close shave on the highway!";
    return "Cruising past traffic on the highway.";
}

let subtitleTimeout = null;

// Typewriter Text Effect - Persistent Subtitles Fading out after 4.5 seconds
function renderCommentaryText(text) {
    const display = dom.commentaryText;
    display.textContent = '';
    display.style.opacity = '1';
    
    if (subtitleTimeout) clearTimeout(subtitleTimeout);
    
    let index = 0;
    const charsPerSec = 45;
    const interval = 1000 / charsPerSec;
    
    function type() {
        if (index < text.length) {
            display.textContent += text.charAt(index);
            index++;
            setTimeout(type, interval);
        } else {
            // Persist subtitles for 4.5 seconds after speech/typewriter finishes
            subtitleTimeout = setTimeout(() => {
                display.style.transition = 'opacity 0.8s ease-out';
                display.style.opacity = '0';
                setTimeout(() => {
                    if (display.style.opacity === '0') {
                        display.textContent = '';
                    }
                }, 800);
            }, 4500);
        }
    }
    display.style.transition = 'none';
    type();
}

// Play TTS Audio - Tracks isSpeaking status to block overlapping speech
async function playNarratorVoice(text, voice) {
    stopAudio();
    
    currentTtsRequestId++;
    const myRequestId = currentTtsRequestId;
    
    // Set isSpeaking immediately to block new ticks while fetching/playing
    isSpeaking = true;
    
    if (serverTtsEnabled) {
        try {
            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, voice })
            });
            
            if (myRequestId !== currentTtsRequestId) return;
            
            if (!response.ok) {
                isSpeaking = false;
                if (response.status === 503) {
                    fallbackToWebSpeech("Server disabled TTS");
                }
                playBrowserTtsFallback(text, voice);
                return;
            }
            
            const audioBuffer = await response.arrayBuffer();
            initAudio();
            
            if (myRequestId !== currentTtsRequestId) return;
            
            isSpeaking = true;
            audioCtx.decodeAudioData(audioBuffer, (decodedData) => {
                if (myRequestId !== currentTtsRequestId) return;
                
                const source = audioCtx.createBufferSource();
                source.buffer = decodedData;
                
                const gainNode = audioCtx.createGain();
                gainNode.gain.value = masterVolume;
                
                source.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                
                source.onended = () => {
                    if (myRequestId === currentTtsRequestId) {
                        isSpeaking = false;
                    }
                };
                
                source.start(0);
                currentAudioSource = source;
            }, (e) => {
                console.error("Error decoding audio buffer:", e);
                isSpeaking = false;
                if (myRequestId === currentTtsRequestId) {
                    playBrowserTtsFallback(text, voice);
                }
            });
        } catch (err) {
            console.error("Flask TTS request failed, using browser Web Speech:", err);
            isSpeaking = false;
            if (myRequestId === currentTtsRequestId) {
                playBrowserTtsFallback(text, voice);
            }
        }
    } else {
        playBrowserTtsFallback(text, voice);
    }
}

function playBrowserTtsFallback(text, voiceName) {
    if (!window.speechSynthesis) return;
    
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.volume = masterVolume;
    
    if (voiceName === 'Hugo') {
        utterance.pitch = 0.75;
        utterance.rate = 0.85;
    } else if (voiceName === 'Kiki') {
        utterance.pitch = 1.15;
        utterance.rate = 1.05;
    } else {
        utterance.pitch = 0.95;
        utterance.rate = 1.15;
    }
    
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
        let selectedVoice = null;
        if (voiceName === 'Kiki') {
            selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Female') || v.name.includes('Zira') || v.name.includes('Google US English')));
        } else {
            selectedVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Male') || v.name.includes('David') || v.name.includes('Google UK English Male')));
        }
        if (selectedVoice) utterance.voice = selectedVoice;
    }
    
    isSpeaking = true;
    utterance.onend = () => { isSpeaking = false; };
    utterance.onerror = () => { isSpeaking = false; };
    
    window.speechSynthesis.speak(utterance);
}

function stopAudio() {
    isSpeaking = false;
    if (currentAudioSource) {
        try {
            currentAudioSource.stop();
        } catch (e) {}
        currentAudioSource = null;
    }
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
}

// --- DEBUG PANEL UPDATES ---
function updateDebugEventPanel(ev) {
    dom.debugEventType.textContent = ev.event;
    dom.debugMetaSpeed.textContent = `${ev.speed} km/h`;
    dom.debugMetaCombo.textContent = `x${ev.combo}`;
    dom.debugMetaVehicle.textContent = ev.vehicle_type;
    dom.debugMetaDist.textContent = `${ev.distance_survived}m`;
    
    dom.debugJsonDisplay.textContent = JSON.stringify(ev, null, 2);
}

function updateDebugPipeline(data) {
    dom.debugContextTags.innerHTML = '';
    if (data.context_tags && data.context_tags.length > 0) {
        data.context_tags.forEach(tag => {
            const span = document.createElement('span');
            span.className = 'context-tag';
            span.textContent = tag;
            dom.debugContextTags.appendChild(span);
        });
    } else {
        dom.debugContextTags.innerHTML = '<span class="empty-placeholder">No active tags</span>';
    }
    
    dom.debugMetricMomentum.textContent = data.momentum.toUpperCase();
    
    // Set color code on momentum status
    const mom = dom.debugMetricMomentum;
    mom.className = 'metric-val';
    if (data.momentum === 'rising') mom.classList.add('success');
    else if (data.momentum === 'falling') mom.style.color = 'var(--accent-pink)';
    else mom.style.color = 'var(--text-dim)';
    
    dom.debugMetricPool.textContent = data.pool_used;
    dom.debugMetricVoice.textContent = `${data.voice} (${data.mode.toUpperCase()})`;
}

// --- OVERLAY TRIGGERS ---
function startGame() {
    initAudio();
    dom.startOverlay.classList.add('hidden');
    dom.hud.classList.remove('hidden');
    dom.broadcastPanel.classList.remove('hidden');
    
    gameState = STATE.PLAYING;
    
    // High score display init
    dom.hudHighscore.textContent = highScore.toLocaleString();
    
    // Dispatch game start event
    triggerGameplayEvent('game_start', 'car');
}

function restartGame() {
    stopAudio();
    
    // Clear graphics arrays
    trafficVehicles.forEach(v => scene.remove(v));
    trafficVehicles = [];
    particles.forEach(p => scene.remove(p));
    particles = [];
    
    // Reset state values
    score = 0;
    distanceSurvived = 0;
    comboCount = 0;
    elapsedPlayTime = 0;
    gameSpeed = BASE_SPEED;
    recentEvents = [];
    highScoreBeatenThisRun = false;
    narrativeBuffer.events = [];
    narrativeBuffer.lastTickTime = 0;
    processedNearMisses.clear();
    processedOvertakes.clear();
    
    // Reset player car position
    currentLane = 1;
    playerVehicle.position.set(0, 0.35, 0);
    playerVehicle.rotation.set(0, 0, 0);
    
    // Reset headlights SpotLight intensity
    playerVehicle.children.forEach(c => {
        if (c.isSpotLight) c.intensity = 3;
    });
    
    // Reset UI
    dom.hudScore.textContent = '000,000';
    dom.hudSpeed.textContent = '0';
    dom.hudDistance.textContent = '0';
    dom.comboBadge.classList.add('hidden');
    dom.commentaryText.textContent = "Restarting commentary feed...";
    
    // Reset speedometer progress gauge
    const speedProgressElement = document.getElementById('speedometer-progress');
    if (speedProgressElement) {
        speedProgressElement.style.strokeDashoffset = '190';
    }
    
    dom.gameoverOverlay.classList.add('hidden');
    gameState = STATE.PLAYING;
    
    triggerGameplayEvent('game_start', 'car');
}

function showGameOverScreen(finalText) {
    dom.finalScore.textContent = Math.round(score).toLocaleString();
    dom.finalDistance.textContent = `${Math.round(distanceSurvived)}m`;
    dom.finalCombo.textContent = `x${comboCount}`;
    dom.finalSpeed.textContent = `${Math.round(gameSpeed * 1.8)} km/h`;
    
    dom.finalCommentary.textContent = finalText;
    
    dom.gameoverOverlay.classList.remove('hidden');
}

// --- MAIN RENDER LOOP ---
function render() {
    // Camera shake offset math
    let shakeOffset = new THREE.Vector3();
    if (cameraShake.duration > 0) {
        const shakePct = 1.0 - (cameraShake.elapsed / cameraShake.duration);
        const randIntensity = cameraShake.intensity * shakePct;
        shakeOffset.set(
            (Math.random() - 0.5) * randIntensity,
            (Math.random() - 0.5) * randIntensity,
            (Math.random() - 0.5) * randIntensity
        );
    }
    
    // Dynamic Camera Follow positioning
    const baseOffset = new THREE.Vector3(0, 3.8, 8.8); // Chase cam offset behind Z=0
    
    // Zoom slightly on high speed (widens field of view)
    const speedRatio = gameSpeed / MAX_SPEED;
    camera.fov = 50 + speedRatio * 15;
    camera.updateProjectionMatrix();
    
    // Position camera relative to player car (adds smooth follow lag behind swerves)
    const targetCamX = THREE.MathUtils.lerp(camera.position.x, playerVehicle.position.x, 0.12);
    
    camera.position.set(
        targetCamX + shakeOffset.x,
        baseOffset.y + shakeOffset.y,
        baseOffset.z + shakeOffset.z
    );
    camera.lookAt(playerVehicle.position.x * 0.8, 1.2, -15);
    
    // Execute renderer frame
    renderer.render(scene, camera);
}

function onWindowResize() {
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

// Launch application
window.onload = init;
