# DeepMoat 重构工作区

本目录是 Python(FastAPI) → Rust(axum) 重构的所有产物落点。**只读** `app/` 与 `fe/`，**不动原代码**。

## 自驱启动

```bash
# 喂给一个长跑 agent（建议 claude --dangerously-skip-permissions 或 Workflow 根 agent）
cat refactor/00_meta/MASTER_PROMPT.md
```

## 目录

```
refactor/
├── 00_meta/          # 主控提示词、进度、决策记录、阻塞问题
├── 01_discovery/     # P1 现状盘点
├── 02_specs/         # P2 PRD / 功能说明 / 名词表
├── 03_api/           # P3 OpenAPI 契约
├── 04_design/        # P4 架构与详设
├── 05_impl_plan/     # P5 里程碑与任务拆分
├── 06_tests/         # P8 测试方案与金标准
└── _workspace/       # P6/P7 真实代码 PoC
    ├── backend/      # Rust workspace（cargo）
    └── frontend/     # Vue 3 美化版（不动原 fe/）
```

## 已拍板锚点

- 详见 `00_meta/DECISIONS.md`

## 多环境

### deepvalue仓库
windows环境：C:\codes\github\deepvalue
mac环境：/Users/raywang/codes/github/deepvalue

### deepmoat 仓库
windows环境：C:\codes\github\deepmoat\
mac环境:/Users/raywang/codes/github/deepmoat
