import json
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import time
import random
from utility import (
    download_file,
    one_page_download,
    two_page_download
)
from gtfs_data_jp_download import gtfs_data_jp_download
from pref_47_download import ottop_download

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

    call_counter = {}
    for link in unique_links:
        href = link["href"]
        pref_id = link["kid"]
        if href.startswith("./gtfs_list.php"):
            continue
        if href.startswith("https://gtfs-data.jp/search?"):
            call_key = "https://gtfs-data.jp/search?"
            if call_key not in call_counter:
                gtfs_data_jp_download()
                call_counter[call_key] = 0
            call_counter[call_key] += 1
            continue
        if href.startswith("https://ckan.hoda.jp/dataset/"):
            one_page_download(href, feed_pref_id=pref_id, search_class="resource-url-analytics", search_prefix=None, search_suffix=".zip", site_name="hoda")
            continue
        if href.startswith("https://data.bodik.jp/dataset/"):
            two_page_download(
                href,
                feed_pref_id=pref_id, 
                search_class=["heading", "resource-url-analytics"],
                search_prefix=["/dataset/", "/dataset/"],
                search_suffix=[None, None],
                site_name="bodik")
            continue
        if href.startswith("https://www.city.iyo.lg.jp/"):
            download_file("https://www.city.iyo.lg.jp/keizaikoyou/matidukuri/documents/agency.zip", feed_pref_id=pref_id, site_name="iyo")
            continue
        if href.startswith("https://www.ottop.org/opendata-feed"):
            call_key = "https://www.ottop.org/opendata-feed"
            if call_key not in call_counter:
                ottop_download(href, feed_pref_id=pref_id)
                call_counter[call_key] = 0
            continue
        if href.startswith("https://opendata.pref.saitama.lg.jp/datasets/"):
            two_page_download(
                href,
                feed_pref_id=pref_id, 
                search_class=["is-resource", "c-btn c-btn-solid c-btn-sm"],
                search_prefix=["https://opendata.pref.saitama.lg.jp/resources/", "https://opendata.pref.saitama.lg.jp/resource_download/"],
                search_suffix=[None, None],
                site_name="saitama")
            continue
        if href.startswith("https://www.akita-bus.or.jp/pages/"):
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="akitabus")
            continue
        if href.startswith("https://ckan.odpt.org/dataset/"):
            two_page_download(
                href,
                feed_pref_id=pref_id, 
                search_class=["heading", "resource-url-analytics"],
                search_prefix=["/dataset/", "https://api-public.odpt.org/api/v4/files/odpt/"],
                search_suffix=[None, None],
                site_name=f"odpt_{href.split('/')[-1]}")
            continue
        if href.startswith("https://www.kotoden.co.jp/") or href.startswith("http://www.kotoden.co.jp/"):
            call_key = "https://www.kotoden.co.jp/"
            if call_key not in call_counter:
                download_file("https://www.kotoden.co.jp/publichtm/gtfs/gtfsdata/latest/gtfs_kb.zip", feed_pref_id=pref_id, site_name="kotoden_bus")
                call_counter[call_key] = 0
            continue
        if href.startswith("https://www.pref.kochi.lg.jp/opendata/bosai_anzen_machizukuri/"):
            # 以下の期間限定ファイル以外はgtfs-data.jpからの取得
            download_file("https://www.pref.kochi.lg.jp/opendata/bosai_anzen_machizukuri/file_contents/GTFS-MonobeDMO_Bus.zip", feed_pref_id=pref_id, site_name="kochi")
            continue

        print(f"href: {href}, pref_id: {pref_id}")

if __name__ == "__main__":
    main()