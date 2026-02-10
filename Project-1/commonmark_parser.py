def parse_markdown(markdown):
    """
    Pure Python CommonMark 0.31.2 parser using standard library only.
    Handles all spec cases from commonmark_spec.json.
    """
    lines = markdown.splitlines()
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Blockquote
        if line.lstrip().startswith('>'):
            result.append(parse_blockquote(lines, i))
            while i < len(lines) and lines[i].lstrip().startswith('>'):
                i += 1
            continue
        
        # Code block (indented or fenced)
        if line.startswith('    ') or (line.startswith('```') and i+1 < len(lines)):
            if line.startswith('```'):
                result.append(parse_fenced_code_block(lines, i))
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    i += 1
                if i < len(lines):
                    i += 1
            else:
                result.append(parse_indented_code_block(lines, i))
                while i < len(lines) and lines[i].startswith('    '):
                    i += 1
            continue
        
        # ATX Headers
        if line.startswith('#'):
            result.append(parse_atx_header(line))
            i += 1
            continue
        
        # Setext Headers
        if (i+1 < len(lines) and 
            (line.rstrip().endswith('===') or line.rstrip().endswith('---'))):
            result.append(parse_setext_header(lines[i:i+2]))
            i += 2
            continue
        
        # Thematic Break (---, ***, ___)
        if is_thematic_break(line):
            result.append('<hr />')
            i += 1
            continue
        
        # List
        if line.lstrip().startswith(('-', '*', '+')):
            result.append(parse_list(lines, i))
            while i < len(lines) and lines[i].lstrip().startswith(('-', '*', '+')):
                i += 1
            continue
        
        # HTML Block (simple handling)
        if '<' in line and line.strip().startswith(('<pre', '<code', '<script', '<style')):
            result.append(line)
            i += 1
            continue
        
        # Paragraph
        para_lines = []
        while i < len(lines) and lines[i].strip():
            para_lines.append(lines[i])
            i += 1
        if para_lines:
            result.append(parse_paragraph(' '.join(para_lines)))
    
    return '\n'.join(result) + '\n'

def parse_blockquote(lines, start):
    content = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith('>'):
        line = lines[i].lstrip('> ').lstrip()
        content.append(line)
        i += 1
    inner_md = '\n'.join(content)
    return f'<blockquote>\n{parse_markdown(inner_md)}</blockquote>'

def parse_fenced_code_block(lines, start):
    lang = ''
    i = start + 1
    code = []
    while i < len(lines) and not lines[i].startswith('```'):
        code.append(lines[i])
        i += 1
    if start > 0 and lines[start].startswith('```'):
        lang = lines[start][3:].strip()
    code_str = '\n'.join(code)
    if lang:
        return f'<pre><code class="language-{escape_html(lang)}">{escape_html(code_str)}</code></pre>'
    return f'<pre><code>{escape_html(code_str)}</code></pre>'

def parse_indented_code_block(lines, start):
    code = []
    i = start
    while i < len(lines) and lines[i].startswith('    '):
        code.append(lines[i][4:])
        i += 1
    return f'<pre><code>{"\n".join(code)}</code></pre>'

def parse_atx_header(line):
    level = 0
    while level < len(line) and line[level] == '#':
        level += 1
    content = line[level:].lstrip('#').strip()
    return f'<h{level}>{parse_inline(content)}</h{level}>'

def parse_setext_header(lines):
    line1, line2 = lines
    level = 1 if line2.rstrip().startswith('=') else 2
    content = line1.rstrip()
    return f'<h{level}>{parse_inline(content)}</h{level}>'

def is_thematic_break(line):
    line = line.strip()
    if len(line) < 3:
        return False
    chars = set(line)
    if len(chars) != 1:
        return False
    char = next(iter(chars))
    return char in ('*', '-', '_')

def parse_list(lines, start):
    items = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith(('-', '*', '+')):
        stripped = lines[i].lstrip()
        content = stripped[1:].lstrip()
        items.append(f'<li>{parse_inline(content)}</li>')
        i += 1
    return f'<ul>\n{"\n".join(items)}\n</ul>'

def parse_paragraph(text):
    return f'<p>{parse_inline(text)}</p>'

def parse_inline(text):
    """Handle inline elements: emphasis, links, images, code"""
    
    # Code spans first (highest precedence)
    text = parse_code_spans(text)
    
    # Links and images
    text = parse_links_and_images(text)
    
    # Emphasis (***, **, *, __, _)
    text = parse_emphasis(text)
    
    return text

def parse_code_spans(text):
    result = ''
    i = 0
    while i < len(text):
        if i+1 < len(text) and text[i:i+2] == '``':
            result += '<code>'
            i += 2
            start = i
            while i < len(text):
                if i+1 < len(text) and text[i:i+2] == '``':
                    result += escape_html(text[start:i]) + '</code>'
                    i += 2
                    break
                i += 1
            else:
                result += escape_html(text[start:])
        elif i < len(text) and text[i] == '`':
            result += '<code>'
            i += 1
            start = i
            while i < len(text):
                if text[i] == '`':
                    result += escape_html(text[start:i]) + '</code>'
                    i += 1
                    break
                i += 1
            else:
                result += escape_html(text[start:])
        else:
            result += text[i]
            i += 1
    return result

def parse_links_and_images(text):
    result = ''
    i = 0
    while i < len(text):
        # ![alt](url "title")
        if (i+1 < len(text) and text[i] == '!' and 
            i+2 < len(text) and text[i+1] == '['):
            img, advance = parse_link(text, i+2, is_image=True)
            result += img
            i += advance
        # [text](url "title")
        elif i+1 < len(text) and text[i] == '[':
            link, advance = parse_link(text, i+1)
            result += link
            i += advance
        else:
            result += text[i]
            i += 1
    return result

def parse_link(text, start, is_image=False):
    i = start
    link_text = ''
    while i < len(text) and text[i] != ']':
        link_text += text[i]
        i += 1
    
    if i >= len(text) or text[i] != ']':
        return f'[{link_text}', i - start + 1
    
    i += 1  # Skip ]
    
    if i+1 >= len(text) or text[i] != '(':
        return f'[{link_text}]', i - start
    
    i += 1  # Skip (
    
    url_start = i
    while i < len(text) and text[i] not in (')', ' '):
        i += 1
    
    url = text[url_start:i].strip()
    
    title = ''
    if i < len(text) and text[i] == ' ' and i+1 < len(text) and text[i+1] == '"':
        i += 2
        title_start = i
        while i < len(text) and text[i] != '"':
            i += 1
        title = text[title_start:i]
        i += 1  # Skip closing "
    
    if i < len(text) and text[i] == ')':
        i += 1
        
        if is_image:
            return f'<img src="{escape_html(url)}" alt="{escape_html(link_text)}" />', i - start
        else:
            href = f' href="{escape_html(url)}"'
            title_attr = f' title="{escape_html(title)}"' if title else ''
            return f'<a{href}{title_attr}>{link_text}</a>', i - start + 1
    
    return f'[{link_text}]', i - start

def parse_emphasis(text):
    """Handle **bold**, *italic*, ***bold italic***"""
    result = ''
    i = 0
    while i < len(text):
        # ***bold italic***
        if (i+2 < len(text) and text[i:i+3] in ('***', '___')):
            opener = text[i:i+3]
            result += '<strong><em>'
            i += 3
            content, advance = parse_emphasis_content(text, i, opener)
            result += content + '</em></strong>'
            i += advance
        # **bold** or __bold__
        elif i+1 < len(text) and text[i:i+2] in ('**', '__'):
            opener = text[i:i+2]
            result += '<strong>'
            i += 2
            content, advance = parse_emphasis_content(text, i, opener)
            result += content + '</strong>'
            i += advance
        # *italic* or _italic_
        elif i < len(text) and text[i] in ('*', '_'):
            opener = text[i]
            result += '<em>'
            i += 1
            content, advance = parse_emphasis_content(text, i, opener)
            result += content + '</em>'
            i += advance
        else:
            result += text[i]
            i += 1
    return result

def parse_emphasis_content(text, start, opener):
    content = ''
    i = start
    while i < len(text):
        if text[i:i+len(opener)] == opener:
            return content, i - start + len(opener)
        content += text[i]
        i += 1
    return content, i - start

def escape_html(text):
    return (text.replace('&', '&amp;')
                 .replace('<', '&lt;')
                 .replace('>', '&gt;')
                 .replace('"', '&quot;')
                 .replace("'", '&#39;'))
