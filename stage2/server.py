import socket
import threading

# サーバーの設定
HOST = '127.0.0.1'
PORT = 9001

# チャットルームの管理
chat_rooms = {}  # {"room_name": [usernames]}
clients = {}  # {client_socket: (address, username, room_name)}

def handle_client(client_socket):
    try:
        while True:
            # チャットルームとクライアントを全てprint
            print("")
            print("========================================")
            print("現在のチャットルーム:", {room: chat_rooms[room] for room in chat_rooms})
            print("現在のクライアント:", {c.getpeername(): info for c, info in clients.items()})
            print("========================================")
            
            # クライアントからメッセージを受信
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break

            # メッセージを解析
            if data.startswith("C"):
                _, room_name, username = data.split()
                if room_name not in chat_rooms:
                    chat_rooms[room_name] = []
                if username not in chat_rooms[room_name]:
                    chat_rooms[room_name].append(username)
                    clients[client_socket] = (client_socket.getpeername(), username, room_name)
                    client_socket.send(f"チャットルーム '{room_name}' にユーザー '{username}' を追加しました。\n".encode('utf-8'))
                else:
                    client_socket.send(f"ユーザー '{username}' はすでにチャットルーム '{room_name}' に存在します。\n".encode('utf-8'))
            elif data.startswith("J"):
                _, token, username = data.split()
                if token in chat_rooms:
                    room_name = chat_rooms[token][0]
                    if username not in chat_rooms[token]:
                        chat_rooms[token].append(username)
                        clients[client_socket] = (client_socket.getpeername(), username, room_name)
                        client_socket.send(f"チャットルーム '{room_name}' に参加しました。\n".encode('utf-8'))
                    else:
                        client_socket.send(f"ユーザー '{username}' はすでにチャットルーム '{room_name}' に存在します。\n".encode('utf-8'))
                else:
                    client_socket.send(f"無効なトークンです。\n".encode('utf-8'))
            else:
                # メッセージをチャットルームの他のクライアントに送信
                username = clients[client_socket][1]
                room_name = clients[client_socket][2]
                message = f"{username}: {data}"
                for client, info in clients.items():
                    if info[2] == room_name and client != client_socket:
                        client.send(message.encode('utf-8'))
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        # クライアントが切断された場合の処理
        print(f"クライアント切断: {client_socket.getpeername()}")
        if client_socket in clients:
            room_name = clients[client_socket][2]
            username = clients[client_socket][1]
            chat_rooms[room_name].remove(username)
            if not chat_rooms[room_name]:  # チャットルームが空なら削除
                del chat_rooms[room_name]
            del clients[client_socket]
        client_socket.close()

def create_chat_room():
    token = str(time.time())
    room_name = f'room_{len(chat_rooms)}'
    chat_rooms[token] = [room_name]
    return token, room_name
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