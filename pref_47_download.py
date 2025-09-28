import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .utility import download_file

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
