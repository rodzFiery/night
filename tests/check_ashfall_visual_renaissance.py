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
    assert "/static/ashfall-living-atmosphere-86.js?v=2" in PAGE
    assert "ASHFALL_ATMOSPHERE?.update({mode,camera,width:w,height:h,levels:" in PAGE
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
    environment=(ROOT/"app/static/ashfall-environment-88.js").read_text(encoding="utf-8")
    assert "/static/ashfall-environment-88.js?v=1" in PAGE
    assert "window.ASHFALL_ENVIRONMENT_88?.draw(ctx);" in PAGE
    assert PAGE.index("window.ASHFALL_ENVIRONMENT_88?.draw(ctx);") < PAGE.index("const buildings=[")
    assert "createElement(\"canvas\")" in environment
    assert "if(!cache||key!==cacheKey)" in environment
    assert "ASHFALL_ENVIRONMENT_88" in environment
    assert "Math.hypot(x,y)" in environment
    lighting=(ROOT/"app/static/ashfall-lighting-89.js").read_text(encoding="utf-8")
    assert "/static/ashfall-lighting-89.js?v=1" in PAGE
    assert "ASHFALL_LIGHTING_89?.underlay(ctx,b,key,level)" in PAGE
    assert "ASHFALL_LIGHTING_89?.foreground(ctx,w,h,mode)" in PAGE
    assert PAGE.index("ASHFALL_LIGHTING_89?.underlay(ctx,b,key,level)") < PAGE.index("const artReady=window.ASHFALL_ART?.render")
    assert "createRadialGradient" in lighting
    assert "createLinearGradient" in lighting
    assert "level>=30" in lighting and "level>=15" in lighting
    living=(ROOT/"app/static/ashfall-living-settlement-90.js").read_text(encoding="utf-8")
    assert "/static/ashfall-living-settlement-90.js?v=1" in PAGE
    assert "ASHFALL_LIVING_90?.paint(ctx,t,view)" in atmosphere
    assert "ASHFALL_LIVING_90={paint,settings,version:90}" in living
    assert "levels:Object.fromEntries" in PAGE
    assert "if(level<=0)continue" in living
    assert "requestAnimationFrame" not in living
    wilderness=(ROOT/"app/static/ashfall-wilderness-91.js").read_text(encoding="utf-8")
    assert "/static/ashfall-wilderness-91.js?v=1" in PAGE
    assert "ASHFALL_WILDERNESS_91?.tile(ctx,iso,x,y,kind,seed,originX,originY)" in PAGE
    assert "ASHFALL_WILDERNESS_91?.prop(ctx,iso,x,y,kind,seed,originX,originY)" in PAGE
    assert "ASHFALL_WILDERNESS_91?.landmark(ctx,iso,x,y,kind)" in PAGE
    assert "ASHFALL_WILDERNESS_91={tile,prop,landmark,settings:config,version:91}" in wilderness
    for biome in ("forest","scrub","ridge","dust"):
        assert biome+":" in wilderness
    assert "requestAnimationFrame" not in wilderness
    gpu=(ROOT/"app/static/ashfall-gpu-92.js").read_text(encoding="utf-8")
    assert "/static/ashfall-gpu-92.js?v=1" in PAGE
    assert "ASHFALL_GPU_92?.update({mode,camera,width:w,height:h,originX:world.haven.x,originY:world.haven.y})" in PAGE
    assert 'getContext("webgl2"' in gpu
    assert "webglcontextlost" in gpu and "webglcontextrestored" in gpu
    assert "pointerEvents:\"none\"" in gpu
    assert 'view.mode!=="wilderness"' in gpu
    assert "gl.drawArrays(gl.TRIANGLES,0,3)" in gpu
    # ASHFALL 93: fullscreen triangle, correct alpha contract and bounded GPU allocation.
    assert "gl_VertexID==1?3.0:-1.0" in gpu
    assert "gl_VertexID==2?3.0:-1.0" in gpu
    assert "premultipliedAlpha:false" in gpu
    assert "outColor=vec4(shaded,alpha)" in gpu
    assert "settings.maxPixels" in gpu
    assert "pixelBudget/Math.max(1,view.width*view.height)" in gpu
    assert "vec3 scrub=" in gpu and "vec3 canopy=" in gpu
    assert "float erosion=" in gpu

    assert "requestAnimationFrame" not in gpu

    # ASHFALL 94: original vector artwork is loaded and versioned for all six buildings.
    assert "/static/ashfall-art-13.js?v=94" in PAGE
    art_loader=(ROOT/"app/static/ashfall-art-13.js").read_text(encoding="utf-8")
    assert 'img.src="/static/ashfall-art/"+key+".svg?v="+94' in art_loader
    from xml.etree import ElementTree
    for building in ("hq","farm","lumber","salvage","fuel","barracks"):
        asset=ROOT/"app/static/ashfall-art"/(building+".svg")
        source=asset.read_text(encoding="utf-8")
        assert "ASHFALL 94" in source
        root=ElementTree.fromstring(source)
        assert root.attrib.get("viewBox")=="0 0 512 400"
        assert len(list(root.iter()))>=25

    # ASHFALL 95: authored ground material asset with an independent fallback.
    roads=ROOT/"app/static/ashfall-art/settlement-roads-95.svg"
    assert roads.exists()
    from xml.etree import ElementTree as _ET
    _ET.parse(roads)
    ground=(ROOT/"app/static/ashfall-ground-20.js").read_text(encoding="utf-8")
    assert "/static/ashfall-ground-20.js?v=95" in PAGE
    assert 'authoredRoads.src="/static/ashfall-art/settlement-roads-95.svg?v=1"' in ground
    assert "if(authoredRoadsReady&&authoredRoads.naturalWidth)" in ground
    assert "objects.push({...p" in PAGE


    for key in ("hq","farm","lumber","salvage","fuel","barracks"):
        assert key+":" in lighting




if __name__=="__main__":
    test_renaissance()
    print("ASHFALL 85 visual-only integration checks passed")
