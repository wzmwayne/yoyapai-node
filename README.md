# yoyapai-node

免费节点订阅自动抓取 - 每日更新 Clash / V2Ray 节点

## 说明

本仓库通过 GitHub Actions 自动抓取 [yoyapai.com](https://yoyapai.com/category/mianfeijiedian) 的免费节点分享文章，下载最新的 Clash (`.yaml`) 和 V2Ray (`.txt`) 订阅文件，经处理后保存到仓库中。

**更新频率**: 每天北京时间 09:00 自动运行，也可在 Actions 页面手动触发。

## 文件说明

| 文件 | 说明 |
|------|------|
| `newest.yaml` | 最新 Clash (Mihomo) 订阅文件 |
| `newest.txt` | 最新 V2Ray 订阅文件 |
| `full.yaml` | 所有文章合并去重后的完整 Clash 订阅文件 |
| `scraper.py` | 抓取全部文章列表，提取节点订阅链接 |
| `process_nodes.py` | 下载节点文件，添加说明性假节点，保存到仓库 |
| `.github/workflows/scrape.yml` | GitHub Actions 工作流配置 |

## 使用方法

### Clash (Mihomo / Clash Verge Rev / FlClash)

将 `newest.yaml` 的原始链接添加到客户端：

```
https://raw.githubusercontent.com/wzmwayne/yoyapai-node/main/newest.yaml
```

### V2Ray (V2RayN / V2RayNG / Shadowrocket)

将 `newest.txt` 的原始链接添加到客户端：

```
https://raw.githubusercontent.com/wzmwayne/yoyapai-node/main/newest.txt
```

### 完整合并订阅（Clash）

`full.yaml` 汇总了所有历史文章中的节点并自动去重，适合需要更多节点选择的场景：

```
https://raw.githubusercontent.com/wzmwayne/yoyapai-node/main/full.yaml
```

## 节点说明

文件中包含一个名为 `说明` 的代理分组和一个名为 `说明-节点抓取自yoyapai.com免费分享` 的虚拟节点，用于说明节点来源。此节点无法实际使用，如需排除可在客户端中过滤掉名称包含 `说明` 的节点。

## 工作原理

```
GitHub Actions 定时触发 (09:00 CST)
        │
        ▼
  scraper.py
  ┌─────────────────────────────────┐
  │ 1. 请求 yoyapai.com 分类页      │
  │ 2. 解析最新文章链接             │
  │ 3. 访问文章页提取 freenode URL   │
  │ 4. 输出 latest_urls.json        │
  └─────────────────────────────────┘
        │
        ▼
  process_nodes.py
  ┌─────────────────────────────────┐
  │ 1. 下载 .yaml / .txt 文件       │
  │ 2. YAML: 追加假 proxy + group   │
  │ 3. TXT: 追加假 vmess:// 链接    │
  │ 4. 下载全部历史 .yaml 文件      │
  │ 5. 合并去重 → full.yaml         │
  │ 6. 保存 newest.yaml / .txt      │
  └─────────────────────────────────┘
        │
        ▼
  git commit & push
  更新仓库中的订阅文件
```

## 本地运行

```bash
pip install requests beautifulsoup4 pyyaml
python scraper.py
python process_nodes.py
```

运行后会生成 `newest.yaml`、`newest.txt` 和 `full.yaml`。

## License

MIT
