"""Read-only host verification with a synthetic process; never uses real rc9 scripts."""
from pathlib import Path
import http.client
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Support'))
import host

class HostTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.addCleanup(self._cleanup_temp)
        self.base = Path(self.td.name)
        self.root = self.base / 'Development'
        self.tool = self.root / host.TOOL_REL
        self.tool.mkdir(parents=True)
        for rel in host.REQUIRED:
            p = self.tool / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('# synthetic fixture only\n',encoding='utf-8')
        (self.root / '01-Learning' / 'Alpha-Service' / '.git').mkdir(parents=True)
        (self.root / 'Beta-App' / '.git').mkdir(parents=True)
        # A Python process fixture emulates the PowerShell CLI without evaluating
        # the backend. Invoke through sys.executable on Windows AND Linux: Windows
        # cannot execute a Unix shebang file directly (WinError 193).
        self.fake = self.base / 'fake-pwsh.py'
        self.fake.write_text('''#!/usr/bin/env python3
import sys, json, os, pathlib, zipfile, time
argv=sys.argv[1:]; arg=lambda n,default='':argv[argv.index(n)+1] if n in argv else default
root=pathlib.Path(arg('-DevelopmentRoot')); script=arg('-File')
if arg('-Note')=='SLOW':time.sleep(6)
if '-ListProjects' in argv:
 print('01-Learning/Alpha-Service');print('Beta-App');sys.exit(0)
if 'Publish-Structure.ps1' in script:
 scope=arg('-Scope');prefix='DEVELOPMENT' if scope=='Workspace' else 'PROJECT-STRUCTURE'
 cov={'schema':'structure-map/1','fully_enumerated':scope=='Workspace','exceptions':[]}
 with zipfile.ZipFile(root/(prefix+'-HANDOFF.zip'),'w') as z:z.writestr('COVERAGE.json',json.dumps(cov))
 (root/(prefix+'-MAP.md')).write_text('# fixture map')
 (root/(prefix+'-TREE.txt')).write_text('fixture tree')
 print('UPDATED: '+str(root));sys.exit(0)
if 'New-Organization-Audit.ps1' in script:
 scope=arg('-Scope');file=root/('DEVELOPMENT-ORGANIZATION-MAP.md' if scope=='Workspace' else 'PROJECT-ORGANIZATION-MAP.md')
 file.write_text('<!-- AI-Development-Continuity:organization-audit/1; generated report -->\\n- Fully enumerated: **'+ ('True' if scope=='Workspace' else 'False')+'**\\n')
 print('ORGANIZATION AUDIT MAP: '+str(file));sys.exit(0)
if 'New-Project-Deep-Handoff.ps1' in script:
 if '-PreviewIgnoredInclusion' in argv:
  text=arg('-IncludeIgnoredPathsText')
  paths=[x.strip().replace('\\\\','/') for x in text.splitlines() if x.strip()]
  if 'force-error' in text:
   print('Synthetic backend refused unsafe selection');sys.exit(3)
  print('PREVIEW: %s individually selected ignored source file(s).' % len(paths))
  for p in paths: print('  INCLUDE: '+p)
  print('IGNORED_APPROVAL_SHA256='+'a'*64)
  sys.exit(0)
 if '-IncludeIgnoredPathsText' in argv and '-ApproveIgnoredDigest' not in argv:sys.exit(4)
 dest=root/'00-Shared-Guides'/'AI-Development-Continuity'/'Reports'/'Deep-Handoff'/'fixture';dest.mkdir(parents=True,exist_ok=True)
 zipname=dest/'Latest.zip';cov={'schema':'ai-project-handoff-2','safe_to_resume':arg('-Mode')=='Source','mode':arg('-Mode'),'blockers':[],'unknowns':['Contents not enumerated: .git']}
 with zipfile.ZipFile(zipname,'w') as z:z.writestr('COVERAGE.json',json.dumps(cov))
 print('GIT: reading state');print('ZIP: '+str(zipname));sys.exit(0)
sys.exit(8)
''',encoding='utf-8')
        self.fake.chmod(0o755)
        self.h = host.AppHost(self.root, live=True, pwsh=[sys.executable, str(self.fake)])
        # Prevent test activity from pruning or writing project logs outside fixtures.
        self.h.log_dir = self.base / 'logs';self.h.log_dir.mkdir()
        self.h.last_project_file=self.base/'last.json'
        # unittest runs cleanups in reverse order: wait for the worker first,
        # then remove this disposable directory. A completed STATUS can precede
        # the final last-project/log housekeeping by a few milliseconds.
        self.addCleanup(self._wait_for_worker)

    def _wait_for_worker(self):
        job = getattr(self.h, 'job', None)
        worker = getattr(job, 'worker_thread', None)
        if worker is not None:
            worker.join(timeout=12)
            if worker.is_alive():
                raise AssertionError('Synthetic worker did not finish before fixture cleanup')

    def _cleanup_temp(self):
        for attempt in range(6):
            try:
                self.td.cleanup()
                return
            except OSError as exc:
                if os.name != 'nt' or getattr(exc, 'winerror', None) not in (32, 145) or attempt == 5:
                    raise
                time.sleep(0.12 * (attempt + 1))

    def finish(self):
        for _ in range(300):
            v=self.h.status(0)
            if v['status']!='running': return v
            time.sleep(.04)
        self.fail('Synthetic process did not finish')

    def test_icon_asset_belongs_to_local_allowlist(self):
        server=host.Server(host.AppHost(self.root,live=False))
        self.addCleanup(server.server_close)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(),thread.join(timeout=5)))
        for filename, expected in (('/favicon.ico','image/x-icon'),
                                   ('/favicon-32.png','image/png'),
                                   ('/continuity-studio.svg','image/svg+xml')):
            with self.subTest(filename=filename):
                con=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=5)
                con.request('GET',filename,headers={'Host':f'127.0.0.1:{server.server_port}'})
                res=con.getresponse();data=res.read();ctype=res.getheader('Content-Type')
                self.assertEqual(200,res.status)
                self.assertEqual(expected,ctype)
                self.assertGreater(len(data),150)
                con.close()

    def test_sibling_prefix_rejected(self):
        sibling=self.base/'Development-evil';sibling.mkdir()
        self.assertFalse(host.under(sibling,self.root))

    def test_path_traversal_rejected(self):
        for v in ('../evil','/etc','C:\\Windows','a/../Beta-App','a//b','a|b'):
            with self.subTest(value=v),self.assertRaises(ValueError):host.validate_project(self.root,v)

    def test_shared_tooling_rejected(self):
        with self.assertRaises(ValueError):host.validate_project(self.root,'00-Shared-Guides')

    def test_valid_nested_project(self):
        self.assertEqual('01-Learning/Alpha-Service',host.validate_project(self.root,'01-Learning/Alpha-Service'))

    def test_link_rejected(self):
        try:
            p=self.root/'link';p.symlink_to(self.root/'Beta-App',target_is_directory=True)
        except (OSError,NotImplementedError):return
        with self.assertRaises(ValueError):host.validate_project(self.root,'link')

    def test_short_sandbox_location_independent_of_extraction(self):
        runs = host.sandbox_runs_dir()
        self.assertEqual('ContinuityStudio-RC9-Sandbox', runs.name)
        self.assertTrue(runs.is_absolute())
        self.assertFalse(runs.is_relative_to(host.APP.resolve()))

    def test_sandbox_only_refuses_unmarked_root(self):
        gated = host.AppHost(self.root, live=True,
                             pwsh=[sys.executable, str(self.fake)], sandbox_only=True)
        with self.assertRaisesRegex(ValueError, 'Sandbox-only'):
            gated.backend()

    def test_demo_host_refuses_execution(self):
        demo=host.AppHost(self.root, live=False, pwsh=[sys.executable, str(self.fake)])
        with self.assertRaises(ValueError):demo.build({'mode':'structure','settings':{'scope':'workspace'}})

    def test_exact_argument_array(self):
        k,sc,rel,argv=self.h.build({'mode':'deep','settings':{'projectPath':'Beta-App','capture':'source',
            'note':'fix "quotes"; do not execute','honorGitIgnore':True,'includeDiffs':True,'maxFileMB':8,'maxPackageMB':150}})
        self.assertEqual('deep',k);self.assertEqual('project',sc)
        self.assertEqual('fix "quotes"; do not execute',argv[argv.index('-Note')+1]);self.assertIn('-NonInteractive',argv);self.assertIn('-NoOpen',argv)

    def test_honor_gitignore_disabled_explicit_flag(self):
        _,_,_,argv=self.h.build({'mode':'deep','settings':{'projectPath':'Beta-App','honorGitIgnore':False}})
        self.assertIn('-HonorGitIgnore:$false',argv)

    def test_invalid_limits(self):
        for limit in (0,65,'999',True):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.h.build({'mode':'deep','settings':{'projectPath':'Beta-App','maxFileMB':limit}})

    # Phase 3B: preview is explicit, one-use, bound to project and exact paths.
    def test_ignored_path_validation(self):
        valid, paths = host.normalize_ignored_paths('src/a.py\r\nsrc\\b.py')
        self.assertEqual('src/a.py\nsrc/b.py', valid)
        self.assertEqual(['src/a.py','src/b.py'], paths)
        for bad in ('../bad.py','/root/file.py','a//b.py','src/*.py','C:\\secret.py',
                    'src/.\\x.py','src/a.py\nsrc/A.PY','src/file[1].py', 'a'*1025):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                host.normalize_ignored_paths(bad)

    def test_ignored_preview_http_requires_token_and_origin(self):
        server=host.Server(self.h)
        self.addCleanup(server.server_close)
        thread=threading.Thread(target=server.serve_forever,daemon=True)
        thread.start()
        self.addCleanup(lambda:(server.shutdown(),thread.join(timeout=5)))
        endpoint='/api/deep/preview-ignored'
        body=json.dumps({'projectPath':'Beta-App','pathsText':'src/a.py'})
        def call(token, origin):
            conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
            headers={'Host':f'127.0.0.1:{server.server_port}', 'Content-Type':'application/json',
                     'X-ADC-Token':token,'Origin':origin}
            conn.request('POST',endpoint,body=body,headers=headers)
            res=conn.getresponse(); val=json.loads(res.read()); status=res.status;conn.close()
            return status,val
        allowed=f'http://127.0.0.1:{server.server_port}'
        self.assertEqual(403,call('',allowed)[0])
        self.assertEqual(403,call(self.h.token,'http://malicious.local')[0])
        code,val=call(self.h.token,allowed)
        self.assertEqual(200,code)
        self.assertEqual(['src/a.py'],val['paths'])
        self.assertEqual('a'*64,val['digest'])

    def test_ignored_preview_requires_live(self):
        demo=host.AppHost(self.root, live=False, pwsh=[sys.executable,str(self.fake)])
        with self.assertRaises(ValueError):
            demo.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py'})

    def test_ignored_preview_is_read_only_and_returns_digest(self):
        got=self.h.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py\nsrc/b.py'})
        self.assertEqual(['src/a.py','src/b.py'],got['paths'])
        self.assertEqual('a'*64,got['digest'])
        self.assertEqual(300,got['expiresInSeconds'])
        self.assertFalse((self.tool/'Reports').exists(), 'Preview cannot publish a ZIP')

    def test_ignored_preview_disallows_bad_project_and_missing_paths(self):
        for req in ({'projectPath':'Beta-App','pathsText':'../private'},
                    {'projectPath':'Not-A-Project','pathsText':'src/a.py'},
                    {'projectPath':'Beta-App','pathsText':''}):
            with self.subTest(req=req),self.assertRaises(ValueError):
                self.h.preview_ignored(req)

    def test_ignored_capture_requires_issued_approval(self):
        settings={'projectPath':'Beta-App','capture':'source',
                  'ignoredInclusion':{'pathsText':'src/a.py','digest':'a'*64}}
        with self.assertRaisesRegex(ValueError,'Preview approval'):
            self.h.start({'mode':'deep','settings':settings})

    def test_ignored_approval_rejects_project_and_selection_mismatch(self):
        got=self.h.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py'})
        for project,text in [('01-Learning/Alpha-Service','src/a.py'),('Beta-App','src/b.py')]:
            settings={'projectPath':project,'capture':'source',
                      'ignoredInclusion':{'pathsText':text,'digest':got['digest']}}
            with self.subTest(project=project,text=text),self.assertRaisesRegex(ValueError,'mismatched'):
                self.h.start({'mode':'deep','settings':settings})

    def test_ignored_approval_expires(self):
        got=self.h.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py'})
        self.h.ignored_preview['expires']=time.monotonic()-1
        with self.assertRaisesRegex(ValueError,'stale'):
            self.h.start({'mode':'deep','settings':{'projectPath':'Beta-App','capture':'source',
                'ignoredInclusion':{'pathsText':'src/a.py','digest':got['digest']}}})

    def test_ignored_approval_is_one_use_and_uses_exact_argv(self):
        got=self.h.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py'})
        request={'mode':'deep','settings':{'projectPath':'Beta-App','capture':'source',
                 'ignoredInclusion':{'pathsText':'src/a.py','digest':got['digest']}}}
        self.h.start(request)
        self.assertEqual('src/a.py', self.h.job.args[self.h.job.args.index('-IncludeIgnoredPathsText')+1])
        self.assertEqual(got['digest'], self.h.job.args[self.h.job.args.index('-ApproveIgnoredDigest')+1])
        self.assertIsNone(self.h.ignored_preview)
        self.assertEqual('complete',self.finish()['status'])
        with self.assertRaisesRegex(ValueError,'Preview approval'):
            self.h.start(request)

    def test_ignored_approval_disallows_context_and_disabled_ignore(self):
        got=self.h.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py'})
        for extras in ({'capture':'context'},{'honorGitIgnore':False}):
            settings={'projectPath':'Beta-App','capture':'source',
                      'ignoredInclusion':{'pathsText':'src/a.py','digest':got['digest']},**extras}
            with self.subTest(extras=extras),self.assertRaisesRegex(ValueError,'requires Deep Source'):
                self.h.start({'mode':'deep','settings':settings})

    def test_ignored_approval_blocks_overlapping_work(self):
        self.h.ignored_preview_running=True
        with self.assertRaisesRegex(ValueError,'operation is running'):
            self.h.start({'mode':'deep','settings':{'projectPath':'Beta-App'}})
        with self.assertRaisesRegex(ValueError,'already running'):
            self.h.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py'})

    def test_ordinary_deep_run_never_picks_up_stale_approval(self):
        self.h.preview_ignored({'projectPath':'Beta-App','pathsText':'src/a.py'})
        self.h.start({'mode':'deep','settings':{'projectPath':'Beta-App','capture':'source'}})
        self.assertNotIn('-ApproveIgnoredDigest',self.h.job.args)
        self.assertEqual('complete',self.finish()['status'])

    def test_fixture_launcher_uses_real_executable(self):
        kind,scope,rel,argv = self.h.build({'mode':'structure','settings':{'scope':'workspace'}})
        self.assertEqual([sys.executable, str(self.fake)], argv[:2])
        self.assertEqual(str(self.tool / host.SCRIPTS['structure']), argv[argv.index('-File') + 1])

    def test_discovery_uses_existing_script(self):
        self.assertEqual(['01-Learning/Alpha-Service','Beta-App'],[p['path'] for p in self.h.projects()])

    def test_structure_complete(self):
        self.h.start({'mode':'structure','settings':{'scope':'workspace'}})
        v=self.finish();self.assertEqual('complete',v['status']);self.assertEqual(3,len(v['artifacts']))

    def test_project_structure_incomplete(self):
        self.h.start({'mode':'structure','settings':{'scope':'project','projectPath':'Beta-App'}})
        self.assertEqual('incomplete',self.finish()['status'])

    def test_organization_bold_markdown_coverage(self):
        self.h.start({'mode':'organization','settings':{'scope':'workspace'}})
        self.assertEqual('complete',self.finish()['status'])

    def test_org_directory_incomplete(self):
        self.h.start({'mode':'organization','settings':{'scope':'project','projectPath':'Beta-App'}})
        self.assertEqual('incomplete',self.finish()['status'])

    def test_worker_lifecycle_exposed_for_safe_cleanup(self):
        self.h.start({'mode':'organization','settings':{'scope':'project','projectPath':'Beta-App'}})
        self.assertEqual('incomplete', self.finish()['status'])
        worker = self.h.job.worker_thread
        self.assertIsNotNone(worker)
        worker.join(timeout=8)
        self.assertFalse(worker.is_alive(), 'The full synthetic run must finish before temp cleanup')

    def test_deep_complete(self):
        self.h.start({'mode':'deep','settings':{'projectPath':'Beta-App','capture':'source'}})
        self.assertEqual('complete',self.finish()['status'])

    def test_deep_context_needs_review(self):
        self.h.start({'mode':'deep','settings':{'projectPath':'Beta-App','capture':'context'}})
        v=self.finish()
        self.assertEqual('incomplete',v['status'])
        self.assertIn('Context-only',v['detail'])

    def _realistic_deep_coverage(self, *, safe=True, unknowns=None, blockers=None, mode='Source'):
        """Write a real ZIP member in a disposable test root (no rc9 execution)."""
        dest=self.tool/'Reports'/'Deep-Handoff'/'test-fixture'
        dest.mkdir(parents=True,exist_ok=True)
        path=dest/'Latest.zip'
        data={'schema':'ai-project-handoff-2','safe_to_resume':safe,
              'mode':mode,'blockers':blockers or [],
              'unknowns':['Contents not enumerated: .git'] if unknowns is None else unknowns}
        with zipfile.ZipFile(path,'w') as za:
            za.writestr('COVERAGE.json',json.dumps(data))
        return host.status_from_coverage('deep',self.root,'project',['ZIP: '+str(path)],0,time.time())

    def test_expected_git_folder_exclusion_is_informational(self):
        result=self._realistic_deep_coverage(safe=True)
        self.assertEqual('complete',result['status'])
        self.assertEqual([],result['warnings'])
        self.assertIn('.git',result['detail'])

    def test_other_unknowns_still_require_review(self):
        result=self._realistic_deep_coverage(safe=True, unknowns=[
            'Contents not enumerated: .git','Contents not enumerated: private-notes'])
        self.assertEqual('incomplete',result['status'])
        self.assertEqual(['Contents not enumerated: private-notes'],result['warnings'])

    def test_git_exception_does_not_override_unsafe_verdict(self):
        result=self._realistic_deep_coverage(safe=False)
        self.assertEqual('incomplete',result['status'])
        self.assertTrue(result['warnings'])

    def test_blockers_still_require_review_with_git_exception(self):
        result=self._realistic_deep_coverage(safe=True, blockers=['Uncaptured changed source file'])
        self.assertEqual('incomplete',result['status'])
        self.assertIn('Uncaptured changed source file',result['warnings'])

    def test_exit_zero_no_files_is_unknown(self):
        v=host.status_from_coverage('deep',self.root,'project',[],0,time.time())
        self.assertEqual('unknown',v['status'])

    def test_bad_schema_unknown(self):
        file=self.root/'DEVELOPMENT-HANDOFF.zip'
        with zipfile.ZipFile(file,'w') as z:z.writestr('COVERAGE.json','{"schema":"invalid","fully_enumerated":true}')
        v=host.status_from_coverage('structure',self.root,'workspace',[],0,time.time())
        self.assertEqual('unknown',v['status'])

    def test_single_running_job_guard(self):
        self.h.job=host.RunJob('structure','workspace',[],self.root,self.base/'j.log')
        with self.assertRaises(ValueError):self.h.start({'mode':'structure','settings':{'scope':'workspace'}})

    def test_no_output_outside_root(self):
        v=host.status_from_coverage('deep',self.root,'project',['ZIP: '+str(self.base/'outside.zip')],0,time.time())
        self.assertEqual('unknown',v['status'])

    def test_log_path_scoped(self):
        self.h.start({'mode':'structure','settings':{'scope':'workspace'}})
        v=self.finish();self.assertTrue(Path(v['log']).is_file())
        with self.assertRaises(ValueError):self.h.open_path(str(self.base/'private.txt'))

    def test_cancel_interrupts_synthetic_child(self):
        self.h.start({'mode':'deep','settings':{'projectPath':'Beta-App','capture':'source','note':'SLOW'}})
        # Confirm there was a real child to terminate (no cancellation claims on noop).
        for _ in range(100):
            if self.h.job.proc is not None: break
            time.sleep(.02)
        self.assertIsNotNone(self.h.job.proc)
        self.h.cancel()
        v=self.finish()
        self.assertEqual('cancelled',v['status'])
        self.assertFalse(v['artifacts'])

    def test_bootstrap_reports_live(self):
        v=self.h.bootstrap();self.assertEqual('live',v['mode']);self.assertTrue(v['ready']);self.assertEqual(43,len(v['token']))

    def test_http_auth_origin_and_assets(self):
        s=host.Server(self.h)
        t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
        self.addCleanup(lambda:(s.shutdown(),s.server_close(),t.join(timeout=3)))
        c=http.client.HTTPConnection('127.0.0.1',s.server_port,timeout=5)
        c.request('GET','/api/bootstrap');r=c.getresponse();data=json.loads(r.read());self.assertEqual(200,r.status)
        c.request('POST','/api/run',body='{}',headers={'Content-Type':'application/json'});r=c.getresponse();r.read();self.assertEqual(403,r.status)
        c.request('POST','/api/run',body='{}',headers={'Content-Type':'application/json','X-ADC-Token':data['token'],'Origin':'https://attacker.example'});r=c.getresponse();r.read();self.assertEqual(403,r.status)
        c.request('GET','/app.js');r=c.getresponse();self.assertEqual(200,r.status);self.assertIn(b'initializeDesktop',r.read())
        c.close()

if __name__=='__main__':unittest.main()
