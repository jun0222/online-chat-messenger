import socket
import threading

# ユーザー名を入力させる
username = input('ユーザー名を入力してください: ').encode('utf-8')

# ユーザー名のバイト数を取得
username_len = len(username)

print(f'ユーザー名のバイト数: {username_len}')
if username_len > 255:
    print('ユーザー名が長すぎます')
    exit()

def find_available_port(start_port):
    port = start_port
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            port += 1

# 初期ポート番号を設定
initial_port = 9050
port = find_available_port(initial_port)
print(f'使用するポート番号: {port}')

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ''

# サーバ側のアドレスとポート
server_address = '0.0.0.0'
server_port = 9001

# 空の文字列も0.0.0.0として使用できる
sock.bind((address, port))

# サーバからのデータ受信スレッド
def receive_messages():
    while True:
        # サーバからのデータ受信
        data, server = sock.recvfrom(4096)
        if data == b'TIMEOUT':
            print('\nタイムアウトしました。接続を終了します。')
            break
        if data == b'INVALID_DATA_DISCONNECT':
            print('\n不正なデータを受信しました。接続を終了します。')
            break
        print(f'\n受信しました: {data.decode("utf-8")}')
        print('メッセージを入力してください: ', sep="")
    sock.close()
    exit()

thread = threading.Thread(target=receive_messages, daemon=True)
thread.start()

MAX_SEND_FAILURES = 3
send_failures = 0

try:
    while True:
        # 実際のメッセージ
        chat_message = input('メッセージを入力してください: ').encode('utf-8')

        # 1バイトで username_len を送信するために bytes([username_len]) を使用
        message = bytes([username_len]) + username + chat_message

        print(f'\n送信データ: {message}')

        try:
            # サーバへのデータ送信
            sent = sock.sendto(message, (server_address, server_port))
            print(f'送信 {sent} バイト')
            send_failures = 0  # 送信成功時に失敗カウントをリセット
        except Exception as e:
            print(f'送信に失敗しました: {e}')
            send_failures += 1
            if send_failures >= MAX_SEND_FAILURES:
                print('送信失敗が続いたため、接続を終了します。')
                break

finally:
    sock.close()
    print('接続終了')