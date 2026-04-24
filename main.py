#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py - 个人本地知识库爬虫 v.5

命令行入口和命令分发中心，负责处理用户输入并调用相应的模块。
"""

import argparse
from utils.crawler import crawl_page, resume_crawl
from utils.fetcher import close_session
from urllib.parse import urlparse

# 命令行规范（个人使用极简）
parser = argparse.ArgumentParser(description="个人本地知识库爬虫 v.5")
parser.add_argument("command", choices=["crawl", "resume"], help="crawl=开始爬取 | resume=续爬")
parser.add_argument("--url", help="目标网站URL（仅crawl需要）")
parser.add_argument("--resume-url", help="指定续爬根URL（可选，覆盖进度文件中的域名）")
parser.add_argument("--depth", type=int, default=3, help="爬取深度，默认3")

def save_failed_urls(url):
    with open("failed_urls.txt", "a", encoding="utf-8") as f:
        f.write(f"{url}\n")

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        if args.command == "crawl":
            if not args.url:
                print("[错误] crawl命令需要--url参数")
                exit(1)
            domain = f"{urlparse(args.url).scheme}://{urlparse(args.url).netloc}"
            print(f"[开始] 爬取域名：{domain}，深度：{args.depth}")
            crawl_page(args.url, domain, args.depth)

        elif args.command == "resume":
            resume_crawl(url=args.resume_url)

        print("[完成] 爬取结束，已自动保存进度+清理临时文件")
        
        # 创建爬虫完成标记文件
        from pathlib import Path
        marker = Path("./output/.crawl_completed")
        marker.touch(exist_ok=True)
        print("✅ 爬虫完成，已生成增量索引标记。")
    
    except Exception as e:
        print(f"[崩溃] 错误：{str(e)}，已保存当前进度")
    finally:
        # ✅ 自动关闭资源，完美退出
        close_session()