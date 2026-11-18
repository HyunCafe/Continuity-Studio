#!/usr/bin/env python3
"""Continuity Studio: stdlib-only loopback Windows app host.

The UI is the approved independent design. Default is DEMO (no backend). An
explicit --live argument opts into existing rc9 PowerShell operations.
This file never modifies, copies or installs the backend scripts.
"""
from __future__ import annotations
import argparse
import collections
import datetime as dt
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import webbrowser
import zipfile

APP = Path(__file__).resolve().parents[1]
ASSET = APP / 'GUI'
TOOL_REL = Path('00-Shared-Guides') / 'AI-Development-Continuity'
SCRIPTS = {
    'structure': Path('Publish-Structure.ps1'),
    'organization': Path('Organization') / 'New-Organization-Audit.ps1',
    'deep': Path('Deep') / 'New-Project-Deep-Handoff.ps1',
}
REQUIRED = [*SCRIPTS.values(), Path('New-Development-Structure.ps1')]
MIME = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
        '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml', '.png': 'image/png',
        '.ico': 'image/x-icon'}
MAX_JSON = 8192
MAX_JSON_REVIEWED_INCLUSION = 36864  # Only deep preview / capture accept path lists.
MAX_PROJECTS = 5000
LOG_KEEP = 30
# Private Phase-3A engine expects exact ignored-file paths and a preview digest.
# Keep the GUI review authorization ephemeral; the engine rechecks source bytes.
IGNORED_PREVIEW_TTL_SECONDS = 300
IGNORED_PREVIEW_TIMEOUT_SECONDS = 180
IGNORED_LIST_MAX = 16000
IGNORED_DIGEST_RE = re.compile(r'^IGNORED_APPROVAL_SHA256=([0-9a-fA-F]{64})$', re.M)


def normalize_ignored_paths(value: str) -> tuple[str, list[str]]:
    """Conservative transport validation; PowerShell remains final policy authority."""
    if not isinstance(value, str) or not value.strip() or len(value) > IGNORED_LIST_MAX:
        raise ValueError('Provide 1–100 exact ignored source paths (maximum 16000 characters).')
    paths = []
    seen = set()
    for line in value.splitlines():
        path = line.strip().replace('\\', '/')
        if not path:
            continue
        parts = path.split('/')
        if (len(path) > 1024 or path.startswith('/') or path.endswith('/')
                or any(x in ('', '.', '..') for x in parts)
                or any(ord(ch) < 32 or ord(ch) == 127 or ch in ':*?<>|"[]' for ch in path)):
            raise ValueError('Ignored inclusion requires exact project-relative file paths; no links, globs or traversal.')
        key = path.casefold()
        if key in seen:
            raise ValueError('Duplicate ignored source path.')
        seen.add(key)
        paths.append(path)
        if len(paths) > 100:
            raise ValueError('Maximum 100 selected ignored source files.')
    if not paths:
        raise ValueError('Ignored source list is empty.')
    return '\n'.join(paths), paths



def under(path: Path, root: Path) -> bool:
    """True only if target is root or a descendant; never sibling-prefix."""
    try:
        return os.path.commonpath([str(path.resolve()), str(root.resolve())]).casefold() == str(root.resolve()).casefold()
    except (OSError, ValueError):
        return False


def redirected(path: Path, root: Path) -> bool:
    """Reject links/junctions in every ancestor from root to selected path."""
    try:
        p = path.absolute()
        base = root.absolute()
        while True:
            if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
                return True
            if os.path.normcase(str(p)) == os.path.normcase(str(base)):
                return False
            if p.parent == p:
                return True
            p = p.parent
    except OSError:
        return True


def validate_root(root: Path):
    if not root.is_dir():
        raise ValueError('Development root does not exist: ' + str(root))
    if redirected(root, root):
        raise ValueError('Development root cannot be a link or junction')
    return root.absolute()


def validate_project(root: Path, value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError('Choose an existing project')
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value) or ':' in value:
        raise ValueError('Invalid project path')
    normalized = value.replace('\\', '/')
    if normalized.startswith('/') or '//' in normalized or any(p in ('', '.', '..') for p in normalized.split('/')):
        raise ValueError('Project must be a relative directory without traversal')
    if any(c in normalized for c in '<>"|?*'):
        raise ValueError('Invalid Windows project path')
    child = root.joinpath(*normalized.split('/'))
    if not under(child, root) or not child.is_dir() or redirected(child, root):
        raise ValueError('Project missing, outside Development, or crosses a link/junction')
    if under(child, root / '00-Shared-Guides') or under(child, root / '08-Archive'):
        raise ValueError('Shared tools and archive directories are not project selections')
    return normalized


def bounded_json(path: Path, max_size=4*1024*1024):
    if not path.is_file() or path.stat().st_size > max_size or path.is_symlink():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError, ValueError):
        return None


def read_zip_coverage(path: Path):
    try:
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 3 * 1024**3:
            return None
        with zipfile.ZipFile(path) as z:
            info = z.getinfo('COVERAGE.json')
            if info.file_size > 4 * 1024 * 1024:
                return None
            return json.loads(z.read(info).decode('utf-8-sig'))
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        return None


def expected_git_admin_exclusion(value: object) -> bool:
    """rc9 deliberately excludes .git internals while separately capturing Git state.

    This precise informational inventory disclosure is not a missing source
    file. Do not generalize to other exclusions or ignore unknown evidence.
    """
    return isinstance(value, str) and value.strip().casefold() == 'contents not enumerated: .git'


def status_from_coverage(kind: str, root: Path, scope: str, lines: list[str], exitcode: int,
                         started: float):
    """Never claim coverage is complete based solely on exit status."""
    result = dict(status='unknown', title='Finished, but coverage is unverified.',
                  detail='Review the diagnostic log.', artifacts=[], warnings=[])
    if exitcode != 0:
        result.update(status='failed', title=f'Operation failed (exit {exitcode}).',
                      detail='See the log for the backend error. Any prior outputs may still exist.')
        return result
    paths: list[Path] = []
    if kind == 'structure':
        prefix = 'DEVELOPMENT' if scope == 'workspace' else 'PROJECT-STRUCTURE'
        file = root / (prefix + '-HANDOFF.zip')
        if not file.exists() or file.stat().st_mtime < started - 3:
            return result
        coverage = read_zip_coverage(file)
        paths = [file, root / (prefix + '-MAP.md'), root / (prefix + '-TREE.txt')]
        if not isinstance(coverage, dict) or coverage.get('schema') != 'structure-map/1':
            result['warnings'] = ['COVERAGE.json missing or unexpected inside handoff ZIP']
        else:
            complete = coverage.get('fully_enumerated') is True
            result.update(status='complete' if complete else 'incomplete',
                          title='Structure map created.' if complete else 'Structure map needs review.',
                          detail='Coverage fully enumerated.' if complete else 'Some paths were skipped; inspect COVERAGE.json.')
            result['warnings'] = [str(x)[:300] for x in coverage.get('exceptions', [])[:8]] if isinstance(coverage.get('exceptions'),list) else []
    elif kind == 'organization':
        file = root / ('DEVELOPMENT-ORGANIZATION-MAP.md' if scope == 'workspace' else 'PROJECT-ORGANIZATION-MAP.md')
        if not file.is_file() or file.stat().st_mtime < started - 3:
            return result
        paths = [file]
        raw = file.read_text(encoding='utf-8-sig', errors='replace')[:2*1024*1024]
        if not raw.startswith('<!-- AI-Development-Continuity:organization-audit/1; generated report -->'):
            result['warnings'] = ['Report signature missing; coverage cannot be verified.']
        else:
            match = re.search(r'- Fully enumerated:\s*\*{0,2}(True|False)\*{0,2}', raw, re.I)
            if match:
                complete = match.group(1).lower() == 'true'
                result.update(status='complete' if complete else 'incomplete',
                              title='Organization map created.' if complete else 'Organization map needs review.',
                              detail='Directory coverage verified.' if complete else 'Some paths were skipped; inspect the report.')
            else:
                result['warnings'] = ['Cannot interpret coverage section in organization report.']
    else:
        matches = [re.match(r'^ZIP:\s*(.+?)\s*$', l) for l in lines]
        marked = [m.group(1) for m in matches if m]
        if not marked:
            return result
        file = Path(marked[-1])
        tool = root / TOOL_REL / 'Reports' / 'Deep-Handoff'
        if not under(file, tool) or not file.is_file() or redirected(file, root) or file.stat().st_mtime < started - 3:
            result['warnings'] = ['Backend ZIP path missing, stale, or outside expected report folder.']
            return result
        paths = [file, file.parent / 'Latest-START-HERE.md', file.parent / 'Latest-COVERAGE.json']
        coverage = read_zip_coverage(file)
        if not isinstance(coverage, dict) or coverage.get('schema') != 'ai-project-handoff-2':
            result['warnings'] = ['ZIP coverage metadata missing or unexpected.']
        else:
            blockers = coverage.get('blockers') if isinstance(coverage.get('blockers'), list) else []
            unknowns = coverage.get('unknowns') if isinstance(coverage.get('unknowns'), list) else []
            # An ordinary Git repository always has .git, which rc9 excludes
            # from recursive inventory intentionally. Git state is captured via
            # Git commands instead. This exact benign notice does not make an
            # otherwise safe source handoff incomplete. All other unknowns and
            # all blockers still require review.
            material_unknowns = [x for x in unknowns if not expected_git_admin_exclusion(x)]
            expected_git_note = len(material_unknowns) != len(unknowns)
            safe = coverage.get('safe_to_resume') is True
            complete = safe and not blockers and not material_unknowns
            if complete:
                detail = ('Backend reports safe to resume; internal .git files were deliberately excluded.'
                          if expected_git_note else 'Backend reports safe to resume.')
            elif not safe and coverage.get('mode') == 'Context':
                detail = 'Context-only package omits implementation source; not a complete coding handoff.'
            else:
                detail = 'Read the coverage report before using this package to continue development.'
            result.update(status='complete' if complete else 'incomplete',
                          title='Deep handoff created.' if complete else 'Deep handoff needs review.',
                          detail=detail)
            result['warnings'] = [str(x)[:300] for x in (blockers + material_unknowns)[:8]]
            if not complete and not result['warnings']:
                result['warnings'] = ['Backend did not mark this handoff safe to resume. Inspect COVERAGE.json.']
    result['artifacts'] = [dict(name=p.name, path=str(p)) for p in paths if p.is_file() and not redirected(p, root) and under(p, root)]
    return result


class RunJob:
    def __init__(self, kind: str, scope: str, args: list[str], root: Path, log_path: Path):
        self.kind, self.scope, self.args, self.root, self.log_path = kind, scope, args, root, log_path
        self.status = 'running'
        self.title = 'Running ' + kind + '…'
        self.detail = 'Starting PowerShell backend.'
        self.warnings = []
        self.artifacts = []
        self.events = collections.deque(maxlen=600)
        self.counter = 0
        self.exitcode = None
        self.started = time.time()
        self.proc = None
        # Allows the isolated test harness to await the entire worker lifecycle,
        # including log closure and post-result metadata updates.
        self.worker_thread = None
        self.cancel_requested = False
        self.lock = threading.RLock()

    def add(self, line):
        with self.lock:
            self.counter += 1
            self.events.append((self.counter, str(line).rstrip('\n')[:2500]))

    def snapshot(self, since=0):
        with self.lock:
            return dict(status=self.status, title=self.title, detail=self.detail,
                        warnings=self.warnings, artifacts=self.artifacts,
                        exitcode=self.exitcode, events=[dict(id=i, text=x) for i,x in self.events if i>since],
                        cursor=self.counter, log=str(self.log_path))


def sandbox_runs_dir() -> Path:
    """Short, temporary location for disposable rc9 workspaces.

    Independent of where the user extracts this package, preventing ordinary
    Git object paths from exceeding Windows path limits. Does not change any
    system-wide long-path or Git settings.
    """
    return (Path(tempfile.gettempdir()) / 'ContinuityStudio-RC9-Sandbox').resolve()


def approved_test_sandbox(root: Path) -> bool:
    """Allow real engine execution only inside an accepted disposable fixture.

    The v1.2 test distribution intentionally has no unrestricted live launcher.
    """
    try:
        actual = root.resolve()
        runs = sandbox_runs_dir()
        if (not actual.is_relative_to(runs) or actual.name != 'Development'
                or actual.parent.parent != runs or redirected(actual, actual)):
            return False
        marker = bounded_json(actual / '.adc-test-sandbox.json', 4096)
        return (isinstance(marker, dict)
                and marker.get('kind') == 'continuity-studio-real-rc9-sandbox-1'
                and marker.get('root') == str(actual))
    except (OSError, ValueError):
        return False


class AppHost:
    def __init__(self, root: Path, live: bool, pwsh: str | list[str] | tuple[str, ...] | None = None,
                 sandbox_only: bool = False):
        self.live = live
        self.sandbox_only = sandbox_only
        self.root = root.absolute()
        # Production: a single pwsh.exe path. Tests may supply an explicit
        # executable + Python fixture script, avoiding Windows WinError 193
        # (Windows cannot directly execute a shebang-only Python text file).
        selected = pwsh if pwsh is not None else shutil.which('pwsh')
        self.pwsh = list(selected) if isinstance(selected, (list, tuple)) else ([selected] if selected else [])
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.job: RunJob | None = None
        self.authorized_paths: set[str] = set()
        self.ignored_preview = None  # session-local, one-use and time-limited
        self.ignored_preview_running = False
        self.last_client = time.monotonic()
        self.log_dir = APP / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        self.last_project_file = APP / 'Support' / 'last-project.json'

    def backend(self):
        if not self.live:
            raise ValueError('The preview mode cannot execute PowerShell')
        if self.sandbox_only and not approved_test_sandbox(self.root):
            raise ValueError('Sandbox-only safety gate: this is not a recognized disposable test root.')
        validate_root(self.root)
        tool = self.root / TOOL_REL
        missing = [str(x) for x in REQUIRED if not (tool/x).is_file()]
        if missing:
            raise ValueError('Existing rc9 backend not found; missing: ' + ', '.join(missing))
        if not self.pwsh:
            raise ValueError('PowerShell 7 (pwsh) was not found; install/locate it first')
        return tool

    def bootstrap(self):
        issue = ''
        if self.live:
            try:
                self.backend()
            except ValueError as exc:
                issue = str(exc)
        last = bounded_json(self.last_project_file, 4096)
        return dict(mode='live' if self.live else 'demo', testSandbox=bool(self.sandbox_only and approved_test_sandbox(self.root)), token=self.token, root=str(self.root),
                    ready=self.live and not issue, error=issue,
                    lastProject=str(last.get('project','')) if isinstance(last,dict) else '')

    def projects(self):
        tool = self.backend()
        spec = [*self.pwsh,'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
                '-File', str(tool / SCRIPTS['deep']),'-DevelopmentRoot',str(self.root),'-ListProjects','-NonInteractive']
        flags = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        cp = subprocess.run(spec,cwd=str(tool),capture_output=True,timeout=60,
                            encoding='utf-8',errors='replace',creationflags=flags)
        if cp.returncode != 0:
            raise ValueError('Project discovery failed: '+(cp.stderr or cp.stdout)[-400:])
        names = []
        for line in cp.stdout.splitlines():
            if len(names)>=MAX_PROJECTS:
                break
            try:
                rel = validate_project(self.root,line.strip())
                if rel not in names:
                    names.append(rel)
            except ValueError:
                continue
        return [dict(id=p, name=Path(p).name, path=p, type='Git project') for p in names]

    def build(self, request: dict):
        tool = self.backend()
        kind = request.get('mode')
        if kind not in SCRIPTS:
            raise ValueError('Unknown capability')
        settings = request.get('settings')
        if not isinstance(settings,dict):
            raise ValueError('Settings must be an object')
        scope = settings.get('scope','workspace') if kind!='deep' else 'project'
        if scope not in ('workspace','project'):
            raise ValueError('Unknown scope')
        rel = validate_project(self.root,settings.get('projectPath')) if scope=='project' else ''
        a = [*self.pwsh,'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass',
             '-File',str(tool / SCRIPTS[kind]),'-DevelopmentRoot',str(self.root)]
        if kind != 'deep':
            a.extend(['-Scope','Directory' if scope=='project' else 'Workspace'])
            if rel:
                a.extend(['-Directory',rel])
            if kind=='structure':
                if settings.get('directoriesOnly') is True: a.append('-DirectoriesOnly')
                if settings.get('noGit') is True: a.append('-NoGitDetails')
            elif settings.get('sizes') is True:
                a.append('-IncludeSizes')
        else:
            cap = settings.get('capture','source')
            if cap not in ('source','context'):
                raise ValueError('Deep mode must be source or context')
            note = settings.get('note','')
            if not isinstance(note,str) or len(note)>2000 or '\x00' in note:
                raise ValueError('Task note exceeds limits')
            a.extend(['-Project',rel,'-Mode','Source' if cap=='source' else 'Context','-NonInteractive','-NoOpen'])
            if note.strip(): a.extend(['-Note',note.strip()])
            if settings.get('honorGitIgnore') is False: a.append('-HonorGitIgnore:$false')
            if settings.get('includeDiffs') is False: a.append('-NoDiffs')
            for field,sw,low,high,default in (
                ('maxFileMB','-MaxFileMB',1,64,8), ('maxPackageMB','-MaxPackageMB',10,2048,150)):
                v = settings.get(field,default)
                if type(v)!=int or not low<=v<=high:
                    raise ValueError(field+' is outside backend range')
                if v!=default: a.extend([sw,str(v)])
        return kind, scope, rel, a

    def preview_ignored(self, request: dict):
        """Read-only reviewed-inclusion preflight; never creates a handoff ZIP."""
        if not isinstance(request, dict):
            raise ValueError('Expected a preview request object.')
        tool = self.backend()
        project = validate_project(self.root, request.get('projectPath'))
        text, paths = normalize_ignored_paths(request.get('pathsText'))
        with self.lock:
            if (self.ignored_preview_running
                    or (self.job is not None and self.job.status == 'running')):
                raise ValueError('An operation is already running.')
            self.ignored_preview = None
            self.ignored_preview_running = True
        try:
            spec = [*self.pwsh, '-NoLogo', '-NoProfile', '-NonInteractive',
                    '-ExecutionPolicy', 'Bypass', '-File', str(tool / SCRIPTS['deep']),
                    '-DevelopmentRoot', str(self.root), '-Project', project,
                    '-Mode', 'Source', '-NonInteractive', '-NoOpen',
                    '-IncludeIgnoredPathsText', text, '-PreviewIgnoredInclusion']
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            try:
                cp = subprocess.run(spec, cwd=str(tool), stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, encoding='utf-8',
                                    errors='replace', timeout=IGNORED_PREVIEW_TIMEOUT_SECONDS,
                                    creationflags=flags)
            except subprocess.TimeoutExpired as exc:
                raise ValueError('Ignored-source preview timed out; no approval issued.') from exc
            if cp.returncode:
                # Avoid exposing the raw request or entire backend trace as an API error.
                diagnostic = (cp.stderr or cp.stdout or '').strip()[-350:]
                raise ValueError('Ignored-source preview rejected the selection: ' + diagnostic)
            found = IGNORED_DIGEST_RE.findall(cp.stdout)
            included = [line.strip()[len('INCLUDE: '):] for line in cp.stdout.splitlines()
                        if line.strip().startswith('INCLUDE: ')]
            if len(found) != 1 or len(included) != len(paths):
                raise ValueError('Backend preview response was incomplete; approval withheld.')
            if sorted(x.casefold() for x in included) != sorted(x.casefold() for x in paths):
                raise ValueError('Backend preview file set differs from the requested paths.')
            digest = found[0].lower()
            with self.lock:
                self.ignored_preview = dict(project=project, paths_text=text, digest=digest,
                                            expires=time.monotonic() + IGNORED_PREVIEW_TTL_SECONDS)
            return dict(projectPath=project, paths=included, digest=digest,
                        expiresInSeconds=IGNORED_PREVIEW_TTL_SECONDS)
        finally:
            with self.lock:
                self.ignored_preview_running = False

    def start(self, request):
        kind,scope,project,argv = self.build(request)
        settings = request['settings']
        approval = settings.get('ignoredInclusion')
        with self.lock:
            if self.ignored_preview_running or (self.job and self.job.status=='running'):
                raise ValueError('Another operation is running')
            if approval is not None:
                if kind != 'deep' or settings.get('capture', 'source') != 'source' or settings.get('honorGitIgnore', True) is not True:
                    raise ValueError('Reviewed ignored inclusion requires Deep Source mode with Git-ignore protection on.')
                if not isinstance(approval, dict) or set(approval) != {'pathsText', 'digest'}:
                    raise ValueError('Invalid ignored inclusion approval payload.')
                paths_text, _ = normalize_ignored_paths(approval['pathsText'])
                provided_digest = approval['digest']
                if not isinstance(provided_digest, str) or not re.fullmatch(r'[a-fA-F0-9]{64}', provided_digest):
                    raise ValueError('Invalid ignored inclusion digest.')
                review = self.ignored_preview
                if (not review or time.monotonic() > review['expires']
                        or project != review['project'] or paths_text != review['paths_text']
                        or not hmac.compare_digest(provided_digest.lower(), review['digest'])):
                    raise ValueError('Preview approval is missing, stale or mismatched. Preview the exact files again.')
                argv.extend(['-IncludeIgnoredPathsText', paths_text,
                             '-ApproveIgnoredDigest', review['digest']])
                self.ignored_preview = None  # one use, including a failed capture
            name = re.sub(r'[^A-Za-z0-9_-]', '-', kind+'-'+(project or 'workspace'))[:60]
            file = self.log_dir / (dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-'+name+'.log')
            self.job = RunJob(kind,scope,argv,self.root,file)
            self.authorized_paths = set()
            t = threading.Thread(target=self.run_worker,args=(self.job,project),daemon=True)
            self.job.worker_thread = t
            t.start()
            return self.job.snapshot()

    def run_worker(self, job: RunJob, project: str):
        flags = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        lines = []
        try:
            old = sorted(self.log_dir.glob('*.log'),key=lambda x:x.stat().st_mtime, reverse=True)
            for p in old[LOG_KEEP:]:
                try: p.unlink()
                except OSError: pass
            with job.log_path.open('w',encoding='utf-8') as log:
                log.write('Continuity Studio live run - '+dt.datetime.now().isoformat()+'\n')
                # -File position may shift for the test-only Python launcher.
                script_index = job.args.index('-File') + 1
                log.write('Executable: '+job.args[0]+'\nBackend: '+job.args[script_index]+'\n')
                log.flush()
                if job.cancel_requested:
                    with job.lock:
                        job.status='cancelled'; job.title='Cancelled before process start.'
                        job.detail='No process was launched.'
                    return
                proc = subprocess.Popen(job.args,cwd=str(self.root/TOOL_REL),stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1,
                                       encoding='utf-8',errors='replace',creationflags=flags)
                with job.lock: job.proc = proc
                assert proc.stdout
                if job.cancel_requested and proc.poll() is None:
                    self._terminate_child(proc)
                with proc.stdout:
                    for line in proc.stdout:
                        text = line.rstrip('\r\n')
                        job.add(text)
                        if len(lines)<20000:
                            lines.append(text)
                        if log.tell()<16*1024*1024:
                            log.write(text+'\n');log.flush()
                code=proc.wait()
            verdict = status_from_coverage(job.kind, job.root, job.scope, lines, code,job.started)
            with job.lock:
                if job.cancel_requested:
                    job.status='cancelled'
                    job.title='Operation interrupted by user.'
                    job.detail='Publication may have been interrupted. Check log and backend outputs before re-running.'
                else:
                    job.status=verdict['status']
                    job.title=verdict['title']; job.detail=verdict['detail']
                    job.warnings=verdict['warnings']
                    job.artifacts=verdict['artifacts']
                job.exitcode=code
            with self.lock:
                self.authorized_paths = {str(Path(p['path']).resolve()) for p in job.artifacts}
                self.authorized_paths.add(str(job.log_path.resolve()))
                self.authorized_paths.add(str(job.log_path.parent.resolve()))
            if project and job.status in ('complete','incomplete'):
                tmp=self.last_project_file.with_suffix('.tmp')
                tmp.write_text(json.dumps(dict(project=project)),encoding='utf-8')
                tmp.replace(self.last_project_file)
        except Exception as exc:
            with job.lock:
                job.status='failed';job.title='Desktop host could not complete the operation.'
                job.detail=str(exc)[:400];job.exitcode=-1
                job.add('HOST ERROR: '+str(exc))

    @staticmethod
    def _terminate_child(proc):
        if proc.poll() is not None: return
        try:
            if os.name=='nt':
                subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],
                               capture_output=True,timeout=8,creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                proc.terminate()
        except (OSError,subprocess.TimeoutExpired):
            try: proc.kill()
            except OSError: pass

    def cancel(self):
        with self.lock:
            job=self.job
            if not job or job.status!='running':
                raise ValueError('No operation is running')
            with job.lock:
                job.cancel_requested=True
                proc=job.proc
        if proc and proc.poll() is None:
            self._terminate_child(proc)
        return {'requested': True, 'warning':'Cancellation can leave temporary stages. Check the run log.'}

    def status(self,since=0):
        job=self.job
        if not job:return {'status':'idle','cursor':0,'events':[]}
        return job.snapshot(since)

    def open_path(self,path):
        if not isinstance(path,str):
            raise ValueError('Invalid path')
        p=Path(path).resolve()
        with self.lock:
            allowed = str(p) in self.authorized_paths
        if not allowed or not p.exists():
            raise ValueError('Path not in confirmed outputs for this run')
        if os.name!='nt':
            raise ValueError('Windows-only file opening')
        os.startfile(str(p))
        return {'opened':True}


class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self, host: AppHost):
        super().__init__(('127.0.0.1',0),Handler)
        self.host_app = host


class Handler(BaseHTTPRequestHandler):
    def log_message(self,format,*args):
        return

    def headers_common(self,ctype='application/json; charset=utf-8'):
        self.send_header('Content-Type',ctype)
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cross-Origin-Resource-Policy','same-origin')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")

    def send_json(self,obj,status=200):
        data=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.headers_common();self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

    def valid_host(self):
        expected='127.0.0.1:'+str(self.server.server_port)
        return self.headers.get('Host','')==expected

    def valid_origin(self):
        val=self.headers.get('Origin','')
        return not val or val == 'http://127.0.0.1:'+str(self.server.server_port)

    def do_GET(self):
        if not self.valid_host():
            return self.send_json({'error':'Host mismatch'},403)
        self.server.host_app.last_client=time.monotonic()
        path=urlparse(self.path).path
        if path=='/api/ping':
            return self.send_json({'ok':True})
        if path=='/api/bootstrap':
            return self.send_json(self.server.host_app.bootstrap())
        if path=='/api/projects':
            try:return self.send_json({'projects':self.server.host_app.projects()})
            except Exception as exc:return self.send_json({'error':str(exc)},422)
        if path=='/api/status':
            q=parse_qs(urlparse(self.path).query)
            try:since=max(0,int(q.get('since',['0'])[0]))
            except ValueError:since=0
            return self.send_json(self.server.host_app.status(since))
        if path in ('/','/index.html'):
            f=ASSET/'index.html'
        elif path in ('/app.js','/styles.css','/favicon-32.png','/favicon.ico',
                      '/continuity-studio.png','/continuity-studio.svg'):
            f=ASSET / ('continuity-studio.ico' if path == '/favicon.ico' else path[1:])
        else:
            return self.send_json({'error':'Not found'},404)
        data=f.read_bytes()
        self.send_response(200);self.headers_common(MIME[f.suffix]);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

    def do_POST(self):
        if not self.valid_host() or not self.valid_origin():
            return self.send_json({'error':'Origin mismatch'},403)
        auth=self.headers.get('X-ADC-Token','')
        if not hmac.compare_digest(auth,self.server.host_app.token):
            return self.send_json({'error':'Unauthorized'},403)
        try:
            path=urlparse(self.path).path
            n=int(self.headers.get('Content-Length','0'))
            limit = MAX_JSON_REVIEWED_INCLUSION if path in ('/api/run','/api/deep/preview-ignored') else MAX_JSON
            if n<0 or n>limit:
                return self.send_json({'error':'Request too large'},413)
            val=json.loads(self.rfile.read(n).decode('utf-8'))
            if not isinstance(val,dict):
                raise ValueError('Expected a JSON object')
            if path=='/api/run':out=self.server.host_app.start(val)
            elif path=='/api/deep/preview-ignored':out=self.server.host_app.preview_ignored(val)
            elif path=='/api/cancel':out=self.server.host_app.cancel()
            elif path=='/api/open':out=self.server.host_app.open_path(val.get('path'))
            else:return self.send_json({'error':'Unknown action'},404)
            return self.send_json(out)
        except (ValueError,OSError,UnicodeError,json.JSONDecodeError) as exc:
            return self.send_json({'error':str(exc)},422)


def find_edge():
    found=shutil.which('msedge') or shutil.which('msedge.exe')
    if found:return found
    if os.name=='nt':
        for env in ('PROGRAMFILES(X86)','PROGRAMFILES','LOCALAPPDATA'):
            base=os.environ.get(env)
            if base:
                p=Path(base)/'Microsoft'/'Edge'/'Application'/'msedge.exe'
                if p.is_file():return str(p)
    return ''


def serve(host:AppHost,open_browser:bool=True):
    server=Server(host)
    url=f'http://127.0.0.1:{server.server_port}/'
    if open_browser:
        edge=find_edge()
        if edge:
            subprocess.Popen([edge,'--app='+url,'--new-window'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:
            webbrowser.open(url)
    if sys.stdout is not None:
        print('Continuity Studio '+('LIVE' if host.live else 'PREVIEW')+' host: '+url,flush=True)
    def idle_guard():
        while True:
            time.sleep(10)
            if time.monotonic()-host.last_client > 100:
                active=host.job and host.job.status=='running'
                if not active:
                    server.shutdown();return
    threading.Thread(target=idle_guard,daemon=True).start()
    try:server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt:pass
    finally:server.server_close()


def main():
    parser=argparse.ArgumentParser(description='Isolated desktop GUI host; preview is the default.')
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--live',action='store_true',help='Explicitly enable rc9 PowerShell operations')
    group.add_argument('--demo',action='store_true',help='Use fictional UI preview (default)')
    parser.add_argument('--sandbox-only',action='store_true',help='Require the disposable test-workspace identity')
    parser.add_argument('--root',default=str(Path.home()/'Desktop'/'Development'))
    parser.add_argument('--no-browser',action='store_true',help=argparse.SUPPRESS)
    a=parser.parse_args()
    if a.live and not a.sandbox_only:
        parser.error('This test distribution does not allow unrestricted live mode. Use Open Safe Sandbox GUI.cmd.')
    serve(AppHost(Path(a.root),a.live,sandbox_only=a.sandbox_only),not a.no_browser)


if __name__=='__main__':main()
