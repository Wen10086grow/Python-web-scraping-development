Python 爬虫开发实验 —— 源码与运行结果
=====================================
运行环境：Windows 11，Python 3.13
依赖：requests、beautifulsoup4、pandas
目标站点：中国新闻网滚动新闻列表页（公开页面）

文件说明
--------
step1_request.py      仅验证请求是否成功（状态码、HTML 长度、容器是否命中）
step2_parse_list.py   仅解析列表页，打印前 3 条，核对条目数与链接
step3_crawl_csv.py    完整抓取：列表页 + 二级请求详情页补作者/来源，写入 result.csv
step4_news_crawler.py 审查后重构版：CrawlerConfig + NewsCrawler 类，写入 result_oop.csv
step5_verify.py       用 pandas 回读 result.csv 做数据校验（形状、缺失值、重复、时间分布）

result.csv            步骤3 的输出（utf-8-sig 编码，Excel 可直接打开）
result_oop.csv        步骤4 重构版的输出，内容与 result.csv 一致

运行截图/
  shot1_request.png   图1  step1 运行输出
  shot2_parse.png     图2  step2 运行输出
  shot3_csv.png       图3  step3 完整抓取并落盘 CSV
  shot4_oop.png       图4  step4 重构版运行日志
  shot5_excel.png     图5  result.csv 在 Excel 中的显示效果
  shot6_verify.png    图6  step5 pandas 校验结果

运行顺序
--------
    python step1_request.py
    python step2_parse_list.py
    python step3_crawl_csv.py
    python step4_news_crawler.py
    python step5_verify.py

说明
----
数据抓取时间为 2026-11-18 下午，标题为当日实时新闻。若晚些重跑，
CSV 与截图中的新闻标题会随站点更新而变化，这是正常现象。
