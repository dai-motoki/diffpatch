# diffpatch

**注意** 
本機能は実験的かつLLMの揺らぎにより差分Patchが適用されない問題が発生します。
未解決問題なのでプルリク歓迎します。（python純正でのPatch適応は失敗が多く、subprocessによりシェルコマンドを呼び出す設計にしています）
部分的な修正は成功確率が高いので、大掛かりな修正は別の方法をお試しください。

diffpatchは、ファイルの内容を指定された要求に基づいて変更するAI機能です。Anthropic APIを使用して変更内容を生成し、unified diffフォーマットでパッチを適用します。

## 機能

- 指定されたファイルの内容を読み込む
- Anthropic APIを使用して、要求に基づいた変更内容を生成
- 生成されたdiffをカラフルに表示
- ユーザーの確認後、変更を適用
- オプションでdiffファイルを保存

## 使用方法

```
export ANTHROPIC_API_KEY=sk-a~~~~~~~ 
python diffp.py -f <ファイル名> -r <変更要求> [-s <y/n>] [-rf <要求ファイル>]
```

### オプション

- `-f`, `--file`: 変更対象のファイル名（必須）
- `-r`, `--request`: 変更の要求（-rfが指定されていない場合は必須）
- `-s`, `--save-diff`: diffを保存するかどうか（y/n、デフォルトはn）
- `-rf`, `--request-file`: 要求を含むファイル

## 依存関係

- anthropic
- logging
- argparse
- difflib
- tempfile
- subprocess
- os
- datetime

## 注意事項

- Anthropic APIキーが環境変数に設定されている必要があります
- パッチの適用には`patch`コマンドが使用されるため、システムにインストールされている必要があります

## エラーハンドリング

- APIリクエスト、ファイル操作、パッチ適用時のエラーを適切に処理します
- パッチ適用のタイムアウトは3秒に設定されています

## ログ

- 重要な操作やエラーはログに記録されます
- デフォルトのログレベルは WARNING です

## 貢献

バグ報告や機能リクエストは、Issueトラッカーを使用してください。プルリクエストも歓迎します。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルを参照してください。
```

このREADMEは、スクリプトの主な機能、使用方法、依存関係、注意事項などを簡潔に説明しています。必要に応じて、インストール手順やより詳細な使用例を追加することもできます。
