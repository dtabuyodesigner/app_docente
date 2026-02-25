import os
import glob
import re

html_files = glob.glob('static/*.html')

header_html = """
        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background: white; padding: 6px 12px; border-radius: 8px; border: 1px solid #ddd; display: flex; align-items: center; gap: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <span style="font-size: 1.1rem;">📚</span>
                    <select id="globalGroupSelect" onchange="changeActiveGroup(this.value)" style="border: none; background: transparent; font-weight: 600; font-size: 0.9rem; color: #003366; cursor: pointer; outline: none;">
                        <option value="">Cargando grupos...</option>
                    </select>
                </div>
            </div>
        </div>
"""

script_tag = '\n    <script src="/static/js/global_groups.js"></script>\n</body>'

for filepath in html_files:
    # Skip the ones we already modified manually:
    if filepath in ['static/index.html', 'static/alumnos.html', 'static/asistencia.html', 'static/evaluacion.html']:
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the nav block ending
    nav_end = content.find('</div>', content.find('class="nav"')) + 6
    if nav_end > 5: # Found nav block
        # Check if already injected
        if "globalGroupSelect" not in content:
            # Inject header right after nav
            content = content[:nav_end] + header_html + content[nav_end:]
            
            # Inject script tag before </body>
            content = content.replace('</body>', script_tag)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Injected into {filepath}")

