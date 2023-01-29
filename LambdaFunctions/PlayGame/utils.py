import json
import math
import os
import time

import boto3
import Constants

dynamodb = boto3.client('dynamodb')
db = boto3.resource('dynamodb')


def get_ws_client(event):
    domainName = event["requestContext"]["domainName"]
    domain = Constants.domain_mapping[domainName]
    return boto3.client('apigatewaymanagementapi', endpoint_url="https://" + domain + "/" + event["requestContext"]["stage"])


def get_room_name(game_type, player_size):
    return Constants.table_mapping[game_type][player_size]


def _is_uid_exist(table_name: str, uid) -> bool:
    try:
        res = dynamodb.get_item(
            TableName=table_name,
            Key={'user_id': {'S': uid}}
        )
    except:
        return False
    if 'Item' in res:
        return True
    return False


def get_current_state(user_id, t_name) -> dict:
    res = dynamodb.get_item(
        TableName=t_name,
        Key={'user_id': {'S': user_id}
             }
    )
    return {Constants.piece_mapping['1']: res['Item']['Piece_0_pos']['S'], Constants.piece_mapping['2']: res['Item']['Piece_1_pos']['S'], Constants.piece_mapping['3']: res['Item']['Piece_2_pos']['S'], Constants.piece_mapping['4']: res['Item']['Piece_3_pos']['S']}


def _fetch_data(table_name: str, key: str, column: str):
    try:
        res = dynamodb.get_item(
            TableName=table_name,
            Key={'user_id': {'S': key}
                 }
        )
    except:
        return False
    if 'Item' in res:
        return res['Item'][column]['S']
    return False


def update_column(uid, t_name, column, val):
    table = db.Table(t_name)
    resp = table.update_item(
        Key={'user_id': uid},
        UpdateExpression=f"SET {column}=:s",
        ExpressionAttributeValues={':s': val}
    )


def delete_entry(tname, uid):
    dynamodb.delete_item(
        TableName=tname,
        Key={
            'user_id': {'S': uid}
        }
    )


def is_in_any_game_play(user_id, dev_id, connectionId, ws_client):
    t1_name = get_room_name('public', '2')
    t2_name = get_room_name('public', '4')
    t3_name = get_room_name('private', '2')
    t4_name = get_room_name('private', '4')
    room_name = ''
    if _is_uid_exist(t1_name, user_id):
        room_name = t1_name
    elif _is_uid_exist(t2_name, user_id):
        room_name = t2_name
    elif _is_uid_exist(t3_name, user_id):
        room_name = t3_name
    elif _is_uid_exist(t4_name, user_id):
        room_name = t4_name

    if not room_name:
        return False

    if room_name and _fetch_data(room_name, user_id, 'device_id') != dev_id:
        message = {'status': 'False', 'state': 'InGame',
                   'msg': "Please login with same Device Untill current Game finished!!"}
        broadcast_info_to_players(ws_client, user_id, room_name, [
                                  connectionId], message)
        return True

    if _fetch_data(room_name, user_id, 'connectionId') != connectionId:
        update_column(user_id, room_name, "connectionId", connectionId)
        update_column(user_id, room_name, "Availability", "Online")

    c_state = get_current_state(user_id, room_name)
    dice_turn = _fetch_data(room_name, user_id, 'Dice_turn')
    message = {'status': 'False', 'state': 'InGame', 'current_state': c_state,
               'Dice_turn': dice_turn, 'msg': 'User Already in GamePlay!!'}
    broadcast_info_to_players(ws_client, user_id, room_name, [
                              connectionId], message)
    return True


def is_in_lobby(user_id, dev_id, connectionId, ws_client):
    user_id = _fetch_data('Lobby', user_id, 'user_id')
    if not user_id:
        return False
    if _fetch_data('Lobby', user_id, 'device_id') != dev_id:
        message = {'status': 'False', 'state': 'InLobby',
                   'msg': "Please login with same Device Untill Game finished!!"}
        broadcast_info_to_players(ws_client, user_id, 'Lobby', [
                                  connectionId], message)
        return True
    if _fetch_data('Lobby', user_id, 'connectionId') != connectionId:
        update_column(user_id, 'Lobby', "connectionId", connectionId)
        update_column(user_id, 'Lobby', "Availability", "Online")

    past_timestamp = _fetch_data('Lobby', user_id, 'req_timestamp')
    current_timestamp = time.time()
    wait_time = str(
        math.ceil(60 - (current_timestamp - float(past_timestamp))))

    message = {'action': 'MatchMaking', "status": True, 'result': {
        'Timer': wait_time, 'state': 'InLobby', 'message': "user is already in Lobby!!"}}
    broadcast_info_to_players(ws_client, user_id, 'Lobby', [
                              connectionId], message)
    return True


def broadcast_info_to_players(ws_client, uid, room_name, connectionIds: list, message):
    try:
        for connectionId in connectionIds:
            ws_client.post_to_connection(
                Data=json.dumps(message).encode('utf-8'),
                ConnectionId=connectionId
            )
    except:
        print(f"{uid} is disconnected(offline)")
        update_column(uid, room_name, "Availability", "Offline")


def is_all_pieces_in_home(uid, room_name) -> bool:
    c_state = get_current_state(uid, room_name)
    if c_state[Constants.piece_mapping['1']] == '0' and c_state[Constants.piece_mapping['2']] == '0' and c_state[Constants.piece_mapping['3']] == '0' and c_state[Constants.piece_mapping['4']] == '0':
        return True
    return False


def get_home_data(user_id, room_name) -> dict:
    c_state = get_current_state(user_id, room_name)
    Dice_turn = _fetch_data(room_name, user_id, 'Dice_turn')
    Dice_num = _fetch_data(room_name, user_id, 'Dice_num')
    home_data = {'playerId': user_id, 'Dice_turn': Dice_turn,
                 'Dice_num': Dice_num, 'current_state': c_state, 'score': 'tbd'}
    # home_data = {'status': 'True', 'state': 'InGame', 'playerId': user_id, 'Dice_turn': Dice_turn ,'Dice_num': Dice_num ,'current_state': c_state, 'score': 'tbd'}
    return home_data


def broadcast_home_data(tableId, room_name):
    players = tableId.split('_')
    if len(players) == 2:
        U1 = get_home_data(players[0], room_name)
        U2 = get_home_data(players[1], room_name)
        return {
            players[0]: {'Home0': U1, 'Home2': U2},
            players[1]: {'Home0': U2, 'Home2': U1}
        }
    elif len(players) == 4:
        U1 = get_home_data(players[0], room_name)
        U2 = get_home_data(players[1], room_name)
        U3 = get_home_data(players[2], room_name)
        U4 = get_home_data(players[3], room_name)
        return {
            players[0]: {'Home0': U1, 'Home1': U2, 'Home2': U3, 'Home3': U4},
            players[1]: {'Home0': U2, 'Home1': U3, 'Home2': U4, 'Home3': U1},
            players[2]: {'Home0': U3, 'Home1': U4, 'Home2': U1, 'Home3': U2},
            players[3]: {'Home0': U4, 'Home1': U1, 'Home2': U2, 'Home3': U3}
        }


def broadcast_piece_click(ws_client, user_id, room_name, piece_id, move, next_user):
    TableId = _fetch_data(room_name, user_id, 'Table_no')
    players = TableId.split('_')
    uids = list(players)
    p_index = str(players.index(user_id))
    uids.remove(user_id)
    if next_user not in uids:
        uids.append(next_user)
    click_info = {}
    if len(players) == 2:
        click_info = {'0': {players[1]: '2'}, '1': {players[0]: '2'}}
    elif len(players) == 4:
        click_info = {
            '0': {players[1]: '1', players[2]: '2', players[3]: '3'},
            '1': {players[2]: '1', players[3]: '2', players[0]: '3'},
            '2': {players[3]: '1', players[0]: '2', players[1]: '3'},
            '3': {players[0]: '1', players[1]: '2', players[2]: '3'}
        }
    for uid in uids:
        message = {'action': 'GamePlay', "status": True, 'result': {'piece_move': {
            'Home': click_info[p_index][uid], 'pieceId': piece_id, 'move_count': move}, 'Home_data': {'Home0': 'NA'}}}
        if next_user == uid:
            home_data = get_home_data(next_user, room_name)
            message = {'action': 'GamePlay', "status": True, 'result': {'piece_move': {
                'Home': click_info[p_index][uid], 'pieceId': piece_id, 'move_count': move}, 'Home_data': {'Home0': home_data}}}
        conn = _fetch_data(room_name, uid, 'connectionId')
        print("In broadcast_piece_click", uid, conn, message)
        broadcast_info_to_players(ws_client, uid, room_name, [conn], message)


def ValidatePayload(action, payload):
    if action == 'GamePlay':
        for GK in Constants.GamePlaykeys:
            if GK not in payload or not payload[GK]:
                print("invalid GamePlay payload")
                return False
    elif action == 'MatchMaking':
        for MK in Constants.MatchMakingkeys:
            if MK not in payload or not payload[MK]:
                print("invalid MatchMaking payload")
                return False
    else:
        print("invalid action name payload")
        return False
    return True
