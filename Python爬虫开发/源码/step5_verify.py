"""
step5_verify.py —— 步骤 3-2：用 pandas 回读 CSV 做结构化校验

CSV 写完不等于写对。这一步不联网，只回读文件，核对四件事：
1. 编码：能否按 utf-8-sig 正常读入（读不进来说明编码写错了）
2. 列名与形状：列是否齐全、行数是否与抓取条数一致
3. 缺失值：哪些字段有空值，空值来自哪里
4. 抽样：前 3 条是否与原网页对得上
"""

import pandas as pd

df = pd.read_csv("result.csv", encoding="utf-8-sig")

print("数据形状 (行, 列):", df.shape)
print("列名:", list(df.columns))
print("\n缺失值统计:")
print(df.isna().sum().to_string())

print("\n作者出现次数 Top5:")
print(df["author"].value_counts().head(5).to_string())

print("\n前 3 条抽样:")
for i, r in df.head(3).fillna("—").iterrows():
    print(f"  {i + 1}. [{r['pub_time']}] {r['title'][:26]}")
    print(f"     作者: {r['author']} | 来源: {r['source']}")

print("\n链接去重:", df["url"].nunique(), "/", len(df), "(无重复即通过)")
