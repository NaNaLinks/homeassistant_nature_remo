# Nature Remo - Home Assistant カスタム統合

⭐ この統合が役に立った場合は、GitHubでスターを付けていただけると嬉しいです。

Nature RemoをHome Assistantに連携するためのカスタムインテグレーションです。  
エアコンや照明の操作、温度・湿度などの情報をHome Assistant上でまとめて扱えるようになります。

---

## ⚠️ ご注意
このカスタムインテグレーションは、Nature社およびHome Assistantの**非公式**な統合です。  
利用にあたっては、**自己責任で**ご使用いただきますようお願いいたします。

---

## 主な機能

- Nature Remoに登録された家電（エアコン・照明）の操作
- 温度・湿度・照度・人感センサーのデータ取得
- Nature Remo E / E Liteによるスマートメーターの電力データ取得
- カスタムサービスによる照明の詳細な制御（モード指定など）
- signals に基づいて生成されたリモートエンティティを使って IR コマンドを送信

---

## インストール方法

1. 本リポジトリを以下のパスに配置してください：

```
<設定フォルダ>/custom_components/nature_remo/
```

2. Home Assistantを再起動してください。

---

## セットアップ手順

1. Home Assistantの「設定 → デバイスとサービス → 統合を追加」から `Nature Remo` を選択します。
2. アクセストークン（APIキー）と統合の名前を入力します。
   - トークンは [Nature公式サイト](https://home.nature.global) から発行できます。
3. 登録済みのデバイスや家電が自動的に追加されます。

---

## オプション設定

- データの更新間隔（秒単位）を指定できます。
  - デフォルトは `60秒` に設定されています。

⚠️ Nature Remo Cloud API にはリクエスト制限があります。  
更新間隔を短く設定しすぎると、APIの制限に達する可能性があります。

---

## 対応エンティティ一覧

| 種類    | 説明                                                              |
|---------|-------------------------------------------------------------------|
| climate | エアコンの操作（冷房・暖房・除湿など）                           |
| light   | 照明の操作（オン／オフ、モード切替）                              |
| sensor  | 温度、湿度、照度、人感、電力（買電／売電）                        |
| remote  | IR／AC／LIGHTのアプライアンスに定義された signals を送信できる   |

※ 今後、さらに対応デバイスやエンティティを拡張予定です。

---

## サンプル：リモートエンティティの使い方

Nature Remoに定義された `signals` 情報をもとに `remote` エンティティが生成されます。  
Home Assistant上から `remote.send_command` を使って信号を送信できます。

### 例：サービス呼び出し

以下のように `remote.send_command` を使って信号を送信します：

```yaml
service: remote.send_command
target:
  entity_id: remote.living_room_remote  # リモートエンティティID
data:
  command: "電源"  # Remoに登録されたボタン名
```

---

## 作者情報

- 作成者：[@nanosns](https://github.com/nanosns) (NaNaRin)
- 所属・運営：[@NaNaLinks](https://github.com/NaNaLinks)
- SNS： [note](https://note.com/nanomana)

---

## ライセンス

MIT License