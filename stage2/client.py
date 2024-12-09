import socket

# サーバーの設定
HOST = '127.0.0.1'
PORT = 9001


def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
        print(f"サーバーに接続しました: {HOST}:{PORT}")

        while True:
            # サーバーからのメッセージを受信
            response = client_socket.recv(1024).decode('utf-8')
            if not response:
                print("サーバーから切断されました。")
                break
            print(response.strip())

            # ユーザー入力を送信
            message = input(">> ").strip()
            client_socket.send(message.encode('utf-8'))
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    start_client()
