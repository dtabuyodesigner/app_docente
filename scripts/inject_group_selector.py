import os
import glob
import re

# We want to inject into almost all HTML files in static/
html_files = glob.glob('static/*.html')

header_html = """
        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;" class="injected-group-selector">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: white; padding: 6px 12px; border-radius: 8px; border: 1px solid #ddd; display: flex; align-items: center; gap: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <span style="font-size: 1.1rem;">📚</span>
                    <select id="globalGroupSelect" onchange="changeActiveGroup(this.value)" style="border:none; background:transparent; font-weight:600; font-size:0.9rem; color:var(--primary, #003366); cursor:pointer; outline:none; width:140px; margin:0; padding:2px 5px; text-overflow:ellipsis;">
                        <option value="">Cargando grupos...</option>
                    </select>
                </div>
            </div>
        </div>
"""

script_tag = '\n    <script src="/static/js/global_groups.js"></script>'

for filepath in html_files:
    # Skip login and already "featured" ones if needed, but we check for duplicates anyway
    if filepath == 'static/login.html':
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    modified = False

    # 1. Inject Header HTML if missing
    if "globalGroupSelect" not in content:
        # Preferred: right after <div class="nav">...</div>
        nav_match = re.search(r'<div[^>]*class="nav"[^>]*>.*?</div>', content, re.DOTALL)
        if nav_match:
            pos = nav_match.end()
            content = content[:pos] + header_html + content[pos:]
            modified = True
            print(f"Injected header into {filepath}")
        else:
            # Fallback: After <div class="container">
            container_match = re.search(r'<div[^>]*class="container"[^>]*>', content)
            if container_match:
                pos = container_match.end()
                content = content[:pos] + header_html + content[pos:]
                modified = True
                print(f"Injected header into {filepath}")
            else:
                # Last resort: after <body>
                body_match = re.search(r'<body[^>]*>', content)
                if body_match:
                    pos = body_match.end()
                    content = content[:pos] + header_html + content[pos:]
                    modified = True
                    print(f"Injected header into {filepath}")

    # 2. Inject Script Tag if missing
    if "global_groups.js" not in content:
        if "</body>" in content:
            content = content.replace('</body>', script_tag + '\n</body>')
            modified = True
            print(f"Injected script into {filepath}")
        else:
            print(f"Could not find </body> in {filepath}")

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

