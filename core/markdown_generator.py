import os
from datetime import datetime

class MarkdownGenerator:
    @staticmethod
    def generate_concept_stub(title, raw_input, llm_content):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        template = f"""---
aliases: []
tags:
  - concept
  - ai-generated
date_created: {date_str}
---
# {title}

> [!info] 🤖 Nota gerada via LLM (Semi-Auto)
> **Input original:** {raw_input}

{llm_content}
"""
        return template

    @staticmethod
    def generate_daily_note(date_str, summary_content):
        template = f"""---
tags:
  - daily
date: {date_str}
---
# Resumo Diário: {date_str}

> [!info] 🤖 Resumo de Capturas Diárias

{summary_content}
"""
        return template
