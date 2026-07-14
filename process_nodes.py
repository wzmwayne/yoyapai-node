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


def get_proxy_link(proxy):
    """Generate a unique link for a proxy based on server+port+password/uuid."""
    server = str(proxy.get("server", ""))
    port = str(proxy.get("port", ""))
    password = proxy.get("password", proxy.get("uuid", proxy.get("id", "")))
    return f"{server}:{port}:{password}"


def rename_duplicate_name(name, existing_names):
    """If name already exists, append -1, -2, etc."""
    if name not in existing_names:
        return name
    counter = 1
    while f"{name}-{counter}" in existing_names:
        counter += 1
    return f"{name}-{counter}"


def merge_yamls(yaml_contents):
    """Merge multiple YAML files, deduplicate by link, rename duplicate names."""
    all_proxies = []
    seen_links = set()
    latest_groups = []
    latest_rules = []

    for i, content in enumerate(yaml_contents):
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            continue

        # Collect proxies
        for proxy in data.get("proxies", []):
            if not isinstance(proxy, dict):
                continue
            link = get_proxy_link(proxy)
            if link not in seen_links:
                seen_links.add(link)
                all_proxies.append(proxy)

        # Use latest article's groups and rules
        if i == 0:
            latest_groups = data.get("proxy-groups", [])
            latest_rules = data.get("rules", [])

    # Rename duplicate names
    used_names = set()
    renamed_proxies = []
    for proxy in all_proxies:
        name = proxy.get("name", "unnamed")
        if name in used_names:
            new_name = rename_duplicate_name(name, used_names)
            proxy = dict(proxy)
            proxy["name"] = new_name
            used_names.add(new_name)
        else:
            used_names.add(name)
        renamed_proxies.append(proxy)

    # Build merged data using latest article's groups/rules as base
    merged = {}
    merged["proxies"] = renamed_proxies

    # Build set of valid proxy names after renaming
    valid_names = set(p.get("name", "unnamed") for p in renamed_proxies)
    valid_names.add(FAKE_PROXY_NAME)

    # Special references valid in proxy-groups: built-in keywords + all group names
    special_refs = {"DIRECT", "REJECT"}
    for g in latest_groups:
        if isinstance(g, dict) and "name" in g:
            special_refs.add(g["name"])

    # Rebuild proxy-groups: keep only valid proxy names + special refs
    groups = latest_groups if latest_groups else []
    groups = [g for g in groups if isinstance(g, dict) and g.get("name") != "说明"]

    for g in groups:
        if "proxies" in g and isinstance(g["proxies"], list):
            g["proxies"] = [p for p in g["proxies"]
                            if p in valid_names or p in special_refs]
        if "use" in g and isinstance(g["use"], list):
            g["use"] = [p for p in g["use"] if p in valid_names]

    # Ensure all proxies are referenced in an "all" type group
    has_all_group = any(g.get("type") == "all" for g in groups if isinstance(g, dict))
    if not has_all_group:
        groups.append({
            "name": "所有节点",
            "type": "all",
            "proxies": [p.get("name", "unnamed") for p in renamed_proxies],
        })

    merged["proxy-groups"] = groups
    merged["rules"] = latest_rules

    return merged


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


def process_full():
    """Download all YAML files from all articles, merge, deduplicate, save full.yaml."""
    print("\n" + "=" * 60)
    print("合并去重生成 full.yaml")
    print("=" * 60)

    with open("all_urls.json", "r", encoding="utf-8") as f:
        all_data = json.load(f)

    articles = all_data.get("articles", [])
    yaml_urls = [a["yaml"] for a in articles if a.get("yaml")]

    if not yaml_urls:
        print("  [SKIP] 无 YAML 链接")
        return

    print(f"\n  共 {len(yaml_urls)} 个 YAML 文件待下载\n")

    yaml_contents = []
    for url in yaml_urls:
        try:
            content = download_file(url)
            data = yaml.safe_load(content)
            if isinstance(data, dict) and "proxies" in data:
                count = len(data.get("proxies", []))
                print(f"    -> {count} 个代理")
                yaml_contents.append(content)
            else:
                print(f"    -> [WARN] 无效 YAML，跳过")
        except Exception as e:
            print(f"    -> [ERROR] {e}")

    if not yaml_contents:
        print("  [SKIP] 无有效 YAML 内容")
        return

    # Merge and deduplicate
    print(f"\n  合并 {len(yaml_contents)} 个 YAML 文件...")
    merged = merge_yamls(yaml_contents)

    # Add fake proxy + group
    merged["proxies"].append(FAKE_PROXY)
    if "proxy-groups" not in merged:
        merged["proxy-groups"] = []
    merged["proxy-groups"].append(FAKE_GROUP)

    output = yaml.dump(merged, allow_unicode=True, default_flow_style=False, sort_keys=False)

    with open("full.yaml", "w", encoding="utf-8") as f:
        f.write(output)

    total = len(merged.get("proxies", []))
    print(f"  [OK] full.yaml 已保存（{total} 个代理节点，含说明节点）")


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

    # Step 2: Download & process YAML (newest.yaml)
    if info["yaml"]:
        print("[1/2] 处理 YAML 订阅...")
        yaml_bytes = download_file(info["yaml"])
        modified_yaml = process_yaml(yaml_bytes)
        with open("newest.yaml", "w", encoding="utf-8") as f:
            f.write(modified_yaml)
        print(f"  -> newest.yaml 已保存\n")
    else:
        print("  [SKIP] 无 YAML 链接\n")

    # Step 3: Download & process TXT (newest.txt)
    if info["txt"]:
        print("[2/2] 处理 TXT 订阅...")
        txt_bytes = download_file(info["txt"])
        modified_txt = process_txt(txt_bytes)
        with open("newest.txt", "w", encoding="utf-8") as f:
            f.write(modified_txt)
        print(f"  -> newest.txt 已保存\n")
    else:
        print("  [SKIP] 无 TXT 链接\n")

    # Step 4: Merge all YAMLs into full.yaml
    process_full()

    print("=" * 60)
    print("完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
