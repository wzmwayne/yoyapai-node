import re
import json
import base64
import requests
import yaml


FAKE_PROXY_NAME = "说明-节点抓取自yoyapai.com免费分享"

FAKE_PROXY = {
    "name": FAKE_PROXY_NAME,
    "type": "trojan",
    "server": "127.0.0.1",
    "port": 443,
    "password": "dummy",
    "udp": True,
    "skip-cert-verify": True,
}

FAKE_GROUP = {
    "name": "说明",
    "type": "select",
    "proxies": [FAKE_PROXY_NAME],
}

FAKE_VMESS_PAYLOAD = {
    "v": "2",
    "ps": FAKE_PROXY_NAME,
    "add": "127.0.0.1",
    "port": "443",
    "id": "00000000-0000-0000-0000-000000000000",
    "aid": "0",
    "net": "tcp",
    "type": "none",
    "host": "",
    "path": "",
    "tls": "",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
}


def download_file(url):
    print(f"  [GET] {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.content


def process_yaml(content):
    """Download YAML, add fake proxy + proxy-group, return modified YAML string."""
    data = yaml.safe_load(content)

    if not isinstance(data, dict):
        print("  [WARN] YAML 解析结果不是字典，跳过修改")
        return content.decode("utf-8")

    # Add fake proxy to proxies list
    if "proxies" in data and isinstance(data["proxies"], list):
        # Remove existing fake proxy if present (re-run safety)
        data["proxies"] = [p for p in data["proxies"] if isinstance(p, dict) and p.get("name") != FAKE_PROXY_NAME]
        data["proxies"].append(FAKE_PROXY)
    else:
        data["proxies"] = [FAKE_PROXY]

    # Add fake group to proxy-groups list
    if "proxy-groups" in data and isinstance(data["proxy-groups"], list):
        data["proxy-groups"] = [g for g in data["proxy-groups"] if isinstance(g, dict) and g.get("name") != "说明"]
        data["proxy-groups"].append(FAKE_GROUP)
    else:
        data["proxy-groups"] = [FAKE_GROUP]

    output = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"  [OK] YAML 已添加假 proxy + proxy-group")
    return output


def process_txt(content):
    """Decode base64 V2Ray subscription, append fake VMess link, re-encode."""
    try:
        decoded = base64.b64decode(content).decode("utf-8")
    except Exception:
        # Maybe it's plain text, try utf-8 directly
        decoded = content.decode("utf-8")

    fake_vmess = "vmess://" + base64.b64encode(
        json.dumps(FAKE_VMESS_PAYLOAD, ensure_ascii=False).encode()
    ).decode()

    # Append the fake link as a new line
    decoded = decoded.rstrip("\n") + "\n" + fake_vmess + "\n"

    encoded = base64.b64encode(decoded.encode()).decode()
    print(f"  [OK] TXT 已追加假 vmess:// 链接")
    return encoded


def main():
    print("=" * 60)
    print("下载并处理节点文件")
    print("=" * 60)

    # Step 1: Read JSON
    with open("latest_urls.json", "r", encoding="utf-8") as f:
        info = json.load(f)

    print(f"\n  标题: {info['title']}")
    print(f"  日期: {info['date']}")
    print(f"  YAML: {info['yaml']}")
    print(f"  TXT:  {info['txt']}\n")

    # Step 2: Download & process YAML
    if info["yaml"]:
        print("[1/2] 处理 YAML 订阅...")
        yaml_bytes = download_file(info["yaml"])
        modified_yaml = process_yaml(yaml_bytes)
        with open("newest.yaml", "w", encoding="utf-8") as f:
            f.write(modified_yaml)
        print(f"  -> newest.yaml 已保存\n")
    else:
        print("  [SKIP] 无 YAML 链接\n")

    # Step 3: Download & process TXT
    if info["txt"]:
        print("[2/2] 处理 TXT 订阅...")
        txt_bytes = download_file(info["txt"])
        modified_txt = process_txt(txt_bytes)
        with open("newest.txt", "w", encoding="utf-8") as f:
            f.write(modified_txt)
        print(f"  -> newest.txt 已保存\n")
    else:
        print("  [SKIP] 无 TXT 链接\n")

    print("=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
