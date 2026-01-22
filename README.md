# codex-test

面向华律网律师端的即时咨询库筛选小程序示例。

## 功能
- 从咨询导出的 CSV 中筛选更有价值的客户提问。
- 可配置评分规则（预算、紧急程度、重点领域、关键词等）。
- 输出包含评分和理由的结果，便于快速跟进。

## 使用方式
1. 准备 CSV 文件（字段名大小写不敏感，建议包含：`id`、`title`、`content`、`category`、`budget`、`urgency`、`location`、`created_at`）。
2. 调整 `config.json` 里的评分权重。
3. 运行脚本：

```bash
python app.py --input sample_data.csv --output selected.csv --min-score 60
```

输出 `selected.csv` 会包含评分与筛选理由。

## 评分逻辑说明
- **描述越详细**：分数越高。
- **预算高/紧急程度高**：加分。
- **重点领域**：按配置加权。
- **关键事实词**：出现则加分。

## 注意事项
- 该示例仅做离线筛选，不涉及自动抓取或绕过平台限制。
- 建议在合规前提下使用平台提供的导出或开放接口。
