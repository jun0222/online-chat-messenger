import socket
import threading
import struct
import uuid

# サーバーの設定
HOST = '127.0.0.1'
TCP_PORT = 9001
UDP_PORT = 9002

# チャットルームの管理
chat_rooms = {}  # {"room_name": {"tokens": [token1, ...], "users": {}, "udp_clients": []}}

def handle_tcp_client(client_socket):
    try:
        while True:
            print(f"[handle_tcp_client] クライアント {client_socket.getpeername()} からデータ受信を待機中...")
            header = receive_all(client_socket, 32)
            if not header:
                print(f"[handle_tcp_client] クライアントが切断しました: {client_socket.getpeername()}")
                break

            # ヘッダーのデコード
            try:
                room_name_size, operation, state, operation_payload_size = struct.unpack('!BBB29s', header)
                room_name_size = int(room_name_size)
                operation_payload_size = int(operation_payload_size.strip(b'\x00').decode('utf-8'))
                print(f"[handle_tcp_client] 受信ヘッダー: room_name_size={room_name_size}, operation={operation}, state={state}, payload_size={operation_payload_size}")
            except struct.error as e:
                print(f"[handle_tcp_client] ヘッダー解析エラー: {e}")
                break

            # ボディの受信
            body = receive_all(client_socket, room_name_size + operation_payload_size)
            if not body:
                print("[handle_tcp_client] ボディ受信エラー: データが不足しています")
                break

            room_name = body[:room_name_size].decode('utf-8')
            payload = body[room_name_size:].decode('utf-8')

            print(f"[handle_tcp_client] 受信データ: room_name='{room_name}', payload='{payload}'")

            if operation == 1 and state == 0:  # 新しいチャットルーム作成
                username = payload
                tokens = [str(uuid.uuid4()) for _ in range(5)]  # トークンを生成

                if room_name not in chat_rooms:
                    chat_rooms[room_name] = {"tokens": tokens, "users": {}, "udp_clients": []}
                chat_rooms[room_name]["users"][tokens[0]] = username

                print(f"[handle_tcp_client] チャットルーム '{room_name}' が作成されました。トークン: {tokens}")

                # 各トークンをクライアントに送信
                for token in tokens:
                    try:
                        response_payload = token
                        response_header = struct.pack(
                            '!BBB29s',
                            len(room_name),
                            1,
                            2,
                            str(len(response_payload)).encode('utf-8').ljust(29, b'\x00')
                        )
                        response_body = struct.pack(
                            f'!{len(room_name)}s{len(response_payload)}s',
                            room_name.encode('utf-8'),
                            response_payload.encode('utf-8')
                        )
                        print(f"[handle_tcp_client] トークン送信: header={response_header}, body={response_body}")
                        client_socket.send(response_header + response_body)
                        print(f"[handle_tcp_client] トークンを送信しました: {response_payload}")
                    except Exception as e:
                        print(f"[handle_tcp_client] トークン送信エラー: {e}")

            elif operation == 3 and state == 0:  # UDPポート情報の受信
                try:
                    udp_port = int(payload)
                    udp_address = (client_socket.getpeername()[0], udp_port)
                    if room_name in chat_rooms:
                        chat_rooms[room_name]["udp_clients"].append(udp_address)
                        print(f"[handle_tcp_client] UDP情報を登録: {udp_address}, room_name={room_name}")
                        client_socket.send(f"UDP通信に切り替えます\n".encode('utf-8'))
                    else:
                        print(f"[handle_tcp_client] 無効なルーム名: {room_name}")
                        client_socket.send("無効なルーム名です\n".encode('utf-8'))
                except ValueError as e:
                    print(f"[handle_tcp_client] UDP情報エラー: {e}")
                    client_socket.send("エラー: 無効な形式のデータ\n".encode('utf-8'))
    except Exception as e:
        print(f"[handle_tcp_client] エラー: {e}")
    finally:
        print(f"[handle_tcp_client] クライアント接続終了: {client_socket.getpeername()}")
        client_socket.close()

def udp_chat_server():
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind((HOST, UDP_PORT))
    print(f"[udp_chat_server] UDPサーバーが起動しました: {HOST}:{UDP_PORT}")

    while True:
        try:
            data, addr = udp_sock.recvfrom(1024)
            message = data.decode('utf-8')
            print(f"[udp_chat_server] 受信データ: {message} from {addr}")

            # UDPクライアントリストを検索してメッセージをブロードキャスト
            for room_name, room_data in chat_rooms.items():
                if addr in room_data["udp_clients"]:
                    print(f"[udp_chat_server] ルーム '{room_name}' でメッセージ受信: {message}")
                    for client in room_data["udp_clients"]:
                        if client != addr:  # 自分以外にブロードキャスト
                            udp_sock.sendto(message.encode('utf-8'), client)
        except Exception as e:
            print(f"[udp_chat_server] エラー: {e}")

def receive_all(sock, length):
    data = b""
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            break
        data += packet
    return data

def start_server():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((HOST, TCP_PORT))
    tcp_sock.listen(5)
    print(f"[start_server] TCPサーバーが起動しました: {HOST}:{TCP_PORT}")

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
