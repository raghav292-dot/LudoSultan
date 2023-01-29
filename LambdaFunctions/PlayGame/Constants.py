domain_mapping = {
    'wsocket.ludo4g.com': '0z4c4vktp8.execute-api.ap-south-1.amazonaws.com',
    'wsocket.ludosultan.com': 'dnipb2guye.execute-api.ap-south-1.amazonaws.com',
}

table_mapping = {
    'public': {'2': '2PlayerRoomPublic', '4': '4PlayerRoomPublic'},
    'private': {'2': '2PlayerRoomPrivate', '4': '4PlayerRoomPrivate'},
    'connection_data': 'PlayersMetadata'
}

piece_mapping = {
    '1': 'Piece_0_pos',
    '2': 'Piece_1_pos',
    '3': 'Piece_2_pos',
    '4': 'Piece_3_pos'
}
match_making_timer = '60'  # in seconds
piece_move_timer = '20'  # in seconds

LobbyTTLArn = 'arn:aws:states:ap-south-1:455664674507:stateMachine:LobbyTTL'

move_pos = {
    "P1movablePositionIndex": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57],
    "P2movablePositionIndex": [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 58, 59, 60, 61, 62, 63],
    "P3movablePositionIndex": [26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 64, 65, 66, 67, 68, 69],
    "P4movablePositionIndex": [39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 70, 71, 72, 73, 74, 75]
}

winning_pos = {
    "P1_pos": 'xyz',
    "P2_pos": 'xyz',
    "P3_pos": 'xyz',
    "P4_pos": 'xyz'
}

GamePlaykeys = ['playerId', 'players',
                'betAmount', 'lobby', 'deviceId', 'pieceId']
MatchMakingkeys = ['playerId', 'players', 'betAmount', 'lobby', 'deviceId']
