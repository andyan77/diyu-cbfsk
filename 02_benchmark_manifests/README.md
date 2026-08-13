# 02_benchmark_manifests/

本目录是**公开**评测清单目录，目录名由 S5／D-27 裁决固定，不得改名（旧名 `02_benchmarks_hidden/` 已废止）。

## 只允许存放

`benchmark_schema`、`frozen_manifest`、`content_hashes`、`runner_interface`、`result_summary`、非秘密元数据。

## 一律禁止存放

隐藏题正文、参考答案、评分细则的保密部分、隐藏品牌完整事实包、生成参数、隐藏运行原始输出。

原因是 Git 克隆提供完整对象历史，**目录命名不构成读取权限隔离**。隐藏内容必须物理隔离于主仓，存放位置由 Founder 裁决为 STORE-A（独立私有仓库，受限访问），M2 前落地（`COND-011`）。完整边界见 [`governance/storage/hidden_benchmark_storage_contract.yaml`](../governance/storage/hidden_benchmark_storage_contract.yaml)，由 `ci/checkers/check_hidden_benchmark_boundary.py` 对工作树与全部 Git 历史双向扫描守卫。

## M0 当前状态

M0 只建立目录与本边界说明，**未产生任何 manifest、hash 或 result summary**。首批冻结清单在 M2 评测冻结时产生。
