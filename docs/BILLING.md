# dev-artifacts 收款与门控（爱发电 afdian）

## 定位
多子项目聚合仓，各子项目独立定价与门控，顶层 billing.py 提供统一网关。

## 定价档位（顶层，与 billing.py 对齐）
| 档位 | 价格 | 限制 |
|---|---|---|
| Free | ¥0 | 3 次/天 |
| Pro | ¥99/月 | 不限次 |
| 企业 | ¥999/月 | 定制+API |

## 收款流程（先体验后付费）
1. 免费 3 次/天，超限 402 + 升级链接（爱发电 https://afdian.com/@Zeon7744）
2. 付款 → `billing.AfdianGateway.query_callback` 核验 → 本地提权
3. 无 key 走 `noop` 安全降级

## 环境变量
`JZ_AFDIAN_USER` / `JZ_AFDIAN_TOKEN` / `BILLING_GATEWAY`（noop|afdian）
