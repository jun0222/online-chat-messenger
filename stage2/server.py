import socket
import time
import threading

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001
print(f'サーバー起動。ポート番号: {server_port}')

# ソケットを特殊なアドレス0.0.0.0とポート9001に紐付け
sock.bind((server_address, server_port))

# 接続中のクライアントを保存
clients = {}
invalid_data_count = {}  # クライアントごとの不正データカウンター
HEARTBEAT_INTERVAL = 5
TIMEOUT = 10
INVALID_DATA_THRESHOLD = 3  # 不正データの許容回数

# チャットルームの情報
chat_rooms = {}

# チャットルームを作成し、トークンを返す
def create_chat_room():
    token = str(time.time())
    chat_rooms[token] = []
    # トークンとルーム名を紐付け
    room_name = f'room_{len(chat_rooms)}'
    chat_rooms[token].append(room_name)
    return token

def check_clients():
    while True:
        # クライアントの最終接続時刻を確認し、タイムアウトしたクライアントを削除
        current_time = time.time()
        for address, last_seen in list(clients.items()):
            if current_time - last_seen > TIMEOUT:
                print(f'タイムアウト: {address}')
                del clients[address]
                if address in invalid_data_count:
                    del invalid_data_count[address]
                # タイムアウト通知を送信
                sock.sendto(b'TIMEOUT', address)
        time.sleep(HEARTBEAT_INTERVAL)

# クライアントの接続状態をチェックするスレッド
threading.Thread(target=check_clients, daemon=True).start()

while True:
    print(f"\nメッセージ返信待機中... {server_address}:{server_port}")

    try:
        # クライアントからのデータ受信
        data, address = sock.recvfrom(4096)
        print(f'\nメッセージを受信 {len(data)} バイト: {address}')
        print(f'受信データ: {data}')

        # データ形式の検証
        if len(data) < 2:
            raise ValueError("データが不正です。最小の長さを満たしていません。")

        # 最初の1バイトを取得し、ユーザー名のバイト数を取得
        username_len = data[0]
        if len(data) < username_len + 1:
            raise ValueError("データが不正です。ユーザー名の長さが一致しません。")

        # username_lenの次のバイトからユーザー名を取得
        username = data[1:username_len + 1].decode('utf-8')
        token = data[username_len + 1:].decode('utf-8')

        if address not in clients:
            # 初回接続時にトークンをチェック
            if token not in chat_rooms:
                # トークンが無効な場合、新しいチャットルームを作成
                new_token = create_chat_room()
                chat_rooms[new_token].append(address)
                sock.sendto(f'無効なトークンです。新しいチャットルームを作成しました。トークン: {new_token}'.encode('utf-8'), address)
                token = new_token  # 新しいトークンを使用してチャットを続ける
            else:
                chat_rooms[token].append(address)
            print(f'ユーザー名: {username}')
            print(f'トークン: {token}')

        # クライアントの最終接続時刻を更新
        clients[address] = time.time()
        invalid_data_count[address] = 0  # 正常なデータが来たらカウンターをリセット

        # 受信したメッセージを他のクライアントに送信
        for client_address in clients:
            if client_address != address:
                print(f'クライアントにメッセージを送信: {client_address}')
                sock.sendto(data, client_address)
                print('送信完了')

    except (ValueError, UnicodeDecodeError) as e:
        print(f"不正なデータを受信: {address}, 理由: {e}")
        if address not in invalid_data_count:
            invalid_data_count[address] = 0
        invalid_data_count[address] += 1

        if invalid_data_count[address] >= INVALID_DATA_THRESHOLD:
            print(f"不正データが連続で検出されました。クライアントを削除: {address}")
            if address in clients:
                del clients[address]
            if address in invalid_data_count:
                del invalid_data_count[address]