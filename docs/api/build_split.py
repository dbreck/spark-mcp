#!/usr/bin/env python3
import json, os, re, hashlib, sys
from pathlib import Path
from html import unescape

OUT_ROOT = Path("clean")  # workspace-relative /clean
SOURCE = Path("spark_api_v2_complete.json")

KB_LIMIT = 120 * 1024

# Utilities
_slugify_re = re.compile(r"[^a-z0-9]+")

def slugify(name: str) -> str:
    s = name.strip().lower()
    s = s.replace("&", " and ")
    s = _slugify_re.sub("-", s)
    s = s.strip("-")
    return s

# HTML to Markdown conversion per rules
_codeblock_re = re.compile(r"<pre>\s*<code(?:[^>]*class=\"([^\"]+)\")?[^>]*>([\s\S]*?)</code>\s*</pre>", re.I)

_heading_re = re.compile(r"<h([1-6])[^>]*>([\s\S]*?)</h\1>", re.I)

_link_re = re.compile(r"<a[^>]*href=\"([^\"]+)\"[^>]*>([\s\S]*?)</a>", re.I)

_table_re = re.compile(r"<table[\s\S]*?</table>", re.I)
_tr_re = re.compile(r"<tr[^>]*>([\s\S]*?)</tr>", re.I)
_td_th_re = re.compile(r"<(td|th)[^>]*>([\s\S]*?)</(td|th)>", re.I)

_script_like_re = re.compile(r"<(script|iframe|style)[\s\S]*?>[\s\S]*?</\1>", re.I)
_img_re = re.compile(r"<img[^>]*>", re.I)

_list_item_re = re.compile(r"<li[^>]*>([\s\S]*?)</li>", re.I)
_ul_re = re.compile(r"</?(ul|ol)[^>]*>", re.I)
_br_re = re.compile(r"<br\s*/?>", re.I)
_p_re = re.compile(r"</?p[^>]*>", re.I)
_bold_re = re.compile(r"</?(strong|b)[^>]*>", re.I)
_italic_re = re.compile(r"</?(em|i)[^>]*>", re.I)
_code_inline_re = re.compile(r"</?code[^>]*>", re.I)
_tag_re = re.compile(r"<[^>]+>")

_whitespace_re = re.compile(r"\n{3,}")
_spaces_re = re.compile(r"[ \t]{2,}")



def html_to_md(html: str) -> str:
    if not html:
        return ""
    s = str(html)
    # Remove dangerous/irrelevant blocks
    s = _script_like_re.sub("", s)
    s = _img_re.sub("", s)

    # Convert code blocks first
    def _codeblock_sub(m):
        lang = (m.group(1) or "").strip()
        code = unescape(m.group(2) or "")
        lang = lang.replace("language-", "").strip()
        fence = f"```{lang}\n{code}\n```" if lang else f"```\n{code}\n```"
        return "\n" + fence + "\n"
    s = _codeblock_re.sub(_codeblock_sub, s)

    # Links
    s = _link_re.sub(lambda m: f"{unescape(m.group(2)).strip()} ({m.group(1).strip()})", s)

    # Headings (cap at ###)
    def _heading_sub(m):
        level = int(m.group(1))
        level = 3 if level > 3 else level
        text = unescape(_strip_tags(m.group(2))).strip()
        return "\n" + ("#" * level) + f" {text}\n"
    s = _heading_re.sub(_heading_sub, s)

    # Lists: turn each li into "- item"
    s = _list_item_re.sub(lambda m: "\n- " + unescape(_strip_tags(m.group(1))).strip(), s)
    s = _ul_re.sub("\n", s)

    # Tables -> markdown table when simple
    def _table_sub(tblm):
        tbl = tblm.group(0)
        rows = _tr_re.findall(tbl)
        cells = [ _td_th_re.findall(r) for r in rows ]
        # Build a simple table if rectangular
        flat = [[unescape(_strip_tags(c[1])).strip() for c in row] for row in cells if row]
        if not flat:
            return ""
        header = flat[0]
        # If header row lengths vary or only 1 col, fallback to list
        if len(header) < 2 or any(len(r)!=len(header) for r in flat):
            lines = []
            for r in flat:
                lines.append("- " + " | ".join([x for x in r if x]))
            return "\n" + "\n".join(lines) + "\n"
        sep = ["---"] * len(header)
        out = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
        for r in flat[1:]:
            out.append("| " + " | ".join(r) + " |")
        return "\n" + "\n".join(out) + "\n"
    s = _table_re.sub(_table_sub, s)

    # Line breaks and paragraphs
    s = _br_re.sub("\n", s)
    s = _p_re.sub("\n", s)

    # Inline styles
    s = _bold_re.sub("**", s)
    s = _italic_re.sub("_", s)

    # Inline code (remaining)
    s = _code_inline_re.sub("`", s)

    # Strip any remaining tags
    s = _tag_re.sub("", s)

    # Decode entities
    s = unescape(s)

    # Normalize whitespace
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _whitespace_re.sub("\n\n", s)
    s = re.sub("\n +", "\n", s)
    s = s.strip()
    return s


def _strip_tags(x: str) -> str:
    return _tag_re.sub("", x or "")


def one_line_summary(text: str, fallback: str="") -> str:
    t = (text or "").strip()
    if not t:
        t = fallback or ""
    # Take first sentence-like chunk up to 12 words
    words = re.split(r"\s+", t)
    return " ".join(words[:12]).strip()


def extract_path_from_url(req: dict) -> str:
    url = req.get("urlObject") or {}
    path_parts = url.get("path") or []
    if path_parts:
        path = "/" + "/".join([p for p in path_parts if p])
        return path
    raw = req.get("url") or ""
    # Fallback: parse after domain
    m = re.search(r"https?://[^/]+(/[^?]*)", raw)
    if m:
        return m.group(1)
    return raw


def extract_query_params(req: dict):
    url = req.get("urlObject") or {}
    q = url.get("query") or []
    params = []
    for it in q:
        name = it.get("key")
        if not name:
            continue
        desc = it.get("description", {})
        dtext = desc.get("content") if isinstance(desc, dict) else (desc or "")
        dmd = html_to_md(dtext)
        params.append({
            "name": name,
            "type": "string",
            "required": False,
            "summary": one_line_summary(dmd)
        })
    return params


def extract_path_params(req: dict):
    url = req.get("urlObject") or {}
    vars_ = url.get("variable") or []
    out = []
    for v in vars_:
        k = v.get("key")
        if not k:
            continue
        desc = v.get("description", {})
        dtext = desc.get("content") if isinstance(desc, dict) else (desc or "")
        dmd = html_to_md(dtext)
        out.append({
            "name": k,
            "type": "string",
            "required": True,
            "summary": one_line_summary(dmd)
        })
    return out


def extract_headers(item_request: dict) -> list:
    headers = []
    for h in item_request.get("header", []) or []:
        name = h.get("key") or h.get("name")
        if not name:
            continue
        val = h.get("value") or ""
        headers.append({"name": name, "required": False, "summary": val})
    return headers


def detect_pagination(req: dict):
    q = [ (it.get("key") or "") for it in (req.get("urlObject",{}).get("query") or []) ]
    style = None
    params = []
    if any(k in q for k in ("page","per_page")):
        style = "page"
        params = [k for k in ("page","per_page") if k in q]
    elif any(k in q for k in ("limit","next","cursor")):
        style = "cursor"
        params = [k for k in ("limit","next","cursor") if k in q]
    return {"supported": bool(style), "style": style, "params": params} if style else {"supported": False}


def detect_filtering(req: dict):
    keys = [ (it.get("key") or "") for it in (req.get("urlObject",{}).get("query") or []) ]
    filt = [k for k in keys if re.search(r"_(eq|cont|lt|lte|gt|gte|in|not_in|starts|ends)$", k)]
    return sorted(set(filt))


def detect_ordering(req: dict):
    keys = [ (it.get("key") or "") for it in (req.get("urlObject",{}).get("query") or []) ]
    out = []
    if "order" in keys:
        out.append("order")
    if "direction" in keys:
        out.append("direction")
    return out


def ensure_dirs():
    for sub in ["meta","core","reference","resources","forms","_index"]:
        (OUT_ROOT / sub).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, obj: dict):
    data = json.dumps(obj, ensure_ascii=False, indent=2)
    # Validation: no raw HTML remains
    if re.search(r"<[^>]+>", data):
        # attempt to strip any remaining tags inside string values only
        data = re.sub(r"<[^>]+>", "", data)
    path.write_text(data, encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def split_if_large(base_path: Path, base_obj: dict):
    # Only split resources with endpoints
    endpoints = base_obj.get("endpoints") or []
    if not endpoints:
        write_json(base_path, base_obj)
        return [base_path.name]
    # Try writing to measure size
    tmp = json.dumps(base_obj, ensure_ascii=False, indent=2)
    if len(tmp.encode("utf-8")) <= KB_LIMIT:
        write_json(base_path, base_obj)
        return [base_path.name]
    # Split endpoints across parts
    parts = []
    chunk = []
    acc_size = 0
    def size_of_eps(eps):
        return len(json.dumps({**base_obj, "endpoints": eps}, ensure_ascii=False, indent=2).encode("utf-8"))
    for ep in endpoints:
        est = size_of_eps(chunk + [ep])
        if est > KB_LIMIT and chunk:
            parts.append(chunk)
            chunk = [ep]
        else:
            chunk.append(ep)
    if chunk:
        parts.append(chunk)
    filenames = []
    # create part files
    for idx, eps in enumerate(parts, start=1):
        obj = {**base_obj, "endpoints": eps}
        obj["parts"] = []  # fill later
        part_name = f"{base_path.stem}.part{idx}.json"
        write_json(OUT_ROOT / "resources" / part_name, obj)
        filenames.append(part_name)
    # update parts pointers
    for name in filenames:
        p = OUT_ROOT / "resources" / name
        obj = json.loads(p.read_text(encoding="utf-8"))
        obj["parts"] = filenames
        write_json(p, obj)
    return filenames


def build_core_files(collection: dict):
    # Core slugs as specified. Content may not be present; produce empty content_md if missing.
    core_slugs = [
        ("Introduction", "introduction"),
        ("Getting Started", "getting-started"),
        ("Environments", "environments"),
        ("Understanding the Data", "understanding-the-data"),
        ("Authorization", "authorization"),
        ("Pagination", "pagination"),
        ("Filtering", "filtering"),
        ("Ordering", "ordering"),
        ("GET", "get"),
        ("Create & Update", "create-and-update"),
        ("Status Codes", "status-codes"),
    ]
    info_desc = html_to_md(collection.get("info",{}).get("description") or "")
    files = []
    for title, slug in core_slugs:
        obj = {
            "title": title,
            "category": "Core",
            "content_md": info_desc if title == "Introduction" else "",
            "examples": []
        }
        path = OUT_ROOT / "core" / f"{slug}.json"
        write_json(path, obj)
        files.append(path)
    return files


def walk_items(items, parent_names=None):
    parent_names = parent_names or []
    for it in items or []:
        name = it.get("name") or ""
        children = it.get("item")
        yield {
            "node": it,
            "name": name,
            "path": parent_names + [name],
            "children": children,
        }
        if children:
            yield from walk_items(children, parent_names + [name])


def build_resources(collection: dict):
    files = []
    # Find top-level "API v2" node
    api_v2 = None
    for node in collection.get("item", []):
        if (node.get("name") or "").strip().lower() == "api v2":
            api_v2 = node
            break
    if not api_v2:
        return files
    for res in api_v2.get("item", []) or []:
        res_name = res.get("name") or ""
        res_slug = slugify(res_name)
        endpoints = []
        # resource-level description
        res_notes = html_to_md(res.get("description") or "")
        for ep in res.get("item", []) or []:
            req = ep.get("request") or {}
            method = (req.get("method") or "").upper()
            if not method:
                continue
            path = extract_path_from_url(req)
            if not path:
                continue
            eid = ep.get("id") or ep.get("_postman_id") or ""
            qparams = extract_query_params(req)
            pparams = extract_path_params(req)
            headers = extract_headers(req)
            pagination = detect_pagination(req)
            filtering = detect_filtering(req)
            ordering = detect_ordering(req)
            # descriptions
            ep_desc = html_to_md(ep.get("description") or "")
            summary = one_line_summary(ep_desc, fallback=ep.get("name") or res_name)
            # request/response examples
            request_examples = []
            response_examples = []
            for resp in ep.get("response", []) or []:
                status = resp.get("code") or resp.get("status") or None
                # body may be in 'body' or 'originalRequest' sample - Postman variations
                body = resp.get("body")
                if body:
                    code = f"```json\n{body}\n```"
                    response_examples.append({"status": status, "code": code})
            endpoint = {
                "id": eid,
                "name": ep.get("name") or "",
                "method": method,
                "path": path,
                "query_params": qparams,
                "path_params": pparams,
                "headers": headers,
                "pagination": pagination,
                "filtering": filtering,
                "ordering": ordering,
                "request_body_schema": None,
                "request_examples": request_examples,
                "response_examples": response_examples,
                "errors": [],
                "notes": one_line_summary(res_notes) if not ep_desc else ep_desc
            }
            endpoints.append(endpoint)
        obj = {
            "title": res_name,
            "category": "API v2",
            "resource": res_slug,
            "endpoints": endpoints
        }
        # write (with splitting if large)
        base_path = OUT_ROOT / "resources" / f"{res_slug}.json"
        part_names = split_if_large(base_path, obj)
        files.extend([OUT_ROOT / "resources" / n for n in part_names])
    return files


def build_forms(collection: dict):
    files = []
    # Look for Forms at top-level
    for node in collection.get("item", []) or []:
        if (node.get("name") or "").strip().lower() == "forms":
            for form_item in node.get("item", []) or []:
                form_name = form_item.get("name") or ""
                form_slug = slugify(form_name)
                endpoints = []
                for ep in form_item.get("item", []) or []:
                    req = ep.get("request") or {}
                    method = (req.get("method") or "").upper()
                    path = extract_path_from_url(req)
                    eid = ep.get("id") or ep.get("_postman_id") or ""
                    endpoints.append({
                        "id": eid,
                        "name": ep.get("name") or "",
                        "method": method,
                        "path": path,
                        "query_params": extract_query_params(req),
                        "path_params": extract_path_params(req),
                        "headers": extract_headers(req),
                        "pagination": {"supported": False},
                        "filtering": [],
                        "ordering": [],
                        "request_body_schema": None,
                        "request_examples": [],
                        "response_examples": [],
                        "errors": [],
                        "notes": html_to_md(ep.get("description") or "")
                    })
                obj = {
                    "title": form_name,
                    "category": "Forms",
                    "resource": form_slug,
                    "endpoints": endpoints
                }
                path = OUT_ROOT / "forms" / f"{form_slug}.json"
                write_json(path, obj)
                files.append(path)
    # Specific mapping hint for POST Registration Form
    return files


def finalize_meta(all_files: list):
    manifest = []
    search_index = []
    for f in all_files:
        stat = f.stat()
        # load for endpoints count and search index
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            obj = {}
        endpoints = obj.get("endpoints") or []
        manifest.append({
            "file": str(f),
            "title": obj.get("title") or obj.get("resource") or f.stem,
            "category": obj.get("category") or ("Core" if f.parent.name=="core" else ""),
            "bytes": stat.st_size,
            "sha256": sha256_file(f),
            "endpoints": len(endpoints)
        })
        # search index per endpoint
        for ep in endpoints:
            rec = {
                "id": ep.get("id") or "",
                "title": ep.get("name") or "",
                "category": obj.get("category") or "",
                "subcategory": obj.get("title") or "",
                "method": ep.get("method") or "",
                "path": ep.get("path") or "",
                "summary": one_line_summary(ep.get("notes") or ep.get("name") or ""),
                "file": str(f)
            }
            # ensure <= 600 chars
            for k,v in list(rec.items()):
                if isinstance(v, str) and len(v) > 600:
                    rec[k] = v[:600]
            search_index.append(rec)
    # write meta files
    write_json(OUT_ROOT / "meta" / "manifest.json", {"files": manifest})
    write_json(OUT_ROOT / "meta" / "search-index.json", search_index)

    # toc
    lines = ["# Documentation Index", ""]
    # Core
    lines.append("## Core")
    for f in sorted([p for p in all_files if p.parent.name=="core"], key=lambda x: x.name):
        lines.append(f"- {f.name}")
    # Resources
    lines.append("\n## API v2 Resources")
    for f in sorted([p for p in all_files if p.parent.name=="resources"], key=lambda x: x.name):
        lines.append(f"- {f.name}")
    # Forms
    forms = [p for p in all_files if p.parent.name=="forms"]
    if forms:
        lines.append("\n## Forms")
        for f in sorted(forms, key=lambda x: x.name):
            lines.append(f"- {f.name}")
    (OUT_ROOT / "_index" / "toc.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_outputs():
    # No HTML tags remain
    for path in OUT_ROOT.rglob("*.json"):
        data = path.read_text(encoding="utf-8")
        if re.search(r"<[^>]+>", data):
            raise SystemExit(f"Raw HTML remains in {path}")
    # Every endpoint has method and path (only for dict JSONs with endpoints)
    for path in OUT_ROOT.rglob("*.json"):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("endpoints"), list):
            for ep in obj.get("endpoints") or []:
                if not ep.get("method") or not ep.get("path"):
                    raise SystemExit(f"Missing method/path in endpoint in {path}")
    # Manifest and search-index reference existing files
    mani = json.loads((OUT_ROOT/"meta"/"manifest.json").read_text(encoding="utf-8"))
    for rec in mani.get("files") or []:
        if not Path(rec.get("file")).exists():
            raise SystemExit(f"Manifest references missing file: {rec.get('file')}")
    sidx = json.loads((OUT_ROOT/"meta"/"search-index.json").read_text(encoding="utf-8"))
    for rec in sidx:
        if not Path(rec.get("file")).exists():
            raise SystemExit(f"Search index references missing file: {rec.get('file')}")


def main():
    ensure_dirs()
    collection = json.loads(SOURCE.read_text(encoding="utf-8"))
    core_files = build_core_files(collection)
    res_files = build_resources(collection)
    form_files = build_forms(collection)
    all_files = core_files + res_files + form_files
    finalize_meta(all_files)
    validate_outputs()
    # Summary
    n = len(all_files) + 2  # meta files
    print(json.dumps({"ok": True, "files": n, "out_root": f"/{OUT_ROOT.as_posix()}"}))

if __name__ == "__main__":
    main()
