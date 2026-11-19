"""
step3_crawl_csv.py —— 步骤 3：数据持久化 + 异常处理

在 step2 的基础上补两件事：
1. 作者字段列表页没有，需要二次请求详情页，从 #author_baidu 取「作者」
2. 把结果写进 result.csv（utf-8-sig，Excel 直接双击不乱码），
   并保证任何一条详情页失败都不会让整个程序崩掉。
"""

import csv
import time
import random
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.chinanews.com.cn"
LIST_URL = "https://www.chinanews.com.cn/scroll-news/news1.html"
OUT_FILE = "result.csv"

ITEM_LIMIT = 30        # 只取前 30 条，控制请求量
DELAY = 0.3            # 每条间隔 0.3 秒，礼貌爬取，不对站点造成压力

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def decode(resp: requests.Response) -> str:
    """确定性地解码正文：先按 UTF-8，失败再按 GB18030（兼容 GB2312/GBK）。

    站点部分页面不带 charset 声明，chardet 会把 UTF-8 字节误判成 GB2312，
    导致「作者：张三」变成「дҪңиҖ…пјҡеј дёү」这样的乱码，
    所以这里不再依赖 apparent_encoding，改为按顺序试探。
    """
    for enc in ("utf-8", "gb18030"):
        try:
            return resp.content.decode(enc)
        except UnicodeDecodeError:
            continue
    return resp.content.decode("utf-8", errors="replace")


def get_html(url: str, retry: int = 2) -> str:
    """带重试的 GET：超时或 5xx 时退避重试，最终失败则抛出异常由调用方兜底。"""
    for i in range(retry + 1):
        try:
            resp = SESSION.get(url, timeout=10)
            resp.raise_for_status()
            return decode(resp)
        except requests.RequestException:
            if i == retry:
                raise
            time.sleep(1 + i)


def text_of(node, default: str = "") -> str:
    """安全取文本：节点不存在时返回空字符串，而不是抛 AttributeError。"""
    return node.get_text(strip=True) if node else default


def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for li in soup.select("div.content_list li")[:ITEM_LIMIT]:
        a = li.select_one("div.dd_bt > a")
        if a is None:
            continue
        items.append({
            "title":    a.get_text(strip=True),
            "pub_time": text_of(li.select_one("div.dd_time")),
            "url":      urljoin(BASE, a["href"]),
        })
    return items


def fill_detail(item: dict) -> dict:
    """请求详情页，补齐「作者」「来源」「精确发布时间」。任何异常都降级为空串。"""
    try:
        soup = BeautifulSoup(get_html(item["url"]), "html.parser")

        author = text_of(soup.select_one("#author_baidu"))
        item["author"] = author.split("：", 1)[-1].strip() if author else ""

        source = text_of(soup.select_one("#source_baidu"))
        item["source"] = source.split("：", 1)[-1].strip() if source else ""

        pub = text_of(soup.select_one("#pubtime_baidu"))
        if pub:                                  # 详情页时间精确到秒，优先使用
            item["pub_time"] = pub
    except Exception as e:                       # 单条失败不影响整体
        item["author"] = item.get("author", "")
        item["source"] = item.get("source", "")
        item["error"] = type(e).__name__
    return item


def main() -> None:
    rows = parse_list(get_html(LIST_URL))
    print(f"列表页解析完成，共 {len(rows)} 条，开始补全详情页字段……")

    ok = fail = 0
    for i, item in enumerate(rows, 1):
        fill_detail(item)
        if item.get("error"):
            fail += 1
        else:
            ok += 1
        print(f"  [{i:>2}/{len(rows)}] {item['pub_time']:<20} "
              f"{item['author'] or '—':<8} {item['title'][:24]}")
        time.sleep(DELAY + random.uniform(0, 0.2))   # 加抖动，降低被识别为爬虫的概率

    fields = ["title", "pub_time", "author", "source", "url"]
    with open(OUT_FILE, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print("-" * 62)
    print(f"成功 {ok} 条，失败 {fail} 条")
    print(f"已写入 {OUT_FILE}（编码 utf-8-sig，共 {len(rows)} 行数据）")


if __name__ == "__main__":
    main()
