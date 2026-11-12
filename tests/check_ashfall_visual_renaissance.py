"""ASHFALL 85 — visual-only renaissance integration guardrails."""
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
PAGE=(ROOT/"app/ashfall_world.html").read_text(encoding="utf-8")
CSS=(ROOT/"app/static/ashfall-visual-renaissance-85.css").read_text(encoding="utf-8")

class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.canvas=[]
        self.body=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="link":self.links.append(a.get("href",""))
        if tag=="canvas":self.canvas.append(a.get("id"))
        if tag=="body":self.body.append(a.get("class",""))

def test_renaissance():
    parsed=Assets()
    parsed.feed(PAGE)
    assert "ashfall-renaissance" in parsed.body
    assert "world" in parsed.canvas
    assert "/static/ashfall-visual-renaissance-85.css?v=1" in parsed.links
    assert CSS.count("{")==CSS.count("}"),"Unbalanced CSS blocks"
    assert "pointer-events:none" in CSS,"Atmospheric overlays must not capture canvas input"
    assert "prefers-reduced-motion" in CSS
    assert "focus-visible" in CSS
    assert "@media (max-width:760px)" in CSS
    assert "ashfall-renaissance .bottom" in CSS
    assert "ashfall-renaissance .top" in CSS
    assert "ashfall-renaissance .left" in CSS
    atmosphere=(ROOT/"app/static/ashfall-living-atmosphere-86.js").read_text(encoding="utf-8")
    assert "/static/ashfall-living-atmosphere-86.js?v=1" in PAGE
    assert "ASHFALL_ATMOSPHERE?.update({mode,camera,width:w,height:h})" in PAGE
    assert "pointerEvents:\"none\"" in atmosphere
    assert "prefers-reduced-motion" in atmosphere
    assert "visibilitychange" in atmosphere
    assert "requestAnimationFrame" in atmosphere
    architecture=(ROOT/"app/static/ashfall-architecture-87.js").read_text(encoding="utf-8")
    assert "/static/ashfall-architecture-87.js?v=1" in PAGE
    assert PAGE.index('ashfall-art-13.js?v=4') < PAGE.index('ashfall-architecture-87.js?v=1')
    assert "ASHFALL_ART_EVOLUTION" in architecture
    assert "original(ctx,left,top,width,height,key,level)" in architecture
    for key in ("hq","farm","lumber","salvage","fuel","barracks"):
        assert 'key==="'+key+'"' in architecture
    assert "level>=15" in architecture and "level>=30" in architecture and "level>=50" in architecture


if __name__=="__main__":
    test_renaissance()
    print("ASHFALL 85 visual-only integration checks passed")
