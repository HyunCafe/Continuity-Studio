/* AI Development Continuity — visual UX prototype.
   No backend adapter, PowerShell invocation, filesystem APIs, or network requests.
   All projects and run results are fictional and marked as such. */
(() => {
  'use strict';
  let projects = Object.freeze([
    {id:'alpha', name:'Alpha-Service', path:'01-Applications/Alpha-Service', type:'Web application'},
    {id:'beta', name:'Beta-App', path:'01-Applications/Beta-App', type:'Desktop application'},
    {id:'docs', name:'Docs-Lab', path:'02-Research/Docs-Lab', type:'Documentation'},
    {id:'design', name:'Design-System', path:'03-Shared/Design-System', type:'UI components'},
    {id:'cli', name:'CLI-Toolkit', path:'04-Utilities/CLI-Toolkit', type:'Command-line tools'},
    {id:'notes', name:'Research-Notes', path:'02-Research/Research-Notes', type:'Research notes'}
  ]);
  const modes = Object.freeze({
    structure:{title:'Structure Map', description:'Generate a compact overview of your entire Development workspace or a selected project.', category:'Workspace or project', button:'Preview structure map', output:['*-MAP.md','*-TREE.txt','*-HANDOFF.zip']},
    organization:{title:'Organization Audit', description:'Understand the folder hierarchy while keeping build caches and dependency noise out of the way.', category:'Workspace or project', button:'Preview organization audit', output:['*-ORGANIZATION-MAP.md']},
    deep:{title:'Deep Project Handoff', description:"Package a project's source, documentation and working context for another AI session.", category:'Project-specific', button:'Preview handoff', output:['Latest.zip','Latest-START-HERE.md','Latest-COVERAGE.json']}
  });
  const $ = id => document.getElementById(id);
  const desktop = { enabled:false, ready:false, sandbox:false, token:'', root:'', cursor:0, timer:null, issue:'', heartbeat:null };

  const state = {
    mode:'deep', theme:'dark', lastProject:'beta', busy:false, runId:0,
    settings: {
      structure:{scope:'workspace',project:'beta',directoriesOnly:false,noGit:false},
      organization:{scope:'workspace',project:'beta',sizes:false},
      deep:{project:'beta',capture:'source',note:'',honorGitIgnore:true,includeDiffs:true,maxFileMB:8,maxPackageMB:150}
    }, results:{structure:null,organization:null,deep:null}
  };
  const icon = name => `<svg aria-hidden="true"><use href="#i-${name}"></use></svg>`;
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const selectedProject = () => projects.find(p => p.id === state.settings[state.mode].project) || null;
  const needsProject = () => state.mode === 'deep' || state.settings[state.mode].scope === 'project';
  const current = () => state.settings[state.mode];
  const announce = message => { $('announcement').textContent = message; };
  const getOutputs = () => {
    const m = state.mode, s = current();
    if (m === 'deep') return modes.deep.output;
    const base = s.scope === 'workspace' ? 'DEVELOPMENT' : 'PROJECT-STRUCTURE';
    if (m === 'structure') return [`${base}-MAP.md`,`${base}-TREE.txt`,`${base}-HANDOFF.zip`];
    return [s.scope === 'workspace' ? 'DEVELOPMENT-ORGANIZATION-MAP.md' : 'PROJECT-ORGANIZATION-MAP.md'];
  };
  function updateProjectList(){
    if (!needsProject()) return;
    const q = $('projectSearch').value.trim().toLocaleLowerCase();
    const filtered = projects.filter(p => (p.name+' '+p.path+' '+p.type).toLocaleLowerCase().includes(q));
    $('projectCount').textContent = `${filtered.length} of ${projects.length} ${desktop.enabled?'discovered':'fictional'} projects`;
    $('projectList').innerHTML = filtered.map(p => `<button class="project-row" type="button" data-project="${esc(p.id)}" data-help="${esc('Choose '+p.name+' for this task. Selecting it does not start anything or change files.')}" aria-pressed="${p.id === current().project}">${icon('folder')}<span><b>${esc(p.name)}</b><small>${esc(p.path)}</small></span><span class="selected-indicator">${icon('check')}</span></button>`).join('') || '<div class="empty-projects">No projects match that search.</div>';
    $('selectedProjectText').textContent = selectedProject() ? `Selected: ${selectedProject().name} · ${selectedProject().path}` : 'Select a project to continue.';
    $('projectList').querySelectorAll('[data-project]').forEach(btn => btn.addEventListener('click', () => {
      current().project = btn.dataset.project;
      updateProjectList();
    }));
  }
  function updateAdvanced(){
    const m=state.mode, s=current();
    $('advanced').hidden = m === 'organization';
    if(m === 'structure'){
      $('advancedContent').innerHTML = `<label class="toggle-line" data-help="Lists folders without making the detailed file-by-file index. Useful for a quick overview."><input type="checkbox" data-setting="directoriesOnly" ${s.directoriesOnly?'checked':''}><span class="checkbox-copy"><b>Directories only</b><small>Skip the full file index</small></span></label><label class="toggle-line" data-help="Leaves out Git change-history details. Normally leave this off when preparing information for another AI session."><input type="checkbox" data-setting="noGit" ${s.noGit?'checked':''}><span class="checkbox-copy"><b>Skip Git details</b><small>Faster overview without branch and change information</small></span></label>`;
    }else if(m === 'deep'){
      $('advancedContent').innerHTML = `<label class="toggle-line" data-help="A .gitignore file lists things the project normally leaves out. Keeping this on helps avoid packing unnecessary or possibly private files; still review ZIPs before sharing."><input type="checkbox" data-setting="honorGitIgnore" ${s.honorGitIgnore?'checked':''}><span class="checkbox-copy"><b>Honor .gitignore</b><small>Recommended privacy-aware behavior</small></span></label><label class="toggle-line" data-help="Includes unfinished changes that have not yet been saved as a Git checkpoint. Helpful for continuing work in a new AI session."><input type="checkbox" data-setting="includeDiffs" ${s.includeDiffs?'checked':''}><span class="checkbox-copy"><b>Include Git diffs</b><small>Preserve uncommitted work in progress</small></span></label><div class="mini-grid"><label class="small-input" data-help="Limits the size of each file copied into the ZIP. Larger files may be skipped. MiB is similar to a megabyte.">Maximum file size (MiB)<input type="number" data-number="maxFileMB" value="${s.maxFileMB}" min="1" max="64" step="1"></label><label class="small-input" data-help="The most space the finished ZIP should use. A smaller limit is easier to share, but it may leave out files. MiB is similar to a megabyte.">Package budget (MiB)<input type="number" data-number="maxPackageMB" value="${s.maxPackageMB}" min="10" max="2048" step="1"></label></div>`;
    }else $('advancedContent').innerHTML='';
    $('advancedContent').querySelectorAll('[data-setting]').forEach(el => el.addEventListener('change', () => { s[el.dataset.setting] = el.checked; }));
    $('advancedContent').querySelectorAll('[data-number]').forEach(el => el.addEventListener('change', () => {
      const min=Number(el.min),max=Number(el.max),v=Number(el.value);
      s[el.dataset.number]=Number.isFinite(v) && v>=min && v<=max ? Math.round(v) : (el.dataset.number==='maxFileMB'?8:150);
      el.value=String(s[el.dataset.number]);
    }));
  }
  function renderMode(){
    const m=state.mode,s=current(),config=modes[m];
    $('workflowKicker').textContent=({structure:'MAP YOUR WORKSPACE',organization:'REVIEW YOUR FOLDERS',deep:'PREPARE A HANDOFF'})[m];
    $('pageTitle').textContent=config.title;
    $('pageDescription').textContent=config.description;
    $('breadcrumbMode').textContent=config.title;
    $('scopeChip').textContent=config.category;
    document.querySelectorAll('.nav-item').forEach(b => b.setAttribute('aria-current', b.dataset.mode === m ? 'page':'false'));
    $('scopeField').hidden=m==='deep';
    $('projectField').hidden=!needsProject();
    $('deepFields').hidden=m!=='deep';
    $('organizationFields').hidden=m!=='organization';
    document.querySelectorAll('[data-scope]').forEach(b=>b.setAttribute('aria-pressed',String(s.scope===b.dataset.scope)));
    if(m==='deep'){
      document.querySelectorAll('[data-capture]').forEach(b=>b.setAttribute('aria-pressed',String(s.capture===b.dataset.capture)));
      $('taskNote').value=s.note;
      $('noteCount').textContent=`${s.note.length} / 240`;
      $('captureHelp').textContent=s.capture==='source'?'Includes source, relevant documentation and Git context.':'Omits implementation source; unsuitable as a complete coding handoff.';
    }
    if(m==='organization') $('sizeCheck').checked=s.sizes;
    $('previewButton').querySelector('span').textContent=desktop.enabled?({structure:'Generate structure map',organization:'Generate organization map',deep:'Create deep handoff'}[m]):config.button;
    const last=projects.find(p=>p.id===state.lastProject);
    $('recentProject').hidden=!last;
    if(last) $('recentProject').querySelector('span').textContent='Use last: '+last.name;
    $('projectSearch').value='';
    $('advanced').open=false;
    updateAdvanced();
    updateProjectList();
    updateResult();
  }
  function outcomeSummary(status, m){
    const result={
      complete:{title:'Sample: Complete',description:'The example capture finished, and its coverage is reported complete.',icon:'check'},
      incomplete:{title:'Sample: Needs review',description:'The example capture finished, but the next session should review the limitations.',icon:'alert'},
      unknown:{title:'Sample: Coverage unknown',description:'The example process finished, but coverage or output integrity could not be confirmed.',icon:'info'},
      failed:{title:'Sample: Failed',description:'The example process stopped before a verified output was available.',icon:'x'},
      cancelled:{title:'Sample: Preview cancelled',description:'The visual simulation stopped. No files or processes were affected.',icon:'info'},
      running:{title:'Simulating the workflow…',description:'Demonstrating visual feedback only. No engine is running.',icon:'refresh'}
    };
    return result[status] || result.incomplete;
  }
  function resultHtml(r){
    if(!r) return desktop.enabled ? `<div class="result-empty"><div class="empty-illustration">${icon('box')}</div><h3>${desktop.ready?'Ready to generate':'Backend unavailable'}</h3><p>${esc(desktop.ready?'Choose a workflow and generate a real output using the existing PowerShell scripts.':desktop.issue)}</p><small>${desktop.ready?'Results are checked against generated reports; no simulated results.':'Existing rc9 installation is not modified.'}</small></div>` : `<div class="result-empty"><div class="empty-illustration">${icon('box')}</div><h3>Ready to preview</h3><p>Select the capture options, then preview how a completion result would appear.</p><small>No actual files are created in this UI study.</small></div>`;
    if(desktop.enabled) return liveResultHtml(r);
    const status=outcomeSummary(r.status,r.mode);
    let html=`<div class="result-status ${esc(r.status)}" data-help="${esc({complete:'The example says all expected information was captured.',incomplete:'The example is missing something. Review the notes before sharing.',unknown:'The example cannot confirm what information was captured.',failed:'The example stopped with an error.',cancelled:'You stopped the preview; nothing was saved.',running:'This is a sample progress display, not a real scan.'}[r.status]||'Review this sample result.')}"><div class="result-symbol">${icon(status.icon)}</div><div><h3>${esc(status.title)}</h3><p>${esc(status.description)}</p><span class="mini-badge">SYNTHETIC EXAMPLE · ${esc(r.target)}</span></div></div>`;
    if(r.status==='running') {
      html+=`<div class="result-divider"></div><h4 class="result-section-title">Activity</h4><p class="field-help" id="stageText">${esc(r.stage||'Preparing preview…')}</p><div class="sample-log" aria-label="Simulated progress">${esc(r.events.join('\n'))}</div>`;
    }else if(r.status==='cancelled'){
      html+=`<div class="result-divider"></div><p class="field-help">Preview cancellation is illustrative. The eventual backend cancellation policy will be designed separately.</p>`;
    } else if (r.status==='unknown') {
      html+=`<div class="result-divider"></div><h4 class="result-section-title">Why verification is unknown</h4><ul class="warnings"><li>Example: the coverage report is missing or unreadable.</li><li>Inspect the generated reports and diagnostic log before relying on the output.</li></ul>`;
    } else if (r.status==='failed') {
      html+=`<div class="result-divider"></div><h4 class="result-section-title">Illustrative error</h4><ul class="warnings"><li>Example: the selected project could not be read.</li><li>Show the actionable error and retain diagnostic output rather than closing the window.</li></ul>`;
    }else{
      html+=`<div class="result-divider"></div><h4 class="result-section-title">Example outputs</h4>`;
      html+=r.outputs.map((f,i)=>`<div class="artifact">${icon(f.endsWith('.zip')?'box':'map')}<span><b>${esc(f)}</b><small>${i===0?'Primary result':'Supporting artifact'} · sample filename</small></span></div>`).join('');
      if(r.status==='incomplete'){
        html+=`<div class="result-divider"></div><h4 class="result-section-title">Why this needs review</h4><ul class="warnings"><li>${esc(r.warning)}</li><li>Review the coverage report before sharing a handoff.</li></ul>`;
      }
    }
    html+=`<button class="details-button" type="button" id="detailsButton" aria-expanded="${!!r.detailsOpen}">${icon('list')} ${r.detailsOpen?'Hide':'Show'} example activity</button>`;
    if(r.detailsOpen) html+=`<pre class="sample-log" aria-label="Synthetic example log">${esc(r.events.join('\n')+'\n[DEMO] All output is fictional.')}</pre>`;
    return html;
  }
  function updateResult(){
    const r=state.results[state.mode];
    $('resultBody').innerHTML=resultHtml(r);
    $('resultBody').querySelectorAll('[data-open-artifact]').forEach(b=>b.addEventListener('click',()=>openLiveArtifact(b.dataset.openArtifact)));
    $('resetResult').disabled=state.busy || !r;
    const details=$('detailsButton');if(details) details.addEventListener('click',()=>{r.detailsOpen=!r.detailsOpen;updateResult();});
    $('previewButton').hidden=state.busy;
    $('cancelButton').hidden=!state.busy;
    $('resetButton').disabled=state.busy;
    $('outcomeChoice').disabled=state.busy;
    document.querySelectorAll('.nav-item').forEach(b=>b.disabled=state.busy);
    if(!state.busy) $('previewButton').disabled=(desktop.enabled&&!desktop.ready)||(needsProject()&&!selectedProject());
  }
  function clearResult(){if(state.busy)return;state.results[state.mode]=null;updateResult();}
  function switchMode(m){if(state.busy||!modes[m])return;state.mode=m;renderMode();announce(modes[m].title+' selected.');}
  function resetSettings(){
    if(state.busy)return;
    const m=state.mode,s=state.settings;
    if(m==='structure') s.structure={scope:'workspace',project:s.structure.project,directoriesOnly:false,noGit:false};
    if(m==='organization') s.organization={scope:'workspace',project:s.organization.project,sizes:false};
    if(m==='deep') s.deep={project:s.deep.project,capture:'source',note:'',honorGitIgnore:true,includeDiffs:true,maxFileMB:8,maxPackageMB:150};
    renderMode();
  }
  function preview(){
    if(state.busy)return;
    if(desktop.enabled) { startLive(); return; }
    const m=state.mode,s=current(),project=selectedProject();
    if(needsProject()&&!project)return;
    const target=needsProject()?project.name:'Entire workspace';
    const requested=$('outcomeChoice').value;
    const outcome=m==='deep'&&s.capture==='context'&&requested==='complete'?'incomplete':requested;
    const warning=m==='deep'&&s.capture==='context'?'Context-only mode deliberately omits implementation source.':
      m==='deep'?'Example: two source files were skipped; check the handoff manifest.':
      m==='organization'?'Example: one protected directory could not be enumerated.':
      'Example: one linked folder was skipped during enumeration.';
    const r={mode:m,status:'running',target,outputs:getOutputs(),warning,detailsOpen:false,stage:'Preparing…',events:['[DEMO] Starting example '+m+' for '+target]};
    const phases=['Discovering sample projects…','Reading sample workspace structure…','Preparing example outputs…','Interpreting fictional coverage…'];
    const id=++state.runId;
    state.busy=true;state.results[m]=r;updateResult();announce('Synthetic preview started.');
    let i=0;
    const tick=()=>{
      if(id!==state.runId || !state.busy)return;
      if(i<phases.length){r.stage=phases[i];r.events.push('[DEMO] '+phases[i]);i++;if(state.mode===m)updateResult();setTimeout(tick,330);}
      else {r.status=outcome;r.stage='';r.events.push('[DEMO] Preview finished: '+outcome);state.busy=false;state.lastProject=project?project.id:state.lastProject;if(state.mode===m)updateResult();announce('Synthetic preview finished: '+outcome+'.');}
    };
    setTimeout(tick,180);
  }
  function cancelPreview(){if(desktop.enabled){cancelLive();return;}if(!state.busy)return;state.runId++;state.busy=false;const r=state.results[state.mode];if(r){r.status='cancelled';r.events.push('[DEMO] User canceled the simulation.');}updateResult();announce('Preview canceled.');}
  function toggleTheme(){
    state.theme=state.theme==='dark'?'light':'dark';
    document.documentElement.dataset.theme=state.theme;
    $('themeButton').innerHTML=state.theme==='dark'?`${icon('sun')}<span>Light mode</span>`:`${icon('moon')}<span>Dark mode</span>`;
    $('themeButton').setAttribute('aria-label',state.theme==='dark'?'Switch to light mode':'Switch to dark mode');
  }
  // The UI remains a stand-alone fictional preview when opened from disk.
  // Only the explicit Windows host at 127.0.0.1 provides an authenticated API.
  function liveResultHtml(r){
    const status = r.status;
    const meta = {
      running:['Running…','The existing PowerShell backend is processing this request.','refresh'],
      complete:['Complete','Output created and coverage checked.','check'],
      incomplete:['Needs review','Output created; coverage reports limitations.','alert'],
      unknown:['Coverage unknown','PowerShell finished, but the expected reports could not be verified.','info'],
      failed:['Failed','The backend reported a failure. Review the diagnostic log.','x'],
      cancelled:['Interrupted','The backend was stopped; partial staging may remain.','info']
    }[status] || ['Unknown','Review the log.','info'];
    let html=`<div class="result-status ${esc(status)}" data-help="${esc({complete:'The output exists and its coverage report says it is complete.',incomplete:'The output exists but some information is missing. Read the notes before sharing.',unknown:'The app cannot confirm whether all expected information was captured.',failed:'The operation stopped with an error. Check the log.',cancelled:'The operation was interrupted and may have left temporary files.',running:'The real PowerShell operation is still working.'}[status]||'Review this result.')}"><div class="result-symbol">${icon(meta[2])}</div><div><h3>${esc(r.title||meta[0])}</h3><p>${esc(r.detail||meta[1])}</p><span class="mini-badge">${desktop.sandbox?"SANDBOX · REAL POWERSHELL":"LIVE POWERSHELL"} · ${esc(r.target)}</span></div></div>`;
    if((r.artifacts||[]).length){
      html+='<div class="result-divider"></div><h4 class="result-section-title">Verified outputs</h4>';
      for(const a of r.artifacts){
        html+=`<div class="artifact">${icon(a.name.endsWith('.zip')?'box':'map')}<span><b>${esc(a.name)}</b><small title="${esc(a.path)}">${esc(a.path)}</small></span><button type="button" class="small-action" data-open-artifact="${esc(a.path)}">Open</button></div>`;
      }
    }
    if((r.warnings||[]).length){
      html+='<div class="result-divider"></div><h4 class="result-section-title">Review notes</h4><ul class="warnings">'+r.warnings.map(x=>`<li>${esc(x)}</li>`).join('')+'</ul>';
    }
    if(status==='running'){
      html+='<div class="result-divider"></div><h4 class="result-section-title">Current activity</h4>';
      html+=`<pre class="sample-log">${esc((r.events||[]).slice(-9).join('\n')||'Starting PowerShell…')}</pre>`;
    }
    if(r.log){
      html+=`<button type="button" class="details-button" id="detailsButton" aria-expanded="${!!r.detailsOpen}">${icon('list')} ${r.detailsOpen?'Hide':'Show'} live log</button>`;
      if(r.detailsOpen) html+=`<pre class="sample-log" aria-label="Actual backend output">${esc((r.events||[]).slice(-160).join('\n'))}</pre>`;
      if(status!=='running') html+=`<button type="button" class="small-action" data-open-artifact="${esc(r.log)}">Open diagnostic log</button>`;
    }
    return html;
  }
  async function api(path,payload){
    const opt={cache:'no-store'};
    if(payload!==undefined){
      opt.method='POST';
      opt.headers={'Content-Type':'application/json','X-ADC-Token':desktop.token};
      opt.body=JSON.stringify(payload);
    }
    const response=await fetch(path,opt);
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||`Desktop host error ${response.status}`);
    return data;
  }
  async function initializeDesktop(){
    try{
      const info=await api('/api/bootstrap');
      if(!desktop.heartbeat)desktop.heartbeat=setInterval(()=>api('/api/ping').catch(()=>{}),25000);
      if(info.mode!=='live')return;  // Default desktop launch keeps UI in demo mode.
      desktop.enabled=true;desktop.token=info.token;desktop.root=info.root;desktop.sandbox=info.testSandbox===true;
      desktop.ready=info.ready;desktop.issue=info.error||'';
      projects=[];state.lastProject=null;
      for(const s of Object.values(state.settings))s.project='';
      document.title='Continuity Studio — AI Development Continuity';
      const small=document.querySelector('.workspace-mini small');
      if(small)small.textContent=desktop.sandbox?'SANDBOX TEST ROOT':'LIVE DEVELOPMENT ROOT';
      const rootLabel=document.querySelector('.workspace-mini b');
      if(rootLabel){rootLabel.textContent=info.root;rootLabel.title=info.root;}
      document.querySelector('.sidebar-bottom p').textContent=desktop.sandbox?'These are real rc9 scripts, but only fictional sandbox project files are used.':'Existing PowerShell engines are invoked only when you choose Generate.';
      document.querySelector('.preview-label').textContent=desktop.sandbox?'SANDBOX · REAL ENGINES':'LIVE WINDOWS BETA';
      const footer=document.querySelector('.statusbar');
      if(footer){footer.children[0].textContent=desktop.sandbox?'DISPOSABLE SANDBOX · UNMODIFIED RC9 ENGINES':'LIVE MODE · EXISTING RC9 BACKEND';footer.children[1].textContent=info.root;footer.children[1].title=info.root;
        const keys=footer.querySelector('.statuskeys');if(keys)keys.textContent='Ctrl+1/2/3 switch · Ctrl+Enter generate';}
      const note=document.querySelector('.bottom-note span');
      if(note) note.textContent='Live outputs will be checked against coverage evidence. A completed process is not automatically a complete handoff.';
      const expl=document.querySelector('.panel-footer > p');
      if(expl)expl.textContent=desktop.sandbox?'Runs copied rc9 scripts against your synthetic test project only.':'Generates actual output using the installed PowerShell engine.';
      const h=document.querySelector('.panel-heading.result-header h2');if(h)h.textContent='Execution status';
      const hp=document.querySelector('.panel-heading.result-header p');if(hp)hp.textContent='Actual backend progress and coverage';
      document.querySelector('.result-tools').hidden=true;
      state.results={structure:null,organization:null,deep:null};
      renderMode();
      if(!desktop.ready){announce('PowerShell backend unavailable. '+desktop.issue);return;}
      const discovered=await api('/api/projects');
      projects=(discovered.projects||[]).map(p=>({...p,id:p.path}));
      if(info.lastProject && projects.some(p=>p.id===info.lastProject)){
        state.lastProject=info.lastProject;
        for(const s of Object.values(state.settings))s.project=info.lastProject;
      }else if(projects.length){
        // First suggestion is selected, but is NOT mislabelled as previously used.
        for(const s of Object.values(state.settings))s.project=projects[0].id;
      }
      renderMode();
      announce(`${projects.length} projects discovered from the existing backend.`);
    }catch(e){
      desktop.enabled=true;desktop.ready=false;desktop.issue=e.message;
      renderMode();announce('Desktop host unavailable: '+e.message);
    }
  }
  async function startLive(){
    if(state.busy||!desktop.ready)return;
    const project=selectedProject();if(needsProject()&&!project)return;
    const m=state.mode,s={...current(),projectPath:needsProject()?project.path:''};
    const target=project&&needsProject()?project.name:'Entire workspace';
    const result={mode:m,status:'running',title:'Starting backend…',detail:'Launching PowerShell.',target,
                  artifacts:[],warnings:[],events:[],log:'',detailsOpen:false};
    state.busy=true;state.results[m]=result;updateResult();
    try{
      const initial=await api('/api/run',{mode:m,settings:s});
      result.log=initial.log;
      desktop.cursor=0;
      await pollLive(m,result);
    }catch(e){
      state.busy=false;result.status='failed';result.title='Could not start operation';result.detail=e.message;
      updateResult();announce(result.title+': '+e.message);
    }
  }
  async function pollLive(m,result){
    if(!state.busy||state.results[m]!==result)return;
    try{
      const snapshot=await api('/api/status?since='+desktop.cursor);
      desktop.cursor=snapshot.cursor||desktop.cursor;
      result.events.push(...(snapshot.events||[]).map(e=>e.text));
      if(result.events.length>400)result.events.splice(0,result.events.length-400);
      result.status=snapshot.status;result.title=snapshot.title||result.title;
      result.detail=snapshot.detail||result.detail;result.log=snapshot.log||result.log;
      result.warnings=snapshot.warnings||[];result.artifacts=snapshot.artifacts||[];
      if(snapshot.status!=='running'){
        state.busy=false;
        if(snapshot.status==='complete'||snapshot.status==='incomplete'){
          const p=selectedProject();if(p)state.lastProject=p.id;
        }
        announce('Live operation '+snapshot.status+'.');
      }
      if(state.mode===m)updateResult();
      if(state.busy)desktop.timer=setTimeout(()=>pollLive(m,result),600);
    }catch(e){
      state.busy=false;result.status='unknown';result.title='Connection to desktop host interrupted';
      result.detail=e.message+'. The backend might still be running. Check the host logs.';
      updateResult();announce(result.title);
    }
  }
  async function cancelLive(){
    if(!state.busy)return;
    if(!confirm('Interrupt the PowerShell operation? Publication may be in progress. Temporary files or staging may remain.'))return;
    try{
      await api('/api/cancel',{});
      announce('Cancellation requested. Checking backend termination…');
    }catch(e){announce('Cancellation request failed: '+e.message);}
  }
  async function openLiveArtifact(path){
    if(!desktop.enabled)return;
    try{await api('/api/open',{path});}
    catch(e){announce('Could not open output: '+e.message);alert('Could not open output: '+e.message);}
  }
  // Plain-language help: delayed mouse hover, immediate keyboard focus, and click/tap on ? icons.
  // Text is inserted with textContent, so help descriptions cannot execute markup.
  function setupHelp(){
    const tip=$('helpTooltip');
    const delayMs=600;
    let target=null, timer=null, pinned=false;
    const clearTimer=()=>{if(timer!==null){clearTimeout(timer);timer=null;}};
    const close=()=>{
      clearTimer();
      if(target)target.removeAttribute('aria-describedby');
      target=null;pinned=false;tip.hidden=true;
    };
    const position=()=>{
      if(!target||tip.hidden||!target.isConnected){close();return;}
      const r=target.getBoundingClientRect(), pad=10, gap=10;
      const w=tip.offsetWidth,h=tip.offsetHeight;
      let x=r.left+(r.width-w)/2;
      x=Math.max(pad,Math.min(x,window.innerWidth-w-pad));
      let y=r.bottom+gap;
      if(y+h>window.innerHeight-pad)y=r.top-h-gap;
      y=Math.max(pad,Math.min(y,window.innerHeight-h-pad));
      tip.style.left=Math.round(x)+'px';tip.style.top=Math.round(y)+'px';
    };
    const show=el=>{
      if(!el||!el.isConnected||!el.dataset.help)return;
      if(target&&target!==el)target.removeAttribute('aria-describedby');
      target=el;clearTimer();
      tip.textContent=el.dataset.help;
      // Reset prior coordinates before measuring: a resized window can leave the
      // previous fixed-position tooltip outside the viewport and distort its size.
      tip.style.left='0px';
      tip.style.top='0px';
      tip.hidden=false;
      el.setAttribute('aria-describedby','helpTooltip');
      position();
    };
    const schedule=el=>{
      if(pinned)return;
      if(target===el&&!tip.hidden)return;
      clearTimer();
      if(target&&target!==el)close();
      if(el)timer=setTimeout(()=>show(el),delayMs);
    };
    document.addEventListener('pointerover',e=>{
      if(e.pointerType==='touch')return;
      const el=e.target.closest?.('[data-help]');
      if(!el||el.contains(e.relatedTarget))return;
      schedule(el);
    });
    document.addEventListener('pointerout',e=>{
      if(pinned)return;
      const el=e.target.closest?.('[data-help]');
      if(!el||el.contains(e.relatedTarget))return;
      close();
    });
    document.addEventListener('focusin',e=>{
      const el=e.target.closest?.('[data-help]');
      if(el&&e.target.matches(':focus-visible'))show(el);
    });
    document.addEventListener('focusout',e=>{
      if(target&&!pinned&&target.contains(e.target))close();
    });
    document.addEventListener('click',e=>{
      const b=e.target.closest?.('.help-dot[data-help]');
      if(b){
        e.preventDefault();e.stopPropagation();
        if(target===b&&pinned){close();return;}
        show(b);pinned=true;
      }else if(pinned||!tip.hidden){close();}
    });
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!tip.hidden)close();});
    window.addEventListener('resize',()=>{if(!tip.hidden)position();});
    // Scrolling a form should never leave a detached explanation floating onscreen.
    document.addEventListener('scroll',()=>{if(!tip.hidden)close();},true);
  }

  function init(){
    setupHelp();
    document.querySelectorAll('.nav-item').forEach(b=>b.addEventListener('click',()=>switchMode(b.dataset.mode)));
    document.querySelectorAll('[data-scope]').forEach(b=>b.addEventListener('click',()=>{if(state.busy)return;current().scope=b.dataset.scope;renderMode();}));
    document.querySelectorAll('[data-capture]').forEach(b=>b.addEventListener('click',()=>{if(state.busy)return;state.settings.deep.capture=b.dataset.capture;renderMode();}));
    $('recentProject').addEventListener('click',()=>{current().project=state.lastProject;$('projectSearch').value='';updateProjectList();});
    $('projectSearch').addEventListener('input',updateProjectList);
    $('taskNote').addEventListener('input',()=>{state.settings.deep.note=$('taskNote').value;$('noteCount').textContent=$('taskNote').value.length+' / 240';});
    $('sizeCheck').addEventListener('change',()=>{state.settings.organization.sizes=$('sizeCheck').checked;});
    $('resetButton').addEventListener('click',resetSettings);
    $('resetResult').addEventListener('click',clearResult);
    $('previewButton').addEventListener('click',preview);
    $('cancelButton').addEventListener('click',cancelPreview);
    $('themeButton').addEventListener('click',toggleTheme);
    // Native Windows <select> menus do not reliably send hover events for
    // individual options. Explain the currently selected outcome on the
    // control itself, and provide visible text beside it.
    const sampleHelp={
      complete:'Complete: the example finishes and all expected information is accounted for.',
      incomplete:'Needs review: the example finishes, but some information may be missing.',
      unknown:'Coverage unknown: the example finishes, but the app cannot confirm what was included.',
      failed:'Failure: the example cannot finish. You would need to check the error before retrying.'
    };
    const updateSampleHelp=()=>{
      const sel=$('outcomeChoice');
      if(!sel)return;
      sel.dataset.help=sampleHelp[sel.value]||'Choose an example result to preview.';
      const desc=$('sampleOutcomeHelp');
      if(desc)desc.textContent=sel.dataset.help;
    };
    $('outcomeChoice').addEventListener('change',updateSampleHelp);
    updateSampleHelp();
    document.addEventListener('keydown',e=>{
      if(e.ctrlKey&&['1','2','3'].includes(e.key)){e.preventDefault();switchMode(['structure','organization','deep'][Number(e.key)-1]);}
      else if(e.ctrlKey&&e.key.toLowerCase()==='f'&&needsProject()){e.preventDefault();$('projectSearch').focus();}
      else if(e.ctrlKey&&e.key==='Enter'&&modes[state.mode]){e.preventDefault();preview();}
    });
    renderMode();
    if(location.protocol==='http:' && location.hostname==='127.0.0.1') initializeDesktop();
  }
  document.addEventListener('DOMContentLoaded',init);
  // Only expose read-only inspection/test methods. Nothing connects to an engine.
  window.ADC_UX_TEST = Object.freeze({
    mode:()=>state.mode, theme:()=>state.theme, projectCount:()=>projects.length,
    selectedProject:()=>selectedProject()?.name, busy:()=>state.busy,
    result:()=>state.results[state.mode]?.status || 'idle',
    hasBackend:()=>desktop.enabled&&desktop.ready
  });
})();
