
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
        console.log('Connected to server');
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
    console.log(isMe)
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


// This is the entry point.  It runs when the webpage finishes loading
window.addEventListener('load', async function() {
    // Force it to load images before connecting
    [mySpaceshipImage, otherSpaceshipImage] = await Promise.all([
        loadImage('Images/my_spaceship.png'),
        loadImage('Images/other_spaceship.png')
    ]);
    connect();
});