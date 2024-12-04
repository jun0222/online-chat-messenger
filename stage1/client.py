import socket

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ''
port = 9050

# サーバ側のアドレスとポート
server_address = '0.0.0.0'
server_port = 9001

# 送信するメッセージ
message = 'クライアントから送信したメッセージです'.encode('utf-8')

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