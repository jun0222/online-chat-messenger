import socket

# AF_INETを使用し、UDPソケットを作成
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = '0.0.0.0'
server_port = 9001
print('サーバー起動。ポート番号: {}'.format(server_port))

# ソケットを特殊なアドレス0.0.0.0とポート9001に紐付け
sock.bind((server_address, server_port))

while True:
   print('メッセージ返信待機中...')

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

   # クライアントへのデータ送信
   if data:
      sent = sock.sendto(data, address)
      print('メッセージを送信 {} バイト:  {}'.format(sent, address))