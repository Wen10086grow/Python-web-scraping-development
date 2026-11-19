"""
step1_request.py —— 步骤 2-1：只验证「能不能把网页拿下来」

Vibe Coding 第一步不做解析，只做最小化验证：
发一次 GET 请求，确认状态码是 200、确认 HTML 里真的有我们需要的内容。
跑通之后再往下走，避免一上来就写完整脚本、报错时不知道错在哪一层。
"""

import requests

URL = "https://www.chinanews.com.cn/scroll-news/news1.html"

# 带上浏览器 UA：不加 UA 时部分站点会直接返回 403 或空页面
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def fetch(url: str) -> requests.Response:
    """发送 GET 请求并返回响应对象。"""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()                   # 4xx / 5xx 直接抛异常，不把错误页当正文
    resp.encoding = resp.apparent_encoding    # 编码常与响应头不一致，交给 chardet 判断
    return resp


if __name__ == "__main__":
    resp = fetch(URL)
    html = resp.text
    print("状态码:", resp.status_code)
    print("Content-Type:", resp.headers.get("Content-Type"))
    print("HTML 长度:", len(html), "字符")
    print("命中 content_list 容器:", "content_list" in html)
    print("-" * 62)
    # 只打印开头一小段，换行压平，确认拿到的确实是目标页面而不是验证码/错误页
    print("正文开头:", " ".join(html[:160].split()))
