#!/usr/bin/env python3
"""
Universal minifier for HTML, CSS, JS and JSON files.
Requires: pip install htmlmin jsmin cssmin
"""

import os
import re
import json
import argparse
import fnmatch
from pathlib import Path
from collections import defaultdict

import htmlmin
from jsmin import jsmin
from cssmin import cssmin


def minify_css(css_text):
    """Minify CSS using cssmin."""
    return cssmin(css_text)


def minify_js(js_text, aggressive=False):
    """
    Minify JavaScript using jsmin.
    If aggressive=True, additionally collapses all whitespace (including newlines)
    into a single space. Warning: this may break code that relies on line breaks
    (e.g., after return, in template strings, or regex with comments). Use with caution.
    """
    minified = jsmin(js_text)
    if aggressive:
        # Collapse all whitespace sequences to a single space
        minified = re.sub(r'\s+', ' ', minified)
        # Remove spaces around operators and punctuation to save more bytes
        minified = re.sub(r'\s*([=+\-*/%&|^<>!?:;,{}()])\s*', r'\1', minified)
    return minified.strip()


def minify_json(json_text):
    """Minify JSON by removing unnecessary whitespace."""
    try:
        data = json.loads(json_text)
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def minify_html(html_text):
    """Minify HTML using htmlmin with aggressive settings."""
    # First, inline style/script minification
    def minify_style(match):
        return f"<style>{minify_css(match.group(1))}</style>"

    def minify_script(match):
        return f"<script>{minify_js(match.group(1))}</script>"

    html_text = re.sub(r'<style[^>]*>(.*?)</style>', minify_style, html_text,
                       flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r'<script[^>]*>(.*?)</script>', minify_script, html_text,
                       flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML comments
    html_text = re.sub(r'<!--.*?-->', '', html_text, flags=re.DOTALL)

    # Use htmlmin for final compression
    return htmlmin.minify(
        html_text,
        remove_comments=True,
        remove_empty_space=True,
        remove_all_empty_space=True,
        reduce_empty_attributes=True,
        reduce_boolean_attributes=True,
        remove_optional_attribute_quotes=True,
        keep_pre=False
    )


def process_file(file_path, output_path, in_place=False, backup=False, aggressive_js=False):
    """
    Minify a single file based on its extension.
    Returns (success, message, original_size, new_size, file_type)
    """
    ext = file_path.suffix.lower()
    try:
        original_size = file_path.stat().st_size
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Choose minifier based on extension
        if ext in ('.html', '.htm'):
            minified = minify_html(content)
            file_type = 'HTML'
        elif ext == '.css':
            minified = minify_css(content)
            file_type = 'CSS'
        elif ext == '.js':
            minified = minify_js(content, aggressive=aggressive_js)
            file_type = 'JS'
        elif ext == '.json':
            minified = minify_json(content)
            file_type = 'JSON'
        else:
            return False, f"Skipped (unsupported extension): {file_path.name}", 0, 0, None

        # Determine output path
        if in_place:
            out = file_path
        else:
            out = output_path
            out.parent.mkdir(parents=True, exist_ok=True)

        # Write minified content
        with open(out, 'w', encoding='utf-8') as f:
            f.write(minified)

        new_size = out.stat().st_size
        return True, f"{file_type} processed: {file_path.name}", original_size, new_size, file_type

    except Exception as e:
        return False, f"Error processing {file_path.name}: {e}", 0, 0, None


def should_ignore(rel_path, exclude_patterns):
    """Check if relative path matches any exclude pattern."""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(str(rel_path), pattern) or fnmatch.fnmatch(rel_path.name, pattern):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description='Minify HTML, CSS, JS and JSON files with advanced options.'
    )
    parser.add_argument('input_dir', nargs='?', default='.',
                        help='Input directory (default: current directory)')
    parser.add_argument('output_dir', nargs='?',
                        help='Output directory (default: same as input if not in-place)')
    parser.add_argument('-r', '--recursive', action='store_true',
                        help='Process subdirectories recursively')
    parser.add_argument('--in-place', action='store_true',
                        help='Minify files directly, overwriting originals')
    parser.add_argument('--backup', action='store_true',
                        help='Create .bak backup before in-place minification')
    parser.add_argument('--ext', nargs='+', default=['.html', '.htm', '.css', '.js', '.json'],
                        help='File extensions to process (default: .html .htm .css .js .json)')
    parser.add_argument('--exclude', nargs='*', default=[],
                        help='Exclude files/directories matching these glob patterns')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed processing messages')
    parser.add_argument('--stats', action='store_true',
                        help='Show statistics by file type')
    parser.add_argument('--aggressive-js', action='store_true',
                        help='Aggressively minify JavaScript by removing all newlines (may break code!)')

    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    if not input_dir.is_dir():
        print(f"Error: '{input_dir}' is not a valid directory.")
        return

    # Normalize extensions (add leading dot if missing)
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.ext]

    # Prepare output directory
    if args.in_place:
        output_dir = input_dir
    else:
        output_dir = Path(args.output_dir).resolve() if args.output_dir else input_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    # Collect files
    if args.recursive:
        all_files = list(input_dir.rglob('*'))
    else:
        all_files = list(input_dir.glob('*'))

    # Filter by extension
    files_to_process = [f for f in all_files if f.is_file() and f.suffix.lower() in extensions]

    if not files_to_process:
        print("No matching files found.")
        return

    print(f"Found {len(files_to_process)} file(s) to process.\n")

    # Process files
    results = []  # (file_path, success, message, orig, new, file_type)
    total_orig = 0
    total_new = 0

    for file_path in files_to_process:
        # Compute relative path for exclusion check
        try:
            rel_path = file_path.relative_to(input_dir)
        except ValueError:
            # File not under input_dir (shouldn't happen with rglob)
            continue

        if should_ignore(rel_path, args.exclude):
            if args.verbose:
                print(f"Ignored (excluded): {rel_path}")
            continue

        # Prepare output path (preserve subdirectory structure if recursive)
        if args.recursive and not args.in_place:
            out_path = output_dir / rel_path
        else:
            out_path = output_dir / file_path.name

        # Backup if requested
        if args.in_place and args.backup and file_path.exists():
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            if not backup_path.exists():  # avoid overwriting existing backup
                import shutil
                shutil.copy2(file_path, backup_path)
                if args.verbose:
                    print(f"Backup created: {backup_path.name}")

        success, msg, orig, new, ftype = process_file(
            file_path, out_path, in_place=args.in_place, aggressive_js=args.aggressive_js
        )
        results.append((rel_path if args.recursive else file_path.name, success, msg, orig, new, ftype))

        if args.verbose or not success:
            print(msg)
        if success:
            total_orig += orig
            total_new += new

    # Summary
    print("\n" + "=" * 70)
    successful = sum(1 for _, s, _, _, _, _ in results if s)
    failed = len(results) - successful
    print(f"Total files processed: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")

    if successful == 0:
        return

    print(f"\nMinified files saved in: {output_dir if not args.in_place else '(in-place)'}")

    if args.stats:
        # Statistics by file type
        stats = defaultdict(lambda: {'orig': 0, 'new': 0, 'count': 0})
        for _, success, _, orig, new, ftype in results:
            if success and ftype:
                stats[ftype]['orig'] += orig
                stats[ftype]['new'] += new
                stats[ftype]['count'] += 1

        print("\nStatistics by type:")
        print(f"{'Type':<10} {'Count':>6} {'Original (B)':>15} {'New (B)':>15} {'Saved (B)':>12} {'%':>8}")
        print("-" * 80)
        for ftype in sorted(stats.keys()):
            o = stats[ftype]['orig']
            n = stats[ftype]['new']
            cnt = stats[ftype]['count']
            saved = o - n
            pct = (saved / o * 100) if o else 0
            print(f"{ftype:<10} {cnt:>6} {o:>15,} {n:>15,} {saved:>12,} {pct:>7.1f}%")
        print("-" * 80)

    # Detailed file list
    print("\nDetailed per-file results:")
    print(f"{'File':<50} {'Original':>12} {'New':>12} {'Change':>12} {'%':>8}")
    print("-" * 100)

    # Sort results by file name
    sorted_results = sorted(results, key=lambda x: x[0])
    for name, success, _, orig, new, _ in sorted_results:
        if success:
            change = new - orig
            pct = (change / orig * 100) if orig else 0
            print(f"{str(name)[:50]:<50} {orig:>12,} {new:>12,} {change:>12,} {pct:>7.1f}%")

    # Totals
    total_change = total_new - total_orig
    total_pct = (total_change / total_orig * 100) if total_orig else 0
    print("-" * 100)
    print(f"{'TOTAL':<50} {total_orig:>12,} {total_new:>12,} {total_change:>12,} {total_pct:>7.1f}%")


if __name__ == "__main__":
    main()