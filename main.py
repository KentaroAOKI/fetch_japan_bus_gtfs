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
    two_page_download,
    wget_download_file
)
from gtfs_data_jp_download import gtfs_data_jp_download
from pref_47_download import ottop_download

def main():
    enable_download = True  # ダウンロードを有効にするかどうか
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
            if enable_download == False:
                continue
            continue
        if href.startswith("https://gtfs-data.jp/search?"):
            if enable_download == False:
                continue
            call_key = "https://gtfs-data.jp/search?"
            if call_key not in call_counter:
                gtfs_data_jp_download()
                call_counter[call_key] = 0
            call_counter[call_key] += 1
            continue
        if href.startswith("https://ckan.hoda.jp/dataset/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class="resource-url-analytics", search_prefix=None, search_suffix=".zip", site_name="hoda")
            continue
        if href.startswith("https://data.bodik.jp/dataset/"):
            if enable_download == False:
                continue
            two_page_download(
                href,
                feed_pref_id=pref_id, 
                search_class=["heading", "resource-url-analytics"],
                search_prefix=["/dataset/", "/dataset/"],
                search_suffix=[None, None],
                site_name="bodik")
            continue
        if href.startswith("https://www.city.iyo.lg.jp/"):
            if enable_download == False:
                continue
            download_file("https://www.city.iyo.lg.jp/keizaikoyou/matidukuri/documents/agency.zip", feed_pref_id=pref_id, site_name="iyo")
            continue
        if href.startswith("https://www.ottop.org/opendata-feed"):
            if enable_download == False:
                continue
            call_key = "https://www.ottop.org/opendata-feed"
            if call_key not in call_counter:
                ottop_download(href, feed_pref_id=pref_id)
                call_counter[call_key] = 0
            continue
        if href.startswith("https://opendata.pref.saitama.lg.jp/datasets/"):
            if enable_download == False:
                continue
            two_page_download(
                href,
                feed_pref_id=pref_id, 
                search_class=["is-resource", "c-btn c-btn-solid c-btn-sm"],
                search_prefix=["https://opendata.pref.saitama.lg.jp/resources/", "https://opendata.pref.saitama.lg.jp/resource_download/"],
                search_suffix=[None, None],
                site_name="saitama")
            continue
        if href.startswith("https://www.akita-bus.or.jp/pages/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="akitabus")
            continue
        if href.startswith("https://ckan.odpt.org/dataset/"):
            if enable_download == False:
                continue
            two_page_download(
                href,
                feed_pref_id=pref_id, 
                search_class=["heading", "resource-url-analytics"],
                search_prefix=["/dataset/", "https://api-public.odpt.org/api/v4/files/odpt/"],
                search_suffix=[None, None],
                site_name=f"odpt_{href.split('/')[-1]}")
            continue
        if href.startswith("https://www.kotoden.co.jp/") or href.startswith("http://www.kotoden.co.jp/"):
            if enable_download == False:
                continue
            call_key = "https://www.kotoden.co.jp/"
            if call_key not in call_counter:
                download_file("https://www.kotoden.co.jp/publichtm/gtfs/gtfsdata/latest/gtfs_kb.zip", feed_pref_id=pref_id, site_name="kotoden_bus")
                call_counter[call_key] = 0
            continue
        if href.startswith("https://www.pref.kochi.lg.jp/opendata/bosai_anzen_machizukuri/"):
            if enable_download == False:
                continue
            # 以下の期間限定ファイル以外はgtfs-data.jpからの取得
            download_file("https://www.pref.kochi.lg.jp/opendata/bosai_anzen_machizukuri/file_contents/GTFS-MonobeDMO_Bus.zip", feed_pref_id=pref_id, site_name="kochi")
            continue
        if href.startswith("https://www.city.mutsu.lg.jp/kurashi/koutsu/businfoformat/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="mutsu")
            continue
        if href.startswith("https://www.city.yatsushiro.lg.jp/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="yatsushiro")
            continue
        if (href.startswith("https://km.bus-vision.jp/")
            or href.startswith("https://mc.bus-vision.jp/")
            or href.startswith("https://loc.bus-vision.jp/")
            or href.startswith("http://bus-vision.jp/")):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix="gtfsFeed", site_name="bus-vision", enable_multiple=True)
            continue
        if href.startswith("https://yamaguchi-opendata.jp/ckan/dataset/352080-gtfsjp"):
            if enable_download == False:
                continue
            wget_download_file("https://yamaguchi-opendata.jp/ckan/dataset/2dbaeb43-5134-4880-90a3-62870504f1d3/resource/0293f992-9abe-42ad-bf88-e5b287280072/download/352080gtfs-jp.zip",
                          feed_pref_id=pref_id, site_name="yamaguchi")
            continue
        if href.startswith("https://yamaguchi-opendata.jp/ckan/dataset/352101_kotsu001"):
            if enable_download == False:
                continue
            wget_download_file("https://yamaguchi-opendata.jp/ckan/dataset/db885818-b1bd-4848-986f-45119e8acb31/resource/c804039c-7d37-4e45-9288-f09fc1bbd249/download/hikari_gtfs_20250401_.zip",
                          feed_pref_id=pref_id, site_name="yamaguchi")
            continue
        if href.startswith("https://www.keneibus.jp/local/OpenData/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class="icon-zip", search_prefix=None, search_suffix=".zip", site_name="keneibus")
            continue
        if href.startswith("https://ckan.open-governmentdata.org/dataset"):
            if enable_download == False:
                continue
            wget_download_file("https://ckan.open-governmentdata.org/dataset/57a14e0e-1778-439b-bd9e-4ad4ca1d8efb/resource/0ab0534b-4cf5-4c94-98b4-b1982275825d/download/403491_fureaibus_gtfs_20250401.zip",
                          feed_pref_id=pref_id, site_name="open-governmentdata")
            continue
        if (href.startswith("https://www.city.komaki.aichi.jp/admin/soshiki/toshiseisakubu/") or
            href.startswith("https://www.city.kiyosu.aichi.jp/kurashi_joho/seikatsu_kankyo/")
        ):
            if enable_download == False:
                continue
            # GTFSデータが見つからない
            continue
        if (href.startswith("https://www.city.obu.aichi.jp/kurashi/sumai/bus/") or
            href.startswith("https://www.city.inuyama.aichi.jp/shisei/toukei/")
        ):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="aichi")
            continue
        if (href.startswith("https://www.city.ichinomiya.aichi.jp/machidukuri/chiikikoutsuu/")):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class="ga-opd", search_prefix=None, search_suffix=".zip", site_name="aichi")
            continue

        if (href.startswith("https://www.town.aichi-togo.lg.jp/soshikikarasagasu/johokohoka/gyomuannai/")):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class="icon2", search_prefix=None, search_suffix=".zip", site_name="aichi")
            continue
        if href.startswith("https://www.city.inazawa.aichi.jp/"):
            if enable_download == False:
                continue
            one_page_download("https://www.city.inazawa.aichi.jp/0000004849.html", feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="aichi")
            continue
        if href.startswith("http://opendata.sagabus.info/"):
            if enable_download == False:
                continue
            download_file("http://opendata.sagabus.info/saga-current.zip", feed_pref_id=pref_id, site_name="sagabus")
            continue
        if href.startswith("https://www.km-bus.tokyo/route/odaiba/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="km-bus")
            continue
        if href.startswith("https://bus.fujikyu.co.jp/rosen/gtfs"):
            if enable_download == False:
                continue
            wget_download_file("https://gtfs-jp.buskita.com/fxc/gtfs.zip", feed_pref_id=pref_id, site_name="fujikyu_fxc")
            wget_download_file("https://gtfs-jp.buskita.com/fmo_shonan/gtfs.zip", feed_pref_id=pref_id, site_name="fujikyu_fmo_shonan")
            wget_download_file("https://gtfs-jp.buskita.com/fmo/gtfs.zip", feed_pref_id=pref_id, site_name="fujikyu_fmo")
            wget_download_file("https://gtfs-jp.buskita.com/fjb/gtfs.zip", feed_pref_id=pref_id, site_name="fujikyu_fjb")
            continue
        if href.startswith("https://www.city.ozu.ehime.jp/site/opendata/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class=None, search_prefix=None, search_suffix=".zip", site_name="ozu")
            continue
        if href.startswith("https://www.town.shodoshima.lg.jp/gyousei/choseijoho/opendeta/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class="icon2", search_prefix=None, search_suffix=".zip", site_name="shodoshima")
            continue
        if href.startswith("https://opendata.pref.kagawa.lg.jp/dataset/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class="download", search_prefix=None, search_suffix=".zip", site_name="kagawa")
            continue
        if href.startswith("https://opendata.pref.tokushima.lg.jp/dataset/"):
            if enable_download == False:
                continue
            one_page_download(href, feed_pref_id=pref_id, search_class="download", search_prefix=None, search_suffix="source-url", site_name="tokushima")
            continue
        if href.startswith("https://yonkoh.co.jp/archives/info-cat/gtfsjp"):
            if enable_download == False:
                continue
            two_page_download(
                href,
                feed_pref_id=pref_id, 
                search_class=[None, None],
                search_prefix=["https://yonkoh.co.jp/archives/info/gtfs", None],
                search_suffix=[None, ".zip"],
                site_name=f"yonkoh_{href.split('/')[-1]}",
                search_contents=[["この記事を読む"], None],
                href_suffix=["/", ""])
            continue
        print(f"href: {href}, pref_id: {pref_id}")

if __name__ == "__main__":
    main()