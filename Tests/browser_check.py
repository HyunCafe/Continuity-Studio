"""Optional Playwright browser test; use python -m unittest ... or run directly."""
from pathlib import Path
import sys
import threading
import http.client
import json
from urllib.parse import urlparse
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_host import HostTests
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Support'))
import host

class BrowserIntegration(unittest.TestCase):
    def setUp(self):
        try:from playwright.sync_api import sync_playwright
        except ImportError:self.skipTest('Playwright optional; browser test not run')
        self.sync=sync_playwright
        self.b=HostTests('test_valid_nested_project')
        self.b.setUp()
        self.server=host.Server(self.b.h)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.play=self.sync().start()
        self.browser=self.play.chromium.launch(headless=True,executable_path='/usr/bin/chromium' if Path('/usr/bin/chromium').is_file() else None)
        self.page=self.browser.new_page(viewport={'width':1440,'height':900})
        self.errors=[]
        self.page.on('pageerror',lambda err:self.errors.append(str(err)))
        self._load_page()
    def _load_page(self):
        # This environment blocks browser loopback navigation. Load the EXACT
        # UI markup/styles from disk, and relay browser fetch calls to the real
        # local host through a test-only Python function. No source is changed.
        self.page.expose_binding('__testProxy',self._proxy)
        front=host.ASSET
        html=(front/'index.html').read_text(encoding='utf-8')
        css=(front/'styles.css').read_text(encoding='utf-8')
        js=(front/'app.js').read_text(encoding='utf-8')
        js=js.replace("if(location.protocol==='http:' && location.hostname==='127.0.0.1') initializeDesktop();",'initializeDesktop();')
        bridge="""<script>
          window.fetch=async function(path,opt){
            const r=await window.__testProxy(path,opt||{});
            return {ok:r.status>=200 && r.status<300,status:r.status,json:async()=>r.data};
          };
        </script>"""
        html=html.replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>')
        html=html.replace('<script src="app.js" defer></script>',bridge+'<script>'+js+'</script>')
        self.page.set_content(html,wait_until='load')
    def _proxy(self,source,path,opt):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=10)
        headers=dict(opt.get('headers') or {})
        headers['Origin']='http://127.0.0.1:'+str(self.server.server_port)
        body=opt.get('body')
        conn.request(opt.get('method') or 'GET',path,body=body,headers=headers)
        response=conn.getresponse()
        data=json.loads(response.read())
        output={'status':response.status,'data':data}
        conn.close()
        return output
    def tearDown(self):
        if hasattr(self,'browser'):self.browser.close()
        if hasattr(self,'play'):self.play.stop()
        if hasattr(self,'server'):self.server.shutdown();self.server.server_close();self.thread.join(3)
        if hasattr(self,'b'):self.b.doCleanups()

    def test_complete_deep(self):
        p=self.page
        p.wait_for_function("document.querySelector('.preview-label').textContent.includes('LIVE WINDOWS')",timeout=3000)
        p.wait_for_function("document.getElementById('projectCount').textContent.includes('2 of 2')")
        self.assertIn('Alpha-Service',p.locator('#projectList').inner_text())
        self.assertNotIn('fictional',p.locator('#projectCount').inner_text())
        p.locator('#previewButton').click()
        p.wait_for_function("document.getElementById('resultBody').innerText.includes('Deep handoff created')",timeout=12000)
        self.assertIn('Verified outputs',p.locator('#resultBody').inner_text())
        self.assertIn('Latest.zip',p.locator('#resultBody').inner_text())
        self.assertEqual([],self.errors)
        self.assertEqual('complete',self.b.h.status()['status'])
        shot=Path(__file__).resolve().parents[1]/'docs'/'LIVE-FIXTURE-PREVIEW.png'
        p.screenshot(path=str(shot),full_page=True)

    def test_structure_and_theme(self):
        p=self.page
        p.wait_for_function("document.querySelector('.preview-label').textContent.includes('LIVE WINDOWS')")
        p.locator('[data-mode="structure"]').click()
        p.locator('#themeButton').click()
        self.assertEqual('light',p.locator('html').get_attribute('data-theme'))
        p.locator('#previewButton').click()
        p.wait_for_function("document.getElementById('resultBody').innerText.includes('Structure map created')",timeout=12000)
        self.assertIn('Verified outputs',p.locator('#resultBody').inner_text())
        self.assertEqual([],self.errors)

    def test_missing_backend_disabled(self):
        p=self.page
        self.b.h.root=self.b.base/'missing-development'
        self.page.close()
        self.page=self.browser.new_page(viewport={'width':1440,'height':900})
        self.page.on('pageerror',lambda err:self.errors.append(str(err)))
        self._load_page()
        p=self.page
        p.wait_for_function("document.querySelector('.preview-label').textContent.includes('LIVE WINDOWS')")
        self.assertTrue(p.locator('#previewButton').is_disabled())
        self.assertIn('Backend unavailable',p.locator('#resultBody').inner_text())
        self.assertEqual([],self.errors)

if __name__=='__main__':unittest.main()
