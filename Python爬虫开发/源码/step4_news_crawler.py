"""
step4_news_crawler.py —— 步骤 4：审查后重构为面向对象结构

重构解决 step3 的三个问题：
1. 全局常量与 SESSION 散落，换站点要改多处 —— 抽成 CrawlerConfig
2. 抓取、解析、存储混在 main() 里，无法单测、无法复用
   —— 拆成 fetch / parse_list / parse_detail / save
3. 只打印不记录，出问题无法回溯 —— 加 logging，把失败条目单独落 failed.log
"""

import csv
import logging
import random
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("crawler")


@dataclass
class CrawlerConfig:
    """站点相关的全部可变项集中在这里，换站点只改这个类。"""
    base_url: str = "https://www.chinanews.com.cn"
    list_path: str = "/scroll-news/news1.html"
    item_limit: int = 30
    delay: float = 0.3
    retry: int = 2
    out_file: str = "result_oop.csv"

    # CSS 选择器：站点改版时只需改这里
    sel_list_item: str = "div.content_list li"
    sel_title: str = "div.dd_bt > a"
    sel_time: str = "div.dd_time"
    sel_author: str = "#author_baidu"
    sel_source: str = "#source_baidu"
    sel_pubtime: str = "#pubtime_baidu"

    fields: tuple = ("title", "pub_time", "author", "source", "url")


class NewsCrawler:
    """面向对象的爬虫：一个实例绑定一个站点的一份配置。"""

    def __init__(self, config: CrawlerConfig | None = None):
        self.cfg = config or CrawlerConfig()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
        })
        self.failed: list[tuple[str, str]] = []      # (url, 原因)

    # ---------- 网络层 ----------
    @staticmethod
    def _decode(resp: requests.Response) -> str:
        """先按 UTF-8 解码，失败再按 GB18030；不依赖 chardet 的猜测。"""
        for enc in ("utf-8", "gb18030"):
            try:
                return resp.content.decode(enc)
            except UnicodeDecodeError:
                continue
        return resp.content.decode("utf-8", errors="replace")

    def fetch(self, url: str) -> str:
        for attempt in range(self.cfg.retry + 1):
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                return self._decode(resp)
            except requests.RequestException as e:
                if attempt == self.cfg.retry:
                    raise
                log.warning("请求失败(%s)，%d 秒后重试：%s",
                            type(e).__name__, attempt + 1, url)
                time.sleep(1 + attempt)
        return ""

    # ---------- 解析层 ----------
    @staticmethod
    def _text(node) -> str:
        return node.get_text(strip=True) if node else ""

    @staticmethod
    def _after_colon(s: str) -> str:
        """'作者：张三' -> '张三'；没有冒号则原样返回。"""
        return s.split("：", 1)[-1].strip() if s else ""

    def parse_list(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        rows = []
        for li in soup.select(self.cfg.sel_list_item)[: self.cfg.item_limit]:
            a = li.select_one(self.cfg.sel_title)
            if not a or not a.get("href"):
                continue
            rows.append({
                "title": self._text(a),
                "pub_time": self._text(li.select_one(self.cfg.sel_time)),
                "author": "",
                "source": "",
                "url": urljoin(self.cfg.base_url, a["href"]),
            })
        return rows

    def parse_detail(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        return {
            "author": self._after_colon(
                self._text(soup.select_one(self.cfg.sel_author))),
            "source": self._after_colon(
                self._text(soup.select_one(self.cfg.sel_source))),
            "pub_time": self._text(soup.select_one(self.cfg.sel_pubtime)),
        }

    # ---------- 业务流程 ----------
    def run(self) -> list[dict]:
        list_url = urljoin(self.cfg.base_url, self.cfg.list_path)
        log.info("抓取列表页：%s", list_url)
        rows = self.parse_list(self.fetch(list_url))
        log.info("列表页解析到 %d 条，开始补全详情页", len(rows))

        for i, row in enumerate(rows, 1):
            try:
                detail = self.parse_detail(self.fetch(row["url"]))
                row["author"] = detail["author"] or row["author"]
                row["source"] = detail["source"] or row["source"]
                row["pub_time"] = detail["pub_time"] or row["pub_time"]
            except Exception as e:
                self.failed.append((row["url"], type(e).__name__))
                log.error("[%d/%d] 详情页失败：%s (%s)",
                          i, len(rows), row["url"], type(e).__name__)

            log.info("[%2d/%d] %s | %s | %s",
                     i, len(rows), row["pub_time"],
                     row["author"] or "—", row["title"][:22])
            time.sleep(self.cfg.delay + random.uniform(0, 0.2))
        return rows

    def save(self, rows: list[dict]) -> None:
        with open(self.cfg.out_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.cfg.fields,
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        log.info("已保存 %d 条记录到 %s", len(rows), self.cfg.out_file)

        if self.failed:                     # 失败条目单独留痕，便于重跑
            with open("failed.log", "w", encoding="utf-8") as f:
                f.writelines(f"{u}\t{r}\n" for u, r in self.failed)
            log.warning("失败 %d 条，明细见 failed.log", len(self.failed))

    def summary(self, rows: list[dict]) -> None:
        authors = [r["author"] for r in rows if r["author"]]
        print("-" * 62)
        ok = len(rows) - len(self.failed)
        print(f"总计 {len(rows)} 条 | 成功 {ok} 条 | 失败 {len(self.failed)} 条")
        print(f"作者字段覆盖率: {len(authors)}/{len(rows)} "
              f"= {len(authors) / len(rows):.1%}")
        print(f"去重后作者数: {len(set(authors))}")


if __name__ == "__main__":
    crawler = NewsCrawler()
    data = crawler.run()
    crawler.save(data)
    crawler.summary(data)
