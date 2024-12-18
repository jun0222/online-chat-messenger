import socket
import threading
import struct

HOST = '127.0.0.1'
TCP_PORT = 9001
UDP_PORT = 9002

def receive_all(sock, length):
    data = b""
    while len(data) < length:
        packet = sock.recv(length - len(data))
        if not packet:
            break
        data += packet
    return data

def receive_messages(sock):
    while True:
        try:
            header = receive_all(sock, 32)
            if not header:
                break

            room_name_size, operation, state, operation_payload_size = struct.unpack('!BBB29s', header)
            room_name_size = int(room_name_size)
            operation_payload_size = int(operation_payload_size.strip(b'\x00').decode('utf-8'))

            body = receive_all(sock, room_name_size + operation_payload_size)
            room_name = body[:room_name_size].decode('utf-8')
            payload = body[room_name_size:].decode('utf-8')

            if operation == 1 and state == 2:
                print(f"[トークン受信] {payload}")
            else:
                print(f"[受信] room_name='{room_name}', message='{payload}'")
        except Exception as e:
            print(f"[receive_messages] エラー: {e}")
            break

def udp_send(sock, server_address, room_name):
    while True:
        try:
            message = input("[UDP送信] > ")
            if message.lower() == 'exit':
                break

            room_name_bytes = room_name.encode('utf-8')
            message_bytes = message.encode('utf-8')
            room_name_size = len(room_name_bytes)
            message_size = len(message_bytes)

            packet = struct.pack('!BB', room_name_size, message_size) + room_name_bytes + message_bytes
            sock.sendto(packet, server_address)
        except Exception as e:
            print(f"[udp_send] エラー: {e}")
            break

def udp_receive(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            room_name_size, message_size = struct.unpack('!BB', data[:2])
            room_name = data[2:2 + room_name_size].decode('utf-8')
            message = data[2 + room_name_size:2 + room_name_size + message_size].decode('utf-8')

            print(f"[UDP受信] room_name='{room_name}', message='{message}' from {addr}")
        except Exception as e:
            print(f"[udp_receive] エラー: {e}")
            break

def main():
    username = input("ユーザー名を入力してください: ")
    choice = input("新しいチャットルームを作成しますか？ (y/n): ")

    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.connect((HOST, TCP_PORT))

    if choice.lower() == 'y':
        room_name = input("新しいチャットルーム名を入力してください: ")
        payload = username
        header = struct.pack('!BBB29s', len(room_name), 1, 0, str(len(payload)).encode('utf-8').ljust(29, b'\x00'))
        body = room_name.encode('utf-8') + payload.encode('utf-8')
        tcp_sock.sendall(header + body)  # 重要: sendallを使用
    else:
        room_name = input("参加するチャットルーム名を入力してください: ")
        token = input("トークンを入力してください: ")
        payload = f"{token} {username}"
        header = struct.pack('!BBB29s', len(room_name), 2, 0, str(len(payload)).encode('utf-8').ljust(29, b'\x00'))
        body = room_name.encode('utf-8') + payload.encode('utf-8')
        tcp_sock.sendall(header + body)

    threading.Thread(target=receive_messages, args=(tcp_sock,), daemon=True).start()

    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('0.0.0.0', 0))
    udp_port = udp_sock.getsockname()[1]

    header = struct.pack('!BBB29s', len(room_name), 3, 0, str(len(str(udp_port))).encode('utf-8').ljust(29, b'\x00'))
    body = room_name.encode('utf-8') + str(udp_port).encode('utf-8')
    tcp_sock.sendall(header + body)

    threading.Thread(target=udp_receive, args=(udp_sock,), daemon=True).start()
    udp_send(udp_sock, (HOST, UDP_PORT), room_name)

if __name__ == "__main__":
    main()
