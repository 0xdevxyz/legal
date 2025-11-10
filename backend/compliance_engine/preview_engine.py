"""
Complyo Preview Engine
Generates preview for fixes before deployment
"""

import os
import tempfile
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import difflib
from datetime import datetime
import base64
import logging

logger = logging.getLogger(__name__)


@dataclass
class PreviewResult:
    """Result of a preview generation"""
    preview_id: str
    preview_url: str
    original_html: str
    modified_html: str
    diff_unified: str
    diff_html: str
    changes_summary: Dict[str, int]
    created_at: str


class PreviewEngine:
    """
    Preview Engine for Compliance Fixes
    
    Features:
    - Side-by-side comparison
    - Unified diff view
    - HTML diff with syntax highlighting
    - Temporary preview file generation
    - Change statistics
    """
    
    def __init__(self, temp_dir: str = None):
        """
        Initialize Preview Engine
        
        Args:
            temp_dir: Directory for temporary preview files
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.preview_dir = os.path.join(self.temp_dir, 'complyo_previews')
        
        # Create preview directory if it doesn't exist
        os.makedirs(self.preview_dir, exist_ok=True)
    
    async def generate_preview(
        self,
        original_content: str,
        fix_content: str,
        fix_type: str,
        fix_id: str
    ) -> PreviewResult:
        """
        Generate preview for a fix
        
        Args:
            original_content: Original code/content
            fix_content: Fixed code/content
            fix_type: Type of fix ('html', 'css', 'javascript', etc.)
            fix_id: Unique fix ID
            
        Returns:
            PreviewResult with preview URL and diff information
        """
        try:
            # Generate preview ID
            preview_id = self._generate_preview_id(fix_id)
            
            # Generate diffs
            diff_unified = self._generate_unified_diff(
                original_content, 
                fix_content, 
                fix_type
            )
            
            diff_html = self._generate_html_diff(
                original_content,
                fix_content,
                fix_type
            )
            
            # Calculate change statistics
            changes = self._calculate_changes(original_content, fix_content)
            
            # Generate preview HTML file
            preview_html = self._generate_preview_html(
                original_content,
                fix_content,
                diff_html,
                fix_type,
                changes
            )
            
            # Save preview file
            preview_filename = f"{preview_id}.html"
            preview_path = os.path.join(self.preview_dir, preview_filename)
            
            with open(preview_path, 'w', encoding='utf-8') as f:
                f.write(preview_html)
            
            # Generate preview URL (in production, this would be a proper URL)
            preview_url = f"/api/v2/previews/{preview_id}"
            
            logger.info(f"✅ Preview generated: {preview_id}")
            
            return PreviewResult(
                preview_id=preview_id,
                preview_url=preview_url,
                original_html=original_content,
                modified_html=fix_content,
                diff_unified=diff_unified,
                diff_html=diff_html,
                changes_summary=changes,
                created_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Preview generation failed: {e}")
            raise
    
    def _generate_preview_id(self, fix_id: str) -> str:
        """Generate unique preview ID"""
        timestamp = datetime.now().isoformat()
        content = f"{fix_id}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_unified_diff(
        self,
        original: str,
        modified: str,
        filename: str
    ) -> str:
        """
        Generate unified diff (like git diff)
        
        Args:
            original: Original content
            modified: Modified content
            filename: Filename for diff header
            
        Returns:
            Unified diff string
        """
        original_lines = original.splitlines(keepends=True)
        modified_lines = modified.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    def _generate_html_diff(
        self,
        original: str,
        modified: str,
        fix_type: str
    ) -> str:
        """
        Generate HTML diff with syntax highlighting
        
        Args:
            original: Original content
            modified: Modified content
            fix_type: Type of content for highlighting
            
        Returns:
            HTML string with diff
        """
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        # Use difflib HtmlDiff
        differ = difflib.HtmlDiff(wrapcolumn=80)
        html_diff = differ.make_table(
            original_lines,
            modified_lines,
            fromdesc='Original',
            todesc='Mit Complyo-Fix',
            context=True,
            numlines=3
        )
        
        return html_diff
    
    def _calculate_changes(
        self,
        original: str,
        modified: str
    ) -> Dict[str, int]:
        """
        Calculate change statistics
        
        Returns:
            Dict with additions, deletions, changes
        """
        original_lines = original.splitlines()
        modified_lines = modified.splitlines()
        
        differ = difflib.Differ()
        diff = list(differ.compare(original_lines, modified_lines))
        
        additions = sum(1 for line in diff if line.startswith('+ '))
        deletions = sum(1 for line in diff if line.startswith('- '))
        
        return {
            'additions': additions,
            'deletions': deletions,
            'changes': additions + deletions,
            'original_lines': len(original_lines),
            'modified_lines': len(modified_lines)
        }
    
    def _generate_preview_html(
        self,
        original: str,
        modified: str,
        diff_html: str,
        fix_type: str,
        changes: Dict[str, int]
    ) -> str:
        """
        Generate complete preview HTML page
        
        Returns:
            Complete HTML page with side-by-side comparison
        """
        # Escape HTML for display
        original_escaped = self._escape_html(original)
        modified_escaped = self._escape_html(modified)
        
        html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complyo Preview - {fix_type}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f3f4f6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 24px;
            color: #1f2937;
            margin-bottom: 10px;
        }}
        
        .stats {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
        }}
        
        .stat {{
            padding: 10px 15px;
            background: #f9fafb;
            border-radius: 6px;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #6b7280;
            text-transform: uppercase;
        }}
        
        .stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #1f2937;
        }}
        
        .stat.additions .stat-value {{
            color: #10b981;
        }}
        
        .stat.deletions .stat-value {{
            color: #ef4444;
        }}
        
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .tab {{
            padding: 12px 24px;
            background: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            color: #6b7280;
            transition: all 0.2s;
        }}
        
        .tab:hover {{
            background: #f3f4f6;
        }}
        
        .tab.active {{
            background: #3b82f6;
            color: white;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .comparison {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        .pane {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .pane-header {{
            background: #1f2937;
            color: white;
            padding: 12px 20px;
            font-weight: 600;
        }}
        
        .pane-header.original {{
            background: #ef4444;
        }}
        
        .pane-header.modified {{
            background: #10b981;
        }}
        
        .pane-content {{
            padding: 20px;
            max-height: 600px;
            overflow-y: auto;
        }}
        
        pre {{
            margin: 0;
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .diff-view {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        
        /* Diff styling */
        table.diff {{
            font-family: 'Monaco', 'Menlo', 'Courier New', monospace;
            font-size: 12px;
            border: none;
            width: 100%;
        }}
        
        table.diff td {{
            padding: 2px 10px;
            vertical-align: top;
        }}
        
        .diff_add {{
            background-color: #d1fae5;
            color: #065f46;
        }}
        
        .diff_chg {{
            background-color: #fef3c7;
            color: #92400e;
        }}
        
        .diff_sub {{
            background-color: #fee2e2;
            color: #991b1b;
        }}
        
        .diff_next {{
            background-color: #e0e7ff;
        }}
        
        @media (max-width: 1024px) {{
            .comparison {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .actions {{
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }}
        
        .btn {{
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .btn-primary {{
            background: #3b82f6;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #2563eb;
        }}
        
        .btn-secondary {{
            background: #6b7280;
            color: white;
        }}
        
        .btn-secondary:hover {{
            background: #4b5563;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Complyo Preview - {fix_type.upper()}</h1>
            <p style="color: #6b7280; margin-top: 5px;">
                Vorschau Ihrer Compliance-Fixes vor dem Deployment
            </p>
            
            <div class="stats">
                <div class="stat additions">
                    <div class="stat-label">Hinzugefügt</div>
                    <div class="stat-value">+{changes['additions']}</div>
                </div>
                <div class="stat deletions">
                    <div class="stat-label">Entfernt</div>
                    <div class="stat-value">-{changes['deletions']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Zeilen Original</div>
                    <div class="stat-value">{changes['original_lines']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Zeilen Neu</div>
                    <div class="stat-value">{changes['modified_lines']}</div>
                </div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('side-by-side')">
                Side-by-Side
            </button>
            <button class="tab" onclick="switchTab('diff')">
                Diff-Ansicht
            </button>
        </div>
        
        <div id="side-by-side" class="tab-content active">
            <div class="comparison">
                <div class="pane">
                    <div class="pane-header original">
                        ❌ Original (Vorher)
                    </div>
                    <div class="pane-content">
                        <pre>{original_escaped}</pre>
                    </div>
                </div>
                
                <div class="pane">
                    <div class="pane-header modified">
                        ✅ Mit Complyo-Fix (Nachher)
                    </div>
                    <div class="pane-content">
                        <pre>{modified_escaped}</pre>
                    </div>
                </div>
            </div>
        </div>
        
        <div id="diff" class="tab-content">
            <div class="diff-view">
                {diff_html}
            </div>
        </div>
        
        <div class="actions">
            <button class="btn btn-primary" onclick="approveFix()">
                ✅ Fix annehmen & deployen
            </button>
            <button class="btn btn-secondary" onclick="window.close()">
                Schließen
            </button>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            document.querySelectorAll('.tab').forEach(button => {{
                button.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }}
        
        function approveFix() {{
            if (confirm('Möchten Sie diesen Fix wirklich anwenden?')) {{
                alert('Fix wird angewendet... (Deployment-Funktion wird in Kürze verfügbar sein)');
                // In production: Call deployment API
            }}
        }}
    </script>
</body>
</html>
"""
        
        return html
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML for safe display"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    async def get_preview(self, preview_id: str) -> Optional[str]:
        """
        Get preview HTML by ID
        
        Args:
            preview_id: Preview ID
            
        Returns:
            Preview HTML or None if not found
        """
        preview_path = os.path.join(self.preview_dir, f"{preview_id}.html")
        
        if not os.path.exists(preview_path):
            return None
        
        try:
            with open(preview_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"❌ Failed to read preview {preview_id}: {e}")
            return None
    
    async def delete_preview(self, preview_id: str) -> bool:
        """
        Delete preview file
        
        Args:
            preview_id: Preview ID
            
        Returns:
            True if deleted, False otherwise
        """
        preview_path = os.path.join(self.preview_dir, f"{preview_id}.html")
        
        try:
            if os.path.exists(preview_path):
                os.remove(preview_path)
                logger.info(f"🗑️ Preview deleted: {preview_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete preview {preview_id}: {e}")
            return False
    
    async def cleanup_old_previews(self, max_age_hours: int = 24):
        """
        Clean up old preview files
        
        Args:
            max_age_hours: Maximum age in hours
        """
        try:
            now = datetime.now().timestamp()
            max_age_seconds = max_age_hours * 3600
            
            deleted = 0
            for filename in os.listdir(self.preview_dir):
                if not filename.endswith('.html'):
                    continue
                
                filepath = os.path.join(self.preview_dir, filename)
                file_age = now - os.path.getmtime(filepath)
                
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    deleted += 1
            
            if deleted > 0:
                logger.info(f"🗑️ Cleaned up {deleted} old preview(s)")
                
        except Exception as e:
            logger.error(f"❌ Preview cleanup failed: {e}")


# Global instance
preview_engine = PreviewEngine()

