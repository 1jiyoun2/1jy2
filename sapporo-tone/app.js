/* Sapporo Milk — client-only photo/video winter color grade.
 * Files never leave the browser. The same WebGL shader is used for preview and export.
 * Output is an interpretation of the reference palette, not a pixel-identical guarantee.
 */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const els = {
    input: $('file-input'), drop: $('drop-zone'), empty: $('stage-empty'), media: $('stage-media'),
    canvas: $('result-canvas'), original: $('original-canvas'), rule: $('compare-rule'),
    processing: $('stage-processing'), processingText: $('stage-processing-text'),
    fileInfo: $('file-info'), replace: $('replace-button'), reset: $('reset-button'),
    comparePanel: $('compare-panel'), compare: $('compare-slider'), videoControls: $('video-controls'),
    play: $('play-button'), seek: $('seek-slider'), time: $('video-time'),
    video: $('source-video'), export: $('export-button'), exportStatus: $('export-status'),
    exportFormat: $('export-format-label'), autoInfo: $('auto-info'), stop: $('stop-button'),
    auto: $('auto-exposure'), strength: $('strength'), light: $('light'), warmth: $('warmth'),
    softness: $('softness'), grain: $('grain')
  };
  const defaults = { auto: true, strength: 80, light: 0, warmth: -8, softness: 65, grain: 8 };
  const sampleCanvas = document.createElement('canvas');
  sampleCanvas.width = sampleCanvas.height = 128;
  const sampleContext = sampleCanvas.getContext('2d', { willReadFrequently: true });
  const originalContext = els.original.getContext('2d', { alpha: false });
  let current = null, currentURL = null, glRenderer = null, fallbackContext = null;
  let autoExposure = 0, smoothExposure = 0, rafId = 0, frameCallbackId = null;
  let lastSampleTime = -99, saving = false, stopRecording = null, fileSerial = 0;
  let audioBus = null; // A media element can only be bound to one MediaElementAudioSourceNode.
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
  const easing = (a, b, t) => a + (b - a) * t;

  function status(message, isError = false) {
    els.exportStatus.textContent = message;
    els.exportStatus.style.color = isError ? '#a45b58' : '';
  }
  function busy(message, value) {
    els.processing.hidden = !value;
    els.processingText.textContent = message;
    els.drop.setAttribute('aria-busy', String(value));
  }
  function readableTime(total) {
    if (!Number.isFinite(total) || total < 0) total = 0;
    const n = Math.floor(total);
    return `${String(Math.floor(n / 60)).padStart(2, '0')}:${String(n % 60).padStart(2, '0')}`;
  }
  function updateLabels() {
    for (const id of ['strength', 'light', 'warmth', 'softness', 'grain']) {
      const v = Number(els[id].value);
      $(id + '-value').textContent = id === 'light' || id === 'warmth' ? `${v > 0 ? '+' : ''}${v}` : `${v}%`;
    }
    els.autoInfo.textContent = els.auto.checked ? 'AUTO EXPOSURE' : 'MANUAL EXPOSURE';
  }
  function resetSettings() {
    els.auto.checked = defaults.auto;
    for (const id of ['strength', 'light', 'warmth', 'softness', 'grain']) els[id].value = defaults[id];
    updateLabels();
    if (current) renderFrame();
  }

  const vertexSource = `
    attribute vec2 position;
    varying vec2 uv;
    void main() { uv = (position + 1.0) * 0.5; gl_Position = vec4(position, 0.0, 1.0); }
  `;
  const fragmentSource = `
    precision mediump float;
    varying vec2 uv;
    uniform sampler2D image;
    uniform float uExposure;
    uniform float uStrength;
    uniform float uWarmth;
    uniform float uSoftness;
    uniform float uGrain;
    uniform vec2 uResolution;
    float luminance(vec3 c) { return dot(c, vec3(0.2126,0.7152,0.0722)); }
    float random(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
    void main() {
      vec3 src = texture2D(image, vec2(uv.x, 1.0-uv.y)).rgb;
      vec3 c = src * exp2(uExposure);
      // Soft highlight shoulder retains snow texture instead of hard clipping.
      float shoulder = 0.10 + 0.14*uSoftness;
      c = c / (1.0 + shoulder*c) * (1.0 + shoulder*0.72);
      c = (c - 0.5)*(1.0-0.16*uSoftness) + 0.5;
      c += 0.012*uSoftness*(1.0-smoothstep(0.03,0.56,luminance(c)));
      float y = luminance(c);
      c = mix(vec3(y), c, 0.82);
      float shadow = 1.0-smoothstep(0.08,0.69,y);
      float highlight = smoothstep(0.40,0.95,y);
      // Slate-blue in shadows, milky ivory highlights; deliberately subtle.
      c += vec3(-0.014,0.002,0.025)*shadow;
      c += vec3(0.023,0.013,-0.005)*highlight;
      c += uWarmth * vec3(0.048,0.022,-0.050);
      c = mix(src, c, uStrength);
      float grain = (random(floor(uv*uResolution*0.83))-0.5)*0.055*uGrain*uStrength;
      c += vec3(grain);
      gl_FragColor = vec4(clamp(c,0.0,1.0),1.0);
    }
  `;
  function compile(gl, kind, source) {
    const shader = gl.createShader(kind);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      const why = gl.getShaderInfoLog(shader);
      gl.deleteShader(shader);
      throw new Error('그래픽 처리기를 준비할 수 없습니다: ' + why);
    }
    return shader;
  }
  function createRenderer() {
    const gl = els.canvas.getContext('webgl', { alpha: false, preserveDrawingBuffer: true, antialias: false, powerPreference: 'default' })
      || els.canvas.getContext('experimental-webgl', { alpha: false, preserveDrawingBuffer: true });
    if (!gl) {
      fallbackContext = els.canvas.getContext('2d', { willReadFrequently: true, alpha: false });
      return null;
    }
    const program = gl.createProgram();
    const vs = compile(gl, gl.VERTEX_SHADER, vertexSource);
    const fs = compile(gl, gl.FRAGMENT_SHADER, fragmentSource);
    gl.attachShader(program, vs); gl.attachShader(program, fs); gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error('색감 처리기를 초기화할 수 없습니다.');
    gl.deleteShader(vs); gl.deleteShader(fs); gl.useProgram(program);
    const buffer = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
    const pos = gl.getAttribLocation(program, 'position'); gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);
    const tex = gl.createTexture(); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D,tex);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    gl.uniform1i(gl.getUniformLocation(program,'image'),0);
    const uniforms = Object.fromEntries(['uExposure','uStrength','uWarmth','uSoftness','uGrain','uResolution'].map(k => [k, gl.getUniformLocation(program,k)]));
    return { gl, tex, program, uniforms, maxSize: gl.getParameter(gl.MAX_TEXTURE_SIZE) };
  }
  function mediaDimensions() {
    return current?.kind === 'video'
      ? [els.video.videoWidth, els.video.videoHeight]
      : [current?.image.naturalWidth, current?.image.naturalHeight];
  }
  function fittingSize(w, h, maxSide, maxPixels) {
    const scale = Math.min(1, maxSide / Math.max(w,h), Math.sqrt(maxPixels/(w*h)));
    return [Math.max(1,Math.round(w*scale)),Math.max(1,Math.round(h*scale))];
  }
  function setCanvasSize(width, height) {
    if (els.canvas.width !== width || els.canvas.height !== height) {
      els.canvas.width = width; els.canvas.height = height;
    }
    if (els.original.width !== width || els.original.height !== height) {
      els.original.width = width; els.original.height = height;
    }
  }
  function exposureFor(source) {
    if (!sampleContext) return 0;
    try {
      const w=sampleCanvas.width, h=sampleCanvas.height;
      sampleContext.clearRect(0,0,w,h);
      sampleContext.drawImage(source, 0,0,w,h);
      const bytes = sampleContext.getImageData(0,0,w,h).data;
      const hist=new Uint32Array(256);
      let count=0, bright=0;
      for(let i=0;i<bytes.length;i+=16) {
        const l=Math.round(bytes[i]*0.2126+bytes[i+1]*0.7152+bytes[i+2]*0.0722);
        hist[clamp(l,0,255)]++; count++;
        if(l>197) bright++;
      }
      const percentile= p => {
        const threshold=count*p; let total=0;
        for(let i=0;i<256;i++) {total+=hist[i]; if(total>=threshold) return i/255;}
        return 1;
      };
      const mid=percentile(.50), high=percentile(.92), brightShare=bright/count;
      const isSnow = high>.79 && brightShare>.28 && mid>.47;
      const desired = isSnow ? .66 : .55;
      let ev = Math.log2((desired+.024)/(mid+.024));
      if(ev>0 && high>.78) ev=Math.min(ev,Math.log2(.91/high)+.60);
      return clamp(ev,-1.05,1.45);
    } catch(error) {
      console.warn('Brightness sampling unavailable:',error);
      return 0;
    }
  }
  function settings() {
    return {
      exposure:(els.auto.checked ? smoothExposure : 0)+Number(els.light.value)/100,
      strength:Number(els.strength.value)/100,
      warmth:Number(els.warmth.value)/100,
      softness:Number(els.softness.value)/100,
      grain:Number(els.grain.value)/100
    };
  }
  function pixelGrade(ctx, w, h, cfg) {
    const frame=ctx.getImageData(0,0,w,h); const b=frame.data;
    const gain=Math.pow(2,cfg.exposure), s=cfg.softness;
    const shoulder=.10+.14*s;
    for(let i=0;i<b.length;i+=4) {
      const src=[b[i]/255,b[i+1]/255,b[i+2]/255];
      let c=src.map(v=>{v*=gain; return (v/(1+shoulder*v)*(1+shoulder*.72)-.5)*(1-.16*s)+.5;});
      let y=.2126*c[0]+.7152*c[1]+.0722*c[2];
      const shadowLift=.012*s*(1-smoothstep(.03,.56,y)); c=c.map(v=>v+shadowLift);
      y=.2126*c[0]+.7152*c[1]+.0722*c[2];
      c=c.map(v=>y*.18+v*.82);
      const sh=1-smoothstep(.08,.69,y), hi=smoothstep(.40,.95,y);
      const shadow=[-.014,.002,.025], highlight=[.023,.013,-.005], warming=[.048,.022,-.05];
      for(let j=0;j<3;j++) {
        c[j]+=shadow[j]*sh+highlight[j]*hi+warming[j]*cfg.warmth;
        b[i+j]=clamp(Math.round((src[j]*(1-cfg.strength)+c[j]*cfg.strength)*255),0,255);
      }
    }
    ctx.putImageData(frame,0,0);
  }
  function smoothstep(a,b,x) {const t=clamp((x-a)/(b-a),0,1);return t*t*(3-2*t);}
  function renderFrame(options={}) {
    if(!current) return;
    const source=current.kind === 'video' ? els.video : current.image;
    if(current.kind==='video' && els.video.readyState<2) return;
    const [w,h]=mediaDimensions(); if(!w||!h) return;
    const [pw,ph] = options.width && options.height ? [options.width,options.height] : fittingSize(w,h,1400,1700000);
    setCanvasSize(pw,ph);
    const cfg=settings();
    if(glRenderer) {
      const {gl, uniforms} = glRenderer;
      try {
        gl.viewport(0,0,pw,ph);
        gl.useProgram(glRenderer.program);
        // HTMLImageElement and HTMLVideoElement follow the same texture orientation.
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
        gl.bindTexture(gl.TEXTURE_2D,glRenderer.tex);
        gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,source);
        gl.uniform1f(uniforms.uExposure,cfg.exposure);
        gl.uniform1f(uniforms.uStrength,cfg.strength);
        gl.uniform1f(uniforms.uWarmth,cfg.warmth);
        gl.uniform1f(uniforms.uSoftness,cfg.softness);
        gl.uniform1f(uniforms.uGrain,cfg.grain);
        gl.uniform2f(uniforms.uResolution,pw,ph);
        gl.drawArrays(gl.TRIANGLE_STRIP,0,4);
      } catch(error) {
        console.error('Color rendering failed:',error);
        status('이 파일은 브라우저의 그래픽 처리 기능으로 표시할 수 없습니다.',true);
      }
    } else if(fallbackContext) {
      fallbackContext.drawImage(source,0,0,pw,ph);
      try {pixelGrade(fallbackContext,pw,ph,cfg);} catch(e) {console.error(e);}
    }
    if(!options.skipOriginal) originalContext.drawImage(source,0,0,pw,ph);
  }
  function renderVideoFrame() {
    if(!current || current.kind!=='video' || els.video.paused || els.video.ended) return;
    if(els.auto.checked && els.video.currentTime-lastSampleTime>.85) {
      const target=exposureFor(els.video);
      // Smooth adaptation prevents exposure flicker between consecutive frames.
      autoExposure=target;
      lastSampleTime=els.video.currentTime;
    }
    smoothExposure=easing(smoothExposure,autoExposure,.035);
    renderFrame();
    updateVideoTime();
    rafId=requestAnimationFrame(renderVideoFrame);
  }
  function stopLoop() {cancelAnimationFrame(rafId); rafId=0; if(frameCallbackId!==null && els.video.cancelVideoFrameCallback) els.video.cancelVideoFrameCallback(frameCallbackId); frameCallbackId=null;}
  function updateVideoTime() {
    if(!current || current.kind!=='video') return;
    const total=els.video.duration||0;
    els.time.textContent=`${readableTime(els.video.currentTime)} / ${readableTime(total)}`;
    els.seek.value=total ? Math.round(els.video.currentTime/total*1000) : 0;
    els.play.textContent=els.video.paused || els.video.ended ? '▶' : '❚❚';
  }
  function releaseCurrent() {
    stopLoop();
    els.video.pause(); els.video.removeAttribute('src'); els.video.load();
    if(currentURL) { URL.revokeObjectURL(currentURL);currentURL=null; }
    current=null;
  }
  function isVideo(file) {
    return file.type.startsWith('video/') || /\.(mov|mp4|m4v|webm|ogv)$/i.test(file.name);
  }
  function isImage(file) {
    return file.type.startsWith('image/') || /\.(jpe?g|png|webp|heic|heif|avif)$/i.test(file.name);
  }
  async function loadMedia(file) {
    if(!file || saving) return;
    if(!isVideo(file) && !isImage(file)) return status('사진 또는 영상 파일만 선택할 수 있습니다.',true);
    if(file.size > 900*1024*1024) return status('900MB가 넘는 파일은 이 편집기에서 지원하지 않습니다.',true);
    const serial=++fileSerial;
    releaseCurrent();
    busy('파일을 불러오는 중...',true);
    els.export.disabled=true;
    currentURL=URL.createObjectURL(file);
    const kind=isVideo(file)?'video':'image';
    try {
      if(kind==='image') {
        const img=new Image(); img.decoding='async';
        await new Promise((resolve,reject)=>{img.onload=resolve;img.onerror=()=>reject(new Error('사진을 열 수 없습니다. HEIC 등 지원되지 않는 형식일 수 있습니다.'));img.src=currentURL;});
        if(serial!==fileSerial) return;
        if(!img.naturalWidth || !img.naturalHeight) throw new Error('사진 크기를 확인할 수 없습니다.');
        current={file,kind,image:img};
        autoExposure=exposureFor(img);
      } else {
        const video=els.video;
        video.muted=true;
        video.src=currentURL;
        video.load();
        await new Promise((resolve,reject)=>{
          if(video.readyState>=2) return resolve();
          const onReady=()=>{cleanup();resolve();};
          const onFail=()=>{cleanup();reject(new Error('영상을 열 수 없습니다. 다른 형식으로 변환한 뒤 시도해 주세요.'));};
          function cleanup(){video.removeEventListener('loadeddata',onReady);video.removeEventListener('error',onFail);}
          video.addEventListener('loadeddata',onReady,{once:true});
          video.addEventListener('error',onFail,{once:true});
        });
        if(serial!==fileSerial) return;
        if(!video.videoWidth||!video.videoHeight) throw new Error('영상 크기를 읽을 수 없습니다.');
        current={file,kind}; autoExposure=exposureFor(video);lastSampleTime=-99;
        updateVideoTime();
      }
      smoothExposure=autoExposure;
      els.empty.hidden=true;els.media.hidden=false;
      els.comparePanel.hidden=false;els.videoControls.hidden=kind!=='video';
      els.replace.disabled=false;els.reset.disabled=false;els.export.disabled=false;
      els.exportFormat.textContent=kind==='image'?'사진 · JPG 고화질':'영상 · 브라우저 지원 형식';
      els.fileInfo.textContent=`${file.name} · ${mediaDimensions().join(' × ')}`;
      renderFrame();
      status(kind==='image'?'보정 완료. 비교 슬라이더로 원본과 비교해 보세요.':'보정 미리보기 준비 완료. 영상 저장은 재생 길이만큼 진행됩니다.');
    } catch(error) {
      console.error(error);
      if(serial===fileSerial) {
        releaseCurrent();els.empty.hidden=false;els.media.hidden=true;
        els.comparePanel.hidden=true;els.videoControls.hidden=true;
        els.fileInfo.textContent='파일을 열 수 없습니다';
        status(error.message||'파일을 불러오지 못했습니다.',true);
      }
    } finally {if(serial===fileSerial) busy('',false);}
  }
  function refreshComparison() {
    const pct=Number(els.compare.value);
    els.original.style.clipPath=`inset(0 ${100-pct}% 0 0)`;
    els.rule.style.left=`${pct}%`;
  }
  async function photoExport() {
    const [w,h]=mediaDimensions();
    const maxSize=glRenderer?.maxSize || 4096;
    const [ew,eh]=fittingSize(w,h,Math.min(maxSize,5200),14000000);
    const [pw,ph]=[els.canvas.width,els.canvas.height];
    try {
      // Preserve original image dimensions when feasible, rather than exporting the preview.
      renderFrame({width:ew,height:eh,skipOriginal:true});
      const blob=await new Promise(resolve=>els.canvas.toBlob(resolve,'image/jpeg',0.94));
      if(!blob) throw new Error('사진 파일을 만들지 못했습니다.');
      download(blob, `${current.file.name.replace(/\.[^.]+$/,'')}_sapporo-milk.jpg`);
      status(`저장 준비 완료 · ${ew} × ${eh}px / JPG 고화질${ew<w?' (대용량 원본은 안전한 크기로 조정)':''}`);
    } finally {renderFrame({width:pw,height:ph});}
  }
  function download(blob,filename) {
    const href=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=href;a.download=filename;
    document.body.appendChild(a);a.click();a.remove();
    setTimeout(()=>URL.revokeObjectURL(href),60000);
  }
  function recordingMime() {
    if(!window.MediaRecorder || !els.canvas.captureStream) return '';
    for(const type of ['video/mp4;codecs="avc1.42E01E,mp4a.40.2"','video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm','video/mp4']) {
      try {if(MediaRecorder.isTypeSupported(type)) return type;} catch(e) { /* continue */ }
    }
    return '';
  }
  async function seekTo(time) {
    if(Math.abs(els.video.currentTime-time)<.025 && els.video.readyState>=2) return;
    await new Promise((resolve,reject)=>{
      const cleanup=()=>{els.video.removeEventListener('seeked',done);els.video.removeEventListener('error',bad);clearTimeout(timer);};
      const done=()=>{cleanup();resolve();};const bad=()=>{cleanup();reject(new Error('영상을 이동할 수 없습니다.'));};
      const timer=setTimeout(()=>{cleanup();resolve();},4000);
      els.video.addEventListener('seeked',done,{once:true});els.video.addEventListener('error',bad,{once:true});
      els.video.currentTime=time;
    });
  }
  async function videoExport() {
    const mime=recordingMime();
    if(!mime) throw new Error('이 브라우저는 영상 저장을 지원하지 않습니다. 데스크톱 Chrome 또는 Edge에서 사용해 주세요.');
    const duration=els.video.duration;
    if(!Number.isFinite(duration) || duration<=0) throw new Error('길이를 알 수 없는 영상은 저장할 수 없습니다.');
    if(duration>180) throw new Error('영상 저장은 현재 3분 이하만 지원합니다. 짧게 잘라서 다시 올려주세요.');
    const [sourceW,sourceH]=mediaDimensions();
    const maxSize=glRenderer?.maxSize || 2048;
    const [ew,eh]=fittingSize(sourceW,sourceH,Math.min(maxSize,1920),2073600);
    const [pw,ph]=[els.canvas.width,els.canvas.height];
    const v=els.video;
    stopLoop();v.pause();
    await seekTo(0);
    autoExposure=exposureFor(v);smoothExposure=autoExposure;lastSampleTime=-99;
    renderFrame({width:ew,height:eh});
    const stream=els.canvas.captureStream(30);
    if(!stream?.getVideoTracks().length) throw new Error('영상 프레임을 녹화할 수 없습니다.');
    let audioContext=null, audioDestination=null;
    try {
      const AC=window.AudioContext||window.webkitAudioContext;
      if(AC) {
        if(!audioBus) {
          const ctx=new AC();
          audioBus={ context:ctx, source:ctx.createMediaElementSource(v) };
        }
        audioContext=audioBus.context;
        audioDestination=audioContext.createMediaStreamDestination();
        audioBus.source.connect(audioDestination);
        // No speaker output while exporting; audio goes into the recording stream.
        for(const track of audioDestination.stream.getAudioTracks()) stream.addTrack(track);
        await audioContext.resume();
      }
    } catch(e) {
      console.warn('Audio mux unavailable; exporting video without audio:',e);
      if(audioDestination && audioBus) audioBus.source.disconnect(audioDestination);
      audioDestination=null;
    }
    let recorder;
    try {recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:Math.min(10000000,ew*eh*5),audioBitsPerSecond:128000});}
    catch(error) {stream.getTracks().forEach(t=>t.stop());if(audioDestination && audioBus)audioBus.source.disconnect(audioDestination);if(audioContext)await audioContext.suspend();throw new Error('영상 인코더를 시작할 수 없습니다.');}
    const chunks=[];
    let finished=false, interrupted=false;
    const cleanup=async()=>{
      stopLoop();v.pause();v.muted=true;
      stream.getTracks().forEach(t=>t.stop());
      if(audioDestination && audioBus) audioBus.source.disconnect(audioDestination);
      if(audioContext && audioContext.state==='running') {try{await audioContext.suspend();}catch(_){}}
      els.stop.hidden=true;stopRecording=null;
      renderFrame({width:pw,height:ph});updateVideoTime();
    };
    const finishedPromise=new Promise((resolve,reject)=>{
      recorder.ondataavailable=e=>{if(e.data?.size)chunks.push(e.data);};
      recorder.onerror=e=>reject(new Error(e.error?.message||'영상 인코딩에 실패했습니다.'));
      recorder.onstop=()=>resolve();
    });
    const finish=()=>{if(finished)return;finished=true;try{if(recorder.state!=='inactive')recorder.stop();}catch(e){console.error(e);}};
    stopRecording=()=>{interrupted=true;finish();};
    els.stop.hidden=false;
    try {
      recorder.start(500);
      v.muted=false;
      await v.play();
      const tick=()=>{
        if(finished)return;
        if(els.auto.checked && v.currentTime-lastSampleTime>.85) {
          autoExposure=exposureFor(v);lastSampleTime=v.currentTime;
        }
        smoothExposure=easing(smoothExposure,autoExposure,.035);
        renderFrame({width:ew,height:eh});
        els.export.textContent=`영상 저장 중 ${Math.min(100,Math.round(v.currentTime/duration*100))}%`;
        status(`영상 녹화 중 · ${readableTime(v.currentTime)} / ${readableTime(duration)} · 다른 탭으로 이동하지 마세요.`);
        if(v.ended||v.currentTime>=duration-.035) {finish();return;}
        rafId=requestAnimationFrame(tick);
      };
      rafId=requestAnimationFrame(tick);
      v.addEventListener('ended',finish,{once:true});
      await finishedPromise;
      if(!interrupted) {
        const blob=new Blob(chunks,{type:recorder.mimeType||mime});
        if(!blob.size) throw new Error('녹화된 영상 데이터가 없습니다.');
        const ext=(recorder.mimeType||mime).includes('mp4')?'mp4':'webm';
        download(blob,`${current.file.name.replace(/\.[^.]+$/,'')}_sapporo-milk.${ext}`);
        status(`영상 저장 준비 완료 · ${ew} × ${eh}px / ${ext.toUpperCase()}. 다운로드를 확인해 주세요.`);
      } else status('영상 저장을 중단했습니다.');
    } finally {
      v.removeEventListener('ended',finish);
      if(recorder.state!=='inactive')finish();
      await cleanup();
    }
  }
  async function exportCurrent() {
    if(!current || saving) return;
    saving=true;els.export.disabled=true;els.replace.disabled=true;
    const originalText=els.export.innerHTML;
    try {
      if(current.kind==='image') await photoExport();
      else await videoExport();
    } catch(error) {
      console.error(error);
      status(error.message||'저장 중 오류가 발생했습니다.',true);
    } finally {
      saving=false;els.export.disabled=false;els.replace.disabled=false;
      els.export.innerHTML=originalText;
    }
  }
  async function togglePlayback() {
    if(!current || current.kind!=='video' || saving)return;
    if(!els.video.paused) {els.video.pause();stopLoop();}
    else {
      if(els.video.ended) await seekTo(0);
      try {await els.video.play();stopLoop();rafId=requestAnimationFrame(renderVideoFrame);}
      catch(error){status('영상을 재생하지 못했습니다.',true);}
    }
    updateVideoTime();
  }
  function installEvents() {
    els.drop.addEventListener('click',()=>{if(!current && !saving)els.input.click();});
    els.drop.addEventListener('keydown',e=>{if((e.key==='Enter'||e.key===' ')&&!current){e.preventDefault();els.input.click();}});
    const openFile=()=>{if(!saving)els.input.click();};
    els.replace.addEventListener('click',openFile);
    els.input.addEventListener('change',()=>{const file=els.input.files?.[0];if(file)loadMedia(file);els.input.value='';});
    for(const event of ['dragenter','dragover']) els.drop.addEventListener(event,e=>{e.preventDefault();if(!saving)els.drop.classList.add('dragover');});
    for(const event of ['dragleave','drop']) els.drop.addEventListener(event,e=>{e.preventDefault();els.drop.classList.remove('dragover');});
    els.drop.addEventListener('drop',e=>{if(!saving)loadMedia(e.dataTransfer?.files?.[0]);});
    els.reset.addEventListener('click',resetSettings);
    els.compare.addEventListener('input',refreshComparison);
    els.play.addEventListener('click',togglePlayback);
    els.video.addEventListener('timeupdate',updateVideoTime);
    els.video.addEventListener('pause',()=>{if(!saving)stopLoop();updateVideoTime();});
    els.video.addEventListener('ended',()=>{if(!saving)stopLoop();updateVideoTime();});
    els.seek.addEventListener('input',()=>{if(!current||current.kind!=='video'||saving)return;const t=(els.video.duration||0)*Number(els.seek.value)/1000;els.video.currentTime=t;});
    els.video.addEventListener('seeked',()=>{if(!saving){autoExposure=exposureFor(els.video);smoothExposure=autoExposure;renderFrame();}});
    els.auto.addEventListener('change',()=>{updateLabels();renderFrame();});
    for(const id of ['strength','light','warmth','softness','grain']) els[id].addEventListener('input',()=>{updateLabels();if(current)renderFrame();});
    els.export.addEventListener('click',exportCurrent);
    els.stop.addEventListener('click',()=>stopRecording?.());
    window.addEventListener('beforeunload',()=>{stopLoop();if(currentURL)URL.revokeObjectURL(currentURL);audioBus?.context.close();});
  }
  try {glRenderer=createRenderer();}
  catch(error) {console.warn('WebGL initialization failed:',error); /* Browser graphics APIs may be disabled. */}
  updateLabels();refreshComparison();installEvents();
})();