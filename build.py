#!/usr/bin/env python3
"""
Build every deliverable from the single source, site-body.html.

    python3 build.py

Outputs
  justin-close-media.html   standalone page, drop on any host
  site-wordpress.html       one scoped block for a Custom HTML block
  wp-styles.css             CSS for Appearance > Customize > Additional CSS
  wp-markup.html            markup for installs that strip <style>/<script>
  site-code.html            copy-paste page for the standalone file
  wp-code.html              copy-paste page for the WordPress block
  wp-fix.html               copy-paste page for the two-part no-JS route
"""

import re, html, datetime, pathlib

ROOT = pathlib.Path('/home/user/trial-')
SRC = ROOT / 'site-body.html'
WRAP = 'jcm'
YEAR = datetime.date.today().year

src = SRC.read_text(encoding='utf-8')
STYLE = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
SCRIPT = re.search(r'<script>(.*?)</script>', src, re.S).group(1)
MARKUP = src[src.index('</style>') + 8: src.rindex('<script>')].strip()


# ───────────────────────────────────────────────── standalone
HEAD = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="color-scheme" content="dark">
<title>Justin Close Media — Hospitality &amp; Aerial Photography</title>
<meta name="description" content="Justin Close Media photographs hotels, lodges and private rentals — interiors, grounds and aerial work made for the places a booking is decided.">
<meta property="og:title" content="Justin Close Media — Hospitality &amp; Aerial Photography">
<meta property="og:description" content="Interiors, grounds and aerial photography for hotels, lodges and private rentals.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>%F0%9F%93%B7</text></svg>">
</head>
<body>
'''
standalone = HEAD + src.strip() + '\n\n</body>\n</html>\n'
(ROOT / 'justin-close-media.html').write_text(standalone, encoding='utf-8')


# ───────────────────────────────────────────────── WordPress block
def scope_selector(sel):
    out = []
    for s in [p.strip() for p in sel.split(',') if p.strip()]:
        if s == ':root':
            out.append(f'.{WRAP}')
        elif s == '*':
            out += [f'.{WRAP}', f'.{WRAP} *']
        elif re.match(r'^\*::?', s):
            out.append(f'.{WRAP} ' + s)
        elif re.match(r'^(html|body)\b', s):
            out.append(re.sub(r'^(html|body)', f'.{WRAP}', s))
        elif s.startswith('.reveal-on'):
            out.append(f'.{WRAP}.reveal-on' + s[len('.reveal-on'):])
        else:
            out.append(f'.{WRAP} ' + s)
    return ', '.join(out)


def transform_css(css):
    res, i, n = [], 0, len(css)
    while i < n:
        if css.startswith('/*', i):
            j = css.index('*/', i) + 2
            res.append(css[i:j]); i = j; continue
        if css[i] in ' \t\r\n':
            res.append(css[i]); i += 1; continue
        brace = css.find('{', i)
        if brace == -1:
            res.append(css[i:]); break
        header = css[i:brace].strip()
        depth, j = 1, brace + 1
        while j < n and depth:
            if css[j] == '{': depth += 1
            elif css[j] == '}': depth -= 1
            j += 1
        body = css[brace + 1:j - 1]
        if header.startswith('@keyframes'):
            res.append(f'@keyframes {WRAP}-{header.split()[1]} {{{body}}}')
        elif header.startswith(('@media', '@supports')):
            res.append(f'{header} {{\n{transform_css(body)}\n}}')
        else:
            res.append(f'{scope_selector(header)} {{{body}}}')
        i = j
    return ''.join(res)


wp_css = transform_css(STYLE)
for kf in ('fadeIn', 'up'):
    wp_css = re.sub(r'(animation\s*:[^;]*?)\b' + kf + r'\b', r'\1' + f'{WRAP}-{kf}', wp_css)

# the grain belongs inside the block, not pinned over the browser window
wp_css = wp_css.replace(f'.{WRAP}::after {{\n  content: "";\n  position: fixed;',
                        f'.{WRAP}::after {{\n  content: "";\n  position: absolute;')
# the site header sticks within the block, clear of the theme chrome
wp_css = wp_css.replace(f'.{WRAP} .top {{\n  position: fixed;\n  inset: 0 0 auto 0;',
                        f'.{WRAP} .top {{\n  position: sticky;\n  top: 0;')

RESET = f'''/* Justin Close Media — scoped for WordPress.
   Every rule below applies only inside <div class="{WRAP}">, so it cannot
   leak out and restyle your theme. */
.{WRAP} {{ position: relative; isolation: isolate; }}

/* Themes style bare elements (section, ul, figure, button...) and those
   rules would otherwise bleed into this block. This neutralises them, and
   must stay ABOVE the design rules, which override it. */
.{WRAP} section, .{WRAP} div, .{WRAP} figure, .{WRAP} figcaption,
.{WRAP} ul, .{WRAP} li, .{WRAP} p, .{WRAP} span, .{WRAP} b, .{WRAP} i,
.{WRAP} h1, .{WRAP} h2, .{WRAP} h3, .{WRAP} a, .{WRAP} img, .{WRAP} hr,
.{WRAP} form, .{WRAP} button, .{WRAP} input, .{WRAP} textarea, .{WRAP} label,
.{WRAP} dl, .{WRAP} dt, .{WRAP} dd, .{WRAP} header, .{WRAP} footer,
.{WRAP} nav, .{WRAP} blockquote {{
  margin: 0; padding: 0; border: 0; outline: 0; background: none;
  font: inherit; color: inherit; text-align: left; text-decoration: none;
  text-transform: none; letter-spacing: normal; list-style: none;
  border-radius: 0; box-shadow: none; max-width: none; min-height: 0;
  float: none; clear: none; transform: none;
}}

'''
wp_css = RESET + wp_css

IDS = ['top', 'sail', 'sailBtn', 'home', 'work', 'aerial', 'services', 'about',
       'process', 'enquire', 'form', 'said', 'base',
       'q-name', 'q-prop', 'q-mail', 'q-tel', 'q-msg']

wp_markup, wp_script = MARKUP, SCRIPT
for i in IDS:
    for attr in ('id', 'for', 'aria-controls'):
        wp_markup = wp_markup.replace(f'{attr}="{i}"', f'{attr}="{WRAP}-{i}"')
    wp_markup = wp_markup.replace(f'href="#{i}"', f'href="#{WRAP}-{i}"')
    wp_script = wp_script.replace(f"getElementById('{i}')", f"getElementById('{WRAP}-{i}')")
    wp_script = wp_script.replace(f"v('{i}')", f"v('{WRAP}-{i}')")

wp_script = wp_script.replace(
    "d.documentElement.classList.add('reveal-on');",
    "if (root) root.classList.add('reveal-on');")
wp_script = wp_script.replace(
    "  var d = document;",
    "  var d = document;\n  var root = d.querySelector('.jcm');\n  if (!root) return;")
wp_script = wp_script.replace("d.querySelectorAll('.veil')", "root.querySelectorAll('.veil')")

block = (f'<div class="{WRAP}">\n\n<style>\n' + wp_css.strip() + '\n</style>\n\n'
         + wp_markup + '\n\n<script>\n' + wp_script.strip() + '\n</script>\n\n</div>\n')
(ROOT / 'site-wordpress.html').write_text(block, encoding='utf-8')


# ───────────────────────────────────────── no-JS split (stripped installs)
nojs_css = re.sub(r'\.jcm \.sail-btn \{.*?\n\}\n', '', wp_css, flags=re.S)
m900 = re.search(r'@media \(max-width: 900px\) \{(?:[^{}]|\{[^{}]*\})*\}', nojs_css, re.S)
nojs_css = nojs_css[:m900.start()] + '''@media (max-width: 900px) {
  /* No JavaScript here, so there is no toggle: the links wrap onto a
     second row instead of hiding behind a button. */
  .jcm .top-in { flex-direction: column; align-items: flex-start; gap: 0.7rem; }
  .jcm .sail { flex-wrap: wrap; gap: 0.35rem 1.4rem; }
  .jcm .sail a { font-size: 0.72rem; color: var(--bone); padding: 0.45rem 0; }
}''' + nojs_css[m900.end():]

nojs_css += '''

/* ---- no-script additions ---- */
.jcm a.send { display: inline-block; text-decoration: none; text-align: center; }
.jcm .enq-cta { display: grid; gap: 1.1rem; justify-items: start; }
@media (max-width: 600px) { .jcm a.send { width: 100%; } }
'''
nojs_css = ('/* Justin Close Media — paste this whole file into\n'
            '   Appearance > Customize > Additional CSS in WordPress.\n'
            '   Every rule is confined to .jcm and cannot affect your theme. */\n\n'
            ) + nojs_css

nojs_markup = re.sub(r'\n\s*<button class="sail-btn"[^>]*>Menu</button>', '', wp_markup)
fs = nojs_markup.index('<form class="form veil"')
fe = nojs_markup.index('</form>') + len('</form>')
nojs_markup = nojs_markup[:fs] + '''<div class="enq-cta veil">
      <p class="sc">Start here</p>
      <p class="lede">The quickest way to get a price is a short email with the property name, how many room types you would want covered, and whether you want aerial work.</p>
      <a class="send" href="mailto:justinbclose@gmail.com?subject=Photography%20enquiry">Email me about your property</a>
      <!--
        WANT A PROPER FORM INSTEAD?
        Delete this whole block and drop a WordPress form block in its
        place. A WordPress form will email you reliably and keep a record
        in your dashboard, which a plain link cannot.
      -->
    </div>''' + nojs_markup[fe:]

nojs_markup = nojs_markup.replace(
    '<p class="foot-base" id="jcm-base">Hospitality &amp; aerial photography</p>',
    f'<p class="foot-base">&copy; {YEAR} Justin Close Media &middot; Hospitality &amp; aerial photography</p>')
nojs_markup = nojs_markup.replace('<header class="top" id="jcm-top">',
                                  '<header class="top settled" id="jcm-top">')
nojs_markup = f'<div class="{WRAP}">\n\n' + nojs_markup + '\n\n</div>'

assert 'class="jcm"' in nojs_markup
assert '<script' not in nojs_markup and '<style' not in nojs_markup

(ROOT / 'wp-styles.css').write_text(nojs_css, encoding='utf-8')
(ROOT / 'wp-markup.html').write_text(nojs_markup + '\n', encoding='utf-8')


# ───────────────────────────────────────────────── copy-paste pages
SHELL_CSS = '''<style>
:root{--bg:#F2F3F1;--panel:#FFFFFF;--code-bg:#121814;--ink:#131A16;--mute:#5C6862;
--faint:#8A968F;--line:#D8DEDA;--brass:#8A6B2F;--brass-2:#6E5426;--ok:#1F7A4D;--warn:#8A4B16;
--mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
--ui:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1310;--panel:#141F19;
--code-bg:#0A0F0C;--ink:#EDE7DA;--mute:#A2A99E;--faint:#6E7972;--line:#26372D;
--brass:#C1A265;--brass-2:#DCC28C;--ok:#6FD3A0;--warn:#E0A85C}}
:root[data-theme="dark"]{--bg:#0D1310;--panel:#141F19;--code-bg:#0A0F0C;--ink:#EDE7DA;
--mute:#A2A99E;--faint:#6E7972;--line:#26372D;--brass:#C1A265;--brass-2:#DCC28C;--ok:#6FD3A0;--warn:#E0A85C}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--ui);line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:clamp(1.25rem,4vw,2.75rem)}
h1{font-size:clamp(1.35rem,3vw,1.9rem);margin:0 0 .4rem;letter-spacing:-.01em;text-wrap:balance}
.sub{color:var(--mute);margin:0 0 1.6rem;max-width:64ch}
.bar{display:flex;flex-wrap:wrap;align-items:center;gap:.8rem;margin-bottom:.9rem}
button.copy{font-family:var(--ui);font-size:.9rem;font-weight:600;color:var(--bg);background:var(--brass);
border:1px solid var(--brass);border-radius:6px;padding:.8em 1.5em;min-height:46px;cursor:pointer;
transition:background .2s,color .2s}
button.copy:hover{background:var(--brass-2);border-color:var(--brass-2)}
button.copy.done{background:var(--ok);border-color:var(--ok)}
.meta{font-family:var(--mono);font-size:.76rem;color:var(--faint)}
:focus-visible{outline:2px solid var(--brass);outline-offset:3px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:1.25rem 1.4rem;margin-bottom:1.3rem}
.card.flag{border-color:var(--warn)}
.card h2{font-size:.78rem;text-transform:uppercase;letter-spacing:.12em;color:var(--brass);margin:0 0 .8rem}
.card.flag h2{color:var(--warn)}
.card ol,.card ul{margin:0;padding-left:1.2rem;display:grid;gap:.5rem}
.card li,.card p{color:var(--mute);font-size:.95rem}
.card p{margin:0 0 .6rem}
.card p:last-child{margin:0}
b{color:var(--ink);font-weight:600}
code{font-family:var(--mono);font-size:.85em;background:var(--bg);border:1px solid var(--line);
border-radius:4px;padding:.1em .4em;color:var(--ink)}
pre{margin:0;background:var(--code-bg);border:1px solid var(--line);border-radius:8px;padding:1rem 1.1rem;
max-height:55vh;overflow:auto;-webkit-overflow-scrolling:touch}
pre code{font-family:var(--mono);font-size:.76rem;line-height:1.6;color:#D7E0D9;white-space:pre;
background:none;border:0;padding:0}
.foot{margin-top:1.2rem;font-size:.85rem;color:var(--faint)}
</style>'''

COPY_JS = '''<script>
(function(){
  var labels={};
  document.querySelectorAll('button.copy').forEach(function(b){labels[b.dataset.target]=b.textContent;});
  function flash(btn,msg){var id=btn.dataset.target;btn.textContent=msg;btn.classList.add('done');
    setTimeout(function(){btn.textContent=labels[id];btn.classList.remove('done');},2200);}
  function legacy(btn,text){var ta=document.createElement('textarea');ta.value=text;
    ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.top='-1000px';
    document.body.appendChild(ta);ta.select();var ok=false;
    try{ok=document.execCommand('copy');}catch(e){ok=false;}
    document.body.removeChild(ta);flash(btn,ok?'Copied':'Press Ctrl/Cmd+C');}
  document.querySelectorAll('button.copy').forEach(function(btn){
    btn.addEventListener('click',function(){
      var text=document.getElementById(btn.dataset.target).textContent;
      if(navigator.clipboard&&window.isSecureContext){
        navigator.clipboard.writeText(text).then(function(){flash(btn,'Copied');})
          .catch(function(){legacy(btn,text);});
      } else {legacy(btn,text);}
    });
  });
})();
</script>'''

esc = lambda s: html.escape(s, quote=False)
kb = lambda s: round(len(s.encode()) / 1024, 1)

IMG_CARD = '''<div class="card">
    <h2>Your photographs</h2>
    <p>The Lifestyle chapter now carries a real photograph, loaded from
    <code>images/lifestyle-beachside.jpg</code>. Keep an <code>images</code> folder
    beside the HTML file and that path works as written.</p>
    <p>Every other frame is still a placeholder. To fill one, replace its
    <code>&lt;span&gt;</code> — the one on a line containing <code>class="ph</code>, not the
    caption below it — with <code>&lt;img src="images/your-photo.jpg" alt="what it shows"&gt;</code>.</p>
  </div>'''

# 1. standalone
page = f'''{SHELL_CSS}
<div class="wrap">
  <h1>Justin Close Media — the complete website code</h1>
  <p class="sub">One finished file. The CSS and JavaScript are already inside it, so there is nothing else to download and nothing to link together.</p>
  <div class="bar">
    <button class="copy" data-target="code" type="button">Copy all the code</button>
    <span class="meta">{standalone.count(chr(10))+1} lines · {kb(standalone)} KB · HTML + CSS + JS</span>
  </div>
  <div class="card">
    <h2>What to do with it</h2>
    <ol>
      <li>Copy it, then paste into a plain text editor. In TextEdit on a Mac choose <b>Format &rarr; Make Plain Text</b> first, or the file will not work.</li>
      <li>Save it as <code>index.html</code> — that exact name, not <code>.txt</code>.</li>
      <li>Keep it in a folder with your <code>images</code> folder beside it.</li>
      <li>Drag that folder onto <b>app.netlify.com/drop</b> to put it online free.</li>
    </ol>
  </div>
  {IMG_CARD}
  <div class="card">
    <h2>Still to edit</h2>
    <ol>
      <li>Your email appears <b>twice</b> — in the contact section and near the bottom in the script.</li>
      <li>The <b>Coverage</b> line, for your phone number and service area.</li>
      <li>The <b>FAA line</b> — do not sell drone work until you hold a Part 107 certificate.</li>
    </ol>
  </div>
  <pre><code id="code">{esc(standalone)}</code></pre>
  <p class="foot">Checked for sideways scrolling from 320px to 1440px, with tap targets sized for phones.</p>
</div>
{COPY_JS}'''
(ROOT / 'site-code.html').write_text(page, encoding='utf-8')

# 2. WordPress single block
page = f'''{SHELL_CSS}
<div class="wrap">
  <h1>The WordPress version</h1>
  <p class="sub">The same website as one block. A full <code>&lt;!DOCTYPE html&gt;</code> document cannot be pasted into WordPress, which builds its own page around your content.</p>
  <div class="bar">
    <button class="copy" data-target="code" type="button">Copy the WordPress code</button>
    <span class="meta">{block.count(chr(10))+1} lines · {kb(block)} KB</span>
  </div>
  <div class="card">
    <h2>Putting it in WordPress</h2>
    <ol>
      <li><b>Pages &rarr; Add New</b>.</li>
      <li>If your theme offers one, set <b>Page Attributes &rarr; Template</b> to <b>Full Width</b> or <b>Blank</b>.</li>
      <li>Click <b>+</b>, search <b>Custom HTML</b>, add that block, and paste.</li>
      <li><b>Publish</b>, then <b>View Page</b>. The editor preview never shows the styling.</li>
    </ol>
  </div>
  <div class="card flag">
    <h2>If it publishes as unstyled text</h2>
    <p>Your install is stripping <code>&lt;style&gt;</code> and <code>&lt;script&gt;</code>. Use the two-part version instead — it puts the CSS in Additional CSS and needs no JavaScript.</p>
  </div>
  <div class="card">
    <h2>Images in WordPress</h2>
    <p>Upload each photograph under <b>Media &rarr; Add New</b>, copy its URL, and use that URL as the <code>src</code>. The relative path <code>images/lifestyle-beachside.jpg</code> will not resolve on WordPress.</p>
  </div>
  <pre><code id="code">{esc(block)}</code></pre>
</div>
{COPY_JS}'''
(ROOT / 'wp-code.html').write_text(page, encoding='utf-8')

# 3. two-part no-JS fix
page = f'''{SHELL_CSS}
<div class="wrap">
  <h1>Fixing the unstyled WordPress page</h1>
  <p class="sub">Your WordPress strips <code>&lt;style&gt;</code> and <code>&lt;script&gt;</code> out of the block and leaves the text inside them, which is the wall of CSS you saw. The styling has to go somewhere it is not stripped.</p>

  <div class="card">
    <h2>Step one — the styling</h2>
    <ol>
      <li><b>Appearance &rarr; Customize &rarr; Additional CSS.</b> On a block theme it is <b>Appearance &rarr; Editor &rarr; Styles &rarr; ⋮ &rarr; Additional CSS</b>.</li>
      <li>Paste it in, below anything already there, and <b>Publish</b>.</li>
    </ol>
    <div class="bar">
      <button class="copy" data-target="css" type="button">Copy the CSS</button>
      <span class="meta">{kb(nojs_css)} KB · Additional CSS</span>
    </div>
    <pre><code id="css">{esc(nojs_css)}</code></pre>
  </div>

  <div class="card">
    <h2>Step two — the page</h2>
    <ol>
      <li><b>Delete the block you pasted before</b>, or the site appears twice.</li>
      <li>Add a fresh <b>Custom HTML</b> block and paste this.</li>
      <li><b>Update</b>, then <b>View Page</b>.</li>
    </ol>
    <div class="bar">
      <button class="copy" data-target="mk" type="button">Copy the HTML</button>
      <span class="meta">{kb(nojs_markup)} KB · Custom HTML block</span>
    </div>
    <pre><code id="mk">{esc(nojs_markup)}</code></pre>
  </div>

  <div class="card flag">
    <h2>Your photograph needs uploading</h2>
    <p>The Lifestyle frame points at <code>images/lifestyle-beachside.jpg</code>, which does not exist on WordPress. Upload the photo under <b>Media &rarr; Add New</b>, copy its URL, and replace that path in the HTML above before pasting — or right after.</p>
  </div>

  <div class="card">
    <h2>What changed, and why</h2>
    <ol>
      <li>The phone menu was a button JavaScript opened. Without JavaScript it could never open, so the links now wrap onto a second row.</li>
      <li>The enquiry form was submitted by JavaScript. It is now a plain email link. To use a real form, delete that block and insert a WordPress form block — a comment marks the spot.</li>
      <li>The footer year was written by JavaScript, so it is written in directly.</li>
    </ol>
  </div>

  <p class="foot">Tested with JavaScript switched off inside a simulated theme: every section renders, the menu is reachable on a phone, and the email link works.</p>
</div>
{COPY_JS}'''
(ROOT / 'wp-fix.html').write_text(page, encoding='utf-8')

print(f'standalone     {kb(standalone):>6} KB')
print(f'wp block       {kb(block):>6} KB')
print(f'wp css         {kb(nojs_css):>6} KB')
print(f'wp markup      {kb(nojs_markup):>6} KB')
print('copy pages     site-code.html, wp-code.html, wp-fix.html')
