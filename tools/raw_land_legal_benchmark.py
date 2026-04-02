"""
raw_land_legal_benchmark.py - Build and run a benchmark for deed-legal extraction.

Workflow:
    python tools/raw_land_legal_benchmark.py prepare --county Bay --limit 4
    python tools/raw_land_legal_benchmark.py run
    # Fill gold_transcriptions.csv manually
    python tools/raw_land_legal_benchmark.py compare
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import io
import sys
import time
import urllib.request
from pathlib import Path

import psycopg2
import psycopg2.extras

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from bay_price_extract import _build_driver, _fetch_detail, _find_exact_result, _search_bay
from config import DATABASE_URL
from utils.raw_land_benchmark import compare_legal_texts, extract_legal_candidate, validate_legal_candidate


DEFAULT_BENCHMARK_DIR = Path('output') / 'raw_land_legal_benchmark'
MANIFEST_NAME = 'manifest.csv'
GOLD_NAME = 'gold_transcriptions.csv'
RESULTS_NAME = 'results.csv'
COMPARISON_NAME = 'comparison.csv'
_ANTHROPIC_PRICING = {
    'claude-opus-4-6': {'input_per_million': 5.0, 'output_per_million': 25.0},
}
_REUSABLE_RESULT_STATUSES = {'ok', 'not_found', 'unsupported_county'}


def _benchmark_path(base_dir: Path, name: str) -> Path:
    return base_dir / name


def fetch_raw_land_candidates(county: str | None = None, limit: int | None = None) -> list[dict]:
    where = ["type = 'Raw Land Purchase'"]
    params: list = []

    if county:
        where.append("county = %s")
        params.append(county)

    sql = f"""
        SELECT
            id,
            county,
            date,
            grantor,
            grantee,
            export_legal_desc,
            deed_locator,
            source_file
        FROM transactions
        WHERE {' AND '.join(where)}
        ORDER BY county, date NULLS LAST, id
    """
    if limit is not None:
        sql += ' LIMIT %s'
        params.append(limit)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def write_manifest(rows: list[dict], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = _benchmark_path(out_dir, MANIFEST_NAME)
    gold_path = _benchmark_path(out_dir, GOLD_NAME)

    manifest_rows = []
    gold_rows = []
    for row in rows:
        locator = row.get('deed_locator') or {}
        manifest_rows.append({
            'transaction_id': row.get('id'),
            'county': row.get('county'),
            'date': row.get('date'),
            'grantor': row.get('grantor'),
            'grantee': row.get('grantee'),
            'export_legal_desc': row.get('export_legal_desc'),
            'source_file': row.get('source_file'),
            'book': locator.get('book'),
            'page': locator.get('page'),
            'book_type': locator.get('book_type'),
            'book_page': locator.get('book_page'),
            'clerk_file_number': locator.get('clerk_file_number'),
            'instrument_number': locator.get('instrument_number'),
            'cfn': locator.get('cfn'),
        })
        gold_rows.append({
            'transaction_id': row.get('id'),
            'county': row.get('county'),
            'gold_legal_desc': '',
            'notes': '',
        })

    _write_csv(
        manifest_path,
        manifest_rows,
        [
            'transaction_id', 'county', 'date', 'grantor', 'grantee',
            'export_legal_desc', 'source_file', 'book', 'page', 'book_type',
            'book_page', 'clerk_file_number', 'instrument_number', 'cfn',
        ],
    )
    if not gold_path.exists():
        _write_csv(
            gold_path,
            gold_rows,
            ['transaction_id', 'county', 'gold_legal_desc', 'notes'],
        )

    return manifest_path, gold_path


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict]:
    encodings = ('utf-8-sig', 'cp1252', 'latin1')
    last_error = None
    for encoding in encodings:
        try:
            with path.open('r', newline='', encoding=encoding) as fh:
                return list(csv.DictReader(fh))
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error

    with path.open('r', newline='', encoding='utf-8-sig') as fh:
        return list(csv.DictReader(fh))


def _estimate_anthropic_cost_usd(model: str, input_tokens: int | None, output_tokens: int | None) -> float | None:
    pricing = _ANTHROPIC_PRICING.get(model)
    if pricing is None or input_tokens is None or output_tokens is None:
        return None
    return round(
        (input_tokens / 1_000_000) * pricing['input_per_million']
        + (output_tokens / 1_000_000) * pricing['output_per_million'],
        6,
    )


def _load_existing_results_by_transaction(results_path: Path) -> dict[str, dict]:
    if not results_path.exists():
        return {}
    return {
        str(row.get('transaction_id') or '').strip(): row
        for row in _read_csv(results_path)
        if str(row.get('transaction_id') or '').strip()
    }


def _should_reuse_existing_result(existing_row: dict | None, *, model: str, target_hint: str) -> bool:
    if not existing_row:
        return False
    if str(existing_row.get('status') or '').strip() not in _REUSABLE_RESULT_STATUSES:
        return False
    if str(existing_row.get('model') or '').strip() != str(model).strip():
        return False
    if str(existing_row.get('target_hint') or '').strip() != str(target_hint or '').strip():
        return False
    return True


def _mark_cache_hit(row: dict) -> dict:
    reused = dict(row)
    reused['cache_hit'] = 'True'
    existing_note = str(reused.get('note') or '').strip()
    cache_note = 'Reused existing model result; rerun with --force to refresh.'
    reused['note'] = f'{cache_note} {existing_note}'.strip() if existing_note else cache_note
    return reused


def _fetch_bay_pdf_artifacts(row: dict, artifacts_dir: Path) -> dict:
    from selenium.webdriver.support.ui import WebDriverWait

    locator = {
        'book': row.get('book'),
        'page': row.get('page'),
        'book_type': row.get('book_type'),
        'book_page': row.get('book_page'),
        'clerk_file_number': row.get('clerk_file_number'),
    }
    clerk_file_number = str(locator.get('clerk_file_number') or '').strip()
    if not clerk_file_number:
        raise ValueError('Bay raw-land row is missing clerk_file_number.')

    driver = _build_driver()
    try:
        wait = WebDriverWait(driver, 45)
        rows = _search_bay(driver, wait, clerk_file_number)
        matched = _find_exact_result(rows, locator)
        if not matched:
            raise LookupError('No exact Bay clerk match found for stored locator.')

        detail = _fetch_detail(driver, wait, matched)
        driver.execute_script("document.getElementById('DocumentViewButtonAll').click();")
        time.sleep(5)
        if len(driver.window_handles) < 2:
            raise RuntimeError('Bay clerk site did not open a document preview window.')

        driver.switch_to.window(driver.window_handles[-1])
        pdf_url = driver.current_url
    finally:
        driver.quit()

    with urllib.request.urlopen(pdf_url) as response:
        pdf_bytes = response.read()

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = artifacts_dir / 'source_document.pdf'
    pdf_path.write_bytes(pdf_bytes)

    return {
        'county': 'Bay',
        'matched_document_id': matched.get('document_id'),
        'matched_book': matched.get('book'),
        'matched_page': matched.get('page'),
        'matched_doc_type': matched.get('doc_type'),
        'detail_record_date': detail.get('record_date'),
        'pdf_url': pdf_url,
        'pdf_path': str(pdf_path),
        'pdf_bytes': pdf_bytes,
    }


def _ocr_pdf_pages(pdf_bytes: bytes, artifacts_dir: Path) -> list[str]:
    import pytesseract
    from pdf2image import convert_from_bytes

    pages = convert_from_bytes(pdf_bytes, dpi=150)
    texts = []

    ocr_dir = artifacts_dir / 'ocr'
    ocr_dir.mkdir(parents=True, exist_ok=True)
    for idx, image in enumerate(pages, start=1):
        text = pytesseract.image_to_string(image)
        texts.append(text)
        (ocr_dir / f'page_{idx:02d}.txt').write_text(text, encoding='utf-8')

    return texts


def _load_page_texts(artifacts_dir: Path) -> list[str]:
    ocr_dir = artifacts_dir / 'ocr'
    page_paths = sorted(ocr_dir.glob('page_*.txt'))
    return [path.read_text(encoding='utf-8') for path in page_paths]


def _load_gold_notes(gold_path: Path) -> dict[str, str]:
    notes = {}
    for row in _read_csv(gold_path):
        transaction_id = str(row.get('transaction_id') or '').strip()
        if transaction_id:
            notes[transaction_id] = str(row.get('notes') or '').strip()
    return notes


def _build_target_instruction(target_hint: str | None) -> str:
    hint = str(target_hint or '').strip()
    if not hint:
        return 'No special target hint was provided. Return the complete legal description from the deed.'
    return f'Target hint: {hint}. Return only that requested legal section.'


def _extract_text_from_anthropic_response(response) -> str:
    parts = []
    for block in response.content:
        text = getattr(block, 'text', None)
        if text:
            parts.append(text)
    return '\n'.join(parts).strip()


def _run_anthropic_text_extraction(model: str, page_texts: list[str], target_hint: str | None) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    prompt = (
        'Extract the exact deed legal description.\n'
        f'{_build_target_instruction(target_hint)}\n'
        'Rules:\n'
        '- Return only the legal description text and nothing else.\n'
        '- Remove page headers, page footers, exhibit labels, witness text, and notary text.\n'
        '- Preserve bearings, distances, parcel IDs, lot/block references, and wording as faithfully as possible.\n'
        '- When OCR errors are obvious and unambiguous, silently correct them.\n'
        '- If the legal description is not present, return NOT_FOUND.\n\n'
        'OCR text follows:\n'
    )
    for index, text in enumerate(page_texts, start=1):
        prompt += f'\n[PAGE {index}]\n{text}\n'

    response = client.messages.create(
        model=model,
        max_tokens=3000,
        temperature=0,
        messages=[{'role': 'user', 'content': prompt}],
    )
    candidate = _extract_text_from_anthropic_response(response)
    usage = getattr(response, 'usage', None)
    input_tokens = getattr(usage, 'input_tokens', None)
    output_tokens = getattr(usage, 'output_tokens', None)
    return {
        'candidate_legal_desc': None if candidate == 'NOT_FOUND' else candidate,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'estimated_cost_usd': _estimate_anthropic_cost_usd(model, input_tokens, output_tokens),
    }


def _run_anthropic_vision_extraction(model: str, pdf_bytes: bytes, target_hint: str | None) -> dict:
    import anthropic
    from pdf2image import convert_from_bytes

    client = anthropic.Anthropic()
    page_images = convert_from_bytes(pdf_bytes, dpi=150)
    content = [
        {
            'type': 'text',
            'text': (
                'Extract the exact deed legal description from these deed page images.\n'
                f'{_build_target_instruction(target_hint)}\n'
                'Rules:\n'
                '- Return only the legal description text and nothing else.\n'
                '- Remove page headers, page footers, exhibit labels, witness text, and notary text.\n'
                '- Preserve bearings, distances, parcel IDs, lot/block references, and wording as faithfully as possible.\n'
                '- If the legal description is not present, return NOT_FOUND.'
            ),
        }
    ]
    for image in page_images:
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        content.append(
            {
                'type': 'image',
                'source': {
                    'type': 'base64',
                    'media_type': 'image/png',
                    'data': base64.b64encode(buffer.getvalue()).decode('ascii'),
                },
            }
        )

    response = client.messages.create(
        model=model,
        max_tokens=3000,
        temperature=0,
        messages=[{'role': 'user', 'content': content}],
    )
    candidate = _extract_text_from_anthropic_response(response)
    usage = getattr(response, 'usage', None)
    input_tokens = getattr(usage, 'input_tokens', None)
    output_tokens = getattr(usage, 'output_tokens', None)
    return {
        'candidate_legal_desc': None if candidate == 'NOT_FOUND' else candidate,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'estimated_cost_usd': _estimate_anthropic_cost_usd(model, input_tokens, output_tokens),
    }


def _validation_fields(prefix: str, validation: dict | None) -> dict:
    validation = validation or {}
    return {
        f'{prefix}_validation_passed': validation.get('passed', ''),
        f'{prefix}_validation_reasons': ' | '.join(validation.get('reasons') or []),
        f'{prefix}_validation_similarity_ratio': validation.get('similarity_ratio', ''),
        f'{prefix}_validation_target_parcel': validation.get('target_parcel', ''),
        f'{prefix}_validation_candidate_parcels': ' | '.join(str(value) for value in validation.get('candidate_parcel_numbers') or []),
        f'{prefix}_validation_candidate_bearings': validation.get('candidate_bearing_count', ''),
        f'{prefix}_validation_candidate_distances': validation.get('candidate_distance_count', ''),
    }


def run_benchmark(manifest_path: Path, out_dir: Path) -> Path:
    rows = _read_csv(manifest_path)
    results = []

    for row in rows:
        transaction_id = str(row.get('transaction_id') or '').strip()
        county = str(row.get('county') or '').strip()
        artifacts_dir = out_dir / 'artifacts' / transaction_id

        result = {
            'transaction_id': transaction_id,
            'county': county,
            'method': 'ocr_heuristic',
            'status': 'unsupported_county',
            'page_count': '',
            'start_page': '',
            'end_page': '',
            'start_marker': '',
            'end_marker': '',
            'candidate_legal_desc': '',
            'candidate_chars': '',
            'pdf_path': '',
            'ocr_dir': '',
            'matched_document_id': '',
            'note': '',
        }

        try:
            if county != 'Bay':
                result['note'] = 'Only Bay deed PDF fetching is implemented in this benchmark harness.'
                results.append(result)
                continue

            fetch_result = _fetch_bay_pdf_artifacts(row, artifacts_dir)
            page_texts = _ocr_pdf_pages(fetch_result['pdf_bytes'], artifacts_dir)
            extraction = extract_legal_candidate(page_texts)

            result.update({
                'status': extraction['status'],
                'page_count': len(page_texts),
                'start_page': extraction.get('start_page') or '',
                'end_page': extraction.get('end_page') or '',
                'start_marker': extraction.get('start_marker') or '',
                'end_marker': extraction.get('end_marker') or '',
                'candidate_legal_desc': extraction.get('candidate_legal_desc') or '',
                'candidate_chars': len(extraction.get('candidate_legal_desc') or ''),
                'pdf_path': fetch_result['pdf_path'],
                'ocr_dir': str(artifacts_dir / 'ocr'),
                'matched_document_id': fetch_result.get('matched_document_id') or '',
            })
            if extraction['status'] != 'ok':
                result['note'] = 'OCR completed, but the heuristic extractor did not isolate a legal candidate.'
        except Exception as exc:  # noqa: BLE001
            result['status'] = 'error'
            result['note'] = f'{type(exc).__name__}: {exc}'

        results.append(result)

    results_path = _benchmark_path(out_dir, RESULTS_NAME)
    _write_csv(
        results_path,
        results,
        [
            'transaction_id', 'county', 'method', 'status', 'page_count',
            'start_page', 'end_page', 'start_marker', 'end_marker',
            'candidate_legal_desc', 'candidate_chars', 'pdf_path', 'ocr_dir',
            'matched_document_id', 'note',
        ],
    )
    return results_path


def run_anthropic_benchmark(
    manifest_path: Path,
    gold_path: Path,
    out_dir: Path,
    *,
    mode: str,
    model: str,
    force: bool = False,
) -> Path:
    rows = _read_csv(manifest_path)
    gold_notes = _load_gold_notes(gold_path)
    results_name = f'results_anthropic_{mode}.csv'
    results_path = _benchmark_path(out_dir, results_name)
    existing_results = _load_existing_results_by_transaction(results_path)
    results = []

    for row in rows:
        transaction_id = str(row.get('transaction_id') or '').strip()
        county = str(row.get('county') or '').strip()
        artifacts_dir = out_dir / 'artifacts' / transaction_id
        pdf_path = artifacts_dir / 'source_document.pdf'
        target_hint = gold_notes.get(transaction_id, '')
        existing_row = existing_results.get(transaction_id)

        if not force and _should_reuse_existing_result(existing_row, model=model, target_hint=target_hint):
            results.append(_mark_cache_hit(existing_row))
            continue

        result = {
            'transaction_id': transaction_id,
            'county': county,
            'method': f'anthropic_{mode}',
            'model': model,
            'status': 'unsupported_county',
            'target_hint': target_hint,
            'cache_hit': 'False',
            'candidate_legal_desc': '',
            'candidate_chars': '',
            'input_tokens': '',
            'output_tokens': '',
            'estimated_cost_usd': '',
            'selected_mode': mode,
            'pdf_path': str(pdf_path),
            'note': '',
        }

        try:
            if county != 'Bay':
                result['note'] = 'Only Bay deed PDF fetching is implemented in this benchmark harness.'
                results.append(result)
                continue

            if not pdf_path.exists():
                fetch_result = _fetch_bay_pdf_artifacts(row, artifacts_dir)
                pdf_bytes = fetch_result['pdf_bytes']
            else:
                pdf_bytes = pdf_path.read_bytes()

            page_texts = _load_page_texts(artifacts_dir)
            if not page_texts:
                page_texts = _ocr_pdf_pages(pdf_bytes, artifacts_dir)

            if mode == 'text':
                extraction = _run_anthropic_text_extraction(model, page_texts, target_hint)
                validation = validate_legal_candidate(extraction.get('candidate_legal_desc'), page_texts, target_hint)
                result.update(_validation_fields('text', validation))
            elif mode == 'vision':
                extraction = _run_anthropic_vision_extraction(model, pdf_bytes, target_hint)
                validation = validate_legal_candidate(extraction.get('candidate_legal_desc'), page_texts, target_hint)
                result.update(_validation_fields('vision', validation))
            elif mode == 'hybrid':
                vision_extraction = None
                text_extraction = _run_anthropic_text_extraction(model, page_texts, target_hint)
                text_validation = validate_legal_candidate(text_extraction.get('candidate_legal_desc'), page_texts, target_hint)
                result.update(_validation_fields('text', text_validation))
                result.update({
                    'text_candidate_legal_desc': text_extraction.get('candidate_legal_desc') or '',
                    'text_candidate_chars': len(text_extraction.get('candidate_legal_desc') or ''),
                    'text_input_tokens': text_extraction.get('input_tokens') or '',
                    'text_output_tokens': text_extraction.get('output_tokens') or '',
                    'text_estimated_cost_usd': text_extraction.get('estimated_cost_usd') or '',
                })

                if text_validation.get('passed'):
                    extraction = text_extraction
                    validation = text_validation
                    selected_mode = 'text'
                    vision_extraction = None
                    vision_validation = None
                else:
                    vision_extraction = _run_anthropic_vision_extraction(model, pdf_bytes, target_hint)
                    vision_validation = validate_legal_candidate(vision_extraction.get('candidate_legal_desc'), page_texts, target_hint)
                    result.update(_validation_fields('vision', vision_validation))
                    result.update({
                        'vision_candidate_legal_desc': vision_extraction.get('candidate_legal_desc') or '',
                        'vision_candidate_chars': len(vision_extraction.get('candidate_legal_desc') or ''),
                        'vision_input_tokens': vision_extraction.get('input_tokens') or '',
                        'vision_output_tokens': vision_extraction.get('output_tokens') or '',
                        'vision_estimated_cost_usd': vision_extraction.get('estimated_cost_usd') or '',
                    })

                    if vision_validation.get('passed') or not (text_extraction.get('candidate_legal_desc') or '').strip():
                        extraction = vision_extraction
                        validation = vision_validation
                        selected_mode = 'vision'
                    else:
                        extraction = text_extraction
                        validation = text_validation
                        selected_mode = 'text'

                total_cost = sum(
                    value
                    for value in [
                        text_extraction.get('estimated_cost_usd'),
                        (vision_extraction or {}).get('estimated_cost_usd') if vision_extraction else None,
                    ]
                    if value is not None
                )
                result['estimated_cost_usd'] = round(total_cost, 6) if total_cost else ''
                result['selected_mode'] = selected_mode
                result['note'] = (
                    'Selected OCR-text extraction after validation.'
                    if selected_mode == 'text' and text_validation.get('passed')
                    else 'Text extraction failed validation; evaluated vision fallback.'
                )
            else:
                raise ValueError(f'Unsupported anthropic benchmark mode: {mode}')

            candidate = extraction.get('candidate_legal_desc') or ''
            result.update({
                'status': 'ok' if candidate else 'not_found',
                'candidate_legal_desc': candidate,
                'candidate_chars': len(candidate),
                'input_tokens': extraction.get('input_tokens') or '',
                'output_tokens': extraction.get('output_tokens') or '',
                'estimated_cost_usd': result.get('estimated_cost_usd') or extraction.get('estimated_cost_usd') or '',
            })
            if mode != 'hybrid':
                result['selected_mode'] = mode
                if not validation.get('passed'):
                    reason_text = ' | '.join(validation.get('reasons') or [])
                    result['note'] = f'Validation warning: {reason_text}' if reason_text else result['note']
        except Exception as exc:  # noqa: BLE001
            result['status'] = 'error'
            result['note'] = f'{type(exc).__name__}: {exc}'

        results.append(result)

    fieldnames = [
        'transaction_id', 'county', 'method', 'model', 'status', 'target_hint',
        'cache_hit', 'selected_mode', 'candidate_legal_desc', 'candidate_chars', 'input_tokens',
        'output_tokens', 'estimated_cost_usd', 'pdf_path', 'note',
    ]
    if mode == 'hybrid':
        fieldnames.extend([
            'text_candidate_legal_desc', 'text_candidate_chars', 'text_input_tokens',
            'text_output_tokens', 'text_estimated_cost_usd',
            'text_validation_passed', 'text_validation_reasons',
            'text_validation_similarity_ratio', 'text_validation_target_parcel',
            'text_validation_candidate_parcels', 'text_validation_candidate_bearings',
            'text_validation_candidate_distances',
            'vision_candidate_legal_desc', 'vision_candidate_chars', 'vision_input_tokens',
            'vision_output_tokens', 'vision_estimated_cost_usd',
            'vision_validation_passed', 'vision_validation_reasons',
            'vision_validation_similarity_ratio', 'vision_validation_target_parcel',
            'vision_validation_candidate_parcels', 'vision_validation_candidate_bearings',
            'vision_validation_candidate_distances',
        ])
    else:
        fieldnames.extend([
            f'{mode}_validation_passed', f'{mode}_validation_reasons',
            f'{mode}_validation_similarity_ratio', f'{mode}_validation_target_parcel',
            f'{mode}_validation_candidate_parcels', f'{mode}_validation_candidate_bearings',
            f'{mode}_validation_candidate_distances',
        ])
    _write_csv(results_path, results, fieldnames)
    return results_path


def compare_benchmark(results_path: Path, gold_path: Path, out_dir: Path) -> tuple[Path, dict]:
    results = _read_csv(results_path)
    gold_rows = _read_csv(gold_path)
    gold_by_id = {
        str(row.get('transaction_id') or '').strip(): row
        for row in gold_rows
        if str(row.get('transaction_id') or '').strip()
    }

    comparison_rows = []
    summary = {
        'rows_compared': 0,
        'normalized_exact': 0,
        'average_similarity_ratio': None,
    }
    similarity_values: list[float] = []

    for result in results:
        transaction_id = str(result.get('transaction_id') or '').strip()
        gold_row = gold_by_id.get(transaction_id)
        gold_legal_desc = (gold_row or {}).get('gold_legal_desc') or ''
        if not gold_legal_desc.strip():
            continue

        metrics = compare_legal_texts(result.get('candidate_legal_desc'), gold_legal_desc)
        comparison_rows.append({
            'transaction_id': transaction_id,
            'county': result.get('county'),
            'method': result.get('method'),
            'status': result.get('status'),
            'normalized_exact': metrics['normalized_exact'],
            'similarity_ratio': metrics['similarity_ratio'],
            'candidate_chars': metrics['candidate_chars'],
            'gold_chars': metrics['gold_chars'],
            'candidate_legal_desc': result.get('candidate_legal_desc') or '',
            'gold_legal_desc': gold_legal_desc,
            'candidate_normalized': metrics['candidate_normalized'],
            'gold_normalized': metrics['gold_normalized'],
            'notes': (gold_row or {}).get('notes') or '',
        })
        summary['rows_compared'] += 1
        if metrics['normalized_exact']:
            summary['normalized_exact'] += 1
        if metrics['similarity_ratio'] is not None:
            similarity_values.append(metrics['similarity_ratio'])

    if similarity_values:
        summary['average_similarity_ratio'] = round(sum(similarity_values) / len(similarity_values), 4)

    comparison_path = _benchmark_path(out_dir, COMPARISON_NAME)
    _write_csv(
        comparison_path,
        comparison_rows,
        [
            'transaction_id', 'county', 'method', 'status', 'normalized_exact',
            'similarity_ratio', 'candidate_chars', 'gold_chars',
            'candidate_legal_desc', 'gold_legal_desc',
            'candidate_normalized', 'gold_normalized', 'notes',
        ],
    )
    (out_dir / 'comparison_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return comparison_path, summary


def main() -> None:
    parser = argparse.ArgumentParser(description='Benchmark raw-land deed legal extraction')
    parser.add_argument('--out-dir', default=str(DEFAULT_BENCHMARK_DIR), help='Benchmark artifact directory')
    subparsers = parser.add_subparsers(dest='command', required=True)

    prepare_parser = subparsers.add_parser('prepare', help='Create a benchmark manifest and gold template')
    prepare_parser.add_argument('--county', default='Bay', help='County to sample from')
    prepare_parser.add_argument('--limit', type=int, default=4, help='Number of raw-land transactions to include')

    run_parser = subparsers.add_parser('run', help='Fetch deed PDFs, OCR them, and extract legal candidates')
    run_parser.add_argument('--manifest', help='Path to manifest CSV (defaults to out-dir/manifest.csv)')

    anthropic_parser = subparsers.add_parser('run-anthropic', help='Run Anthropic extraction against the benchmark set')
    anthropic_parser.add_argument('--manifest', help='Path to manifest CSV (defaults to out-dir/manifest.csv)')
    anthropic_parser.add_argument('--gold', help='Path to gold CSV for target hints (defaults to out-dir/gold_transcriptions.csv)')
    anthropic_parser.add_argument('--mode', choices=['text', 'vision', 'hybrid'], default='vision', help='Anthropic benchmark mode')
    anthropic_parser.add_argument('--model', default='claude-opus-4-6', help='Anthropic model id')
    anthropic_parser.add_argument('--force', action='store_true', help='Re-run model extraction even if a cached result already exists')

    compare_parser = subparsers.add_parser('compare', help='Compare extracted candidates against gold transcriptions')
    compare_parser.add_argument('--results', help='Path to results CSV (defaults to out-dir/results.csv)')
    compare_parser.add_argument('--gold', help='Path to gold transcription CSV (defaults to out-dir/gold_transcriptions.csv)')

    args = parser.parse_args()
    out_dir = Path(args.out_dir)

    if args.command == 'prepare':
        rows = fetch_raw_land_candidates(county=args.county, limit=args.limit)
        manifest_path, gold_path = write_manifest(rows, out_dir)
        print(f'Prepared {len(rows)} benchmark rows -> {manifest_path}')
        print(f'Gold transcription template -> {gold_path}')
        return

    if args.command == 'run':
        manifest_path = Path(args.manifest) if args.manifest else _benchmark_path(out_dir, MANIFEST_NAME)
        results_path = run_benchmark(manifest_path, out_dir)
        print(f'Wrote benchmark OCR/extraction results -> {results_path}')
        return

    if args.command == 'run-anthropic':
        manifest_path = Path(args.manifest) if args.manifest else _benchmark_path(out_dir, MANIFEST_NAME)
        gold_path = Path(args.gold) if args.gold else _benchmark_path(out_dir, GOLD_NAME)
        results_path = run_anthropic_benchmark(
            manifest_path,
            gold_path,
            out_dir,
            mode=args.mode,
            model=args.model,
            force=args.force,
        )
        print(f'Wrote Anthropic benchmark results -> {results_path}')
        return

    if args.command == 'compare':
        results_path = Path(args.results) if args.results else _benchmark_path(out_dir, RESULTS_NAME)
        gold_path = Path(args.gold) if args.gold else _benchmark_path(out_dir, GOLD_NAME)
        comparison_path, summary = compare_benchmark(results_path, gold_path, out_dir)
        print(f'Wrote comparison results -> {comparison_path}')
        print(json.dumps(summary, indent=2))
        return


if __name__ == '__main__':
    main()
