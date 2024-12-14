import socket
import threading
import struct

# サーバーの設定
HOST = '127.0.0.1'
PORT = 9001

# データを完全に受信するための関数
def receive_all(sock, length):
    data = b""
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            break
        data += packet
    return data

def receive_messages(sock):
    while True:
        try:
            # ヘッダーを受信（32バイト固定）
            header = receive_all(sock, 32)
            if not header:
                break

            # ヘッダーをデコード
            room_name_size, operation, state, operation_payload_size = struct.unpack('!BBB29s', header)
            room_name_size = int(room_name_size)
            operation_payload_size = int(operation_payload_size.strip(b'\x00').decode('utf-8'))

            # ボディを受信（期待するサイズを計算）
            body = receive_all(sock, room_name_size + operation_payload_size)
            if len(body) < room_name_size + operation_payload_size:
                raise ValueError("受信データが不足しています")

            # ボディを解析
            room_name = body[:room_name_size].decode('utf-8')
            payload = body[room_name_size:].decode('utf-8')

            # メッセージの表示
            if operation == 1 and state == 1:
                print(f"新しいチャットルーム '{room_name}' が作成されました。トークン: {payload}")
            elif operation == 1 and state == 2:
                print(f"チャットルーム '{room_name}' に追加のトークン: {payload}")
            elif operation == 2 and state == 1:
                print(payload)
            else:
                print(f"チャットルーム '{room_name}': {payload}")
        except Exception as e:
            print(f"受信エラー: {e}")
            break

def main():
    username = input("ユーザー名を入力してください: ")
    choice = input("新しいチャットルームを作成しますか？ (y/n): ")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    if choice.lower() == 'y':
        # 新しいチャットルームを作成
        room_name = input("新しいチャットルーム名を入力してください: ")
        payload = f"{username}"
        header = struct.pack('!BBB29s', len(room_name), 1, 0, str(len(payload)).encode('utf-8').ljust(29, b'\x00'))
        body = room_name.encode('utf-8') + payload.encode('utf-8')
        sock.send(header + body)
    else:
        # 既存のチャットルームに参加
        token = input("トークンを入力してください: ")
        payload = f"{token} {username}"
        header = struct.pack('!BBB29s', 0, 2, 0, str(len(payload)).encode('utf-8').ljust(29, b'\x00'))
        body = payload.encode('utf-8')
        sock.send(header + body)

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    try:
        while True:
            message = input()
            if message.lower() == 'exit':
                break
            payload = message
            header = struct.pack('!BBB29s', 0, 0, 0, str(len(payload)).encode('utf-8').ljust(29, b'\x00'))
            body = payload.encode('utf-8')
            sock.send(header + body)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

if __name__ == "__main__":
    main()
