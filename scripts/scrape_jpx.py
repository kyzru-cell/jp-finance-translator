"""
scrape_jpx.py
从 JPX 官网爬取用語集，提取术语名称（仅日语，用于对照我们的 glossary）
"""
import subprocess
import re
import time
import json
from pathlib import Path


def curl_get(url: str) -> str:
    result = subprocess.run(
        ["curl", "-s", "--max-time", "20", "--proxy", "", "-L", url,
         "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.stdout


def scrape_section_terms(section: str) -> list[tuple[str, str]]:
    """返回 [(term_id, term_name), ...]"""
    url = f"https://www.jpx.co.jp/glossary/{section}/index.html"
    html = curl_get(url)
    matches = re.findall(
        r'href="/glossary/[^/]+/(\d+)\.html"[^>]*>([^<]+)',
        html
    )
    return [(num, term.strip()) for num, term in matches]


def scrape_term_detail(section: str, term_id: str) -> str:
    """获取术语详情页，提取定义文本"""
    url = f"https://www.jpx.co.jp/glossary/{section}/{term_id}.html"
    html = curl_get(url)
    # 提取正文段落
    # JPX 详情页结构：<div class="...content..."><p>定义</p>
    paras = re.findall(r'<p[^>]*>([^<]{20,})</p>', html)
    # 过滤导航等噪声
    paras = [p.strip() for p in paras if len(p.strip()) > 30 and '©' not in p]
    return ' '.join(paras[:3]) if paras else ''


if __name__ == '__main__':
    sections = ["a", "ka", "sa", "ta", "na", "ha", "ma", "ya", "ra", "wa",
                "a-g", "h-n", "o-u", "v-z", "0-9"]

    all_terms = []
    for section in sections:
        terms = scrape_section_terms(section)
        print(f"  {section}: {len(terms)} terms")
        for tid, tname in terms:
            all_terms.append({
                "section": section,
                "id": tid,
                "ja": tname,
            })
        time.sleep(0.3)

    print(f"\nTotal: {len(all_terms)} terms")

    # 保存术语列表（不获取详情，节省时间）
    out = Path(__file__).parent.parent / "glossary" / "jpx_terms.json"
    out.write_text(json.dumps(all_terms, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved to {out}")

    # 打印前20条
    for t in all_terms[:20]:
        print(f"  {t['ja']}")
