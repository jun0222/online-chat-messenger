import socket

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
address = ''
port = 9050

# サーバ側のアドレスとポート
server_address = '0.0.0.0'
server_port = 9001

# 送信するメッセージ
message = b'Message to send to the client.'

# 空の文字列も0.0.0.0として使用できる
sock.bind((address,port))

try:
  print('sending {!r}'.format(message))

  # サーバへのデータ送信
  sent = sock.sendto(message, (server_address, server_port))
  print('Send {} bytes'.format(sent))

  # 応答を受信
  print('waiting to receive')

  # サーバからのデータ受信
  data, server = sock.recvfrom(4096)
  print('received {!r}'.format(data))

finally:
  print('closing socket')
  sock.close()