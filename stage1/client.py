import socket

# ユーザー名を入力させる
username = input('ユーザー名を入力してください: ').encode('utf-8')

# ユーザー名のバイト数を取得
username_len = len(username)

print('ユーザー名のバイト数: {}'.format(username_len))
if username_len > 255:
    print('ユーザー名が長すぎます')
    exit()

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ''
port = 9050

# サーバ側のアドレスとポート
server_address = '0.0.0.0'
server_port = 9001

# ユーザー名のバイト数 + ユーザー名 + 実際のメッセージ
message = f"{username_len}".encode('utf-8') + username + b'Hello, World!'

# 空の文字列も0.0.0.0として使用できる
sock.bind((address,port))

try:
  print('送信: {}'.format(message.decode('utf-8')))

  # サーバへのデータ送信
  sent = sock.sendto(message, (server_address, server_port))
  print('送信 {} バイト'.format(sent))

  # 応答を受信
  print('サーバからの応答を待っています...')

  # サーバからのデータ受信
  data, server = sock.recvfrom(4096)
  print('受信しました: {}'.format(data.decode('utf-8')))


finally:
  print('接続終了')
  sock.close()