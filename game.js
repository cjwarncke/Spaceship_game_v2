
// Game variables
let ship_size = null;
let myPlayerID = null;
let gameState = {
    players: {}
};

let keys = {
    rotateLeft: false,
    rotateRight: false,
    thrust: false,
    fireLaser: false
}

// Spaceship Images
let mySpaceshipImage = null;
let otherSpaceshipImage = null;

// Canvas Setup
var canvas = document.getElementById('canvas');
var g = canvas.getContext('2d'); 

// Chat variables
let chatSocket = null;
let chatMessages = []; // store chat history

function loadImage(src) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.src = src;
    });
}

function connect() {
    websocket = new WebSocket('ws://localhost:8765'); //address of server

    websocket.onopen = function() {
        console.log('Connected to game server');
    }

    websocket.onmessage = function(event) {
        const message = JSON.parse(event.data);
        handleMessage(message);
    }
}

function handleMessage(message) {
    switch (message.type) {
        case 'setup':
            myPlayerID = message.player_id;
            ship_size =  message.ship_size;
            gameState.players = message.players;
            console.log('Received setup message');
            startInputLoop();
            break;
        
        case 'game_update':
            gameState.players = message.players;
            renderGame();
            break;
    }
}

function startInputLoop() {
    // Send input to server at 30 FPS
    setInterval(() => {
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({
                type: 'input',
                keys: keys,
                timestamp: Date.now()
            }));
        }
    }, 1000/30); // 30 FPS
}

function renderGame() {
    g.clearRect(0,0,canvas.clientWidth,canvas.clientHeight)

    // Draw all players and lasers
    for (let playerID in gameState.players) {
        const player = gameState.players[playerID];
        drawPlayer(player, playerID == myPlayerID);
        drawLaser(player);
    }
}

function drawPlayer(player, isMe) {
    g.save();
    g.translate(player.x, player.y); //player position
    g.rotate(player.rotation * Math.PI/180); //convert to radians
    const img = isMe ? mySpaceshipImage : otherSpaceshipImage;
    g.drawImage(
        img,
        -ship_size/2, //-25, //negative half width
        -ship_size/2, //-25, //negative half height
        ship_size, //50, //spaceship width
        ship_size //50 //spaceship height
        );
    g.restore();
}

function drawLaser(player) {
    if (player.laser.active) {
        g.strokeStyle = 'red';
        g.lineWidth = 2;
        g.beginPath()
        g.moveTo(player.laser.from.x, player.laser.from.y);
        g.lineTo(player.laser.to.x, player.laser.to.y);
        g.stroke();
    }
}

async function fetchScores() {
    try {
        const response = await fetch('http://localhost:8767/score');
        if (!response.ok) throw new Error('Failed to fetch scores');
        const scores = await response.json();
        updateScoreboard(scores);
    }
    catch (e) {
        console.error('Error fetching scores: ', e);
    }
}

function updateScoreboard(scores) {
    const scoreboard = document.getElementById('scoreboard');
    let html = ''

    let playerScoresHtml = [];
    for (let playerID in scores) {
        // Wrap each player's score in a span with a class
        playerScoresHtml.push(`<span class="player-score">Player ${playerID} Score: ${scores[playerID]}</span>`);
    }
    // Join them without additional separators, as flexbox will handle spacing
    html += playerScoresHtml.join('');
    scoreboard.innerHTML = html;
}

// Keyboard input handling
document.addEventListener('keydown', function(event) {
    switch(event.key) {
        case 'f':
            console.log('keyboard input received')
            keys.thrust = true;
            break;
        case 'j':
            console.log('keyboard input received')
            keys.rotateLeft = true;
            break;
        case 'l':
            console.log('keyboard input received')
            keys.rotateRight = true;
            break;
        case ' ':
            console.log('keyboard input received')
            keys.fireLaser = true;
            break;
    }
});

document.addEventListener('keyup', function(event) {
    switch(event.key) {
        case 'f':
            keys.thrust = false;
            break;
        case 'j':
            keys.rotateLeft = false;
            break;
        case 'l':
            keys.rotateRight = false;
            break;
        case ' ':
            keys.fireLaser = false;
            break;
    }
});

function connectChat() {
    chatSocket = new WebSocket('ws://localhost:8768');

    chatSocket.onopen = () => {
        console.log('Connected to chat server');
    };

    chatSocket.onmessage = (event) => {
        console.log('chat received')
        const message = JSON.parse(event.data);

        switch(message.type) {
            case 'chat_history':
                chatMessages = message.messages;
                renderChat();
                break;

            case 'chat_message':
                chatMessages.push({
                    player_id: message.player_id,
                    message: message.message,
                    timestamp: message.timestamp
                });
                renderChat();
                break;
        }
    };

    chatSocket.onclose = () => {
        console.log('Chat server connection closed');
    };
}

function sendChatMessage(text) {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        console.log('Sending chat')
        chatSocket.send(JSON.stringify({
            type: 'chat_message',
            player_id: myPlayerID,
            message: text
        }));
    }
}

function renderChat() {
    const chatbox = document.getElementById('chatbox');
    chatbox.innerHTML = chatMessages.map(msg => {
        const time = new Date(msg.timestamp * 1000).toLocaleTimeString();
        return `<div><strong>Player ${msg.player_id}:</strong> ${msg.message} <em>(${time})</em></div>`;
    }).join('');
}


// This is the entry point.  It runs when the webpage finishes loading
window.addEventListener('load', async function() {
    //fetchScores(); // Show scores before connecting to game server

    // Force it to load images before connecting to game server
    [mySpaceshipImage, otherSpaceshipImage] = await Promise.all([
        loadImage('Images/my_spaceship.png'),
        loadImage('Images/other_spaceship.png')
    ]);
    connect(); //Connect to game server
    this.setInterval(fetchScores, 1000); //Update scores once per second

    //Connect chat buttons
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('chat-send');

    sendButton.onclick = () => {
        if (chatInput.value.trim()) {
            sendChatMessage(chatInput.value.trim());
            chatInput.value = '';
        }
    };

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendButton.click();
        }
    });

    connectChat(); //Connect to chat server


});