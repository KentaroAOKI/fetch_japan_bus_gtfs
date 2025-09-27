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
    except requests.exceptions.RequestException as e:
        print(f"ファイルのダウンロードに失敗しました: {e}\n")
    time.sleep(random.uniform(2, 3))  # APIへの負荷を避けるために少し待機

def ckan_hoda_download(href, feed_pref_id):
    """
    ckan.hoda.jpのページからGTFSファイルをダウンロードする
    """
    try:
        print(f"Accessing: {href}")
        # ページのHTMLを取得
        response = requests.get(href)
        response.encoding = response.apparent_encoding
        html = response.text
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, "html.parser")
        # resource-url-analyticsクラスのaタグを検索
        download_links = soup.find_all("a", class_="resource-url-analytics")        
        for link in download_links:
            download_url = link.get("href")
            if download_url and download_url.endswith(".zip"):
                print(f"Found download link: {download_url}")
                download_file(download_url, feed_pref_id=feed_pref_id, site_name="hoda")
                break  # 最初の.zipリンクだけ処理                   
    except Exception as e:
        print(f"Error processing {href}: {str(e)}")

def data_bodik_download(href, feed_pref_id):
    """
    data.bodik.jpのページからGTFSファイルをダウンロードする
    """
    try:
        print(f"Accessing: {href}")
        # ページのHTMLを取得
        response = requests.get(href)
        response.encoding = response.apparent_encoding
        html = response.text
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, "html.parser")
        # resource-url-analyticsクラスのaタグを検索
        download_links = soup.find_all("a", class_="heading")        
        for link in download_links:
            download_url = link.get("href")
            if download_url and download_url.startswith("/dataset/"):
                download_url = urljoin(href, download_url)
                data_bodik_dataset_download(download_url, feed_pref_id)
                break  # 最初の.zipリンクだけ処理                   
    except Exception as e:
        print(f"Error processing {href}: {str(e)}")

def data_bodik_dataset_download(href, feed_pref_id):
    """
    data.bodik.jpのページからGTFSファイルをダウンロードする
    """
    try:
        print(f"Accessing: {href}")
        # ページのHTMLを取得
        response = requests.get(href)
        response.encoding = response.apparent_encoding
        html = response.text
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, "html.parser")
        # resource-url-analyticsクラスのaタグを検索
        download_links = soup.find_all("a", class_="resource-url-analytics")        
        for link in download_links:
            download_url = link.get("href")
            if download_url and download_url.startswith("/dataset/"):
                download_url = urljoin(href, download_url)
                download_file(download_url, feed_pref_id=feed_pref_id, site_name="bodik")
                break  # 最初の.zipリンクだけ処理                   
    except Exception as e:
        print(f"Error processing {href}: {str(e)}")

def ottop_download(href, feed_pref_id):
    """
    ottopのページからGTFSファイルをダウンロードする
    """
    try:
        print(f"Accessing: {href}")
        # ページのHTMLを取得
        response = requests.get(href)
        response.encoding = response.apparent_encoding
        html = response.text
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, "html.parser")
        urls = []
        for script in soup.find_all("script", type="application/ld+json"):
            data = json.loads(script.string)
            # JSON-LDは配列/単体/入れ子いずれもあり得るので正規化
            candidates = data if isinstance(data, list) else [data]
            for obj in candidates:
                if obj.get("@type") == "ItemList" and "itemListElement" in obj:
                    for item in obj["itemListElement"]:
                        # ListItemのurlを回収
                        u = item.get("url")
                        if u:
                            urls.append(u)
            # 結果表示
            for download_url in urls:
                print(f"Found download link: {download_url}")
                download_file(download_url, feed_pref_id=feed_pref_id, site_name="ottop")
    except Exception as e:
        print(f"Error processing {href}: {str(e)}")

def main():
    # 保存先ディレクトリを作成
    download_dir = "gtfs_data"
    os.makedirs(download_dir, exist_ok=True)

    # 対象URL
    url = "https://bus-routes.net/gtfs_list.php/"

    # HTML取得
    response = requests.get(url)
    response.encoding = response.apparent_encoding  # 文字化け防止
    html = response.text

    # BeautifulSoupでパース
    soup = BeautifulSoup(html, "html.parser")

    # 目的のaタグを検索
    # <tr class='gtfs'>の要素を探し、その中のgdとvl（県情報）を取得
    links = []
    for gtfs_tr in soup.find_all("tr", class_="gtfs"):
        # gd（GTFSデータのリンク）を取得
        gd_td = gtfs_tr.find("td", class_="gd")
        if gd_td:
            a_tag = gd_td.find("a", href=True)
            if a_tag:
                href = a_tag["href"]
                
                # vl（県情報）を取得 - 最初のvlタグ（県の情報）を取得
                kid_value = None
                kn_td = gtfs_tr.find("td", class_="kn")  # 県情報が含まれるtd
                if kn_td:
                    vl_tag = kn_td.find("a", class_="vl")
                    if vl_tag and vl_tag.get("href"):
                        # /gtfs_list.php?kid=6 から kid=6 を抽出
                        href_vl = vl_tag["href"]
                        if "kid=" in href_vl:
                            kid_value = href_vl.split("kid=")[1].split("&")[0]
                
                links.append({"href": href, "kid": kid_value})

    # 結果出力（hrefがユニークなものだけ処理）
    seen = set()
    unique_links = []
    for link in links:
        href = link["href"]
        pref_id = link["kid"]
        if href in seen:
            continue
        seen.add(href)
        unique_links.append({"href": href, "kid": pref_id})

    for link in unique_links:
        href = link["href"]
        pref_id = link["kid"]
        if href.startswith("./gtfs_list.php"):
            continue
        if href.startswith("https://gtfs-data.jp/search?"):
            continue
        if href.startswith("https://ckan.hoda.jp/dataset/"):
            # ckan_hoda_download(href, feed_pref_id=pref_id)
            continue
        if href.startswith("https://data.bodik.jp/dataset/"):
            # data_bodik_download(href, feed_pref_id=pref_id)
            continue
        if href.startswith("https://www.city.iyo.lg.jp/"):
            # download_file("https://www.city.iyo.lg.jp/keizaikoyou/matidukuri/documents/agency.zip", feed_pref_id=pref_id, site_name="iyo")
            continue
        if href.startswith("https://www.ottop.org/opendata-feed"):
            # ottop_download(href, feed_pref_id=pref_id)
            continue
        print(f"href: {href}, pref_id: {pref_id}")

if __name__ == "__main__":
    main()