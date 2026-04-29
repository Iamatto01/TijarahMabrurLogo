// ===== APP LOGIC =====

let userRole = 'client';

function setLoginRole(role, buttonEl) {
  userRole = role;
  document.getElementById('login-role').value = role;
  document.querySelectorAll('.login-role-btn').forEach(el => {
    el.classList.remove('active');
    el.classList.add('opacity-70');
  });
  if (buttonEl) {
    buttonEl.classList.add('active');
    buttonEl.classList.remove('opacity-70');
  }
}

function doLogin() {
  userRole = document.getElementById('login-role').value;
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app-shell').style.display = 'flex';
  
  const navItems = document.querySelectorAll('.nav-item');
  const adminOnlyItems = document.querySelectorAll('.admin-only');
  
  if (userRole === 'report') {
    // Report Role: Hanya boleh lihat Laporan Servis dan Log Keluar
    navItems.forEach(el => {
      if (el.innerText.includes('Laporan Servis') || el.innerText.includes('Log Keluar')) {
        el.style.display = 'flex';
      } else {
        el.style.display = 'none';
      }
    });
    switchView('view-reports');
  } else if (userRole === 'admin') {
    // Admin Role: Tunjuk semua menu termasuk CMS detail
    navItems.forEach(el => el.style.display = 'flex');
    adminOnlyItems.forEach(el => el.style.display = 'flex');
    switchView('view-dashboard');
  } else {
    // Client Role: Tunjuk semua (normal view), tanpa CMS admin
    navItems.forEach(el => el.style.display = 'flex');
    adminOnlyItems.forEach(el => el.style.display = 'none');
    switchView('view-dashboard');
  }
}

function doLogout() {
  document.getElementById('app-shell').style.display = 'none';
  document.getElementById('login-screen').style.display = 'flex';
}
// Sidebar
function toggleSidebar(){document.getElementById('sidebar').classList.toggle('sidebar-open');document.getElementById('sidebar-overlay').classList.toggle('overlay-open');}

// Notifications
function toggleNotif(){document.getElementById('notif-panel').classList.toggle('hidden');}

// Chat
function toggleChat(){document.getElementById('chat-bubble').classList.toggle('hidden');}
function sendChat(){const inp=document.getElementById('chat-input');if(!inp.value.trim())return;const w=document.querySelector('.chat-window .bg-white');w.innerHTML+=`<p class="bg-blue-50 rounded-lg p-3 text-right">${inp.value}</p>`;inp.value='';setTimeout(()=>{w.innerHTML+=`<p class="bg-gray-100 rounded-lg p-3">Terima kasih! Kami akan hubungi anda segera. 😊</p>`;},800);}

// View switching
let currentView='view-dashboard';
function switchView(viewId,navEl){
  currentView=viewId;
  renderView(viewId);
  document.querySelectorAll('.nav-item').forEach(el=>el.classList.remove('nav-active'));
  if(navEl)navEl.classList.add('nav-active');
  const titles={'view-dashboard':'Dashboard','view-organisasi':'Maklumat Organisasi','view-assets':'Mesin & Aset','view-documents':'Pusat Dokumen','view-mykkp':'MyKKP','view-reports':'Laporan Servis','view-cms':'CMS Detail','view-training':'Latihan & Permintaan','view-settings':'Tetapan'};
  document.getElementById('topbar-title').innerText=titles[viewId]||'Dashboard';
  if(window.innerWidth<768){document.getElementById('sidebar').classList.remove('sidebar-open');document.getElementById('sidebar-overlay').classList.remove('overlay-open');}
}

function renderView(viewId){
  const c=document.getElementById('views-container');
  const renderers={'view-dashboard':renderDashboard,'view-organisasi':renderOrganisasi,'view-assets':renderAssets,'view-documents':renderDocuments,'view-mykkp':renderMyKKP,'view-reports':renderReports,'view-cms':renderCMS,'view-training':renderTraining,'view-settings':renderSettings};
  const fn=renderers[viewId];
  if(fn)c.innerHTML=fn();
}

// Org tabs
function switchOrgTab(tabId,btn){
  document.querySelectorAll('.org-tab').forEach(el=>el.classList.add('hidden'));
  document.querySelectorAll('.tab-btn').forEach(el=>el.classList.remove('tab-active'));
  document.getElementById(tabId).classList.remove('hidden');
  btn.classList.add('tab-active');
}

// Profile edit
let editMode=false;
function toggleEditProfile(){editMode=!editMode;const fields=document.querySelectorAll('.profile-field');const actions=document.getElementById('profile-actions');
  fields.forEach(f=>{if(editMode){f.removeAttribute('readonly');f.classList.add('input-edit');}else{f.setAttribute('readonly','');f.classList.remove('input-edit');}});
  actions.classList.toggle('hidden',!editMode);document.getElementById('btn-edit-profile').innerText=editMode?'❌ Batal Edit':'✏️ Update Profile';
  if(!editMode)renderView('view-organisasi');
}
function saveProfile(){
  APP_DATA.company.name=document.getElementById('pf-name').value;
  APP_DATA.company.address=document.getElementById('pf-addr').value;
  APP_DATA.company.phone=document.getElementById('pf-phone').value;
  APP_DATA.company.email=document.getElementById('pf-email').value;
  APP_DATA.company.website=document.getElementById('pf-web').value;
  saveData(APP_DATA);editMode=false;renderView('view-organisasi');showToast('Profil berjaya dikemaskini!');
}
function cancelEditProfile(){editMode=false;renderView('view-organisasi');}

// Machine CRUD
function filterMachines(){
  const q=(document.getElementById('search-machine')?.value||'').toLowerCase();
  const s=document.getElementById('filter-status')?.value||'all';
  document.querySelectorAll('.machine-card').forEach(c=>{
    const nameMatch=c.dataset.name.includes(q)||c.dataset.pmt.includes(q);
    const statusMatch=s==='all'||c.dataset.status===s;
    c.style.display=(nameMatch&&statusMatch)?'flex':'none';
  });
}

function openAddMachine(){
  openModal('Tambah Mesin Baru',`<div class="space-y-3">
    <div><label class="text-xs text-gray-500">Nama Mesin</label><input id="am-name" class="form-input" placeholder="cth: Boiler Unit C"></div>
    <div class="grid grid-cols-2 gap-3">
      <div><label class="text-xs text-gray-500">No PMT</label><input id="am-pmt" class="form-input" placeholder="PMT-007"></div>
      <div><label class="text-xs text-gray-500">Serial No</label><input id="am-serial" class="form-input" placeholder="BLR-2024-001"></div>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div><label class="text-xs text-gray-500">Lokasi</label><input id="am-loc" class="form-input" placeholder="Loji Utama"></div>
      <div><label class="text-xs text-gray-500">Jenis</label><select id="am-type" class="form-input"><option>Boiler</option><option>Crane</option><option>Pressure Vessel</option><option>Lift</option><option>Forklift</option></select></div>
    </div>
    <div><label class="text-xs text-gray-500">Tarikh Tamat CF</label><input id="am-cf" type="date" class="form-input"></div>
    <button onclick="saveMachine()" class="w-full bg-navy text-white py-2.5 rounded-lg font-medium text-sm mt-2">💾 Simpan</button>
  </div>`);
}

function saveMachine(){
  const m={id:'M'+String(Date.now()).slice(-4),name:document.getElementById('am-name').value,pmt:document.getElementById('am-pmt').value,serial:document.getElementById('am-serial').value,location:document.getElementById('am-loc').value,type:document.getElementById('am-type').value,cfExpiry:document.getElementById('am-cf').value,status:'valid'};
  if(!m.name){showToast('Sila isi nama mesin!');return;}
  const now=new Date();const exp=new Date(m.cfExpiry);const diff=(exp-now)/(1000*60*60*24);
  if(diff<0)m.status='expired';else if(diff<90)m.status='expiring';
  APP_DATA.machines.push(m);saveData(APP_DATA);closeModal();renderView('view-assets');showToast('Mesin berjaya ditambah!');
}

function openEditMachine(id){
  const m=APP_DATA.machines.find(x=>x.id===id);if(!m)return;
  openModal('Edit Mesin',`<div class="space-y-3">
    <div><label class="text-xs text-gray-500">Nama</label><input id="em-name" class="form-input" value="${m.name}"></div>
    <div class="grid grid-cols-2 gap-3">
      <div><label class="text-xs text-gray-500">No PMT</label><input id="em-pmt" class="form-input" value="${m.pmt}"></div>
      <div><label class="text-xs text-gray-500">Serial</label><input id="em-serial" class="form-input" value="${m.serial}"></div>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <div><label class="text-xs text-gray-500">Lokasi</label><input id="em-loc" class="form-input" value="${m.location}"></div>
      <div><label class="text-xs text-gray-500">Jenis</label><input id="em-type" class="form-input" value="${m.type}"></div>
    </div>
    <div><label class="text-xs text-gray-500">Tarikh Tamat CF</label><input id="em-cf" type="date" class="form-input" value="${m.cfExpiry}"></div>
    <div class="flex gap-2 mt-2">
      <button onclick="updateMachine('${id}')" class="flex-grow bg-navy text-white py-2.5 rounded-lg font-medium text-sm">💾 Kemaskini</button>
      <button onclick="deleteMachine('${id}')" class="bg-danger text-white py-2.5 px-4 rounded-lg font-medium text-sm">🗑️</button>
    </div>
  </div>`);
}

function updateMachine(id){
  const m=APP_DATA.machines.find(x=>x.id===id);if(!m)return;
  m.name=document.getElementById('em-name').value;m.pmt=document.getElementById('em-pmt').value;m.serial=document.getElementById('em-serial').value;m.location=document.getElementById('em-loc').value;m.type=document.getElementById('em-type').value;m.cfExpiry=document.getElementById('em-cf').value;
  const now=new Date();const exp=new Date(m.cfExpiry);const diff=(exp-now)/(1000*60*60*24);
  m.status=diff<0?'expired':diff<90?'expiring':'valid';
  saveData(APP_DATA);closeModal();renderView('view-assets');showToast('Mesin berjaya dikemaskini!');
}

function deleteMachine(id){if(!confirm('Padam mesin ini?'))return;APP_DATA.machines=APP_DATA.machines.filter(x=>x.id!==id);saveData(APP_DATA);closeModal();renderView('view-assets');showToast('Mesin telah dipadam.');}

function showMachineDetail(id){
  const m=APP_DATA.machines.find(x=>x.id===id);if(!m)return;
  const reports=APP_DATA.reports.filter(r=>r.machineId===id);
  const qr=generateQR(m.pmt);
  openModal(m.name,`<div class="space-y-4">
    <div class="flex gap-4">
      <div class="flex-grow space-y-2 text-sm">
        <div class="flex"><span class="text-gray-500 w-28">No PMT:</span><span class="font-semibold">${m.pmt}</span></div>
        <div class="flex"><span class="text-gray-500 w-28">Serial No:</span><span class="font-semibold">${m.serial}</span></div>
        <div class="flex"><span class="text-gray-500 w-28">Lokasi:</span><span class="font-semibold">${m.location}</span></div>
        <div class="flex"><span class="text-gray-500 w-28">Jenis:</span><span class="font-semibold">${m.type}</span></div>
        <div class="flex"><span class="text-gray-500 w-28">Tamat CF:</span><span class="font-semibold badge ${m.status==='valid'?'badge-green':m.status==='expired'?'badge-red':'badge-yellow'}">${m.cfExpiry}</span></div>
      </div>
      <div class="text-center"><p class="text-xs text-gray-500 mb-1">QR Code</p>${qr}</div>
    </div>
    <hr>
    <h4 class="font-bold text-sm">📋 Sejarah Laporan</h4>
    ${reports.length?reports.map(r=>`<div class="timeline-item ${r.status}"><div class="flex justify-between"><div><p class="text-sm font-medium">${r.type}</p><p class="text-xs text-gray-500">${r.tech}</p></div><span class="text-xs text-gray-400">${r.date}</span></div></div>`).join(''):'<p class="text-sm text-gray-400">Tiada laporan lagi</p>'}
  </div>`);
}

function generateQR(text){
  const s=80;let svg=`<svg width="${s}" height="${s}" viewBox="0 0 ${s} ${s}" xmlns="http://www.w3.org/2000/svg"><rect width="${s}" height="${s}" fill="white"/>`;
  for(let i=0;i<10;i++)for(let j=0;j<10;j++){if((i+j*7+text.charCodeAt(i%text.length))%3!==0)svg+=`<rect x="${i*8}" y="${j*8}" width="8" height="8" fill="#0A2647"/>`;}
  svg+='</svg>';return svg;
}

// Documents
function selectDoc(idx,el){
  const d=APP_DATA.documents[idx];if(!d)return;
  document.querySelectorAll('.doc-item').forEach(e=>{e.classList.remove('doc-active');});
  el.classList.add('doc-active');
  document.getElementById('doc-viewer-title').innerText=d.name;
  document.getElementById('doc-viewer').innerHTML=`<div class="text-center max-w-md">
    <div class="text-6xl mb-4">📋</div><h3 class="font-bold text-lg text-gray-800 mb-2">${d.name}</h3>
    <p class="text-sm text-gray-500 mb-4">Jenis: ${d.type} | Tarikh: ${d.date}</p>
    <div class="bg-white border-2 border-dashed border-gray-200 rounded-xl p-8 text-gray-400 text-sm"><p class="mb-2">Pratonton Dokumen</p>
    <div class="space-y-2 text-left"><div class="h-3 bg-gray-200 rounded w-full"></div><div class="h-3 bg-gray-200 rounded w-5/6"></div><div class="h-3 bg-gray-200 rounded w-4/6"></div><div class="h-3 bg-gray-200 rounded w-full"></div></div></div>
    <div class="flex gap-3 justify-center mt-4"><button class="bg-navy text-white px-4 py-2 rounded-lg text-sm">📥 Muat Turun</button><button class="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm">🖨️ Cetak</button></div></div>`;
}

function openAddDoc(){
  openModal('Muat Naik Dokumen',`<div class="space-y-3">
    <div><label class="text-xs text-gray-500">Nama Dokumen</label><input id="ad-name" class="form-input" placeholder="cth: HIRARC Loji B"></div>
    <div><label class="text-xs text-gray-500">Jenis</label><select id="ad-type" class="form-input"><option>HIRARC</option><option>CHRA</option><option>NRA</option><option>Policy</option><option>ERP</option></select></div>
    <div class="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center text-gray-400 text-sm cursor-pointer hover:border-safety transition"><p>📁 Seret fail PDF ke sini</p><p class="text-xs mt-1">atau klik untuk pilih fail</p></div>
    <button onclick="saveDoc()" class="w-full bg-navy text-white py-2.5 rounded-lg font-medium text-sm">💾 Simpan</button>
  </div>`);
}
function saveDoc(){
  const d={id:'D'+String(Date.now()).slice(-4),name:document.getElementById('ad-name').value,type:document.getElementById('ad-type').value,date:new Date().toISOString().slice(0,10),status:'active'};
  if(!d.name){showToast('Sila isi nama dokumen!');return;}
  APP_DATA.documents.push(d);saveData(APP_DATA);closeModal();renderView('view-documents');showToast('Dokumen berjaya dimuat naik!');
}

// Reports
function filterReports(type,btn){
  document.querySelectorAll('.report-filter-btn').forEach(b=>b.classList.remove('tab-active'));
  btn.classList.add('tab-active');
  document.querySelectorAll('.report-item').forEach(r=>{r.style.display=(type==='all'||r.dataset.type===type)?'flex':'none';});
}
function showReportDetail(id){
  const r=APP_DATA.reports.find(x=>x.id===id);if(!r)return;
  const m=APP_DATA.machines.find(x=>x.id===r.machineId);
  openModal('Detail Laporan',`<div class="space-y-3 text-sm">
    <div class="flex"><span class="text-gray-500 w-28">Jenis:</span><span class="font-semibold">${r.type}</span></div>
    <div class="flex"><span class="text-gray-500 w-28">Mesin:</span><span class="font-semibold">${m?m.name:'N/A'}</span></div>
    <div class="flex"><span class="text-gray-500 w-28">Tarikh:</span><span class="font-semibold">${r.date}</span></div>
    <div class="flex"><span class="text-gray-500 w-28">Teknisyen:</span><span class="font-semibold">${r.tech}</span></div>
    <div class="flex"><span class="text-gray-500 w-28">Status:</span><span class="badge ${r.status==='completed'?'badge-green':r.status==='pending'?'badge-yellow':'badge-red'}">${r.status}</span></div>
  </div>`);
}
function openAddReport(){
  const machines=APP_DATA.machines.map(m=>`<option value="${m.id}">${m.name} (${m.pmt})</option>`).join('');
  openModal('Tambah Laporan',`<div class="space-y-3">
    <div><label class="text-xs text-gray-500">Mesin</label><select id="ar-machine" class="form-input">${machines}</select></div>
    <div><label class="text-xs text-gray-500">Jenis Laporan</label><select id="ar-type" class="form-input"><option>PMT Service</option><option>PMA Calibration</option><option>Hydrostatic Test</option><option>UT Thickness</option><option>Load Test</option></select></div>
    <div><label class="text-xs text-gray-500">Tarikh</label><input id="ar-date" type="date" class="form-input"></div>
    <div><label class="text-xs text-gray-500">Teknisyen</label><input id="ar-tech" class="form-input" placeholder="Nama teknisyen"></div>
    <button onclick="saveReport()" class="w-full bg-navy text-white py-2.5 rounded-lg font-medium text-sm">💾 Simpan</button>
  </div>`);
}
function saveReport(){
  const r={id:'R'+String(Date.now()).slice(-4),machineId:document.getElementById('ar-machine').value,type:document.getElementById('ar-type').value,date:document.getElementById('ar-date').value,tech:document.getElementById('ar-tech').value,status:'pending'};
  if(!r.date||!r.tech){showToast('Sila lengkapkan maklumat!');return;}
  APP_DATA.reports.push(r);saveData(APP_DATA);closeModal();renderView('view-reports');showToast('Laporan berjaya ditambah!');
}

// Training
function openAddTraining(course){
  openModal('Mohon Latihan',`<div class="space-y-3">
    <div><label class="text-xs text-gray-500">Kursus</label><select id="at-course" class="form-input">
      ${['OSHA Awareness','HIRARC Workshop','First Aid & CPR','Fire Safety Drill','Ergonomics','Chemical Safety'].map(c=>`<option ${c===course?'selected':''}>${c}</option>`).join('')}
    </select></div>
    <div><label class="text-xs text-gray-500">Tarikh Cadangan</label><input id="at-date" type="date" class="form-input"></div>
    <div><label class="text-xs text-gray-500">Bilangan Peserta</label><input id="at-part" type="number" class="form-input" value="20"></div>
    <button onclick="saveTraining()" class="w-full bg-safety text-white py-2.5 rounded-lg font-medium text-sm">📨 Hantar Permohonan</button>
  </div>`);
}
function saveTraining(){
  const t={id:'T'+String(Date.now()).slice(-4),course:document.getElementById('at-course').value,date:document.getElementById('at-date').value,participants:parseInt(document.getElementById('at-part').value)||20,status:'requested'};
  if(!t.date){showToast('Sila pilih tarikh!');return;}
  APP_DATA.training.push(t);saveData(APP_DATA);closeModal();renderView('view-training');showToast('Permohonan berjaya dihantar!');
}

// Settings
function saveUserSettings(){
  APP_DATA.user.name=document.getElementById('st-name').value;
  APP_DATA.user.position=document.getElementById('st-pos').value;
  APP_DATA.user.email=document.getElementById('st-email').value;
  APP_DATA.user.phone=document.getElementById('st-phone').value;
  saveData(APP_DATA);showToast('Profil berjaya dikemaskini!');
}
function toggleNotifPref(key,el){APP_DATA.notifications[key]=!APP_DATA.notifications[key];el.classList.toggle('on');saveData(APP_DATA);}

// Certificates
function showCertificate(id){
  const ct=APP_DATA.certificates.find(x=>x.id===id);if(!ct)return;
  document.getElementById('cert-title').innerText='Sijil '+ct.abbr;
  document.getElementById('cert-body').innerHTML=`<div class="cert-page">
    <div class="cert-logo">${ct.abbr}</div>
    <p class="text-xs text-gray-500 uppercase tracking-widest mb-2">${ct.issuer}</p>
    <h2 class="text-xl font-bold text-navy mb-1">SIJIL PERAKUAN</h2>
    <h3 class="text-base font-semibold text-gray-700 mb-6">${ct.title}</h3>
    <p class="text-sm text-gray-600 mb-1">Dengan ini disahkan bahawa</p>
    <h2 class="text-2xl font-bold text-navy my-3 border-b-2 border-navy pb-2 inline-block px-8">${ct.holder}</h2>
    <p class="text-sm text-gray-600 mt-3">No. K/P: <strong>${ct.ic}</strong></p>
    <p class="text-sm text-gray-600 mt-1">No. Pendaftaran: <strong>${ct.regNo}</strong></p>
    <p class="text-sm text-gray-600 mt-4">telah memenuhi semua syarat dan kelayakan sebagai</p>
    <p class="text-base font-bold text-safety mt-2 mb-4">${ct.title}</p>
    <div class="flex justify-between mt-8 pt-4 border-t border-gray-200 text-xs text-gray-500">
      <div><p>Sah Sehingga:</p><p class="font-bold text-navy text-sm">${ct.validUntil}</p></div>
      <div class="text-right"><p>Dikeluarkan oleh:</p><p class="font-bold text-sm">${ct.issuer}</p><div class="mt-2 border-t border-gray-400 pt-1 text-xs">Tandatangan & Cop Rasmi</div></div>
    </div>
  </div>`;
  document.getElementById('cert-modal').classList.remove('hidden');
}
function closeCert(){document.getElementById('cert-modal').classList.add('hidden');}
function printCert(){const w=window.open('','','width=800,height=600');w.document.write('<html><head><title>Sijil</title><style>body{font-family:serif;padding:2rem}.cert-page{border:3px double #0A2647;padding:3rem;text-align:center}.cert-logo{width:80px;height:80px;margin:0 auto 1rem;background:#0A2647;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.5rem;font-weight:700}</style></head><body>');w.document.write(document.getElementById('cert-body').innerHTML);w.document.write('</body></html>');w.document.close();w.print();}

// Modal
function openModal(title,body){document.getElementById('modal-title').innerText=title;document.getElementById('modal-body').innerHTML=body;document.getElementById('modal-overlay').classList.remove('hidden');}
function closeModal(){document.getElementById('modal-overlay').classList.add('hidden');}

// Toast
function showToast(msg){const t=document.createElement('div');t.className='fixed bottom-20 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white px-6 py-3 rounded-xl shadow-lg text-sm z-[100] transition-opacity';t.innerText=msg;document.body.appendChild(t);setTimeout(()=>{t.style.opacity='0';setTimeout(()=>t.remove(),300);},2500);}

// Init
document.addEventListener('DOMContentLoaded',()=>{renderView('view-dashboard');});
