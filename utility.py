import json
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time
import random

def download_file(download_url, feed_pref_id=0, site_name="unknown", directory="gtfs_data"):
    """
    指定されたURLからファイルをダウンロードする共通関数
    
    Args:
        download_url (str): ダウンロードするファイルのURL
        directory (str): 保存先ディレクトリ（デフォルト: "gtfs_data"）
    
    Returns:
        str: 保存されたファイルのパス、失敗時はNone
    """
    try:
        # ファイルをダウンロード
        dl_url = download_url
        file_response = requests.get(dl_url)
        file_response.raise_for_status()

        # ダウンロード先のファイル名を取得して保存
        content_disposition = file_response.headers.get("Content-Disposition")
        if content_disposition:
            filename = content_disposition.split("filename=")[-1].strip('"')
            filename = f'{feed_pref_id:02}_{site_name}_{filename}'
        else:
            parsed_url = urlparse(download_url)
            if parsed_url.path.endswith(".zip"):
                filename = f"{feed_pref_id:02}_{site_name}_{os.path.basename(parsed_url.path)}"
            else:
                filename = f"{feed_pref_id:02}_{site_name}_{os.path.basename(parsed_url.path)}.zip"
        with open(f"{directory}/{filename}", "wb") as file:
            file.write(file_response.content)
        print(f"ファイルを保存しました: {filename}\n")
        with open(f"{directory}/download_log.txt", "a") as log_file:
            log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')},{filename},{download_url}\n")

    except requests.exceptions.RequestException as e:
        print(f"ファイルのダウンロードに失敗しました: {e}\n")
    time.sleep(random.uniform(2, 3))  # APIへの負荷を避けるために少し待機

def one_page_download(href, feed_pref_id, search_class=None, search_prefix=None, search_suffix=None, site_name="unknown"):
    """
    ページからGTFSファイルをダウンロードする
    """
    try:
        print(f"Accessing: {href}")
        # ページのHTMLを取得
        response = requests.get(href)
        response.encoding = response.apparent_encoding
        html = response.text
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, "html.parser")
        # aタグを検索
        download_links = soup.find_all("a", class_=search_class)
        for link in download_links:
            download_url = link.get("href")
            if download_url and (
                (
                    search_prefix and download_url.startswith(search_prefix)
                ) or (
                    search_suffix and download_url.endswith(search_suffix)
                )
            ):
                if download_url.startswith("/"):
                    download_url = urljoin(href, download_url)
                elif not download_url.startswith("http"):
                    download_url = urljoin(href, download_url)
                download_file(download_url, feed_pref_id=feed_pref_id, site_name=site_name)
                break  # 最初のダウンロードリンクだけ処理                   
    except Exception as e:
        print(f"Error processing {href}: {str(e)}")

def two_page_download(href, feed_pref_id, search_class=[None, None], search_prefix=[None, None], search_suffix=[None, None], site_name="unknown"):
    """
    opendata.pref.saitama.lg.jpのページからGTFSファイルをダウンロードする
    """
    try:
        print(f"Accessing: {href}")
        # ページのHTMLを取得
        response = requests.get(href)
        response.encoding = response.apparent_encoding
        html = response.text
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, "html.parser")
        # is-resourceクラスのaタグを検索
        download_links = soup.find_all("a", class_=search_class[0])
        for link in download_links:
            download_url = link.get("href")
            if download_url and (
                (
                    search_prefix and download_url.startswith(search_prefix[0])
                ) or (
                    search_suffix and download_url.endswith(search_suffix[0])
                )
            ):
                if download_url.startswith("/"):
                    download_url = urljoin(href, download_url)
                elif not download_url.startswith("http"):
                    download_url = urljoin(href, download_url)
                one_page_download(download_url, feed_pref_id, search_class=search_class[1], search_prefix=search_prefix[1], search_suffix=search_suffix[1], site_name=site_name)
                break  # 最初の.zipリンクだけ処理                   
    except Exception as e:
        print(f"Error processing {href}: {str(e)}")
