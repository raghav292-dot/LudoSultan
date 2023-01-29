import json
import random
import test

import boto3
import Constants
import GamePlayTTL_step_function_invoker
import LobbyTTL_step_function_invoker
import utils

client = boto3.client('stepfunctions')
dynamodb = boto3.client('dynamodb')
db = boto3.resource('dynamodb')


def _push_in_lobby(ws_client, connectionId, payload, req_time):
    print("Player waiting in lobby")
    user_id = payload['playerId']
    player_size = payload['players']
    bet_amount = payload['betAmount']
    game_type = payload['lobby']
    device_id = payload['deviceId']
    private_code = ''
    if 'private_code' in payload and payload['lobby'] == 'private':
        private_code = payload['private_code']
    dynamodb.put_item(
        TableName='Lobby',
        Item={
            'user_id': {'S': user_id},
            'Availability': {'S': 'Online'},
            'connectionId': {'S': connectionId},
            'device_id': {'S': device_id},
            'bet_amount': {'S': bet_amount},
            'player_size': {'S': player_size},
            'game_type': {'S': game_type},
            'req_timestamp': {'S': 'NA'},
            'private_code': {'S': private_code}
        }
    )
    LobbyTTL_step_function_invoker.start_timer(user_id, 'Lobby', connectionId)
    message = {'action': 'MatchMaking', "status": True, 'result': {'Timer': Constants.match_making_timer,
                                                                   'state': 'InLobby', 'message': 'Finding the players from Lobby within 60 secs OR Exit'}}
    utils.broadcast_info_to_players(
        ws_client, user_id, 'Lobby', [connectionId], message)


def arrange_table(team, room_name) -> str:
    # generating the table-name joining with '_'(gmail does not contains it) based on joining-sequence and uids
    players_uids = list(
        dict(sorted(team.items(), key=lambda item: item[1])).keys())
    utils.update_column(players_uids[0], room_name, 'Dice_turn', 'True')
    table_no = "_".join(players_uids)
    for uid in players_uids:
        utils.update_column(uid, room_name, 'Table_no', table_no)
    return str(table_no), players_uids[0]


def _create_match_and_remove_user_from_lobby(lobby_uids, payload, current_connectionId):
    current_uid = payload['playerId']
    player_size = payload['players']
    bet_amount = payload['betAmount']
    game_type = payload['lobby']
    device_id = payload['deviceId']
    room_name = utils.get_room_name(game_type, player_size)
    # pushing the current user in GamePlay with table-id
    dynamodb.put_item(
        TableName=room_name,
        Item={
            'user_id': {'S': current_uid},
            'connectionId': {'S': current_connectionId},
            'bet_amount': {'S': bet_amount},
            'device_id': {'S': device_id},
            'Availability': {'S': 'Online'},
            'Dice_turn': {'S': 'False'},
            'Dice_num': {'S': '6'},
            'Dice_num_last': {'S': '0'},
            'Dice_num_sec_last': {'S': '0'},
            'Piece_0_pos': {'S': '0'},
            'Piece_1_pos': {'S': '0'},
            'Piece_2_pos': {'S': '0'},
            'Piece_3_pos': {'S': '0'}
        }
    )
    # pushing the matched users in corresponding GamePlay
    team = {}
    team[current_uid] = current_connectionId
    for uid in lobby_uids:
        connectionId = utils._fetch_data('Lobby', uid, 'connectionId')
        team[uid] = connectionId
        dynamodb.put_item(
            TableName=room_name,
            Item={
                'user_id': {'S': uid},
                'connectionId': {'S': connectionId},
                'bet_amount': {'S': bet_amount},
                'device_id': {'S': device_id},
                'Availability': {'S': 'Online'},
                'Dice_turn': {'S': 'False'},
                'Dice_num': {'S': '6'},
                'Dice_num_last': {'S': '0'},
                'Dice_num_sec_last': {'S': '0'},
                'Piece_0_pos': {'S': '0'},
                'Piece_1_pos': {'S': '0'},
                'Piece_2_pos': {'S': '0'},
                'Piece_3_pos': {'S': '0'}
            }
        )
        # removing the matched users from Lobby
        utils.delete_entry('Lobby', uid)
    table_no, first_user = arrange_table(team, room_name)
    return team, table_no, first_user


def _find_match(payload) -> list:
    # based on bet_amount,game-type and player_size finding match from Lobby
    bet_amount = payload['betAmount']
    player_size = payload['players']
    game_type = payload['lobby']
    uid = []
    print("in find match method for", bet_amount, player_size, game_type)
    paginator = dynamodb.get_paginator('scan')
    for page in paginator.paginate(TableName='Lobby'):
        for row in page['Items']:
            if str(game_type) == 'private':
                if row['bet_amount']['S'] == str(bet_amount) and row['player_size']['S'] == str(player_size) and payload['private_code'] == row['private_code']['S']:
                    uid.append(row['user_id']['S'])
                    if len(uid) == int(player_size) - 1:
                        return uid
            elif row['bet_amount']['S'] == str(bet_amount) and row['player_size']['S'] == str(player_size) and row['game_type']['S'] == str(game_type):
                uid.append(row['user_id']['S'])
                if len(uid) == int(player_size) - 1:
                    print("match found in Lobby")
                    return uid
    print("Currently no match found in Lobby for ",
          bet_amount, player_size, game_type)
    return []


def create_update_metadata(event_data, payload):
    user_id = payload['playerId']
    player_size = payload['players']
    bet_amount = payload['betAmount']
    game_type = payload['lobby']
    device_id = payload['deviceId']
    room_name = utils.get_room_name(
        payload['lobby'], payload['players'])
    dynamodb.put_item(
        TableName=Constants.table_mapping['connection_data'],
        Item={
            'connectionId': {'S': event_data['connectionId']},
            'user_id': {'S': user_id},
            'match_type': {'S': room_name},
            'Availability': {'S': 'Online'},
            'timestamp': {'S': event_data['requestTime']},
            'Description': {'S': "Connected"},
            'identity': {'S': event_data['identity']['sourceIp']}
        }
    )


def is_last_two_dice_turns_six(uid, room_name):
    if utils._fetch_data(room_name, uid, 'Dice_num_sec_last') == '6' and utils._fetch_data(room_name, uid, 'Dice_num_last') == '6':
        return True
    return False


def get_dice_number(uid, room_name) -> str:
    c_state = utils.get_current_state(uid, room_name)
    print(f"current state of {uid} is ", c_state)
    # if all pieces are in home then '6'
    if utils.is_all_pieces_in_home(uid, room_name):
        return '6'
    return str(random.randint(1, 6))


def roll_dice(uid, room_name):
    dicenum = get_dice_number(uid, room_name)
    print(room_name, uid, utils._fetch_data(room_name, uid, 'Dice_turn'),
          utils._fetch_data(room_name, uid, 'Dice_num'), dicenum)
    if utils._fetch_data(room_name, uid, 'Dice_num') == '0':
        table = db.Table(room_name)
        resp = table.update_item(
            Key={'user_id': uid},
            UpdateExpression=f"SET Dice_num=:c",
            ExpressionAttributeValues={':c': dicenum}
        )


def pass_dice_turn_to_next_player(user_id, room_name):
    # if is_last_two_dice_turns_six(user_id, room_name):
    #     pass_dice_turn_to_next_player(user_id, room_name)

    Table_no = utils._fetch_data(room_name, user_id, 'Table_no')
    uids = Table_no.split('_')
    uid_index = uids.index(user_id)
    next_index = (uid_index + 1) % len(uids)
    next_user = uids[next_index]
    utils.update_column(next_user, room_name, 'Dice_turn', 'True')
    roll_dice(next_user, room_name)
    return next_user


def pass_dice_turn(user_id, room_name):
    utils.update_column(user_id, room_name, 'Dice_turn', 'False')
    return pass_dice_turn_to_next_player(user_id, room_name)


def update_piece_position(user_id: str, room_name: str, piece_id: str):
    move = utils._fetch_data(room_name, user_id, 'Dice_num')
    if utils.is_all_pieces_in_home(user_id, room_name):
        move = '1'
    p_name = Constants.piece_mapping[piece_id]
    p_pos = utils._fetch_data(room_name, user_id, p_name)
    # to-do: need to map pos according to game move
    new_pos = str(int(p_pos) + int(move))
    # to-do: check the bite/winning conditions.
    utils.update_column(user_id, room_name, p_name, new_pos)
    dice_num = move
    if move == '1':
        dice_num = utils._fetch_data(room_name, user_id, 'Dice_num')
    Dice_num_sec_last = utils._fetch_data(
        room_name, user_id, 'Dice_num_sec_last')
    # updating 2nd last dice_num
    utils.update_column(user_id, room_name, 'Dice_num_sec_last', dice_num)
    # updating last dice_num
    utils.update_column(user_id, room_name, 'Dice_num_last', Dice_num_sec_last)
    # resetting the dice_num
    utils.update_column(user_id, room_name, 'Dice_num', '0')
    # to-do: check if all pieces are in Destination(winner)
    return move


def game_play(user_id, room_name, piece_id, ws_client):
    # to-do: move piece for and update current state and diceturn
    # move = utils._fetch_data(room_name, user_id, 'Dice_num')
    move = update_piece_position(user_id, room_name, piece_id)
    next_user = pass_dice_turn(user_id, room_name)
    utils.broadcast_piece_click(
        ws_client, user_id, room_name, piece_id, move, next_user)
    return


def lambda_handler(event, context):
    connectionId = event['requestContext']['connectionId']
    ws_client = utils.get_ws_client(event)
    event_data = event['requestContext']
    body = json.loads(event['body'])
    payload = body['requestData']
    action_name = body['action']
    user_id = payload['playerId']
    room_name = utils.get_room_name(payload['lobby'], payload['players'])
    print(f"Got request from {connectionId} client",  payload, action_name)
    if not utils.ValidatePayload(action_name, payload):
        message = {'status': 'Failed',
                   'message': f'Invalid {action_name} Payload!!'}
        utils.broadcast_info_to_players(
            ws_client, user_id, room_name, [connectionId], message)
        return {}

    if utils._is_uid_exist(room_name, user_id):
        # play the game
        print("in GamePlay!!")
        if utils._fetch_data(room_name, user_id, 'connectionId') != connectionId:
            utils.update_column(user_id, room_name,
                                "connectionId", connectionId)
            utils.update_column(user_id, room_name, "Availability", "Online")
            create_update_metadata(event_data, payload)
            print("Metadata updated on connection reset!!")

        # movable piece
        piece_id = payload['pieceId']
        if utils._fetch_data(room_name, user_id, 'Dice_turn') == 'True':
            game_play(user_id, room_name, piece_id, ws_client)
        else:
            print("Invalid Dice_turn(False)!!")
            message = {'status': 'Failed',
                       'message': 'Please wait for Dice_turn!!'}
            utils.broadcast_info_to_players(
                ws_client, uid, room_name, [connectionId], message)
        return {}

    if utils.is_in_lobby(user_id, payload['deviceId'], connectionId, ws_client) or utils.is_in_any_game_play(user_id, payload['deviceId'], connectionId, ws_client):
        return {}

    create_update_metadata(event_data, payload)
    uids = _find_match(payload)
    # if match found
    if uids:
        team, tableId, dice_turn_uid = _create_match_and_remove_user_from_lobby(
            uids, payload, connectionId)
        room_name = utils.get_room_name(
            payload['lobby'], payload['players'])

        print("Broadcasting the game start msg to ", team, tableId)
        Gamedata = utils.broadcast_home_data(tableId, room_name)

        for uid, conn in team.items():
            # dice_turn = utils._fetch_data(room_name, uid, 'Dice_turn')
            # Timer = 'NA'
            # if dice_turn == 'True':
            #     Timer = Constants.piece_move_timer
            # connectionId = utils._fetch_data(room_name, uid, 'connectionId')
            # To-do: start GamePlayTTL timer
            # utils.GamePlayTTL_step_function_invoker.start_timer(user_id, connectionId)
            message = {'action': 'GamePlay', "status": True, 'result': {'piece_move': {
                'Home': 'NA', 'pieceId': 'NA', 'move_count': 'NA'}, 'Home_data': Gamedata[uid]}}
            utils.broadcast_info_to_players(
                ws_client, uid, room_name, [conn], message)
        return {}
    _push_in_lobby(ws_client, connectionId, payload, str(
        event['requestContext']['requestTimeEpoch']))

    return {}
