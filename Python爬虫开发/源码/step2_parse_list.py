"""
step2_parse_list.py —— 步骤 2-2：HTML 已经拿到了，先只解析列表页

目标：从列表页拿到「标题 / 栏目 / 发布时间 / 链接」四列，并只打印前 3 条。
只打印不存盘，是为了先肉眼确认解析逻辑对不对，再往下做持久化。
"""

from bs4 import BeautifulSoup

from step1_request import fetch, URL
from urllib.parse import urljoin

BASE = "https://www.chinanews.com.cn"


def parse_list(html: str) -> list[dict]:
    """解析滚动新闻列表页，返回条目列表（只含列表页可见的字段）。"""
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for li in soup.select("div.content_list li"):
        a = li.select_one("div.dd_bt > a")      # 标题链接
        if a is None:                            # 广告位 / 空行，直接跳过
            continue

        items.append({
            "category": li.select_one("div.dd_lm").get_text(strip=True),
            "title":    a.get_text(strip=True),
            "pub_time": li.select_one("div.dd_time").get_text(strip=True),
            "url":      urljoin(BASE, a["href"]),   # 相对路径补全为绝对地址
        })

    return items


if __name__ == "__main__":
    rows = parse_list(fetch(URL).text)
    print(f"列表页共解析到 {len(rows)} 条记录，前 3 条：\n")
    for i, r in enumerate(rows[:3], 1):
        print(f"[{i}] 栏目: {r['category']}")
        print(f"    标题: {r['title']}")
        print(f"    时间: {r['pub_time']}")
        print(f"    链接: {r['url']}")
        print("-" * 62)
