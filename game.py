import websockets #used for communication with browser
import asyncio
import aiohttp #used for communication with score microservice
import json
import math
import time
#adding async before a function definition adds the function to the event loop

#Game area (defined in game.html)
width = 800
height = 500
thrust_power = 0.3
ship_size = 50
score_to_win = 10
max_players = 2

spawn_points = [
    (100, 250),
    (700, 250)
]

#Players
players = {}

connected_players = {}
game_state = {
    'players': {},
}

game_start_time = None

# This is called every time a new player connects
async def player_connection(websocket):
    if len(game_state['players']) >= max_players:
        await websocket.send(json.dumps({
            'type': 'error',
            'message': 'Game is full. Try again later.'
        }))
        await websocket.close()
        print('Rejected a player connection')
        return
    
    init_data = json.loads(await websocket.recv())
    screen_name = init_data.get('screen_name','Unknown')
    player_id = init_data.get('player_id')
    print(screen_name + ' connected')

    #Add player to connected players
    connected_players[player_id] = websocket

    setup_message = {
        'type': 'setup',
        'screen_name': screen_name,
        'ship_size': ship_size,
        'players' : 1, # temporary. will need to send message with all player ids
    }
    
    # Send setup message to browser
    await websocket.send(json.dumps(setup_message))

    # Initialize player score
    asyncio.create_task(init_player_score(player_id))

    # Add player to the game
    spawn_index = len(game_state['players'])
    x, y = spawn_points[spawn_index]
    game_state['players'][player_id] = {
        'screen_name': screen_name,
        'spawn_index': spawn_index,
        'x':x, 
        'y':y, 
        'vx':0, # starting velocity
        'vy':0, # starting velocity
        'rotation':0, #starting rotation
        'laser': {
            'active': False,
            'cooldown': False,
            'duration': 3,
            'hitTarget': False,
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

    # If second player just joined, broadcast game_start to everyone
    if len(game_state['players']) == 2:
        global game_start_time
        game_start_time = time.time()

        # Reset players to spawn points
        for pid, player in game_state['players'].items():
            x, y = spawn_points[player['spawn_index']]
            player['x'] = x
            player['y'] = y
            player['vx'] = 0
            player['vy'] = 0
            player['rotation'] = 0

        await broadcast_message({
            'type': 'game_start',
            'players': game_state['players']
        })

    # Listen for messages from this player
    try:
        async for message in websocket:
            await handle_player_message(player_id, message)

    except websockets.exceptions.ConnectionClosed:
        print(f'Player {player_id} disconnected')

    finally:
        # Handle Disconnection
        screen_name = game_state['players'][player_id]['screen_name']
        del game_state['players'][player_id]
        del connected_players[player_id]
        await broadcast_message({
            'type': 'game_update',
            'players': game_state['players']
            })
        
        # Send message to remaining players
        message = json.dumps({
            'type': 'player_disconnected',
            'player_name': screen_name
        })
        for websocket in connected_players.values():
            await websocket.send(message)

        await reset_game()

# Process messages from browser
async def handle_player_message(player_id, message):
    data = json.loads(message)
    if data['type'] == 'input':
        keys = data['keys']
        player = game_state['players'][player_id]
        player['keys'] = keys

async def broadcast_message(message):
    for websocket in connected_players.values():
        try:
            await websocket.send(json.dumps(message))
        except:
            break

def get_laser_endpoint(from_x, from_y, angle_rad):
    to_x = from_x
    to_y = from_y
    #Keep extending line until it crosses boundary
    while to_x >= 0 and to_x <= width and to_y >= 0 and to_y <= height:
        to_x += math.cos(angle_rad) * 5
        to_y += math.sin(angle_rad) * 5
    return (to_x, to_y)

def laser_hit(laser_from, laser_to, ship_x, ship_y):
    # Use algorithm for checking if a line intersects a circle
    dx = laser_to['x'] - laser_from['x']
    dy = laser_to['y'] - laser_from['y']
    fx = laser_from['x'] - ship_x
    fy = laser_from['y'] - ship_y

    a = dx**2 + dy**2
    b = 2 * (fx * dx + fy * dy)
    c = fx**2 + fy**2 - ship_size**2

    d = b**2 - 4 * a * c

    # No intersection
    if d < 0:
        return False
    
    d = math.sqrt(d)
    t1 = (-b - d) / (2*a)
    t2 = (-b + d) / (2*a)

    # Intersection
    if (t1 >= 0 and t1 <= 1) or (t2 >= 0 and t2 <= 1):
        return True
    # No intersection
    else:
        return False
    
async def init_player_score(player_id):
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(
                'http://localhost:8767/score/init',
                json={'player_id': player_id}
            )
        except:
            print('Score initialization failed')
    
async def send_score_update(player_id):
    async with aiohttp.ClientSession() as session:
        try:
            response = await session.post(
                'http://localhost:8767/score/hit',
                json={'player_id': player_id}
            )
            data = await response.json()
            if data['score'] >= score_to_win:
                await broadcast_game_over(player_id)
        except:
            print('Score update failed')

async def broadcast_game_over(winner_id):
    winner = game_state['players'][winner_id]
    message = json.dumps({
        'type': 'game_over',
        'winner_name': winner['screen_name']
    })
    for websocket in connected_players.values():
        await websocket.send(message)

    await reset_game()

async def reset_game():
    global current_id
    current_id = 1
    game_state['players'].clear()
    connected_players.clear()
    
    # Reset scores
    async with aiohttp.ClientSession() as session:
        try:
            await session.post('http://localhost:8767/score/reset')
            await session.post('http://localhost:8766/login/reset')
        except:
            print('Reset failed')


async def game_loop():
    while True:
        countdown_active = game_start_time and (time.time() - game_start_time < 4)
        if not countdown_active:
            for player_id, player in game_state['players'].items():
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
                        player['laser']['hitTarget'] = False
                        player['laser']['duration'] = 3
                        player['laser']['cooldown'] = 10

                # Update position
                player['x'] += player['vx']
                player['y'] += player['vy']

                # Apply friction
                player['vx'] *= 0.99
                player['vy'] *= 0.99

                # Keep within bounds
                if player['x'] - (ship_size/2) < 0:
                    player['x'] = (ship_size/2)
                    player['vx'] = 0
                elif player['x'] + (ship_size/2) > width:
                    player['x'] = width - (ship_size/2)
                    player['vx'] = 0

                if player['y'] - (ship_size/2) < 0:
                    player['y'] = (ship_size/2)
                    player['vy'] = 0
                elif player['y'] + (ship_size/2) > height:
                    player['y'] = height - (ship_size/2)
                    player['vy'] = 0

                if player['laser']['active']:
                    # Update laser position
                    angle_rad = math.radians(player['rotation'] - 90)
                    from_x = player['x'] + (ship_size/2) * math.cos(angle_rad)
                    from_y = player['y'] + (ship_size/2) * math.sin(angle_rad)
                    (to_x, to_y) = get_laser_endpoint(from_x, from_y, angle_rad)
                    player['laser']['from']['x'] = from_x
                    player['laser']['from']['y'] = from_y
                    player['laser']['to']['x'] = to_x
                    player['laser']['to']['y'] = to_y

                    # Update laser duration
                    player['laser']['duration'] -= 1
                    if player['laser']['duration'] <= 0:
                        player['laser']['active'] = False

                    # Check for laser hit
                    if not player['laser']['hitTarget']: # A laser can only hit a target once
                        for other_player in game_state['players'].values():
                            if player == other_player:
                                continue # Don't check if player hits their own laser
                            else:
                                if laser_hit(player['laser']['from'], player['laser']['to'], other_player['x'], other_player['y']):
                                    print('Hit detected')
                                    player['laser']['hitTarget'] = True
                                    asyncio.create_task(send_score_update(player_id))

                # Update laser cooldown timer
                if player['laser']['cooldown']:
                    player['laser']['cooldown'] -= 1
                    if player['laser']['cooldown'] <= 0:
                        player['laser']['cooldown'] = False
                

        # Send current game state to all players
        await broadcast_message({
            'type': 'game_update',
            'players': game_state['players']
            })
        
        await asyncio.sleep(1 / 30)  # 30 FPS


async def main():
    server = await websockets.serve(player_connection, 'localhost', 8765) #starts the server. Player connection is the function that is run whenever a new connection is received
    print('Game server is running')
    await asyncio.gather(
        server.wait_closed(),
        game_loop()
    )


if __name__ == "__main__":
    asyncio.run(main())