# Minimum Viable Research Repo (卒研版)

このリポジトリは、**研究テーマそのもの**を Detect→Frame→Model/Hypothesize→Design→Run→Analyze→Update→Communicate→Decide のループで更新しつつ、
Codex CLI と小規模データで検証するための最小構成です。

- 研究単位は常に **「主張＋根拠＋手続＋範囲」**。
- 自動コミット／プッシュは `scripts/auto-commit-push.*` を使ってスケジュール実行します（詳細は `docs/GIT_AUTOCOMMIT.md`）。
- 出発点の基準（DER≤15%, TripleF1≥0.85, QA≥0.70）は中間発表の表（p.9）に準拠。テーマ更新に応じて改訂可。

## 初期セットアップ（共通）

```bash
git init
git checkout -b main
git config user.name  "Your Name"
git config user.email "you@example.com"
# 既存リポに入れるなら origin を設定
git remote add origin <your-remote-url>
```

> Windows では **Git Credential Manager** が既定で使えます。最初の push で一度だけ認証してください。

## すぐ試す（手動実行）

- **Windows (PowerShell)**

```powershell
pwsh -File scripts/auto-commit-push.ps1 -RepoPath .
```

- **macOS / Linux (bash)**

```bash
bash scripts/auto-commit-push.sh .
```

## フォルダ

```
agents/AGENTS.md        ← 本ガイド（テーマ探索版）
themes/frame.yaml       ← テーマ評価のExit条件テンプレ
docs/GIT_AUTOCOMMIT.md  ← 定期コミットの設定手順
scripts/auto-commit-push.ps1 / .sh ← 自動コミット・プッシュ
logs/                   ← スケジュール実行の標準出力ログ置き場
```

