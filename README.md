# NaroEditor

小説家になろう・カクヨム・Pixiv 向けルビ・傍点記法に対応した、Windows 用日本語テキストエディターです。

## 機能

- **マルチタブ / 分割ペイン** — タブを左右・上下に分割して同時編集
- **プロジェクトツリー** — フォルダをプロジェクトとして登録し、ファイルをツリー表示。エクスプローラーの変更をリアルタイムで反映
- **ルビ・傍点の挿入** — なろう/カクヨム・Pixiv 形式に対応したショートカット挿入
- **Markdown プレビュー** — フロート / ドッキング切り替え可能なリアルタイムプレビュー
- **文字コード自動判別** — UTF-8・Shift_JIS・EUC-JP などを自動検出して開く
- **文字数・行数カウント** — ステータスバーにリアルタイム表示
- **テキスト変換** — 全角↔半角、大文字↔小文字、インデント、改行削除など
- **ファイルロック** — 開いているファイルをエクスプローラーから誤って移動しないようロック
- **セッション復元** — 前回終了時のタブを次回起動時に自動で復元
- **ダークテーマ** — 目に優しいダーク UI

## 動作環境

- Windows 10 / 11 (64bit)
- Python 3.10 以上（ソースから実行する場合）

## インストール

### 方法 1：実行ファイル（exe）を使う

[Releases](https://github.com/s1675dis/NaroEditor/releases) ページから `NaroEditor.exe` をダウンロードして実行してください。インストール不要です。

> **初回起動について**  
> 初回はファイルの展開処理が走るため起動に時間がかかります。2回目以降は高速に起動します。

### 方法 2：ソースから実行する

**1. リポジトリをクローン**

```bash
git clone https://github.com/s1675dis/NaroEditor.git
cd NaroEditor
```

**2. 依存ライブラリをインストール**

```bash
pip install -r requirements.txt
```

**3. 起動**

```bash
python NaroEditor.py
```

または `launch.bat` をダブルクリックしてください。

## ショートカット一覧

### ファイル

| 操作 | ショートカット |
|---|---|
| 新規タブ | `Ctrl+N` |
| ファイルを開く | `Ctrl+O` |
| 上書き保存 | `Ctrl+S` |
| 名前を付けて保存 | `Ctrl+Shift+S` |
| タブを閉じる | `Ctrl+W` |

### 編集

| 操作 | ショートカット |
|---|---|
| 元に戻す | `Ctrl+Z` |
| やり直し | `Ctrl+Y` |
| 切り取り | `Ctrl+X` |
| コピー | `Ctrl+C` |
| 貼り付け | `Ctrl+V` |
| 引用符付き貼り付け | `Ctrl+Q` |
| 行削除 | `Ctrl+Enter` |
| すべて選択 | `Ctrl+A` |
| 書き換え禁止（読み取り専用） | `Ctrl+Shift+N` |
| 検索 | `Ctrl+F` |
| 置換 | `Ctrl+R` |

### テキスト変換

| 操作 | ショートカット |
|---|---|
| 小文字に変換 | `Ctrl+L` |
| 大文字に変換 | `Ctrl+Shift+L` |
| 半角に変換 | `Ctrl+G` |
| 全角に変換 | `Ctrl+Shift+G` |
| 空白インデント | `Ctrl+Shift+I` |
| 空白逆インデント | `Ctrl+Shift+U` |
| 改行削除 | `Ctrl+Shift+T` |

### 記法挿入

| 操作 | ショートカット |
|---|---|
| ルビ（なろう / カクヨム） | `Alt+R` |
| ルビ（Pixiv） | `Alt+E` |
| 傍点（なろう / カクヨム） | `Alt+/` |
| 傍点（Pixiv） | `Alt+.` |

### 表示

| 操作 | ショートカット |
|---|---|
| プレビューの表示 / 非表示 | `Ctrl+Shift+P` |
| 左右に分割 | — |
| 上下に分割 | — |

### プロジェクトツリー

| 操作 | 方法 |
|---|---|
| ファイルを開く | クリック |
| フォルダの展開 / 折りたたみ | クリック |
| 名前を変更 | `F2` キー または右クリックメニュー |
| 新規フォルダ / ファイル作成 | 右クリックメニュー |
| 削除 | 右クリックメニュー |
| エクスプローラーで開く | 右クリックメニュー |

## ソースからビルドする（exe 生成）

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --icon NaroEditor.ico --name NaroEditor NaroEditor.py
```

ビルド成果物は `dist/NaroEditor.exe` に出力されます。

> **Dropbox フォルダ内でのビルドについて**  
> Dropbox の同期とWindows Defenderの競合により `dist/` 以下への書き込みが失敗する場合があります。その際は `--distpath C:\temp\dist` のように Dropbox 外のパスを指定してください。

## 設定ファイルの保存場所

`%APPDATA%\NaroEditor\config.json`

プロジェクトフォルダ、タブのセッション情報、ウィンドウ位置などが保存されます。

## ライセンス

このソフトウェアは [GNU General Public License v3.0](LICENSE) のもとで配布されています。

使用ライブラリ：
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — GPL v3 / 商用ライセンス (Riverbank Computing)
- [Qt6](https://www.qt.io/) — LGPL v3 / 商用ライセンス (The Qt Company)
- [chardet](https://github.com/chardet/chardet) — LGPL v2.1
- Python 標準ライブラリ — PSF License
