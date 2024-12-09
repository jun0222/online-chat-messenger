import socket
import threading
import os

# サーバーの設定
HOST = '127.0.0.1'
PORT = 9001

# チャットルームの管理
chat_rooms = {}  # {"room_name": [client_sockets]}
clients = {}  # {client_socket: (address, room_name)}


def handle_client(client_socket):
    try:
        while True:
            # チャットルームとクライアントを全てprint
            print("現在のチャットルーム:", {room: [c.getpeername() for c in clients if clients[c][1] == room] for room in chat_rooms})
            print("現在のクライアント:", {c.getpeername(): info for c, info in clients.items()})
            
            # クライアントからメッセージを受信
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break

            # メッセージを解析
            if data.startswith("CREATE"):
                _, room_name = data.split()
                if room_name not in chat_rooms:
                    chat_rooms[room_name] = []
                    chat_rooms[room_name].append(client_socket)
                    clients[client_socket] = (client_socket.getpeername(), room_name)
                    client_socket.send(f"チャットルーム '{room_name}' を作成しました。\n".encode('utf-8'))
                else:
                    client_socket.send(f"チャットルーム '{room_name}' はすでに存在します。\n".encode('utf-8'))
            elif data.startswith("JOIN"):
                _, room_name = data.split()
                if room_name in chat_rooms:
                    chat_rooms[room_name].append(client_socket)
                    clients[client_socket] = (client_socket.getpeername(), room_name)
                    client_socket.send(f"チャットルーム '{room_name}' に参加しました。\n".encode('utf-8'))
                else:
                    client_socket.send(f"チャットルーム '{room_name}' は存在しません。\n".encode('utf-8'))
            else:
                client_socket.send("無効なコマンドです。CREATE <room_name> または JOIN <room_name> を使用してください。\n".encode('utf-8'))
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        # クライアントが切断された場合の処理
        print(f"クライアント切断: {client_socket.getpeername()}")
        if client_socket in clients:
            room_name = clients[client_socket][1]
            chat_rooms[room_name].remove(client_socket)
            if not chat_rooms[room_name]:  # チャットルームが空なら削除
                del chat_rooms[room_name]
            del clients[client_socket]
        client_socket.close()


def force_release_port(port):
    """ポートを強制的に解放"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_socket:
        try:
            temp_socket.bind((HOST, port))
        except OSError:
            print(f"ポート {port} を使用中の接続を解放します...")
            os.system(f"fuser -k {port}/tcp")  # Linux/Unix 系システムでポートを解放
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
            print(f"新しいクライアント接続: {address}")
            client_socket.send("CREATE <room_name> または JOIN <room_name> を入力してください。\n".encode('utf-8'))
            threading.Thread(target=handle_client, args=(client_socket,)).start()
    except KeyboardInterrupt:
        print("\nサーバーをシャットダウンしています...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
