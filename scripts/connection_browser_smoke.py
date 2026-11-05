"""Test status refresh in Chromium using labeled UI doubles; no provider requests."""
import argparse,json
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--base-url',default='http://127.0.0.1:8012')
 parser.add_argument('--output-dir',default='/tmp/SHOR-connection-browser')
 args=parser.parse_args()
 from urllib.parse import urlparse
 if urlparse(args.base_url).hostname not in {'127.0.0.1','localhost'}:parser.error('Local test instance required')
 out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  for name,w,h in [('desktop',1440,1000),('mobile',390,844)]:
   page=browser.new_page(viewport={'width':w,'height':h},reduced_motion='reduce')
   page.route('**/api/evaluate',lambda route:route.abort())
   page.goto(args.base_url,wait_until='networkidle')
   assert page.locator('#connection-title').inner_text()=='Saved key is not available to this server'
   assert page.locator('#live-button').is_disabled()
   assert page.locator('#preview-button').is_enabled()
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
   with page.expect_response('**/api/connection'):
    page.locator('#recheck-connection').click()
   assert page.locator('#connection-checked-at').inner_text().find('No Gnani requests made')>=0
   page.locator('#gnani-connection').screenshot(path=str(out/(name+'-connection.png')))
   page.screenshot(path=str(out/(name+'-full.png')),full_page=True)
   # These responses are software UI fixtures, not actual authenticated provider evidence.
   fake={'key_present':True,'can_attempt_live':True,'status':'unverified','title':'TEST FIXTURE: key available, unverified','explanation':'UI fixture only','policy_allows_endpoint':None,'actions':['Test-only action'],'checked_at':'2026-11-05T00:00:00Z','gnani':{'authentication_validated':False}}
   page.route('**/api/connection',lambda route:route.fulfill(json=fake))
   page.locator('#recheck-connection').click()
   page.wait_for_function("document.querySelector('#connection-title').textContent.startsWith('TEST FIXTURE')")
   assert page.locator('#live-button').is_enabled()
   assert 'inspect connection' in page.locator('#system-text').text_content()
   page.route('**/api/connection',lambda route:route.fulfill(status=503,json={'detail':'test-only outage'}))
   page.locator('#recheck-connection').click()
   page.get_by_role('heading',name='Cannot read server connection status').wait_for()
   assert page.locator('#live-button').is_disabled()
   assert page.locator('#preview-button').is_enabled()
   page.close()
  browser.close()
 (out/'results.json').write_text(json.dumps({'status':'PASS','checks':['desktop and mobile: actual missing-credential panel, non-billable refresh, blocked live control, preview remains available, no horizontal overflow','UI test double: new credential state enables live without falsely validating authentication','UI test double: status outage disables live and preserves preview'],'provider_requests':0,'screenshots':'Actual server missing-credential state, captured before test doubles'},indent=2))
 print('PASS: desktop/mobile connection, refresh, observed-state changes and safe server outage. Zero provider requests.')

if __name__=='__main__':main()
