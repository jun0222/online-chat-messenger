import socket
import threading

# ユーザー名を入力させる
username = input('ユーザー名を入力してください: ').encode('utf-8')

# ユーザー名のバイト数を取得
username_len = len(username)

print('ユーザー名のバイト数: {}'.format(username_len))
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
print('使用するポート番号: {}'.format(port))

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
            print('タイムアウトしました。接続を終了します。')
            break
        print('受信しました: {}'.format(data.decode('utf-8')))
        print('メッセージを入力してください: ', sep="")
    sock.close()
    exit()

thread = threading.Thread(target=receive_messages, daemon=True)
thread.start()

try:
    while True:
        # 実際のメッセージ
        chat_message = input('メッセージを入力してください: ').encode('utf-8')

        # 1バイトで username_len を送信するために bytes([username_len]) を使用
        message = bytes([username_len]) + username + chat_message

        print('送信データ: {}'.format(message))

        # サーバへのデータ送信
        # 受信はスレッドで行うので、こちらは送信のみ
        sent = sock.sendto(message, (server_address, server_port))
        print('送信 {} バイト'.format(sent))

finally:
    sock.close()
    print('接続終了')