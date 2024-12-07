import socket
import time
import threading

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001
print('サーバー起動。ポート番号: {}'.format(server_port))

# ソケットを特殊なアドレス0.0.0.0とポート9001に紐付け
sock.bind((server_address, server_port))

# 接続中のクライアントを保存
clients = {}
HEARTBEAT_INTERVAL = 5
TIMEOUT = 10

def check_clients():
    while True:
        # クライアントの最終接続時刻を確認し、タイムアウトしたクライアントを削除
        current_time = time.time()
        for address, last_seen in list(clients.items()):
            if current_time - last_seen > TIMEOUT:
                print('クライアントがタイムアウトしました: {}'.format(address))
                del clients[address]
                # タイムアウト通知を送信
                sock.sendto(b'TIMEOUT', address)
        time.sleep(HEARTBEAT_INTERVAL)

# クライアントの接続状態をチェックするスレッド
threading.Thread(target=check_clients, daemon=True).start()

while True:
    print(f"メッセージ返信待機中...{server_address}:{server_port}")

    # クライアントからのデータ受信
    data, address = sock.recvfrom(4096)
    print('メッセージを受信 {} バイト:  {}'.format(len(data), address))
    print('内容: {}'.format(data.decode('utf-8')))
    
    # 最初の1バイトを取得し、ユーザー名のバイト数を取得
    username_len = data[0]
    print('ユーザー名のバイト数: {}'.format(username_len))

    # username_lenの次のバイトからユーザー名を取得
    username = data[1:username_len + 1]
    print('ユーザー名: {}'.format(username.decode('utf-8')))

    # メッセージを取得
    chat_message = data[username_len + 1:]
    print('メッセージ: {}'.format(chat_message.decode('utf-8')))

    # クライアントの最終接続時刻を更新
    clients[address] = time.time()

    # 受信したメッセージを他のクライアントに送信
    for client_address in clients:
        if client_address != address:
            print('クライアントにメッセージを送信: {}'.format(client_address))
            sock.sendto(data, client_address)
            print('送信完了')