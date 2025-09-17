param(
  [string]$RepoPath = (Resolve-Path ".")
)

$ErrorActionPreference = "SilentlyContinue"
Set-Location $RepoPath

# 初回コミットがない場合に備える
$headExists = (git rev-parse --verify HEAD 2>$null) -ne $null
if (-not $headExists) {
  git add -A | Out-Null
  git commit -m "chore(init): initial commit [skip ci]" | Out-Null
}

# 可能なら最新を取り込む（衝突時は次回に再試行）
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if ([string]::IsNullOrEmpty($branch) -or $branch -eq "HEAD") { $branch = "main" }
$hasOrigin = (git remote | Select-String -Pattern '^origin$')
if ($hasOrigin) { git pull --rebase origin $branch | Out-Null }

# 変更があるか？
git diff-index --quiet HEAD -- 2>$null
$changed = $LASTEXITCODE -ne 0

if ($changed) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  git add -A | Out-Null
  git commit -m "auto: save work @ $ts [skip ci]" | Out-Null
  if ($hasOrigin) { git push origin $branch | Out-Null }
  Write-Host "Pushed changes at $ts"
} else {
  Write-Host "No changes."
}
