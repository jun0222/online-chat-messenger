import socket
import threading
import struct
import time
import os
import uuid

# サーバーの設定
HOST = '127.0.0.1'
PORT = 9001

# チャットルームの管理
chat_rooms = {}  # {"room_name": {"tokens": [token1, token2, ...], "users": {token1: username1, token2: username2, ...}}}
clients = {}  # {client_socket: (address, username, token)}

def handle_client(client_socket):
    try:
        while True:
            # チャットルームとクライアントを全てprint
            print("\n========================================")
            print("現在のチャットルーム:", {room: chat_rooms[room]["tokens"] for room in chat_rooms})
            print("現在のクライアント:", {c.getpeername(): info for c, info in clients.items()})
            print("========================================")

            # クライアントからのメッセージを受信
            header = client_socket.recv(32)
            if not header:
                break

            # ヘッダーを解析
            room_name_size, operation, state, operation_payload_size = struct.unpack('!BBB29s', header)
            room_name_size = int(room_name_size)
            operation_payload_size = int(operation_payload_size.strip(b'\x00').decode('utf-8'))

            # ボディを受信
            body = client_socket.recv(room_name_size + operation_payload_size)
            room_name = body[:room_name_size].decode('utf-8')
            payload = body[room_name_size:].decode('utf-8')

            if operation == 1 and state == 0:  # 新しいチャットルーム作成リクエスト
                username = payload
                tokens, room_name = create_chat_room(room_name, username)
                clients[client_socket] = (client_socket.getpeername(), username, tokens[0])

                # チャットルーム作成のレスポンス
                response_header = struct.pack('!BBB29s', room_name_size, 1, 1, str(len(tokens[0])).encode('utf-8').ljust(29, b'\x00'))
                response_body = struct.pack(f'!{room_name_size}s{len(tokens[0])}s', room_name.encode('utf-8'), tokens[0].encode('utf-8'))
                client_socket.send(response_header + response_body)

                # 追加トークンを送信
                for token in tokens[1:]:
                    response_header = struct.pack('!BBB29s', room_name_size, 1, 2, str(len(token)).encode('utf-8').ljust(29, b'\x00'))
                    response_body = struct.pack(f'!{room_name_size}s{len(token)}s', room_name.encode('utf-8'), token.encode('utf-8'))
                    client_socket.send(response_header + response_body)
            elif operation == 2:  # チャットルーム参加
                token, username = payload.split()
                for room, data in chat_rooms.items():
                    if token in data["tokens"]:
                        if token not in data["users"]:
                            chat_rooms[room]["users"][token] = username
                            clients[client_socket] = (client_socket.getpeername(), username, token)
                            response_message = f"チャットルーム '{room}' に参加しました"
                            response_message_bytes = response_message.encode('utf-8')  # UTF-8でエンコード
                            payload_size = len(response_message_bytes)

                            response_header = struct.pack(
                                '!BBB29s',
                                len(room),
                                2,
                                0,
                                str(payload_size).encode('utf-8').ljust(29, b'\x00')
                            )
                            response_body = struct.pack(
                                f'!{len(room)}s{payload_size}s',
                                room.encode('utf-8'),
                                response_message_bytes
                            )
                            print(f"Sending header: room_name_size={len(room)}, operation=2, state=0, payload_size={payload_size}")
                            print(f"Sending body: room_name={room}, payload={response_message}")
                            client_socket.send(response_header + response_body)
                        else:
                            response = f"ユーザー '{username}' はすでにチャットルーム '{room}' に存在します\n"
                            client_socket.send(response.encode('utf-8'))
                        break
                else:
                    response = "無効なトークンです\n"
                    client_socket.send(response.encode('utf-8'))
            else:
                # メッセージをチャットルームの他のクライアントに送信
                username = clients[client_socket][1]
                token = clients[client_socket][2]
                room_name = [room for room, data in chat_rooms.items() if token in data["tokens"]][0]
                message = f"{username}: {payload}"
                for client, info in clients.items():
                    if info[2] in chat_rooms[room_name]["tokens"] and client != client_socket:
                        client.send(message.encode('utf-8'))
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        # クライアントが切断された場合の処理
        print(f"クライアント切断: {client_socket.getpeername()}")
        if client_socket in clients:
            token = clients[client_socket][2]
            username = clients[client_socket][1]
            room_name = [room for room, data in chat_rooms.items() if token in data["tokens"]][0]
            chat_rooms[room_name]["tokens"].remove(token)
            del chat_rooms[room_name]["users"][token]
            if not chat_rooms[room_name]["tokens"]:  # チャットルームが空なら削除
                del chat_rooms[room_name]
            del clients[client_socket]
        client_socket.close()

def create_chat_room(room_name, username):
    tokens = [str(uuid.uuid4()) for _ in range(5)]
    if room_name not in chat_rooms:
        chat_rooms[room_name] = {"tokens": [], "users": {}}
    chat_rooms[room_name]["tokens"].extend(tokens)
    chat_rooms[room_name]["users"][tokens[0]] = username
    return tokens, room_name

def force_release_port(port):
    """ポートを強制的に解放"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
        try:
            temp_socket.bind((HOST, port))
        except OSError:
            print(f"ポート {port} を使用中の接続を解放します...")
            os.system(f"lsof -i tcp:{port} | grep LISTEN | awk '{{print $2}}' | xargs kill")
            # Windows の場合
            # os.system(f"netstat -ano | findstr :{port} | for /f %P in ('findstr LISTENING') do taskkill /F /PID %P")

def start_server():
    # ポートを強制解放
    force_release_port(PORT)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"サーバーが起動しました。{HOST}:{PORT}")

    try:
        while True:
            client_socket, address = server_socket.accept()
            print(f"クライアント接続: {address}")
            threading.Thread(target=handle_client, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("\nサーバーをシャットダウンしています...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
