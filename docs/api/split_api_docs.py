#!/usr/bin/env python3
import json
import re
import os
import hashlib
from bs4 import BeautifulSoup
from pathlib import Path

def _slugify(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"[\s/]+", "-", s.strip())
    s = s.lower()
    s = re.sub(r"[^a-z0-9\-]", "", s)
    s = re.sub(r"-+", "-", s)
    return s

def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def _node_to_text(node) -> str:
    """Convert a BeautifulSoup node to plain text while preserving inline content.

    - Links become "text (url)" or just url if text missing
    - Inline code stays wrapped in backticks
    - No HTML tags in output
    - Whitespace normalized
    """
    if node is None:
        return ""

    # If it's a NavigableString
    if getattr(node, "name", None) is None:
        return _collapse_ws(str(node))

    name = node.name.lower()

    if name == "a":
        text = _collapse_ws(node.get_text("", strip=True))
        href = (node.get("href") or "").strip()
        if href:
            if text and text != href:
                return _collapse_ws(f"{text} ({href})")
            else:
                return href
        return text

    if name in {"code", "kbd", "samp"}:
        return f"`{_collapse_ws(node.get_text())}`"

    if name == "br":
        return "\n"

    # For other inline containers, recursively process children
    pieces = []
    for child in getattr(node, "children", []) or []:
        pieces.append(_node_to_text(child))
    return _collapse_ws(" ".join(p for p in pieces if p is not None))

def _inline_runs(node):
    """Turn an element's children into runs preserving links and code.

    Returns a list of runs: {text, link?}
    """
    runs = []
    if node is None:
        return runs

    def add_text(text, link=None, code=False):
        if not text:
            return
        runs.append({k: v for k, v in {"text": text, "link": link, "code": code}.items() if v not in (None, False, "")})

    for child in getattr(node, "children", []) or []:
        if getattr(child, "name", None) is None:
            t = _collapse_ws(str(child))
            if t:
                add_text(t)
            continue
        name = child.name.lower()
        if name == "a":
            text = _collapse_ws(child.get_text("", strip=True))
            href = (child.get("href") or "").strip()
            add_text(text or href, link=href or None)
        elif name in {"code", "kbd", "samp"}:
            add_text(_collapse_ws(child.get_text()), code=True)
        elif name == "br":
            add_text("\n")
        else:
            # Recurse for other inline containers
            nested = _inline_runs(child)
            runs.extend(nested)
    return runs

def clean_html_content(html_content: str) -> str:
    """Clean HTML content to readable plain text (no tags, keep content)."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    for s in soup(["script", "style"]):
        s.decompose()
    # Convert block-level elements to lines
    lines = []
    for el in soup.find_all(["p", "li", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"]):
        if el.name == "pre":
            text = el.get_text("\n", strip=False)
            lines.append(text.rstrip("\n"))
        else:
            text = _node_to_text(el)
            if text:
                lines.append(text)
    if not lines:
        # Fallback to full text
        return _collapse_ws(soup.get_text(" ", strip=True))
    return "\n\n".join(lines)

def extract_sections_from_html(html_content):
    """Extract sections from HTML based on h1 tags, returning rich blocks.

    Returns a list of dicts: { slug, title, html }
    """
    soup = BeautifulSoup(html_content, "html.parser")
    sections = []

    # Prefer content inside <body> if present
    root = soup.body or soup

    # Find all h1 tags
    h1_tags = root.find_all("h1")
    print(f"Found {len(h1_tags)} h1 tags")

    # Intro content before the first h1 becomes Introduction
    if h1_tags:
        intro_parts = []
        current = root.contents[0] if root.contents else None
        # Iterate siblings until first h1
        for sib in list(root.children):
            if getattr(sib, "name", None) == "h1":
                break
            if getattr(sib, "name", None) is not None:
                intro_parts.append(str(sib))
        if intro_parts:
            sections.append({
                "slug": "introduction",
                "title": "Introduction",
                "html": "".join(intro_parts).strip(),
            })

    for idx, h1 in enumerate(h1_tags):
        section_id = h1.get("id") or _slugify(h1.get_text()) or f"section-{idx+1}"
        section_title = h1.get_text().strip()

        # Capture until next h1
        content_parts = []
        current = h1.next_sibling
        while current and not (getattr(current, "name", None) == "h1"):
            # Keep block-level content only (still as HTML snippets)
            if getattr(current, "name", None) is not None:
                content_parts.append(str(current))
            current = current.next_sibling

        sections.append({
            "slug": section_id,
            "title": section_title,
            "html": "".join(content_parts).strip(),
        })

    return sections

def html_to_blocks(html_fragment: str):
    """Convert HTML fragment to a structured list of blocks without tags.

    Blocks:
      - {type: "heading", level: 2, text, slug}
      - {type: "paragraph", text}
      - {type: "list", style: "unordered"|"ordered", items: [text, ...]}
      - {type: "code", text}
      - {type: "blockquote", text}
      - {type: "table", header: [..], rows: [[..], ...]} (best-effort)
    """
    if not html_fragment:
        return []
    soup = BeautifulSoup(html_fragment, "html.parser")
    for s in soup(["script", "style"]):
        s.decompose()

    blocks = []
    order = 1

    def push_block(block):
        nonlocal order
        # assign order and block_id
        btype = block.get("type", "block")
        base = None
        if btype == "heading":
            base = f"h{block.get('level',0)}-{_slugify(block.get('text',''))}"
        else:
            base = f"{btype}-{order}"
        block["block_id"] = base
        block["order"] = order
        blocks.append(block)
        order += 1

    def handle_element(el):
        name = el.name.lower()
        if name in {"h2", "h3", "h4", "h5", "h6"}:
            level = int(name[1])
            text = _node_to_text(el)
            push_block({"type": "heading", "level": level, "text": text, "slug": _slugify(text), "id": _slugify(text)})
        elif name == "p":
            text = _node_to_text(el)
            runs = _inline_runs(el)
            # Detect simple callouts by prefix
            callout_variant = None
            lowered = text.lower()
            for prefix, variant in [("note:", "note"), ("note :", "note"), ("warning:", "warning"), ("tip:", "tip"), ("caution:", "caution")]:
                if lowered.startswith(prefix):
                    callout_variant = variant
                    # Strip the prefix from runs/text
                    if runs and runs[0].get("text", "").lower().startswith(prefix):
                        runs[0]["text"] = runs[0]["text"][len(prefix):].lstrip()
                    text = text[len(prefix):].lstrip()
                    break
            if callout_variant:
                push_block({"type": "callout", "variant": callout_variant, "text": text, "runs": runs})
            elif text:
                push_block({"type": "paragraph", "text": text, "runs": runs})
        elif name in {"ul", "ol"}:
            style = "unordered" if name == "ul" else "ordered"
            start = None
            try:
                if name == "ol" and el.has_attr('start'):
                    start = int(el.get('start'))
            except Exception:
                start = None
            items = []
            for li in el.find_all("li", recursive=False):
                # Capture inline text and nested lists separately
                li_text_nodes = []
                children_lists = []
                for ch in li.children:
                    if getattr(ch, "name", None) in ("ul", "ol"):
                        children_lists.append(ch)
                    else:
                        li_text_nodes.append(ch)
                # Combine inline text nodes
                li_container = BeautifulSoup("", "html.parser").new_tag("span")
                for n in li_text_nodes:
                    li_container.append(n if getattr(n, "extract", None) is None else n)
                item_text = _node_to_text(li_container)
                item_runs = _inline_runs(li_container)
                child_blocks = []
                for child_list in children_lists:
                    # Recursively serialize nested list to a block, but keep in children array
                    style2 = "unordered" if child_list.name.lower() == "ul" else "ordered"
                    start2 = None
                    try:
                        if child_list.name.lower() == "ol" and child_list.has_attr('start'):
                            start2 = int(child_list.get('start'))
                    except Exception:
                        start2 = None
                    sub_items = []
                    for sub_li in child_list.find_all("li", recursive=False):
                        sub_container = BeautifulSoup("", "html.parser").new_tag("span")
                        for sn in sub_li.children:
                            if getattr(sn, "name", None) in ("ul", "ol"):
                                # ignore deeper levels for now
                                continue
                            sub_container.append(sn if getattr(sn, "extract", None) is None else sn)
                        sub_text = _node_to_text(sub_container)
                        sub_runs = _inline_runs(sub_container)
                        sub_items.append({"text": sub_text, "runs": sub_runs})
                    child_blocks.append({"type": "list", "style": style2, "start": start2, "items": sub_items})
                items.append({"text": item_text, "runs": item_runs, "children": child_blocks if child_blocks else None})
            push_block({"type": "list", "style": style, "start": start, "items": items})
        elif name == "pre":
            # Attempt to detect language from nested <code class="language-xyz">
            lang = None
            inner_code = el.find("code")
            if inner_code and inner_code.has_attr("class"):
                for c in inner_code.get("class", []):
                    m = re.match(r"language-([a-z0-9_+-]+)", c)
                    if m:
                        lang = m.group(1)
                        break
            code_text = el.get_text("\n", strip=False)
            push_block({"type": "code", "text": code_text.rstrip("\n"), "lang": lang})
        elif name == "blockquote":
            text = _node_to_text(el)
            if text:
                push_block({"type": "blockquote", "text": text})
        elif name == "table":
            header = []
            rows = []
            thead = el.find("thead")
            if thead:
                ths = thead.find_all("th")
                header = [_node_to_text(th) for th in ths]
            for tr in el.find_all("tr"):
                cells = tr.find_all(["th", "td"])
                if cells:
                    rows.append([_node_to_text(c) for c in cells])
            # Alignment best-effort from style attributes
            align = []
            first_row_ths = el.find_all("th")
            if first_row_ths:
                for th in first_row_ths:
                    style = (th.get("style") or "").lower()
                    if "text-align:center" in style:
                        align.append("center")
                    elif "text-align:right" in style:
                        align.append("right")
                    else:
                        align.append("left")
            push_block({"type": "table", "header": header, "rows": rows, "align": align})
        elif name == "hr":
            push_block({"type": "separator"})
        # Ignore other tags at block level

    # Iterate only top-level elements in the fragment
    for child in list(soup.children):
        if getattr(child, "name", None) is None:
            # Skip stray strings at top-level
            continue
        handle_element(child)

    return blocks

def clean_json_descriptions(data):
    """Deep-copy-style cleaning of HTML-like strings to plain text.

    Note: We only strip HTML tags; we keep content. This does not attempt to
    preserve block structure (for that use html_to_blocks on known rich fields).
    """
    if isinstance(data, dict):
        for key, value in list(data.items()):
            if isinstance(value, str) and ('<' in value and '>' in value):
                data[key] = clean_html_content(value)
            else:
                clean_json_descriptions(value)
    elif isinstance(data, list):
        for item in data:
            clean_json_descriptions(item)

def write_json(filepath: str, payload: dict):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return os.path.getsize(filepath)

def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    # Load the JSON file
    with open('spark_api_v2_complete.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # For a manifest of created files
    manifest = {"files": []}

    # Extract and save core sections from info.description before generic cleaning
    if 'info' in data and 'description' in data['info']:
        html_content = data['info']['description']
        sections = extract_sections_from_html(html_content)

        for section in sections:
            section_slug = section["slug"]
            section_title = section["title"]
            blocks = html_to_blocks(section.get("html", ""))
            # Normalize known slug for consistency with nav
            if section_slug == "create-update":
                section_slug = "create-and-update"
            section_data = {
                "title": section_title,
                "slug": section_slug,
                "type": "core",
                "blocks": blocks,
            }

            filepath = f"api_json/core/{section_slug}.json"
            size = write_json(filepath, section_data)
            manifest["files"].append({
                "file": filepath,
                "title": section_title,
                "category": "Core",
                "bytes": size,
                "endpoints": 0,
            })
            print(f"Created: {filepath}")

    # Helper to parse query/path parameters with HTML descriptions
    def parse_params(param_list):
        results = []
        for p in param_list or []:
            name = p.get("key") or p.get("name")
            desc_html = None
            # Postman param description may be nested
            if isinstance(p.get("description"), dict):
                desc_html = p["description"].get("content")
            elif isinstance(p.get("description"), str):
                desc_html = p.get("description")
            desc_text = clean_html_content(desc_html) if desc_html else ""
            # Try to infer type from bracket prefix: [integer] Summary
            inferred_type = None
            m = re.match(r"\s*\[([^\]]+)\]\s*(.*)$", desc_text)
            if m:
                inferred_type = m.group(1).strip()
                desc_text = m.group(2).strip()
            results.append({
                "name": name,
                "type": p.get("type") or inferred_type or "string",
                "required": bool(p.get("required", False)),
                "summary": desc_text,
                "example": p.get("value")
            })
        return results

    # Extract and save API v2 endpoints (one file per endpoint)
    verb_map = {"GET": "get", "POST": "post", "PUT": "put", "PATCH": "patch", "DELETE": "delete"}

    if 'item' in data:
        for item in data['item']:
            if item.get('name') == 'API v2' and 'item' in item:
                for api_item in item['item']:
                    resource_title = api_item.get('name', '').strip()
                    resource_slug = _slugify(resource_title)
                    if resource_slug == 'internal-commisions':
                        resource_slug = 'internal-commissions'

                    resource_desc_html = api_item.get('description', '')
                    resource_desc = clean_html_content(resource_desc_html)
                    endpoints = api_item.get('item', []) or []
                    for ep in endpoints:
                        name = ep.get('name', '').strip()
                        req = ep.get('request', {})
                        method = (req.get('method') or '').upper()
                        method_prefix = verb_map.get(method, method.lower())
                        # build filename from endpoint name (strip leading 'Get ' for GET)
                        base_name = name
                        if method == 'GET' and base_name.lower().startswith('get '):
                            base_name = base_name[4:]
                        file_slug = _slugify(base_name)

                        # URL and path
                        url = req.get('url')
                        url_obj = req.get('urlObject') or {}
                        path_segments = url_obj.get('path') or []
                        # Normalize path: either already a list of segments or a single string starting with '/'
                        if isinstance(path_segments, list):
                            path = '/' + '/'.join([s.strip('/') for s in path_segments]) if path_segments else ''
                        else:
                            path = str(path_segments)

                        # Parameters
                        query_params = parse_params(url_obj.get('query'))
                        path_params = parse_params(url_obj.get('variable'))
                        headers = []
                        for h in req.get('header', []) or []:
                            h_desc = h.get('description')
                            if isinstance(h_desc, dict):
                                h_desc = clean_html_content(h_desc.get('content'))
                            elif isinstance(h_desc, str):
                                h_desc = clean_html_content(h_desc)
                            headers.append({
                                "name": h.get('key') or h.get('name'),
                                "value": h.get('value'),
                                "summary": h_desc or ""
                            })

                        # Derived helpers
                        pagination = {
                            "supported": any(p.get('name') == 'page' for p in query_params) or any(p.get('name') == 'per_page' for p in query_params),
                            "style": "page" if any(p.get('name') == 'page' for p in query_params) else None,
                            "params": [x.get('name') for x in query_params if x.get('name') in ('page', 'per_page')]
                        }
                        ordering = [x.get('name') for x in query_params if x.get('name') in ('order', 'direction')]

                        # Request body
                        body = req.get('body') or {}
                        request_body_raw = body.get('raw') if isinstance(body, dict) else None
                        request_body_json = None
                        if isinstance(request_body_raw, str):
                            try:
                                request_body_json = json.loads(request_body_raw)
                            except Exception:
                                request_body_json = None

                        # Responses (examples)
                        responses = []
                        for r in ep.get('response', []) or []:
                            body_text = r.get('body')
                            body_json = None
                            if isinstance(body_text, str):
                                try:
                                    body_json = json.loads(body_text)
                                except Exception:
                                    body_json = None
                            responses.append({
                                "name": r.get('name'),
                                "status": r.get('status'),
                                "code": r.get('code'),
                                "body_text": body_text,
                                "body_json": body_json
                            })

                        endpoint_doc = {
                            "type": "endpoint",
                            "resource": resource_slug,
                            "resource_title": resource_title,
                            "name": name,
                            "method": method,
                            "path": path or url,
                            "url": url,
                            "query_params": query_params,
                            "path_params": path_params,
                            "headers": headers,
                            "pagination": pagination,
                            "ordering": ordering,
                            "request_body_raw": request_body_raw,
                            "request_body_json": request_body_json,
                            "responses": responses,
                            "notes": resource_desc,
                            "notes_blocks": html_to_blocks(resource_desc_html),
                            "postman_id": ep.get('_postman_id') or ep.get('id')
                        }

                        filepath = f"api_json/api-v2/{resource_slug}/{method_prefix}-{file_slug}.json"
                        size = write_json(filepath, endpoint_doc)
                        manifest["files"].append({
                            "file": filepath,
                            "title": name,
                            "category": "API v2",
                            "bytes": size,
                            "endpoints": 1,
                        })
                        print(f"Created: {filepath}")

            elif item.get('name') == 'Forms':
                # Handle forms as separate documents (e.g., Registration Form)
                for form_item in item.get('item', []) or []:
                    form_title = form_item.get('name', '').strip()
                    req = form_item.get('request', {})
                    url = req.get('url')
                    url_obj = req.get('urlObject') or {}
                    query_params = [
                        {"name": p.get('key'), "example": p.get('value'), "required": not p.get('disabled', False)}
                        for p in (url_obj.get('query') or [])
                    ]

                    form_doc = {
                        "type": "form",
                        "title": form_title,
                        "method": req.get('method'),
                        "path": (url_obj.get('path') or [None])[0],
                        "url": url,
                        "query_params": query_params,
                        "description": clean_html_content(req.get('description', '')),
                    }

                    filepath = f"api_json/forms/{_slugify(form_title)}.json"
                    size = write_json(filepath, form_doc)
                    manifest["files"].append({
                        "file": filepath,
                        "title": form_title,
                        "category": "Forms",
                        "bytes": size,
                        "endpoints": 0,
                    })
                    print(f"Created: {filepath}")

    # After extraction, optionally clean remaining HTML fields if needed
    # (Not strictly necessary anymore since we worked off raw values above.)
    # clean_json_descriptions(data)

    # Write manifest to aid navigation/search
    for entry in manifest["files"]:
        try:
            entry["sha256"] = sha256_of_file(entry["file"])
        except Exception:
            pass
    write_json("api_json/meta/manifest.json", manifest)
    print("Created: api_json/meta/manifest.json")

    print("All sections extracted and saved with rich plain-text blocks.")

if __name__ == '__main__':
    main()
