import os
from typing import Dict, Any
from .mermaid_generator import MermaidGenerator
from ...models.context import StructuredContext

class HTMLReportBuilder:
    """
    Generates a standalone HTML debug report for ORACLE analysis.
    """
    @staticmethod
    def build(context: StructuredContext, output_path: str):
        mermaid_code = MermaidGenerator.generate(context.execution_graph)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ORACLE Debug Report - {context.project_name.value}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f4f7f6; }}
        h1, h2 {{ color: #2c3e50; }}
        .card {{ background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .mermaid {{ background: #fff; padding: 20px; border-radius: 8px; }}
        .risk-high {{ color: #e74c3c; font-weight: bold; }}
        .risk-medium {{ color: #f39c12; font-weight: bold; }}
        .evidence {{ font-size: 0.9em; color: #666; font-style: italic; }}
        pre {{ background: #eee; padding: 10px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>ORACLE Debug Report</h1>
    <div class="card">
        <h2>Project Metadata</h2>
        <p><strong>Name:</strong> {context.project_name.value}</p>
        <p><strong>Architecture:</strong> {context.architecture_pattern.value}</p>
        <p><strong>Backend:</strong> {context.backend_framework.value}</p>
    </div>

    <div class="card">
        <h2>Execution Flow (Mermaid)</h2>
        <div class="mermaid">
            {mermaid_code}
        </div>
    </div>

    <div class="card">
        <h2>Runtime Risks</h2>
        <ul>
            {"".join([f'<li><span class="risk-{r.severity.lower()}">[{r.severity}]</span> {r.value}<br><span class="evidence">Evidence: {", ".join(r.evidence)}</span></li>' for r in context.runtime_risks])}
        </ul>
    </div>

    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</body>
</html>
"""
        with open(output_path, 'w') as f:
            f.write(html_template)
        print(f"[✓] HTML Report generated: {output_path}")
