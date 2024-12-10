import socket
import threading

# サーバーの設定
HOST = '127.0.0.1'
PORT = 9001

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if not message:
                break
            print(message)
        except:
            break

def main():
    username = input("ユーザー名を入力してください: ")
    choice = input("新しいチャットルームを作成しますか？ (y/n): ")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    if choice.lower() == 'y':
        # 新しいチャットルームを作成
        room_name = input("新しいチャットルーム名を入力してください: ")
        sock.send(f"C {room_name} {username}".encode('utf-8'))
    else:
        # 既存のチャットルームに参加
        token = input("トークンを入力してください: ")
        sock.send(f"J {token} {username}".encode('utf-8'))

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    try:
        while True:
            message = input()
            if message.lower() == 'exit':
                break
            sock.send(message.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

if __name__ == "__main__":
    main()