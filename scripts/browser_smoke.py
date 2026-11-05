#!/usr/bin/env python3
"""Real Chromium interaction checks using synthetic audio; never calls Gnani.

Run an isolated SHOR server first, then:
  python scripts/browser_smoke.py --base-url http://127.0.0.1:8010
Requires Playwright Python plus Chromium. These are software UI checks, not ASR evidence.
"""
from __future__ import annotations
import argparse
import io
import json
import math
import os
from pathlib import Path
import struct
import wave
from playwright.sync_api import sync_playwright


def tone():
    output=io.BytesIO()
    with wave.open(output,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(16000)
        wav.writeframes(b''.join(struct.pack('<h',int(4000*math.sin(i*2*math.pi*280/16000))) for i in range(16000)))
    return output.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8010')
    parser.add_argument('--output-dir',default='/tmp/SHOR-browser-checks')
    args=parser.parse_args()
    # Local browser checks must never target a public deployment accidentally.
    from urllib.parse import urlparse
    if urlparse(args.base_url).hostname not in {'127.0.0.1','localhost'}:
        parser.error('Use a private local test instance only')
    output=Path(args.output_dir);output.mkdir(parents=True,exist_ok=True)
    checks=[];api_calls=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.getenv('SHOR_CHROMIUM','/usr/bin/chromium'),headless=True,
          args=['--no-sandbox','--disable-dev-shm-usage','--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream'])
        for label,width,height in [('desktop',1440,1000),('tablet',820,1180),('mobile',390,844)]:
            context=browser.new_context(viewport={'width':width,'height':height},reduced_motion='reduce',accept_downloads=True)
            page=context.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:api_calls.append(request.url) if 'api.vachana.ai' in request.url else None)
            page.goto(args.base_url,wait_until='networkidle')
            assert page.title().startswith('SHOR')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),label+' horizontal overflow'
            page.locator('#audio-file').set_input_files({'name':'UI-synthetic-tone.wav','mimeType':'audio/wav','buffer':tone()})
            page.locator('input[name="title"]').fill('UI software test '+label)
            page.locator('#reference').fill('UI synthetic fixture — not speech evidence')
            page.locator('#audio-condition').select_option('synthetic')
            page.locator('#recovery-mode').select_option('adaptive')
            with page.expect_response(lambda r:r.url.endswith('/api/evaluate') and r.request.method=='POST') as result:
                page.locator('#preview-button').click()
            response=result.value;assert response.ok,response.text()
            record=response.json();assert record['mode']=='preview'
            assert all(x['status']=='not_run' and x['metrics'] is None for x in record['results'].values())
            page.locator('#results-state').get_by_text('AUDIO PREVIEW ONLY',exact=False).wait_for()
            assert 'heuristic' in page.locator('#recovery-decision').inner_text()
            assert page.locator('#results-cards audio').count()==3
            # Exercise media loading and playback with actual WAV artifacts.
            audio=page.locator('#results-cards audio').first
            audio.evaluate('(a)=>{a.muted=true;a.load()}')
            page.wait_for_function("document.querySelector('#results-cards audio').readyState >= 1")
            assert abs(audio.evaluate('(a)=>a.duration')-1)<.01
            audio.evaluate('(a)=>a.play()')
            page.wait_for_function("document.querySelector('#results-cards audio').currentTime > 0")
            page.screenshot(path=str(output/(label+'-preview.png')),full_page=True)
            page.locator('#history-search').fill('UI software test '+label)
            page.locator('#history-mode').select_option('preview')
            page.locator('#history-filters button').click()
            page.wait_for_function("document.querySelectorAll('[data-id]').length === 1")
            assert page.locator('[data-id]').first.inner_text().startswith('UI software test '+label)
            page.locator('[data-id]').first.click()
            assert page.locator('#reference-display').inner_text().endswith('UI synthetic fixture — not speech evidence')
            for selector,expected in [('a[href="/api/export.csv"]','.csv'),('a[href="/api/evidence.json"]','.json')]:
                with page.expect_download() as download:
                    page.locator(selector).click()
                assert download.value.suggested_filename.endswith(expected)
            page.once('dialog',lambda d:d.accept())
            with page.expect_response(lambda r:r.request.method=='DELETE') as deleted:
                page.locator('[data-delete]').first.click()
            assert deleted.value.ok
            page.wait_for_function("document.querySelectorAll('[data-id]').length === 0")
            assert page.request.get(args.base_url+'/api/runs/'+record['id']).status==404
            assert page.request.get(args.base_url+'/api/runs/'+record['id']+'/audio/clean').status==404
            assert not errors,errors
            checks.append(label+': upload, adaptive preview, empty metrics, WAV playback, history filter/open, CSV/JSON download, deletion and no horizontal overflow')
            context.close()
        # Corrupt uploads fail safely; genuine API usage remains zero.
        context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        page=context.new_page();page.goto(args.base_url,wait_until='networkidle')
        page.locator('#audio-file').set_input_files({'name':'broken.wav','mimeType':'audio/wav','buffer':b'not wav'})
        with page.expect_response(lambda r:r.url.endswith('/api/evaluate') and r.request.method=='POST') as bad:
            page.locator('#preview-button').click()
        assert bad.value.status==400
        page.wait_for_function("document.getElementById('form-status').textContent.includes('Invalid WAV')")
        assert page.locator('#preview-button').is_enabled()
        checks.append('Malformed WAV: visible safe error and controls recover')
        # Actual browser media capture using Chromium fake device; no real speaker or voice.
        page.locator('#record-button').click()
        page.wait_for_function("document.getElementById('record-button').textContent.includes('Stop')")
        page.wait_for_timeout(1100)
        page.locator('#record-button').click()
        page.wait_for_function("document.getElementById('record-status').textContent.includes('Recorded')")
        assert page.locator('#file-title').inner_text().startswith('SHOR_recording_')
        checks.append('Microphone start/stop with Chromium synthetic media device; no physical microphone validation')
        context.close()
        browser.close()
        denied_browser=p.chromium.launch(executable_path=os.getenv('SHOR_CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-fake-device-for-media-stream'])
        denied=denied_browser.new_context(viewport={'width':1440,'height':1000})
        denied_page=denied.new_page();denied_page.goto(args.base_url,wait_until='networkidle')
        session=denied.new_cdp_session(denied_page)
        session.send('Browser.setPermission',{'permission':{'name':'microphone'},'setting':'denied','origin':args.base_url})
        denied_page.locator('#record-button').click()
        denied_page.wait_for_function("document.getElementById('form-status').textContent.includes('Microphone access denied')")
        assert denied_page.locator('#record-button').inner_text().endswith('Record microphone')
        checks.append('Microphone permission denial: safe user-visible fallback to upload')
        denied.close();denied_browser.close()
    assert not api_calls,'Unexpected external Gnani request'
    result={'status':'PASS','checks':checks,'gnani_requests':0,'audio':'Synthetic tone / Chromium fake microphone; software tests only'}
    (output/'results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
