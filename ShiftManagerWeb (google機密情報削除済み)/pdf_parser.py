#!/usr/bin/env python3
"""
PDF Parser Module - シフト表PDFからシフト情報を抽出するモジュール

本モジュールは、PDFファイル内のテーブルまたはテキストデータから
指定された担当者（target_name）のシフト情報（勤務日および勤務時間）を抽出するためのクラスを提供します。
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import pdfplumber
from PIL import Image
import tempfile

logger = logging.getLogger(__name__)


class PdfParser:
    """PDFからシフト情報を抽出するクラス"""

    def __init__(self, target_name: str):
        """
        初期化

        Args:
            target_name: 検索対象の名前
        """
        self.target_name = target_name
        # 時間形式のパターン（10:00-18:00, 10:00～18:00など）を柔軟に対応
        self.time_pattern = r'(\d{1,2})[\.:](\d{2})\s*[‐\-~〜～－]\s*(\d{1,2})[\.:](\d{2})'

    @staticmethod
    def extract_year_month(filename: str) -> Tuple[int, str]:
        """
        ファイル名から年月情報を抽出

        Args:
            filename: PDFファイル名

        Returns:
            (年, 月) のタプル。月は2桁の文字列形式（例: "05"）
        """
        # 令和X年Y月 形式
        reiwa_match = re.search(r'令和(\d+)年(\d+)月', filename)
        if reiwa_match:
            reiwa_year = int(reiwa_match.group(1))
            month = int(reiwa_match.group(2))
            year = 2018 + reiwa_year
            return year, f"{month:02d}"

        # X年Y月 形式
        year_month_match = re.search(r'(\d+)年(\d+)月', filename)
        if year_month_match:
            year = int(year_month_match.group(1))
            if year < 100:
                year += 2000
            month = int(year_month_match.group(2))
            return year, f"{month:02d}"

        # YYYYMM 形式
        yyyymm_match = re.search(r'(\d{4})(\d{2})', filename)
        if yyyymm_match:
            year = int(yyyymm_match.group(1))
            month = yyyymm_match.group(2)
            return year, month

        # ファイルの最終更新日時を使用
        try:
            pdf_time = os.path.getmtime(filename)
            pdf_date = datetime.fromtimestamp(pdf_time)
            return pdf_date.year, f"{pdf_date.month:02d}"
        except Exception as e:
            logger.error(f"PDF作成日取得エラー: {e}")

        # 現在の日付をフォールバックとして使用
        now = datetime.now()
        return now.year, f"{now.month:02d}"

    def extract_date_from_text(self, text: str) -> Optional[str]:
        """
        テキストから日付を抽出

        Args:
            text: 日付を含む可能性のあるテキスト

        Returns:
            抽出された日付（日のみ）、見つからない場合はNone
        """
        if not text:
            return None

        # "16日" のような形式を検索
        date_match = re.search(r'(\d{1,2})日', text)
        if date_match:
            return date_match.group(1)

        # "16（月）" のような形式を検索
        date_paren_match = re.search(r'(\d{1,2})\s*[\(（]', text)
        if date_paren_match:
            return date_paren_match.group(1)

        # 単なる数字の場合（コンテキストから日付と判断できる場合）
        if text and text.strip().isdigit() and 1 <= int(text.strip()) <= 31:
            return text.strip()

        return None

    def extract_time_from_text(self, text: str) -> Optional[str]:
        """
        テキストから時間範囲を抽出

        Args:
            text: 時間範囲を含む可能性のあるテキスト

        Returns:
            抽出された時間範囲、見つからない場合はNone
        """
        if not text:
            return None

        # 標準的な時間範囲パターン
        time_match = re.search(self.time_pattern, text)
        if time_match:
            return time_match.group(0)

        # 追加の時間パターン: "10時-18時" のような形式
        alt_time_match = re.search(r'(\d{1,2})時\s*[‐\-~〜～－]\s*(\d{1,2})時', text)
        if alt_time_match:
            start_hour = alt_time_match.group(1)
            end_hour = alt_time_match.group(2)
            return f"{start_hour}:00-{end_hour}:00"

        return None

    def name_matches(self, text: str) -> bool:
        """
        テキストに対象の名前が含まれているかチェック（部分一致）

        Args:
            text: チェック対象のテキスト

        Returns:
            名前が含まれている場合はTrue
        """
        if not text:
            return False

        # 完全一致
        if self.target_name == text.strip():
            return True

        # 部分一致（名字や名前の一部だけでもマッチ）
        if self.target_name in text:
            return True

        # 名前の一部が含まれている場合（2文字以上の名前の場合）
        if len(self.target_name) >= 2:
            for i in range(len(self.target_name) - 1):
                if self.target_name[i:i+2] in text:
                    return True

        return False

    def parse_table_format(self, table: List[List[Any]]) -> List[Dict[str, str]]:
        """
        テーブル形式のデータからシフト情報を抽出

        Args:
            table: PDFから抽出されたテーブルデータ

        Returns:
            シフト情報のリスト
        """
        shifts = []

        # テーブルの内容をログに出力（デバッグ用）
        logger.info(f"テーブル解析開始: {len(table)}行 x {len(table[0]) if table else 0}列")
        for i, row in enumerate(table[:5]):  # 最初の5行だけログ出力
            logger.info(f"テーブル行 {i}: {row}")

        # テーブルのヘッダー行を特定
        header_row_index = 0
        for i, row in enumerate(table):
            if row and any(cell and isinstance(cell, str) and ('日' in cell or '曜' in cell) for cell in row):
                header_row_index = i
                logger.info(f"ヘッダー行を特定: {i}行目 - {row}")
                break

        # 日付列と時間列のインデックスを特定
        date_col_index = None
        time_col_index = None
        name_col_index = None

        if len(table) > header_row_index:
            header = table[header_row_index]
            for i, cell in enumerate(header):
                if not cell:
                    continue

                cell_text = str(cell).lower()
                if '日' in cell_text or '曜' in cell_text or '日付' in cell_text:
                    date_col_index = i
                    logger.info(f"日付列を特定: {i}列目 - {cell}")
                elif '時間' in cell_text or '時刻' in cell_text:
                    time_col_index = i
                    logger.info(f"時間列を特定: {i}列目 - {cell}")
                elif '名前' in cell_text or '氏名' in cell_text or '担当' in cell_text:
                    name_col_index = i
                    logger.info(f"名前列を特定: {i}列目 - {cell}")

        # 日付列と時間列が特定できない場合は、デフォルト値を使用
        if date_col_index is None:
            date_col_index = 0
            logger.info(f"日付列が特定できないため、デフォルト値を使用: {date_col_index}列目")
        if time_col_index is None:
            time_col_index = 2  # 一般的なシフト表では時間は3列目にあることが多い
            logger.info(f"時間列が特定できないため、デフォルト値を使用: {time_col_index}列目")

        # 各行を処理
        for row_index, row in enumerate(table):
            if row_index <= header_row_index:
                continue  # ヘッダー行をスキップ

            # 対象の名前を含む行を検索
            name_found = False

            # 名前列が特定されている場合、その列をチェック
            if name_col_index is not None and name_col_index < len(row):
                name_cell = row[name_col_index]
                if name_cell and self.name_matches(str(name_cell)):
                    name_found = True
                    logger.info(f"名前列で一致: {row_index}行目 - {name_cell}")

            # 行全体をチェック
            if not name_found and any(cell and self.name_matches(str(cell)) for cell in row):
                name_found = True
                logger.info(f"行内で名前一致: {row_index}行目")

            if name_found:
                date_str = str(row[date_col_index]) if date_col_index < len(row) and row[date_col_index] else ""
                time_str = str(row[time_col_index]) if time_col_index < len(row) and row[time_col_index] else ""

                logger.info(f"シフト候補: 日付={date_str}, 時間={time_str}")

                # 日付の抽出
                date = None
                date_match = re.search(r'(\d{1,2})日', date_str)
                if date_match:
                    date = date_match.group(1)
                    logger.info(f"日付を抽出: {date}")

                # 時間の抽出
                time = self.extract_time_from_text(time_str)

                # 時間が見つからない場合、行全体から探す
                if not time:
                    for cell in row:
                        if cell:
                            time = self.extract_time_from_text(str(cell))
                            if time:
                                logger.info(f"行内から時間を抽出: {time}")
                                break

                if date and time:
                    logger.info(f"シフト情報を抽出: 日付={date}, 時間={time}")
                    shifts.append({'date': date, 'time': time})

        return shifts

    def parse_text_format(self, text: str) -> List[Dict[str, str]]:
        """
        テキスト形式のデータからシフト情報を抽出

        Args:
            text: PDFから抽出されたテキスト

        Returns:
            シフト情報のリスト
        """
        shifts = []

        if not text:
            return shifts

        # テキストの一部をログに出力（デバッグ用）
        logger.info(f"テキスト解析開始: 長さ {len(text)} 文字")
        logger.info(f"テキストサンプル: {text[:200]}...")

        # 名前が含まれているかチェック
        if self.target_name not in text:
            logger.info(f"テキスト内に名前 '{self.target_name}' が見つかりません")
            # 名前の一部で検索
            if len(self.target_name) >= 2:
                for i in range(len(self.target_name) - 1):
                    part = self.target_name[i:i+2]
                    if part in text:
                        logger.info(f"名前の一部 '{part}' がテキスト内に見つかりました")
                        break

        # パターン1: 名前の後に日付と時間が続く形式
        pattern1 = f'{self.target_name}.*?(\\d{{1,2}})日.*?({self.time_pattern})'
        for match in re.finditer(pattern1, text):
            logger.info(f"パターン1で一致: {match.group(0)[:50]}...")
            shifts.append({'date': match.group(1), 'time': match.group(2)})

        # パターン2: 日付の後に名前と時間が続く形式
        pattern2 = r'(\d{1,2})日.*?' + self.target_name + r'.*?(' + self.time_pattern + r')'
        for match in re.finditer(pattern2, text):
            logger.info(f"パターン2で一致: {match.group(0)[:50]}...")
            shifts.append({'date': match.group(1), 'time': match.group(2)})

        # パターン3: 日付と名前が離れている場合
        dates = re.findall(r'(\d{1,2})日', text)
        if dates:
            logger.info(f"抽出された日付: {dates}")
            name_time_pairs = re.findall(self.target_name + r'.*?(' + self.time_pattern + r')', text)
            logger.info(f"抽出された名前と時間のペア: {name_time_pairs}")

            if len(dates) == len(name_time_pairs):
                logger.info(f"日付と時間のペアを組み合わせ: {len(dates)}件")
                for date, time in zip(dates, name_time_pairs):
                    shifts.append({'date': date, 'time': time})

        # パターン4: 名前の近くに日付と時間がある場合
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if self.name_matches(line):
                logger.info(f"名前を含む行を検出: {i}行目 - {line[:50]}...")
                context_lines = lines[max(0, i-3):min(len(lines), i+4)]
                context_text = '\n'.join(context_lines)
                date_match = re.search(r'(\d{1,2})日', context_text)
                date = date_match.group(1) if date_match else None
                time_match = re.search(self.time_pattern, context_text)
                time = time_match.group(0) if time_match else None
                if date and time:
                    logger.info(f"コンテキストから抽出: 日付={date}, 時間={time}")
                    shifts.append({'date': date, 'time': time})

        return shifts

    def parse_pdf(self, pdf_path: str) -> List[Dict[str, str]]:
        """
        PDFファイルからシフト情報を抽出

        Args:
            pdf_path: PDFファイルのパス

        Returns:
            シフト情報のリスト
        """
        shifts = []

        try:
            logger.info(f"PDF解析開始: {pdf_path}")
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"PDF読み込み成功: {len(pdf.pages)}ページ")

                for page_num, page in enumerate(pdf.pages):
                    logger.info(f"ページ {page_num+1} の解析開始")
                    # まずテーブルを抽出して処理
                    table = page.extract_table()
                    if table:
                        logger.info(f"テーブルを検出: {len(table)}行 x {len(table[0]) if table else 0}列")
                        for row_index, row in enumerate(table):
                            if row_index == 0:
                                continue  # ヘッダー行をスキップ

                            if any(cell and self.name_matches(str(cell or "")) for cell in row):
                                logger.info(f"名前を含む行を検出: {row_index}行目")
                                date_str = str(row[0] or "")
                                time_str = str(row[2] or "") if len(row) > 2 else ""
                                logger.info(f"候補: 日付列={date_str}, 時間列={time_str}")

                                date_match = re.search(r'(\d{1,2})日', date_str)
                                if date_match:
                                    date_num = date_match.group(1)
                                    logger.info(f"日付を抽出: {date_num}")
                                    time_extracted = self.extract_time_from_text(time_str)
                                    if time_extracted:
                                        logger.info(f"時間を抽出: {time_extracted}")
                                        shifts.append({'date': date_num, 'time': time_extracted})
                                        logger.info(f"シフト情報を追加: 日付={date_num}, 時間={time_extracted}")
                    else:
                        logger.info("テーブルは検出されませんでした。テキスト解析を試みます。")
                        text = page.extract_text()
                        if text:
                            logger.info(f"テキストを抽出: {len(text)}文字")
                            pattern = f'{self.target_name}.*?(\\d{{1,2}})日.*?(\\d{{1,2}}[:.:]\\d{{2}}\\s*[‐\-~〜～]\\s*[\\d:.]+)'
                            for match in re.finditer(pattern, text):
                                date = match.group(1)
                                time_str = match.group(2)
                                logger.info(f"テキストからシフト情報を抽出: 日付={date}, 時間={time_str}")
                                shifts.append({'date': date, 'time': time_str})

                            # 追加のパターン
                            if not shifts:
                                # パターン1: 名前の後に日付と時間が続く形式
                                pattern1 = f'{self.target_name}.*?(\\d{{1,2}})日.*?({self.time_pattern})'
                                for match in re.finditer(pattern1, text):
                                    logger.info(f"パターン1で一致: {match.group(0)[:50]}...")
                                    shifts.append({'date': match.group(1), 'time': match.group(2)})

                                # パターン2: 日付の後に名前と時間が続く形式
                                pattern2 = r'(\d{1,2})日.*?' + self.target_name + r'.*?(' + self.time_pattern + r')'
                                for match in re.finditer(pattern2, text):
                                    logger.info(f"パターン2で一致: {match.group(0)[:50]}...")
                                    shifts.append({'date': match.group(1), 'time': match.group(2)})
                        else:
                            logger.info("テキストは抽出できませんでした")

            # 重複を削除
            unique_shifts = []
            seen = set()
            for shift in shifts:
                key = (shift['date'], shift['time'])
                if key not in seen:
                    seen.add(key)
                    unique_shifts.append(shift)

            # 日付順にソート
            sorted_shifts = sorted(unique_shifts, key=lambda x: int(x['date']))
            logger.info(f"PDF解析完了。抽出したシフト数: {len(sorted_shifts)}")
            return sorted_shifts

        except Exception as e:
            logger.error(f"PDF解析中にエラーが発生しました: {e}")
            return []

    def generate_preview_image(self, pdf_path: str, page_num: int = 0) -> Optional[str]:
        """
        PDFの指定ページからプレビュー画像を生成

        Args:
            pdf_path: PDFファイルのパス
            page_num: 画像化するページ番号（0始まり）

        Returns:
            生成された画像のパス、失敗した場合はNone
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    img = page.to_image(resolution=150)

                    # 一時ファイルに保存
                    temp_dir = tempfile.gettempdir()
                    output_path = os.path.join(temp_dir, f"preview_{os.path.basename(pdf_path)}.png")
                    img.save(output_path)

                    return output_path
        except Exception as e:
            logger.error(f"プレビュー画像生成エラー: {e}")

        return None

    def extract_year_month_from_filename(self, filename):
        """ファイル名から年月を抽出する"""
        # 和暦（令和）のパターンを追加
        reiwa_pattern = r'[RＲ令和][0-9０-９]{1,2}'
        reiwa_match = re.search(reiwa_pattern, filename)
        
        year = None
        if reiwa_match:
            # 和暦を西暦に変換
            reiwa_str = reiwa_match.group()
            number = re.search(r'[0-9０-９]{1,2}', reiwa_str).group()
            # 全角数字を半角に変換
            number = number.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            # 令和から西暦への変換（令和1年 = 2019年）
            year = 2018 + int(number)
        
        # 月の抽出（既存のコード）
        month_pattern = r'([０-９0-9]+)月'
        month_match = re.search(month_pattern, filename)
        
        month = None
        if month_match:
            # 全角数字を半角に変換
            month_str = month_match.group(1)
            month_str = month_str.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            month = int(month_str)
        
        if year is None:
            # 年が取得できない場合は現在の年を使用
            current_year = datetime.now().year
            # 月が現在の月より大きい場合は前年の可能性がある
            current_month = datetime.now().month
            if month and month > current_month:
                year = current_year - 1
            else:
                year = current_year
        
        return year, month

    def extract_year_month(self, filepath):
        """
        1. まずファイル名から年月を抽出
        2. 見つからない場合はPDFの内容から抽出（既存の実装）
        """
        filename = os.path.basename(filepath)
        year, month = self.extract_year_month_from_filename(filename)
        
        if year is None or month is None:
            # 既存のPDF内容からの抽出ロジックを使用
            return super().extract_year_month(filepath)
            
        return year, month
