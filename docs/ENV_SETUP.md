# 環境セットアップ（C2-Graph研究用）

## 1. 開発環境
- Python 3.10 系推奨（WhisperX / pyannote.audio が動作確認済）
- CUDA 対応 GPU がない場合は CPU fallback（推論速度低下を許容）
- 推奨 OS: macOS 14 / Ubuntu 22.04 以降

```bash
# poetry 例
poetry env use 3.10
poetry install
```

## 2. 必須ライブラリ
- whisperx==3.*
- pyannote.audio==3.*
- transformers==4.*
- pytorch==2.*
- networkx==3.*
- neo4j==5.*（任意、グラフDB使用時）
- faiss-cpu==1.7.*
- pandas, numpy, scikit-learn

> TODO: `pyproject.toml` / `requirements.txt` を整備し、`poetry export` で記録。

## 3. 音声処理ツール
- FFmpeg（WhisperX 前処理用）
- sox（オーディオ正規化に使用予定）

macOS Homebrew 例:
```bash
brew install ffmpeg sox
```

## 4. WhisperX & diarization
- WhisperX: `whisperx transcribe --model large-v3 --diarize` を基本に、英語専用モデルを使用。
- Diarization: `pyannote/speaker-diarization` のチェックポイントを `.env` で指定。
- TODO: `scripts/pipeline/` に推論スクリプトを追加予定。

## 5. LLM / 推論
- ローカルLLM（例: llama.cpp） or API（OpenAI, Anthropic）を選定し、入出力フォーマットを `docs/LLM_PROMPTS.md` に集約予定。
- API キーは `.env` 管理。`env.example` を作成する。

## 6. 評価環境
- `notebooks/` に Jupyter 環境を配置し、metrics の可視化テンプレートを用意。
- `pytest` + `nbmake` で自動チェックを予定。

## 7. ログ・自動化
- `scripts/watch-auto-commit-push.sh` を利用する場合は `fswatch` をインストール。
- 定期バッチは `cron` または `launchd` を使用。設定例は `docs/GIT_AUTOCOMMIT.md` を参照。

---
最終更新: 2025-09-17
