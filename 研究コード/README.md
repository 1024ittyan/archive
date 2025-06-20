# 国会議事録テキスト分析研究

## 研究概要

本研究では、日本の国会議事録データを用いて、自然言語処理技術（BERT、CyberAgent OpenCALM）による発言内容の分散表現作成とクラスタリング分析を実施しました。政治発言の傾向分析と時系列変化の検証を目的としています。

## 研究目的

- 国会議事録の発言内容を機械学習技術で分析し、政治的な発言パターンを抽出
- 異なる言語モデル（BERT、OpenCALM）による分散表現の比較検証
- クラスタリング分析による発言内容の分類と可視化
- 時系列データにおける政治発言の変化傾向の分析

## ファイル構成

### メインファイル
- `BERT_UnityData.ipynb` - BERT分散表現データの統合分析と可視化
- `BERT1.ipynb` - BERTモデルによる大規模分析
- `Cyber1.ipynb` - CyberAgent OpenCALMモデルによる大規模分析
- `国会議事録API収集用.ipynb` - 国会議事録APIからのデータ収集スクリプト

### BERT分析フォルダ
- `BERT/BERT_分散表現作成.ipynb` - BERTモデルによる分散表現作成
- `BERT/BERT_SilhouetteCoefficient.ipynb` - シルエット係数によるクラスタ数最適化
- `BERT/BERT11cullabels.csv` - 11クラスタのラベルデータ
- `BERT/BERT11cluster_centers.npy` - クラスタ中心点データ

### Cyber分析フォルダ
- `Cyber/Cyber_分散表現作成.ipynb` - OpenCALMモデルによる分散表現作成
- `Cyber/Cyber＿SilhouetteCoefficient.ipynb` - シルエット係数によるクラスタ数最適化
- `Cyber/Cyber11cullabels.csv` - 11クラスタのラベルデータ
- `Cyber/Cyber11cluster_centers.npy` - クラスタ中心点データ

## 技術スタック

### 使用言語・フレームワーク
- **Python 3.10+**
- **Jupyter Notebook**
- **Google Colab**

### 機械学習・自然言語処理
- **Transformers** - Hugging Face Transformersライブラリ
- **BERT** - cl-tohoku/bert-base-japanese-whole-word-masking
- **OpenCALM** - cyberagent/open-calm-7b
- **scikit-learn** - K-meansクラスタリング、PCA次元削減
- **PyTorch** - 深層学習フレームワーク

### データ処理・可視化
- **pandas** - データフレーム操作
- **numpy** - 数値計算
- **matplotlib** - グラフ描画
- **seaborn** - 統計的可視化
- **plotly** - インタラクティブ可視化
- **Dash** - Webアプリケーション作成

### その他ライブラリ
- **janome** - 日本語形態素解析
- **wordcloud** - ワードクラウド生成
- **pyclustering** - クラスタリングアルゴリズム

## 研究手法

### 1. データ収集
- 国会議事録検索システムAPIを使用
- 2018年〜2023年の本会議発言データを収集
- 発言者名、発言内容、会派、日付などのメタデータを取得

### 2. 分散表現作成
#### BERTモデル
- 日本語事前学習済みBERTモデルを使用
- 発言内容を768次元のベクトルに変換
- 平均プーリングによる文章ベクトル化

#### OpenCALMモデル
- CyberAgentの日本語大規模言語モデルを使用
- 発言内容を4096次元のベクトルに変換
- 隠れ状態の平均による文章ベクトル化

### 3. クラスタリング分析
- K-meansアルゴリズムによるクラスタリング
- シルエット係数による最適クラスタ数の決定
- 11クラスタでの分類を実施

### 4. 可視化・分析
- PCAによる次元削減と3次元可視化
- インタラクティブな3Dプロット作成
- クラスタ別の特徴分析
- 時系列変化の検証

## 研究成果

### 技術的成果
- 大規模な国会議事録データ（16,537件）の効率的な処理
- 異なる言語モデルによる分散表現の比較検証
- クラスタリングによる政治発言パターンの自動分類
- インタラクティブな可視化システムの構築

### 分析的成果
- 政治発言の11つの主要パターンの特定
- 発言者・会派別の発言傾向の分析
- 時系列における政治トピックの変化追跡
- 機械学習による政治テキスト分析手法の確立

## 今後の展開

- より大規模なデータセットでの分析
- 他の言語モデルとの比較検証
- リアルタイム分析システムの構築
- 政治予測モデルへの応用

## 参考文献

- 国会議事録検索システムAPI: https://kokkai.ndl.go.jp/
- BERT: Devlin et al. (2019) "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding"
- OpenCALM: CyberAgent (2023) "OpenCALM: An Open Language Model for Japanese"

---

**研究期間**: 2023年〜2024年  
**データ期間**: 2018年〜2023年  
**分析対象**: 国会議事録本会議発言 16,537件
