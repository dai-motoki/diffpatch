from anthropic import Anthropic
import logging
from unittest.mock import patch, MagicMock
import unittest
import argparse
import difflib
import tempfile
import subprocess
import os
import datetime

# ログの設定
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Anthropicクライアントの初期化
anthropic_client = Anthropic()

def generate_text_anthropic(prompt: str):
    logger.info(f"Anthropicリクエストを送信: prompt={prompt[:100]}...")  # 最初の100文字だけログに記録
    try:
        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=8192,
            temperature=1,
            messages=[
                {"role": "user", "content": prompt}
            ],
            extra_headers={"anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"}
        )
        logger.info("Anthropicでテキスト生成成功")
        return {"generated_text": message.content[0].text}
    except Exception as e:
        logger.error(f"Anthropicでのテキト生成中にエラーが発生: {str(e)}")
        raise

def create_diff_prompt(file_name: str, file_contents: str, request: str) -> str:
    prompt = f"""あなたは高精度のdiffツールです。file name: {file_name}の {file_contents}に対して {request}.
     以下の規則に厳密に従ってください：

1. 出力は必ずUnified diff形式にしてください。
2. 出力の最初の2行は以下のようにしてください：
   ```
   --- original
   +++ modified
   ```
3. 各変更箇所（ハンク）の前に、以下のような形式のヘッダーを付けてください：
   ```
   @@ -start,count +start,count @@
   ```
   - startは変更箇所の開始行番号
   - countはハンクに含まれる行数
   - オリジナルと修正後で異なる場合があります
4. できる限り指示されたことにのみ対応すること。余計な実装をしない。
5. 削除された行の先頭に `-` を付けてください。
6. 追加された行の先頭に `+` を付けてください。
7. 変更された行は、削除行と追加行の組み合わせとして表現してください。
8. 各ハンクの前後に3行のコンテキスト（変更されていない行）を含めてください。
9. diff以外の説明や注釈は一切含めないでください。純粋なdiffの出力のみを提供てください。
10. 最小限の変更で対応してください。

ではUnified diffを生成してください：
"""
    response = generate_text_anthropic(prompt)
    return response["generated_text"]  # 辞書から生成されたテキストを直接返す

def apply_patch(original_content, diff_content):
    logger.info("パッチ適用処理を開始します")
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as original_file, \
         tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as patch_file:
        logger.debug(f"一時ファイルを作成しました: original={original_file.name}, patch={patch_file.name}")
        original_file.write(original_content)
        patch_file.write(diff_content)
        original_file.flush()
        patch_file.flush()
        logger.debug("一時ファイルに内容を書き込みました")

        patch_command = f"patch -u {original_file.name} -i {patch_file.name}"
        logger.info(f"パッチコマンドを実行します: {patch_command}")
        try:
            result = subprocess.run(patch_command, shell=True, capture_output=True, text=True, encoding='utf-8', timeout=3)
            logger.debug(f"パッチコマンドの実行結果: stdout={result.stdout}, stderr={result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("パッチコマンドが3秒でタイムアウトしました")
            raise

        with open(original_file.name, 'r', encoding='utf-8') as patched_file:
            patched_content = patched_file.read()
            logger.debug("パッチ適用後の内容を読み込みました")

    logger.info("一時ファイルを削除します")
    os.unlink(original_file.name)
    os.unlink(patch_file.name)

    logger.info("パッチ適用処理が完了しました")
    return patched_content

def modify_file_with_diff(file_name: str, original_content: str, modified_content: str) -> str:
    """
    指定されたファイルの内容をunified diffのパッチを使って変更します。

    :param file_name: 変更対象のファイル名
    :param original_content: 元のファイルの内容
    :param modified_content: 修正後のファイルの内容
    :return: 変更後のファイルの内容
    """
    diff = create_diff_prompt(file_name, original_content, modified_content)
    patched_content = apply_patch(original_content, diff)
    return patched_content

def diffp(file_name: str, request: str, save_diff: str):
    """
    指定されたファイルに対して要望に基づいた変更を行います。
    :param save_diff: Diffを保存するかどうか (y/n)

    :param file_name: 変更対象のファイル名
    :param request: 変更の要望
    :return: 変更後のファイルの内容
    """
    try:
        # ファイルの内容を読み込む
        with open(file_name, 'r', encoding='utf-8') as file:
            original_content = file.read()

        # diffを生成する
        diff_result = create_diff_prompt(file_name, original_content, request)

        # カラフルにdiff結果を表示
        colored_diff = diff_result.replace('\n-', '\n\033[91m-').replace('\n+', '\n\033[92m+').replace('\n@', '\n\033[94m@')
        print(colored_diff + '\033[0m')

        # ユーザーに確認と変更の保存
        user_input = input("変更を適用しますか？ (y/n): ")
        if user_input.lower() != 'y':
            print("変更を中止しました。")
            return None

        # パッチを適用する
        try:
            modified_content = apply_patch(original_content, diff_result)
        except subprocess.TimeoutExpired:
            print("パッチの適用が3秒でタイムアウトしました。処理を中止します。")
            return None
        except Exception as e:
            print(f"パッチの適用中にエラーが発生しました: {str(e)}")
            return None

        # Diffを時間付きで保存（オプション）
        if save_diff == 'y':
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            diff_file_name = f"{file_name}_{timestamp}.diff"
            with open(diff_file_name, 'w', encoding='utf-8') as diff_file:
                diff_file.write(diff_result)
            print(f"Diffが{diff_file_name}に保存されました。")
        else:
            diff_file_name = None

        # 変更後の内容をファイルに書き込む
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(modified_content)

        print(f"{file_name}が正常に更新されました。")
        return modified_content

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ファイルに対して要望に基づいた変更を行います。")
    parser.add_argument("-f", "--file", required=True, help="変更対象のファイル名")
    parser.add_argument("-r", "--request", help="変更の要望")
    parser.add_argument("-s", "--save-diff", choices=['y', 'n'], default='n', help="Diffを保存するかどうか")
    parser.add_argument("-rf", "--request-file", help="要求を含むファイル")
    
    args = parser.parse_args()
    
    if args.request_file:
        with open(args.request_file, 'r', encoding='utf-8') as request_file:
            request = request_file.read().strip()
    else:
        request = args.request
    
    diffp(args.file, request, args.save_diff)