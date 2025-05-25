import websockets #used for communication with browser
import asyncio
import json
import math
#adding async before a function definition adds the function to the event loop

#Game area (defined in game.html)
width = 800
height = 500
thrust_power = 0.3

spawn_points = [
    (100, 250),
    (700, 250)
]

#Players
players = {}
current_id = 1

connected_players = {}
game_state = {
    'players': {},
}


# This is called every time a new player connects
async def player_connection(websocket):
    #Don't let more than 2 players join the game
    if len(game_state['players']) >= 2:
        await websocket.send(json.dumps({
            'type': 'error',
            'message': 'Game is full. Try again later.'
        }))
        await websocket.close()
        print('Rejected a player connection')
        return
    global current_id
    player_id = current_id
    current_id += 1
    print('Player ' + str(player_id) + ' connected')

    #Add player to connected players
    connected_players[player_id] = websocket

    setup_message = {
        'type': 'setup',
        'player_id': player_id,
        'ship_size': 50,
        'players' : 1, # temporary. will need to send message with all player ids
    }
    
    # Send setup message to browser
    await websocket.send(json.dumps(setup_message))

    # Add player to the game
    x, y = spawn_points[player_id -1]
    game_state['players'][player_id] = {
        'x':x, 
        'y':y, 
        'vx':0, # starting velocity
        'vy':0, # starting velocity
        'rotation':0, #starting rotation
        'laser': {
            'active': False,
            'cooldown': False,
            'duration': 3,
            'from': {
                'x': 0,
                'y': 0
            },
            'to': {
                'x': 0,
                'y': 0
            },
        },
        'keys': {
            'rotateLeft': False,
            'rotateRight': False,
            'thrust': False,
            'fireLaser': False
        }
    }

    game_state_message = {
        'type':'game_update',
        'players': game_state['players'],
    }

    # Send starting game state to new player
    await websocket.send(json.dumps(game_state_message))

    # Listen for messages from this player
    async for message in websocket:
        await handle_player_message(player_id, message)

# Process messages from browser
async def handle_player_message(player_id, message):
    data = json.loads(message)
    if data['type'] == 'input':
        keys = data['keys']
        player = game_state['players'][player_id]
        player['keys'] = keys

# Send current game state to all players
async def broadcast_game_state():
    game_update = {
        'type': 'game_update',
        'players': game_state['players']
    }

    for player_id, websocket in connected_players.items():
        try:
            await websocket.send(json.dumps(game_update))
        except:
            break
            #disconnect player

def get_laser_endpoint(from_x, from_y, angle_rad):
    to_x = from_x
    to_y = from_y
    #Keep extending line until it crosses boundary
    while to_x >= 0 and to_x <= width and to_y >= 0 and to_y <= height:
        to_x += math.cos(angle_rad) * 5
        to_y += math.sin(angle_rad) * 5
    return (to_x, to_y)

async def game_loop():
    while True:
        for player in game_state['players'].values():
            keys = player['keys']

            if keys.get('rotateLeft'):
                player['rotation'] -= 5
            if keys.get('rotateRight'):
                player['rotation'] += 5
            if keys.get('thrust'):
                angle_rad = math.radians(player['rotation'] - 90)
                player['vx'] += math.cos(angle_rad) * thrust_power
                player['vy'] += math.sin(angle_rad) * thrust_power
            if keys.get('fireLaser') and not player['laser']['cooldown']:
                    player['laser']['active'] = True
                    player['laser']['duration'] = 3
                    player['laser']['cooldown'] = 10

            # Update position
            player['x'] += player['vx']
            player['y'] += player['vy']

            # Apply friction
            player['vx'] *= 0.99
            player['vy'] *= 0.99

            # Keep within bounds
            if player['x'] < 0:
                player['x'] = 0
                player['vx'] = 0
            elif player['x'] > width:
                player['x'] = width
                player['vx'] = 0

            if player['y'] < 0:
                player['y'] = 0
                player['vy'] = 0
            elif player['y'] > height:
                player['y'] = height
                player['vy'] = 0

            if player['laser']['active']:
                # Update laser position
                from_x = player['x']
                from_y = player['y']
                angle_rad = math.radians(player['rotation'] - 90)
                (to_x, to_y) = get_laser_endpoint(from_x, from_y, angle_rad)
                player['laser']['from']['x'] = from_x
                player['laser']['from']['y'] = from_y
                player['laser']['to']['x'] = to_x
                player['laser']['to']['y'] = to_y

                # Update laser duration
                player['laser']['duration'] -= 1
                if player['laser']['duration'] <= 0:
                    player['laser']['active'] = False

            # Update laser cooldown timer
            if player['laser']['cooldown']:
                player['laser']['cooldown'] -= 1
                if player['laser']['cooldown'] <= 0:
                    player['laser']['cooldown'] = False
                

        await broadcast_game_state()
        await asyncio.sleep(1 / 30)  # 30 FPS


async def main():
    server = await websockets.serve(player_connection, 'localhost', 8765) #starts the server. Player connection is the function that is run whenever a new connection is received
    print('Server is running')
    await asyncio.gather(
        server.wait_closed(),
        game_loop()
    )


if __name__ == "__main__":
    asyncio.run(main())