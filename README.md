## サーバーを終了するとき

まずクライアントを落としてからサーバーを落とすこと。  
そうしないと、サーバーのポートが開放されない時がある。

## request header, body の構造

### データの構造を確認

**Request Header**:

```plaintext
b'\x04\x01\x001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
```

**Request Body**:

```plaintext
b'hogea'
```

#### ヘッダーの構造:

- **RoomNameSize**（1 バイト）: `\x04` = 4
- **Operation**（1 バイト）: `\x01` = 1
- **State**（1 バイト）: `\x00` = 0
- **OperationPayloadSize**（残り 29 バイト）:
  - `b'1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'`
  - `\x31` = ASCII 文字 `'1'` に対応し、残りはすべてゼロバイト。

#### ボディの構造:

- **RoomNameSize（4 バイト）**: ルーム名は `hogea` の最初の 4 バイト `hoge`。
- **OperationPayloadSize**（1 バイト）: 残りの 1 バイト `a`。

---

### 要件との照合

1. **ヘッダー（32 バイト）**

   - **RoomNameSize（1 バイト）**: `\x04` = 4 (OK: 最大 28 バイト以下)
   - **Operation（1 バイト）**: `\x01` = 1 (OK)
   - **State（1 バイト）**: `\x00` = 0 (OK)
   - **OperationPayloadSize（29 バイト）**:
     - ASCII `'1'` と 28 バイトのゼロバイト。OperationPayloadSize の最大値 229 バイト以下で問題なし (OK)

2. **ボディ**
   - **RoomNameSize に基づくルーム名**: 最初の 4 バイト `hoge` は RoomNameSize に基づく値で問題なし (OK)
   - **OperationPayloadSize に基づくペイロード**: 残り 1 バイト `a`。最大 229 バイト以下なので問題なし (OK)

