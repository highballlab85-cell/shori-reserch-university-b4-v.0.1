# データ取得チェックリスト

## 1. AMI Meeting Corpus
- [ ] ライセンス確認（AMI Corpus Agreement）
- [ ] ダウンロード手順記録（`docs/data/ami-download.md` を作成予定）
- [ ] 音声 + トランスクリプト格納先: `data/raw/ami/`
- [ ] トランスクリプト形式（XML → JSON ラベル変換）
- [ ] アクションアイテム注釈の構造を調査し、C2-Graph ラベルへのマッピング案作成

## 2. ICSI Meeting Corpus
- [ ] ライセンス確認・利用可否
- [ ] 音声・トランスクリプトの入手リンク
- [ ] スピーカーIDとタイムスタンプの整合性チェック
- [ ] 既存アノテーション（議題、決定事項）の有無調査

## 3. 自前 triads データ
- [ ] 収集計画（人数、会議時間）
- [ ] 同意取得テンプレート
- [ ] 匿名化手順（個人名→役職名）
- [ ] 音声ファイル格納: `data/raw/inhouse/`
- [ ] 手動アノテーション仕様書ドラフトを準備

## 4. 前処理 TODO
- [ ] 音声正規化スクリプト (`scripts/preprocess/audio_normalize.py`) の作成
- [ ] トランスクリプト整形 (`scripts/preprocess/ami_to_json.py`)
- [ ] Diarization/QC ログのテンプレ (`runs/template/log.md`)

## 5. セキュリティ・プライバシー
- [ ] `.gitignore` に `data/raw/` を追加済みか確認
- [ ] 個人情報を含むファイルは暗号化ストレージで管理
- [ ] 研究外部共有時は再配布不可なデータを除外

---
最終更新: 2025-09-17
