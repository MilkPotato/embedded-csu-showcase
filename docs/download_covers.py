"""
B站封面图自动下载脚本
用法：python download_covers.py
功能：读取 data.js 中所有 B站链接，下载封面图到 assets/covers/ 目录
"""

import re
import os
import json
import time
import urllib.request
import urllib.error

# ==================== 配置 ====================
DATA_JS_PATH = 'js/data.js'
COVERS_DIR = 'assets/covers'
API_BASE = 'https://api.bilibili.com/x/web-interface/view?bvid='
REQUEST_DELAY = 0.5  # 每次请求间隔（秒），避免被B站限流

# ==================== 读取 BV 号 ====================
def extract_bvid_from_js(filepath):
    """从 data.js 中提取所有 BV 号"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 从 videoUrl 字段中提取 BV 号
    pattern = r"videoUrl:\s*'[^']*(BV1[A-Za-z0-9]{9,10})[^']*'"
    matches = re.findall(pattern, content)
    # 去重并保持顺序
    seen = set()
    bvids = []
    for bvid in matches:
        if bvid not in seen:
            seen.add(bvid)
            bvids.append(bvid)
    return bvids


def get_cover_url(bvid):
    """通过 B站 API 获取封面图 URL"""
    url = API_BASE + bvid
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('code') == 0 and data.get('data', {}).get('pic'):
                return data['data']['pic']
            else:
                print(f'  API 返回异常: {data.get("code")} - {data.get("message", "")}')
                return None
    except urllib.error.HTTPError as e:
        print(f'  HTTP 错误: {e.code}')
        return None
    except Exception as e:
        print(f'  请求失败: {e}')
        return None


def download_image(url, save_path):
    """下载图片"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.bilibili.com/',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            with open(save_path, 'wb') as f:
                f.write(data)
        return True
    except Exception as e:
        print(f'  下载失败: {e}')
        return False


def main():
    # 切换到脚本所在目录（docs/）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # 确保封面目录存在
    os.makedirs(COVERS_DIR, exist_ok=True)

    # 提取 BV 号
    print('正在读取 data.js 中的 B站链接...')
    bvids = extract_bvid_from_js(DATA_JS_PATH)
    print(f'共找到 {len(bvids)} 个 BV 号')

    # 统计
    success = 0
    skipped = 0
    failed = 0

    for i, bvid in enumerate(bvids, 1):
        save_path = os.path.join(COVERS_DIR, f'{bvid}.jpg')

        # 如果文件已存在且大于 1KB，跳过
        if os.path.exists(save_path) and os.path.getsize(save_path) > 1024:
            print(f'[{i}/{len(bvids)}] {bvid} → 已存在，跳过')
            skipped += 1
            continue

        print(f'[{i}/{len(bvids)}] {bvid} → 查询中...', end=' ')

        # 获取封面图 URL
        cover_url = get_cover_url(bvid)
        if not cover_url:
            print('[FAIL] 获取封面URL失败')
            failed += 1
            continue

        print(f'下载中...', end=' ')

        # 下载图片
        if download_image(cover_url, save_path):
            file_size = os.path.getsize(save_path) / 1024
            print(f'[OK] ({file_size:.0f} KB)')
            success += 1
        else:
            print('[FAIL] 下载失败')
            failed += 1

        # 请求间隔，避免限流
        if i < len(bvids):
            time.sleep(REQUEST_DELAY)

    # 汇总
    print('\n' + '=' * 40)
    print(f'总计: {len(bvids)} 个视频')
    print(f'[OK] 新增下载: {success}')
    print(f'[SKIP] 已跳过: {skipped}')
    print(f'[FAIL] 失败: {failed}')
    print(f'[DIR] 封面目录: {os.path.abspath(COVERS_DIR)}')
    print('=' * 40)


if __name__ == '__main__':
    main()
