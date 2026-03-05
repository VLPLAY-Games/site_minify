import os
import htmlmin
import re
import json
from pathlib import Path

def minify_css(css_text):
    """Minify CSS"""
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
    css_text = re.sub(r'\s+', ' ', css_text)
    css_text = re.sub(r'\s*([{}:;,])\s*', r'\1', css_text)
    css_text = re.sub(r';}', '}', css_text)
    css_text = re.sub(r':\s+', ':', css_text)
    return css_text.strip()

def minify_js(js_text):
    """Minify JavaScript"""
    js_text = re.sub(r'//.*', '', js_text)
    js_text = re.sub(r'/\*.*?\*/', '', js_text, flags=re.DOTALL)
    js_text = re.sub(r'\s+', ' ', js_text)
    js_text = re.sub(r'\s*([=+\-*/%&|^<>!?:;,{}()])\s*', r'\1', js_text)
    return js_text.strip()

def minify_json(json_text):
    """Minify JSON by removing whitespace while preserving Unicode characters"""
    try:
        # Parse JSON to validate it
        json_data = json.loads(json_text)
        # Dump without whitespace, but ensure Unicode characters are preserved
        return json.dumps(json_data, separators=(',', ':'), ensure_ascii=False)
    except json.JSONDecodeError as e:
        # If JSON is invalid, return original text
        raise Exception(f"Invalid JSON: {e}")

def aggressive_minify(html_content):
    """Aggressive HTML minification (inline styles/scripts + comments)"""
    def minify_style_tags(match):
        css_content = match.group(1)
        return f'<style>{minify_css(css_content)}</style>'
    
    html_content = re.sub(r'<style[^>]*>(.*?)</style>', minify_style_tags, html_content, flags=re.DOTALL | re.IGNORECASE)
    
    def minify_script_tags(match):
        if match.group(1):
            js_content = match.group(1)
            return f'<script>{minify_js(js_content)}</script>'
        return match.group(0)
    
    html_content = re.sub(r'<script[^>]*>(.*?)</script>', minify_script_tags, html_content, flags=re.DOTALL | re.IGNORECASE)
    
    html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'>\s+<', '><', html_content)
    html_content = re.sub(r'\n\s+', ' ', html_content)
    html_content = re.sub(r' +', ' ', html_content)
    html_content = html_content.replace('\n', '').replace('\t', '').replace('\r', '')
    html_content = re.sub(r'\s+([a-zA-Z-]+)=', r' \1=', html_content)
    
    return html_content

def minify_html_file(file_path, output_dir=None):
    """Minify a single HTML file. Returns (success, message, original_size, new_size)"""
    try:
        original_size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # First pass: aggressive custom minification
        minified = aggressive_minify(html_content)
        
        # Second pass: htmlmin library
        minified = htmlmin.minify(
            minified,
            remove_comments=True,
            remove_empty_space=True,
            remove_all_empty_space=True,
            reduce_empty_attributes=True,
            reduce_boolean_attributes=True,
            remove_optional_attribute_quotes=True
        )
        
        if output_dir:
            output_path = output_dir / file_path.name
            output_dir.mkdir(exist_ok=True)
        else:
            output_path = file_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        new_size = os.path.getsize(output_path)
        return True, f"HTML processed: {file_path.name}", original_size, new_size
        
    except Exception as e:
        return False, f"Error processing HTML {file_path.name}: {e}", 0, 0

def minify_css_file(file_path, output_dir=None):
    """Minify a single CSS file. Returns (success, message, original_size, new_size)"""
    try:
        original_size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        minified = minify_css(css_content)
        
        if output_dir:
            output_path = output_dir / file_path.name
            output_dir.mkdir(exist_ok=True)
        else:
            output_path = file_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        new_size = os.path.getsize(output_path)
        return True, f"CSS processed:  {file_path.name}", original_size, new_size
        
    except Exception as e:
        return False, f"Error processing CSS {file_path.name}: {e}", 0, 0

def minify_js_file(file_path, output_dir=None):
    """Minify a single JavaScript file. Returns (success, message, original_size, new_size)"""
    try:
        original_size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        minified = minify_js(js_content)
        
        if output_dir:
            output_path = output_dir / file_path.name
            output_dir.mkdir(exist_ok=True)
        else:
            output_path = file_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        new_size = os.path.getsize(output_path)
        return True, f"JS processed:   {file_path.name}", original_size, new_size
        
    except Exception as e:
        return False, f"Error processing JS {file_path.name}: {e}", 0, 0

def minify_json_file(file_path, output_dir=None):
    """Minify a single JSON file. Returns (success, message, original_size, new_size)"""
    try:
        original_size = os.path.getsize(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            json_content = f.read()
        
        minified = minify_json(json_content)
        
        if output_dir:
            output_path = output_dir / file_path.name
            output_dir.mkdir(exist_ok=True)
        else:
            output_path = file_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        new_size = os.path.getsize(output_path)
        return True, f"JSON processed: {file_path.name}", original_size, new_size
        
    except Exception as e:
        return False, f"Error processing JSON {file_path.name}: {e}", 0, 0

def main():
    data_dir = Path(".")
    output_dir = data_dir  # same directory (overwrite)
    
    # Collect files by extension
    html_files = list(data_dir.glob("*.html"))
    css_files  = list(data_dir.glob("*.css"))
    js_files   = list(data_dir.glob("*.js"))
    json_files = list(data_dir.glob("*.json"))
    
    total_files = len(html_files) + len(css_files) + len(js_files) + len(json_files)
    if total_files == 0:
        print("No .html, .css, .js or .json files found in current directory")
        return
    
    print("Starting minification...")
    print("-" * 60)
    
    results = []  # list of (success, message, original_size, new_size)
    
    # Process HTML files
    for file_path in html_files:
        results.append(minify_html_file(file_path, output_dir))
    
    # Process CSS files
    for file_path in css_files:
        results.append(minify_css_file(file_path, output_dir))
    
    # Process JS files
    for file_path in js_files:
        results.append(minify_js_file(file_path, output_dir))
    
    # Process JSON files
    for file_path in json_files:
        results.append(minify_json_file(file_path, output_dir))
    
    # Print individual results
    for success, message, orig, new in results:
        print(message)
    
    print("-" * 60)
    
    successful = sum(1 for success, _, _, _ in results if success)
    failed = len(results) - successful
    
    # Calculate total original and new size for successful files
    total_orig = sum(orig for success, _, orig, _ in results if success)
    total_new = sum(new for success, _, _, new in results if success)
    
    print(f"\nSummary:")
    print(f"  Total files processed: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    
    if successful > 0:
        print(f"\nMinified files saved in: {output_dir}")
        print("\nDetailed size information (successful files only):")
        print(f"{'File':<30} {'Original':>12} {'New':>12} {'Change':>12} {'%':>8}")
        print("-" * 80)

        details = []
        idx = 0
        all_files = html_files + css_files + js_files + json_files
        for file_path in all_files:
            if idx < len(results) and results[idx][0]:  # success
                success, msg, orig, new = results[idx]
                name = file_path.name
                change = new - orig
                percent = (change / orig) * 100 if orig != 0 else 0
                details.append((name, orig, new, change, percent))
            idx += 1
        
        # Sort details by filename for consistent output
        details.sort(key=lambda x: x[0])
        
        for name, orig, new, change, percent in details:
            print(f"{name:<30} {orig:>12,} {new:>12,} {change:>12,} {percent:>7.1f}%")
        
        print("-" * 80)
        total_change = total_new - total_orig
        total_percent = (total_change / total_orig) * 100 if total_orig != 0 else 0
        print(f"{'TOTAL':<30} {total_orig:>12,} {total_new:>12,} {total_change:>12,} {total_percent:>7.1f}%")

if __name__ == "__main__":
    main()