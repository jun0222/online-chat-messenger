import socket
import threading
import struct
import uuid

# サーバーの設定
HOST = '127.0.0.1'  # ローカルホスト
TCP_PORT = 9001  # TCPポート
UDP_PORT = 9002  # UDPポート

# チャットルームの管理
chat_rooms = {}  # {"room_name": {"tokens": [token1, ...], "users": {}, "udp_clients": []}}

def handle_tcp_client(client_socket):
    """
    TCPクライアントを処理する関数
    """
    try:
        room_name = None
        token = None
        while True:
            print(f"[handle_tcp_client] クライアント {client_socket.getpeername()} からデータ受信を待機中...")
            # 32バイト固定のヘッダーを受信
            header = receive_all(client_socket, 32)
            if not header:
                print(f"[handle_tcp_client] クライアントが切断しました: {client_socket.getpeername()}")
                break

            # ヘッダーを解析
            room_name_size, operation, state, operation_payload_size = struct.unpack('!BBB29s', header)
            room_name_size = int(room_name_size)
            operation_payload_size = int(operation_payload_size.strip(b'\x00').decode('utf-8'))

            # ボディを受信
            body = receive_all(client_socket, room_name_size + operation_payload_size)
            room_name = body[:room_name_size].decode('utf-8')  # ルーム名
            payload = body[room_name_size:].decode('utf-8')  # ペイロードデータ

            # 新しいチャットルーム作成リクエスト
            if operation == 1 and state == 0:
                username = payload
                # トークンを5つ生成
                tokens = [str(uuid.uuid4()) for _ in range(5)]
                if room_name not in chat_rooms:
                    # チャットルームを初期化
                    chat_rooms[room_name] = {"tokens": tokens, "users": {}, "udp_clients": []}
                chat_rooms[room_name]["users"][tokens[0]] = username

                # 各トークンをクライアントに送信
                for token in tokens:
                    response_header = struct.pack('!BBB29s', len(room_name), 1, 2, str(len(token)).encode('utf-8').ljust(29, b'\x00'))
                    response_body = room_name.encode('utf-8') + token.encode('utf-8')
                    client_socket.sendall(response_header + response_body)
                    print(f"[handle_tcp_client] トークンを送信しました: {token}")

            # UDPポート情報登録
            elif operation == 3 and state == 0:
                udp_port = int(payload)  # クライアントのUDPポート番号
                udp_address = (client_socket.getpeername()[0], udp_port)
                if room_name in chat_rooms:
                    # UDPクライアントをルームに追加
                    chat_rooms[room_name]["udp_clients"].append(udp_address)
                    print(f"[handle_tcp_client] UDP情報を登録: {udp_address}, room_name={room_name}")
    except Exception as e:
        print(f"[handle_tcp_client] エラー: {e}")
    finally:
        # クライアント切断時の処理
        if room_name and room_name in chat_rooms:
            for tok, user in chat_rooms[room_name]["users"].items():
                if user == client_socket.getpeername():
                    token = tok
                    break

            if token:
                # ユーザーとトークンを削除
                del chat_rooms[room_name]["users"][token]
                if not chat_rooms[room_name]["users"]:  # ルームが空の場合は削除
                    del chat_rooms[room_name]
                # 切断通知メッセージを送信
                disconnect_message = f"{token} がチャットを終了しました。"
                for udp_client in chat_rooms[room_name]["udp_clients"]:
                    udp_sock.sendto(disconnect_message.encode('utf-8'), udp_client)
                print(f"[handle_tcp_client] {token} が削除されました")
        print(f"[handle_tcp_client] クライアント接続終了: {client_socket.getpeername()}")

def udp_chat_server():
    """
    UDPサーバーを実行する関数
    """
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))
    print(f"[udp_chat_server] UDPサーバーが起動しました: {HOST}:{UDP_PORT}")

    while True:
        try:
            # 最大4096バイトのデータを受信
            data, addr = udp_sock.recvfrom(4096)
            if not data:
                continue

            # ヘッダーを解析
            room_name_size, message_size = struct.unpack('!BB', data[:2])
            room_name = data[2:2 + room_name_size].decode('utf-8')  # ルーム名
            message = data[2 + room_name_size:2 + room_name_size + message_size].decode('utf-8')  # メッセージ

            print(f"[udp_chat_server] 受信データ: room_name='{room_name}', message='{message}' from {addr}")

            if room_name in chat_rooms:
                # ルーム内の他のクライアントにメッセージをリレー
                for client in chat_rooms[room_name]["udp_clients"]:
                    if client != addr:
                        udp_sock.sendto(data, client)
        except Exception as e:
            print(f"[udp_chat_server] エラー: {e}")

def receive_all(sock, length):
    """
    指定されたバイト数を完全に受信するヘルパー関数
    """
    data = b""
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            break
        data += packet
    return data

def start_server():
    """
    サーバーを起動するメイン関数
    """
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((HOST, TCP_PORT))
    tcp_sock.listen(5)
    print(f"[start_server] TCPサーバーが起動しました: {HOST}:{TCP_PORT}")

    # UDPサーバーを別スレッドで起動
    threading.Thread(target=udp_chat_server, daemon=True).start()

    try:
        while True:
            client_socket, address = tcp_sock.accept()
            print(f"[start_server] 新しいクライアント接続: {address}")
            threading.Thread(target=handle_tcp_client, args=(client_socket,), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[start_server] サーバーをシャットダウンしています...")
    finally:
        tcp_sock.close()

if __name__ == "__main__":
    start_server()
