#!/usr/bin/env python3
import sys
import re
import html
from pathlib import Path
from datetime import datetime

USAGE = """Usage:
  docker_bench_to_html.py /path/to/docker-bench-clean.txt
  docker_bench_to_html.py /path/to/docker-bench-clean.txt /path/to/output.html
"""

SECTION_RE = re.compile(r"^\[INFO\]\s+(\d+)\s+-\s+(.*)\s*$")
CHECK_RE = re.compile(r"^\[(PASS|WARN|NOTE|INFO)\]\s+(\d+(?:\.\d+)*)\s+-\s+(.*)\s*$")
BULLET_RE = re.compile(r"^\s*\*\s+(.*)\s*$")

def parse_clean_text(text: str):
    preface = []
    sections = []
    cur_section = None
    cur_item = None

    def ensure_section(num: str, title: str):
        nonlocal cur_section
        cur_section = {
            "num": num,
            "title": title,
            "items": []
        }
        sections.append(cur_section)

    lines = text.splitlines()
    started = False

    for line in lines:
        msec = SECTION_RE.match(line)
        mchk = CHECK_RE.match(line)
        mbul = BULLET_RE.match(line)

        if msec:
            started = True
            cur_item = None
            ensure_section(msec.group(1), msec.group(2))
            continue

        if mchk:
            started = True
            if cur_section is None:
                ensure_section("0", "Uncategorized")
            cur_item = {
                "status": mchk.group(1),
                "id": mchk.group(2),
                "desc": mchk.group(3),
                "details": []
            }
            cur_section["items"].append(cur_item)
            continue

        if mbul and cur_item is not None:
            cur_item["details"].append(mbul.group(1))
            continue

        # 일반 라인: 시작 전이면 preface로, 시작 후면 item details(가장 최근 item)에 붙이거나 무시
        if not started:
            if line.strip() != "":
                preface.append(line)
        else:
            # docker-bench 출력은 종종 INFO 아래에 "      * ..." 같은 줄이 오는데
            # '*' 없는 일반 라인은 의미가 있을 수 있어 최근 item에 붙여줌
            if cur_item is not None and line.strip() != "":
                cur_item["details"].append(line.strip())

    return preface, sections

def counts(sections):
    c = {"PASS": 0, "WARN": 0, "NOTE": 0, "INFO": 0}
    for s in sections:
        for it in s["items"]:
            c[it["status"]] = c.get(it["status"], 0) + 1
    return c

def section_counts(section):
    c = {"PASS": 0, "WARN": 0, "NOTE": 0, "INFO": 0}
    for it in section["items"]:
        c[it["status"]] = c.get(it["status"], 0) + 1
    return c

def build_html(preface, sections, title="Docker Bench for Security Report"):
    total = counts(sections)
    gen = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def esc(s): return html.escape(s, quote=True)

    # Rows
    section_blocks = []
    for s in sections:
        sc = section_counts(s)
        summary_badge = f"""
          <span class="badge pass">PASS {sc['PASS']}</span>
          <span class="badge warn">WARN {sc['WARN']}</span>
          <span class="badge note">NOTE {sc['NOTE']}</span>
          <span class="badge info">INFO {sc['INFO']}</span>
        """
        rows = []
        for it in s["items"]:
            details = "<br>".join(esc(x) for x in it["details"]) if it["details"] else ""
            rows.append(f"""
              <tr class="row" data-status="{it['status']}">
                <td class="status {it['status'].lower()}">{esc(it['status'])}</td>
                <td class="checkid">{esc(it['id'])}</td>
                <td class="desc">{esc(it['desc'])}</td>
                <td class="details">{details}</td>
              </tr>
            """)
        table = f"""
          <table class="tbl">
            <thead>
              <tr><th>Status</th><th>ID</th><th>Description</th><th>Details</th></tr>
            </thead>
            <tbody>
              {''.join(rows)}
            </tbody>
          </table>
        """
        section_blocks.append(f"""
          <details class="section" open>
            <summary>
              <span class="sectitle">{esc(s['num'])} - {esc(s['title'])}</span>
              <span class="secmeta">{summary_badge}</span>
            </summary>
            {table}
          </details>
        """)

    preface_html = ""
    if preface:
        preface_html = "<pre class='preface'>" + esc("\n".join(preface)) + "</pre>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{esc(title)}</title>
  <style>
    :root {{
      --bg: #0b1020;
      --panel: #121a33;
      --muted: #8ea0c5;
      --text: #e9eefc;
      --line: rgba(255,255,255,.08);
      --pass: #1fba7a;
      --warn: #ff5a5f;
      --note: #ffb020;
      --info: #4da3ff;
    }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, "Noto Sans", Arial;
      background: radial-gradient(1200px 600px at 10% 0%, rgba(77,163,255,.18), transparent 60%),
                  radial-gradient(900px 500px at 90% 10%, rgba(31,186,122,.14), transparent 55%),
                  var(--bg);
      color: var(--text);
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
    .top {{
      display: flex; gap: 16px; flex-wrap: wrap; align-items: center; justify-content: space-between;
      margin-bottom: 16px;
    }}
    h1 {{ font-size: 20px; margin: 0; letter-spacing: .2px; }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .cards {{ display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0 18px; }}
    .card {{
      background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.03));
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      min-width: 140px;
      box-shadow: 0 8px 20px rgba(0,0,0,.25);
    }}
    .card .k {{ font-size: 12px; color: var(--muted); }}
    .card .v {{ font-size: 22px; font-weight: 700; margin-top: 6px; }}
    .filter {{
      background: rgba(255,255,255,.04);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 14px;
      margin-bottom: 18px;
    }}
    .filter label {{ margin-right: 14px; cursor: pointer; user-select: none; }}
    .badge {{
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      margin-left: 6px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.04);
    }}
    .badge.pass {{ color: var(--pass); }}
    .badge.warn {{ color: var(--warn); }}
    .badge.note {{ color: var(--note); }}
    .badge.info {{ color: var(--info); }}

    .section {{
      background: rgba(255,255,255,.03);
      border: 1px solid var(--line);
      border-radius: 16px;
      margin-bottom: 12px;
      overflow: hidden;
    }}
    summary {{
      list-style: none;
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      padding: 14px 14px;
      cursor: pointer;
      background: rgba(255,255,255,.03);
    }}
    summary::-webkit-details-marker {{ display:none; }}
    .sectitle {{ font-weight: 700; }}
    .secmeta {{ display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }}
    .tbl {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    .tbl th, .tbl td {{
      border-top: 1px solid var(--line);
      padding: 10px 12px;
      vertical-align: top;
    }}
    .tbl th {{
      text-align: left;
      color: var(--muted);
      font-weight: 600;
      background: rgba(255,255,255,.02);
    }}
    .status {{
      font-weight: 800;
      letter-spacing: .2px;
      width: 72px;
      white-space: nowrap;
    }}
    .status.pass {{ color: var(--pass); }}
    .status.warn {{ color: var(--warn); }}
    .status.note {{ color: var(--note); }}
    .status.info {{ color: var(--info); }}
    .checkid {{ width: 90px; color: var(--muted); white-space: nowrap; }}
    .details {{ color: rgba(233,238,252,.9); }}
    .preface {{
      margin: 0 0 14px;
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.03);
      color: rgba(233,238,252,.9);
      overflow: auto;
    }}
    .hint {{
      margin-top: 14px;
      color: var(--muted);
      font-size: 12px;
    }}
    a {{ color: var(--info); }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div>
        <h1>{esc(title)}</h1>
        <div class="meta">Generated: {esc(gen)}</div>
      </div>
      <div class="meta">Filter + collapse sections for readability</div>
    </div>

    {preface_html}

    <div class="cards">
      <div class="card"><div class="k">PASS</div><div class="v" style="color:var(--pass)">{total['PASS']}</div></div>
      <div class="card"><div class="k">WARN</div><div class="v" style="color:var(--warn)">{total['WARN']}</div></div>
      <div class="card"><div class="k">NOTE</div><div class="v" style="color:var(--note)">{total['NOTE']}</div></div>
      <div class="card"><div class="k">INFO</div><div class="v" style="color:var(--info)">{total['INFO']}</div></div>
    </div>

    <div class="filter">
      <strong>Show:</strong>
      <label><input type="checkbox" class="flt" value="PASS" checked> PASS</label>
      <label><input type="checkbox" class="flt" value="WARN" checked> WARN</label>
      <label><input type="checkbox" class="flt" value="NOTE" checked> NOTE</label>
      <label><input type="checkbox" class="flt" value="INFO" checked> INFO</label>
      <span class="badge" id="shown"></span>
    </div>

    {''.join(section_blocks)}

    <div class="hint">
      서버에 GUI 브라우저가 없으면:<br/>
      - 파일을 로컬로 가져와 열기: <code>scp user@server:/opt/security-lab/reports/*.html .</code><br/>
      - 또는 <code>python3 -m http.server</code>로 임시 웹서버 띄우기
    </div>
  </div>

<script>
  function applyFilters() {{
    const checks = Array.from(document.querySelectorAll('.flt'));
    const allowed = new Set(checks.filter(c => c.checked).map(c => c.value));
    const rows = Array.from(document.querySelectorAll('tr.row'));
    let shown = 0;
    rows.forEach(r => {{
      const st = r.dataset.status;
      const ok = allowed.has(st);
      r.style.display = ok ? '' : 'none';
      if (ok) shown++;
    }});
    
    document.getElementById('shown').textContent = `Showing ${{shown}} checks`;

  }}
  document.querySelectorAll('.flt').forEach(c => c.addEventListener('change', applyFilters));
  applyFilters();
</script>
</body>
</html>
"""

def main():
    if len(sys.argv) not in (2, 3):
        sys.stderr.write(USAGE)
        return 2

    in_path = Path(sys.argv[1])
    if not in_path.exists():
        sys.stderr.write(f"[ERROR] Input not found: {in_path}\n")
        return 1

    out_path = Path(sys.argv[2]) if len(sys.argv) == 3 else in_path.with_suffix(".html")

    text = in_path.read_text(errors="ignore")
    preface, sections = parse_clean_text(text)

    html_doc = build_html(preface, sections, title="Docker Bench for Security Report")
    out_path.write_text(html_doc, encoding="utf-8")

    print(str(out_path))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
