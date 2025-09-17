# 自動コミット & プッシュ設定

変更があれば自動的に `git add -A` → `commit` → `push` します。変更がなければ何もしません。
コミットメッセージには `[skip ci]` を付与しています。

---

## Windows（Task Scheduler）

1. PowerShell 実行ポリシーを一時的にバイパスして登録します：

```powershell
$repo = (Resolve-Path ".").Path
schtasks /Create /SC MINUTE /MO 10 /TN "AutoCommitPush" /TR "powershell.exe -ExecutionPolicy Bypass -File `"$repo\scripts\auto-commit-push.ps1`" -RepoPath `"$repo`" >> `"$repo\logs\auto-commit.log`" 2>&1" /RL LIMITED /F /WD "$repo"
```

- `/SC MINUTE /MO 10` は 10 分おき。必要に応じて変更してください。
- 停止：`schtasks /Delete /TN AutoCommitPush /F`

手動実行：

```powershell
pwsh -File scripts/auto-commit-push.ps1 -RepoPath .
```

---

## macOS / Linux（cron）

```bash
crontab -e
```

以下を追加（10 分おき）：

```
*/10 * * * * cd /path/to/your/repo && bash scripts/auto-commit-push.sh . >> logs/auto-commit.log 2>&1
```

### リアルタイム監視（任意）

- `scripts/watch-auto-commit-push.sh` を使うと、`fswatch` がある環境ではファイル変更を検知して即時に `auto-commit-push.sh` を呼び出します。
- 依存: `fswatch`（推奨）。未導入の場合は自動的にポーリング（既定15秒間隔）。
- 使い方: `bash scripts/watch-auto-commit-push.sh .` を実行し、プロセスを常駐させておきます。`POLL_INTERVAL` や `QUIET_PERIOD` を環境変数で上書きできます。
- サービス化する場合は `launchd` や `systemd` などで常駐実行させてください。

---

## 先にやっておくこと

```bash
git init
git checkout -b main
git config user.name  "Your Name"
git config user.email "you@example.com"
git remote add origin <your-remote-url>     # 既存リモートがある場合
git pull --rebase origin main || true       # 初回は存在しない場合もあるので true 許容
```

> 認証は初回の `git push` で求められます。Windows は Git Credential Manager、macOS は Keychain、Linux は credential store などを利用してください。
