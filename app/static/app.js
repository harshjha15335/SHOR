'use strict';
const $ = (id) => document.getElementById(id);
const state = { keyConfigured: false, selectedAudio: null, recording: false, chunks: [], stream: null, audioContext: null, processor: null, micInput: null, started: 0 };
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = v => typeof v === 'number' ? v.toFixed(2) + '%' : '—';
const status = (msg, bad=false) => { $('form-status').style.color = bad ? '#ffa398' : '#c5f44b'; $('form-status').textContent=msg; };
function selected(file) {
  if (!file) return;
  if (!/\.(wav)$/i.test(file.name)) { status('Please select a WAV file (PCM).', true); return; }
  if (file.size > 8_000_000) {status('File exceeds 8 MB.',true);return;}
  state.selectedAudio = file;
  $('file-title').textContent = file.name;
  $('file-desc').textContent = (file.size / 1048576).toFixed(2) + ' MB · loaded locally';
  status('Audio ready. Add an exact reference transcript for WER/CER.');
  drawWave(file);
}
async function drawWave(file) {
  const canvas=$('waveform'), ctx=canvas.getContext('2d');
  ctx.clearRect(0,0,canvas.width,canvas.height);
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const bytes=await file.arrayBuffer(); const audio=await audioContext.decodeAudioData(bytes);
    const a=audio.getChannelData(0); const w=canvas.width=canvas.clientWidth*devicePixelRatio, h=canvas.height=84*devicePixelRatio;
    ctx.fillStyle='#0c1417';ctx.fillRect(0,0,w,h);ctx.strokeStyle='#c5f44b';ctx.lineWidth=Math.max(1,devicePixelRatio);ctx.beginPath();
    const stride=Math.max(1,Math.ceil(a.length/w));
    for(let i=0;i<w;i++){let peak=0;for(let j=i*stride;j<Math.min(a.length,(i+1)*stride);j++)peak=Math.max(peak,Math.abs(a[j]));ctx.moveTo(i,h/2-peak*h*.43);ctx.lineTo(i,h/2+peak*h*.43)}
    ctx.stroke(); await audioContext.close();
  } catch (e) {status('Could not preview WAV. Ensure it is uncompressed PCM.',true);}
}
function wavBlob(samples, sr) {
  const raw=new Int16Array(samples.length);
  for(let i=0;i<samples.length;i++) raw[i]=Math.round(Math.max(-1,Math.min(1,samples[i]))*32767);
  const buffer=new ArrayBuffer(44 + raw.length*2), view=new DataView(buffer);
  let off=0;function str(v){for(let i=0;i<v.length;i++)view.setUint8(off++,v.charCodeAt(i))}
  str('RIFF');view.setUint32(off,36+raw.length*2,true);off+=4;str('WAVE');str('fmt ');view.setUint32(off,16,true);off+=4;
  view.setUint16(off,1,true);off+=2;view.setUint16(off,1,true);off+=2;view.setUint32(off,sr,true);off+=4;view.setUint32(off,sr*2,true);off+=4;
  view.setUint16(off,2,true);off+=2;view.setUint16(off,16,true);off+=2;str('data');view.setUint32(off,raw.length*2,true);off+=4;
  for(let i=0;i<raw.length;i++,off+=2)view.setInt16(off,raw[i],true);
  return new Blob([buffer],{type:'audio/wav'});
}
async function record() {
  const btn=$('record-button');
  if(state.recording){
    state.recording=false;
    state.processor.disconnect();state.micInput.disconnect();state.stream.getTracks().forEach(t=>t.stop());
    const sr=state.audioContext.sampleRate;
    await state.audioContext.close();
    const len=state.chunks.reduce((n,x)=>n+x.length,0), samples=new Float32Array(len);let at=0;
    state.chunks.forEach(c=>{samples.set(c,at);at+=c.length});
    // WAV is recorded at the browser device sample rate and resampled server-side.
    const blob=wavBlob(samples,sr);
    const file=new File([blob],`shorlab_recording_${Date.now()}.wav`,{type:'audio/wav'});
    selected(file);btn.textContent='● Record microphone';$('record-status').textContent=`Recorded ${(len/sr).toFixed(1)} seconds`;
    return;
  }
  try{
    state.stream=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:false,noiseSuppression:false,autoGainControl:false}});
    state.audioContext=new (window.AudioContext||window.webkitAudioContext)();
    state.micInput=state.audioContext.createMediaStreamSource(state.stream);
    // ScriptProcessor is a compatibility fallback; recorded samples never leave browser until submission.
    state.processor=state.audioContext.createScriptProcessor(4096,1,1);
    state.chunks=[];
    state.processor.onaudioprocess=ev=>{if(state.recording)state.chunks.push(new Float32Array(ev.inputBuffer.getChannelData(0)));ev.outputBuffer.getChannelData(0).fill(0)};
    state.micInput.connect(state.processor);state.processor.connect(state.audioContext.destination);
    state.recording=true;state.started=Date.now();btn.textContent='■ Stop recording';$('record-status').textContent='Recording… max 30 seconds';
    const handle=setInterval(()=>{if(!state.recording){clearInterval(handle);return;}const sec=(Date.now()-state.started)/1000;
       $('record-status').textContent=`Recording… ${Math.floor(sec)} / 30 s`;
       if(sec>=29.5){clearInterval(handle);record();}},250);
  }catch(e){status('Microphone access denied or unavailable. Use a WAV upload.',true)}
}
function renderRun(r){
  $('empty-results').classList.add('hidden');$('results-content').classList.remove('hidden');
  $('results-state').textContent = (r.mode==='live'?'REAL GNANI INFERENCE':'AUDIO PREVIEW ONLY')+' · '+r.status.toUpperCase();
  const clean=r.results.clean.metrics, deg=r.results.degraded.metrics, rec=r.results.recovered.metrics;
  const gain=r.comparison;
  const summary=[
    ['RECORDING',r.duration_seconds+' sec','Source audio duration'],
    ['DEGRADED WER',deg?fmt(deg.wer):'Not measured',deg?'Compared with human reference':'Requires live inference + reference'],
    ['RECOVERY Δ WER',gain?(gain.wer_change_percentage_points>0?'+':'')+gain.wer_change_percentage_points.toFixed(2)+' pp':'Not measured',gain?(gain.recovery_effect.toUpperCase()):'No validated comparison']
  ];
  $('summary-strip').innerHTML=summary.map(a=>`<div class="summary-tile"><label>${esc(a[0])}</label><strong>${esc(a[1])}</strong><small>${esc(a[2])}</small></div>`).join('');
  const variants=[['clean','ORIGINAL SIGNAL','Unmodified speech after necessary mono/16k conversion'],['degraded','STRESSED SIGNAL','Noise and optional simulated telephony channel'],['recovered','RECOVERY PATH','Classical spectral attenuation applied to stressed audio']];
  $('results-cards').innerHTML=variants.map(([name,title,help],i)=>{
    const entry=r.results[name];const m=entry.metrics;
    const transcript=entry.status==='real'?(entry.transcript||'(No speech recognized)'):entry.status==='error'?entry.error:'No API call made in preview mode.';
    const marker=entry.status==='real'?'REAL API RESULT':entry.status==='error'?'API ERROR':'AUDIO-ONLY PREVIEW';
    return `<article class="result-card"><div class="variant-num">0${i+1} / ${marker}</div><h3>${esc(title)}</h3><p class="help">${esc(help)}</p><div class="transcript ${entry.status==='error'?'error':''}">${esc(transcript)}</div><div class="metric-row"><div><small>WORD ERROR</small><strong>${m?fmt(m.wer):'—'}</strong></div><div><small>CHAR ERROR</small><strong>${m?fmt(m.cer):'—'}</strong></div><div><small>CRITICAL RECALL</small><strong>${m?fmt(m.critical_recall):'—'}</strong></div></div><audio controls preload="none" src="/api/runs/${encodeURIComponent(r.id)}/audio/${name}" aria-label="Listen to ${name} signal"></audio></article>`;
  }).join('');
  $('wer-chart').innerHTML=variants.map(([name,title])=>{
    const m=r.results[name].metrics;const v=m?.wer;
    const width=typeof v==='number'?Math.max(0,Math.min(100,v)):0;
    return `<div class="bar-line"><span>${esc(name)}</span><div class="bar-track"><div class="bar-fill" style="width:${width}%"></div></div><span class="bar-value">${typeof v==='number'?v.toFixed(2)+'%':'NOT RUN'}</span></div>`;
  }).join('');
  $('run-notice').textContent=`Source: ${r.provenance.audio}. Noise: ${r.provenance.noise}. Recovery: ${r.provenance.recovery}. ${r.caveat} Run ID: ${r.id}`;
  document.querySelector('#results').scrollIntoView({behavior:'smooth',block:'start'});
}
async function runExperiment(mode){
  if(!state.selectedAudio){status('Choose or record a PCM WAV first.',true);return;}
  const form=new FormData($('experiment-form'));
  form.delete('audio_file');form.append('audio_file',state.selectedAudio,state.selectedAudio.name);
  form.set('mode',mode);form.set('telephony',$('telephony').checked?'true':'false');
  if(!$('ambience_file').files.length)form.delete('ambience_file');
  if(mode==='live'&&!state.keyConfigured){status('Set GNANI_API_KEY in .env and restart the server before live inference.',true);return;}
  const live=$('live-button'), preview=$('preview-button');live.disabled=true;preview.disabled=true;
  status(mode==='live'?'Calling Gnani Prisma on three actual audio variants; results will be saved.':'Generating three audio variants locally; no Gnani API calls.');
  try{
    const res=await fetch('/api/evaluate',{method:'POST',body:form});
    const data=await res.json();if(!res.ok)throw new Error(data.detail||'Request failed');
    renderRun(data);await loadHistory();
    status(mode==='live'?'Real evaluation finished. Inspect the raw transcripts, failures and metrics.':'Audio-only preview generated. Play all three signals; no scores were invented.');
  }catch(e){status(e.message||'Evaluation failed.',true)}finally{live.disabled=false;preview.disabled=false;}
}
async function loadHistory(){try{
  const resp=await fetch('/api/runs');const arr=await resp.json();
  $('run-list').innerHTML=arr.length?arr.map(x=>`<div class="run-row" role="button" tabindex="0" data-id="${esc(x.id)}"><div><b>${esc(x.title)}</b><small>${esc(new Date(x.created_at).toLocaleString())}</small></div><span>${esc(x.model)} · ${esc(x.noise_profile)}</span><span>${typeof x.degraded_wer==='number'?x.degraded_wer.toFixed(2)+'% WER':'No ground truth score'}</span><span class="run-status">${esc(x.status)} ↗</span></div>`).join(''):'<div class="empty-row">No runs saved. Start with a real recording.</div>';
  document.querySelectorAll('[data-id]').forEach(el=>{
    const open=async()=>{try{const r=await fetch('/api/runs/'+encodeURIComponent(el.dataset.id));renderRun(await r.json())}catch(e){status('Could not load saved run',true)}};
    el.addEventListener('click',open);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open()}});
  });
}catch(e){$('run-list').innerHTML='<div class="empty-row">Could not load history</div>';}}
async function boot(){
  const drop=$('dropzone'), inp=$('audio-file');
  drop.addEventListener('click',()=>inp.click());drop.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inp.click()}});
  inp.addEventListener('change',()=>selected(inp.files[0]));
  ['dragenter','dragover'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.add('dragover')}));
  ['dragleave','drop'].forEach(t=>drop.addEventListener(t,e=>{e.preventDefault();drop.classList.remove('dragover')}));
  drop.addEventListener('drop',e=>selected(e.dataTransfer.files[0]));
  $('record-button').addEventListener('click',record);
  $('snr').addEventListener('input',()=>{$('snr-output').textContent=$('snr').value+' dB';});
  $('profile').addEventListener('change',()=>{$('ambience-field').classList.toggle('hidden',$('profile').value!=='uploaded_ambience');});
  $('model').addEventListener('change',()=>{let lang=$('language'); const opt=lang.querySelector('[value="indic-auto"]');
    if($('model').value==='prisma-v3.0'){if(!opt){lang.insertAdjacentHTML('afterbegin','<option value="indic-auto">Auto-detect Indic languages</option>')}lang.value='indic-auto';}
    else{if(opt)opt.remove();lang.value='hi-IN';}
  });
  $('experiment-form').addEventListener('submit',e=>{e.preventDefault();runExperiment('live');});
  $('preview-button').addEventListener('click',()=>runExperiment('preview'));
  try {const r=await (await fetch('/api/health')).json();state.keyConfigured=r.gnani_key_configured;
    $('system-text').textContent=state.keyConfigured?'Gnani API key configured':'No Gnani key · preview ready';
    $('system-dot').classList.toggle('amber',!state.keyConfigured);
  }catch(e){$('system-text').textContent='API server unavailable';}
  loadHistory();
}
boot();
