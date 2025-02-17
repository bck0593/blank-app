import os
import re
import requests
import time
import zipfile
import io
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import streamlit as st

# アプリ名設定
st.set_page_config(page_title="PDFダウンローダー", page_icon="📥")

# 入力されたURL
BASE_URL = st.text_input("PDFをダウンロードしたいURLを入力してください", "https://www.ncbank.co.jp/news/release/2024/")

# 保存先フォルダ
SAVE_FOLDER = "./PDF"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# PDFリンクの取得
def get_pdf_links(base_url):
    response = requests.get(base_url)
    if response.status_code != 200:
        st.error(f"エラー: {BASE_URL}が正しく読み込まれませんでした。")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    pdf_data = []
    
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".pdf"):
            full_url = urljoin(BASE_URL, href)
            title = link.get_text(strip=True)
            if not title:
                title = "unknown_title"

            # タイトルから日付を抽出（仮にyyyy-mm-dd形式を想定）
            date_str = re.search(r'(\d{4}-\d{2}-\d{2})', title)
            date = datetime.strptime(date_str.group(1), '%Y-%m-%d') if date_str else None

            # タイトルをファイル名として使えるように整形
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            safe_title = re.sub(r'[［］]', '', safe_title)  # 全角の角かっこを削除
            safe_title = safe_title.strip()

            if len(safe_title) > 100:
                safe_title = safe_title[:100]

            pdf_data.append((full_url, safe_title, date))

    return pdf_data

# PDFリンクを取得
pdf_data = get_pdf_links(BASE_URL)

# PDFが見つかった場合、選択肢を提供
if pdf_data:
    # PDFの選択
    pdf_titles = [pdf[1] for pdf in pdf_data]
    selected_pdfs = st.multiselect("ダウンロードするPDFを選択してください", pdf_titles)

    # 実行ボタン
    if st.button("実行"):
        if selected_pdfs:
            # ZIPファイルを作成
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for pdf_title in selected_pdfs:
                    # 対応するPDFのURLを取得
                    pdf_url = next(pdf[0] for pdf in pdf_data if pdf[1] == pdf_title)
                    pdf_response = requests.get(pdf_url)
                    
                    if pdf_response.status_code == 200:
                        # PDFをZIPファイルに追加
                        file_name = f"{pdf_title}.pdf"
                        zip_file.writestr(file_name, pdf_response.content)
                    else:
                        st.error(f"ダウンロード失敗: {pdf_url}")

                    # サーバー負荷を避けるための1秒スリープ
                    time.sleep(1)

            # ZIPファイルをダウンロードボタンとして表示
            zip_buffer.seek(0)
            st.download_button(
                label="PDFダウンロード",
                data=zip_buffer,
                file_name="pdf_files.zip",
                mime="application/zip"
            )
        else:
            st.warning("PDFを選択してください。")
else:
    st.warning("PDFは見つかりませんでした。")
