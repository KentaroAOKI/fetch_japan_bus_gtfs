import time
import random
import requests
import json
from utility import download_file

def gtfs_data_jp_download():
    feed_url = "https://api.gtfs-data.jp/v2/feeds"
    download_url = 'https://api.gtfs-data.jp/v2/organizations/{organization_id}/feeds/{feed_id}/files/feed.zip'
    download_dir = "./gtfs_data"

    try:
        # APIからJSONデータを取得
        response = requests.get(feed_url)
        response.raise_for_status()  # ステータスコードが200以外なら例外を発生
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"APIリクエストに失敗しました: {e}")
        return
    except json.JSONDecodeError:
        print("レスポンスをJSONとして解析できませんでした。")
        return

    # 一覧を表示
    feeds = data.get("body", [])
    if not feeds:
        print("データが見つかりませんでした。")
        return

    for i, feed in enumerate(feeds, start=1):
        # 廃止されたフィードはスキップ
        if feed.get("feed_is_discontinued", True):
            print("このフィードは廃止されています。\n")
            continue

        feed_id = feed.get("feed_id")
        organization_id = feed.get("organization_id")
        feed_name = feed.get("feed_name", "不明")
        feed_pref_id = feed.get("feed_pref_id", 0)

        if feed_id == None or organization_id == None:
            print("feed_idまたはorganization_idが不明なため、スキップします。\n")
            continue

        print(f"--- [{i}] ----------------------------------")
        print(f"feed_id        : {feed_id}")
        print(f"organization_id: {organization_id}")
        print(f"フィード名      : {feed_name}")

        try:
            dl_url = download_url.format(feed_id=feed_id, organization_id=organization_id)
            download_file(dl_url, feed_pref_id=feed_pref_id, site_name="gtfs-data", directory=download_dir)
        except requests.exceptions.RequestException as e:
            print(f"ファイルのダウンロードに失敗しました: {e}\n")
        # time.sleep(random.uniform(2, 3))  # APIへの負荷を避けるために少し待機

if __name__ == "__main__":
    gtfs_data_jp_download()
