/* ASHFALL 92 — GPU Terrain Lighting Foundation.
 * Optional WebGL2 surface below the interactive world canvas.
 * World-coordinate, deterministic terrain shader. Zero gameplay mutations.
 * Disabled on context loss, reduced graphics preference or shader failure.
 * The 2D world remains authoritative for interactions and all sprites.
 */
(function(){
"use strict";
const settings={enabled:true,quality:"high",opacity:.16,animate:false};
const main=document.getElementById("world");
if(!main)return;
const surface=document.createElement("canvas");
surface.id="ashfall-gpu-terrain";
surface.setAttribute("aria-hidden","true");
Object.assign(surface.style,{position:"fixed",inset:"0",width:"100%",height:"100%",pointerEvents:"none",zIndex:"1",opacity:String(settings.opacity)});
main.insertAdjacentElement("afterend",surface);
const gl=surface.getContext("webgl2",{alpha:true,antialias:false,depth:false,stencil:false,premultipliedAlpha:true,preserveDrawingBuffer:false,powerPreference:"low-power"});
let program=null,vao=null,uniforms=null,failed=false,active=false;
const vertex=`#version 300 es
precision highp float;
out vec2 uv;
void main(){
 vec2 p=vec2((gl_VertexID==1||gl_VertexID==2)?3.0:-1.0,(gl_VertexID>=2)?3.0:-1.0);
 uv=p*.5+.5;gl_Position=vec4(p,0.0,1.0);
}`;
const fragment=`#version 300 es
precision highp float;
in vec2 uv;
out vec4 outColor;
uniform vec2 uResolution;
uniform vec2 uCamera;
uniform float uZoom;
uniform vec2 uOrigin;
uniform float uMode;
float hash21(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453123);}
float noise2(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);
 return mix(mix(hash21(i),hash21(i+vec2(1,0)),f.x),mix(hash21(i+vec2(0,1)),hash21(i+vec2(1,1)),f.x),f.y);}
void main(){
 vec2 screen=vec2(gl_FragCoord.x,uResolution.y-gl_FragCoord.y);
 vec2 world=(screen-uResolution*.5-uCamera)/max(.1,uZoom);
 // inverse of the isometric projection: x=(a-b)*64, y=(a+b)*32.
 vec2 tile=vec2(world.x/128.0+world.y/64.0,world.y/64.0-world.x/128.0)+uOrigin;
 float n=noise2(tile*.19),micro=noise2(tile*3.5),strata=noise2(tile*.65);
 float ridge=smoothstep(.61,.82,n),moist=smoothstep(.42,.68,strata);
 vec3 soil=mix(vec3(.28,.32,.27),vec3(.43,.37,.28),1.0-moist);
 soil=mix(soil,vec3(.46,.44,.38),ridge*.68);
 float rough=(micro-.5)*.12;
 vec3 lightDir=normalize(vec3(-.65,-.48,.7));
 vec2 e=vec2(.025,0.);
 float dx=noise2(tile*.65+e.xy)-noise2(tile*.65-e.xy);
 float dy=noise2(tile*.65+e.yx)-noise2(tile*.65-e.yx);
 vec3 normal=normalize(vec3(-dx*6.,-dy*6.,1.));
 float diffuse=.48+.52*max(dot(normal,lightDir),0.);
 vec3 shaded=(soil+rough)*diffuse;
 float vignette=1.0-smoothstep(.15,1.0,length((screen-uResolution*.5)/uResolution)*1.25);
 float alpha=(.22+.26*ridge+.13*micro)*vignette;
 // Overlay is deliberately translucent: original painted terrain and
 // existing server-sourced landmarks remain visually authoritative.
 outColor=vec4(shaded*alpha,alpha);
}`;
function shader(type,source){
 const sh=gl.createShader(type);gl.shaderSource(sh,source);gl.compileShader(sh);
 if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS)){const message=gl.getShaderInfoLog(sh);gl.deleteShader(sh);throw Error(message)}
 return sh;
}
function initialize(){
 if(!gl)return false;
 try{
  const v=shader(gl.VERTEX_SHADER,vertex),f=shader(gl.FRAGMENT_SHADER,fragment);
  program=gl.createProgram();gl.attachShader(program,v);gl.attachShader(program,f);gl.linkProgram(program);
  gl.deleteShader(v);gl.deleteShader(f);
  if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
  vao=gl.createVertexArray();
  uniforms=Object.fromEntries(["uResolution","uCamera","uZoom","uOrigin","uMode"].map(k=>[k,gl.getUniformLocation(program,k)]));
  gl.disable(gl.DEPTH_TEST);gl.disable(gl.BLEND);active=true;return true;
 }catch(e){console.warn("ASHFALL GPU renderer fallback:",e);failed=true;active=false;surface.hidden=true;return false}
}
function update(view){
 if(!settings.enabled||!active||failed||!view||view.mode!=="wilderness"){surface.hidden=true;return false}
 surface.hidden=false;
 const dpr=Math.min(window.devicePixelRatio||1,settings.quality==="low"?1:1.5);
 const w=Math.max(1,Math.round(view.width*dpr)),h=Math.max(1,Math.round(view.height*dpr));
 if(surface.width!==w||surface.height!==h){surface.width=w;surface.height=h}
 surface.style.opacity=String(Math.max(0,Math.min(.45,settings.opacity)));
 gl.viewport(0,0,w,h);gl.useProgram(program);gl.bindVertexArray(vao);
 gl.uniform2f(uniforms.uResolution,w,h);
 gl.uniform2f(uniforms.uCamera,(view.camera?.x||0)*dpr,(view.camera?.y||0)*dpr);
 gl.uniform1f(uniforms.uZoom,(view.camera?.zoom||1)*dpr);
 gl.uniform2f(uniforms.uOrigin,Number(view.originX)||0,Number(view.originY)||0);
 gl.uniform1f(uniforms.uMode,1);
 gl.drawArrays(gl.TRIANGLES,0,3);
 return true;
}
surface.addEventListener("webglcontextlost",e=>{e.preventDefault();active=false;surface.hidden=true});
surface.addEventListener("webglcontextrestored",()=>{failed=false;initialize()});
if(!initialize())surface.hidden=true;
window.ASHFALL_GPU_92={update,settings,status:()=>({active,failed,webgl2:!!gl,version:92})};
})();
