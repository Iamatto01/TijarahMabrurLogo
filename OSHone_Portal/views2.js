// ===== VIEW RENDERERS Part 2: MyKKP, Documents, Reports, Training, Settings =====

function renderMyKKP() {
  const c = APP_DATA.company;
  const machines = APP_DATA.machines;
  const validCF = machines.filter(m=>m.status==='valid').length;
  const expiredCF = machines.filter(m=>m.status==='expired').length;
  const expiringCF = machines.filter(m=>m.status==='expiring').length;
  return `<div class="max-w-6xl mx-auto">
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-3">
      <div><h2 class="text-2xl font-bold text-gray-800">🏛️ MyKKP — Portal JKKP</h2><p class="text-sm text-gray-500 mt-1">Sistem Pengurusan Keselamatan & Kesihatan Pekerjaan Malaysia</p></div>
      <a href="https://mykkp.dosh.gov.my" target="_blank" class="bg-navy text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-900 transition flex items-center gap-2">🌐 Buka MyKKP Rasmi ↗</a>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="glass-card stat-card p-4 border-l-4 border-l-success"><p class="text-xs text-gray-500">CF Sah</p><p class="text-2xl font-bold text-success mt-1">${validCF}</p></div>
      <div class="glass-card stat-card p-4 border-l-4 border-l-danger"><p class="text-xs text-gray-500">CF Tamat</p><p class="text-2xl font-bold text-danger mt-1">${expiredCF}</p></div>
      <div class="glass-card stat-card p-4 border-l-4 border-l-warning"><p class="text-xs text-gray-500">CF Akan Tamat</p><p class="text-2xl font-bold text-warning mt-1">${expiringCF}</p></div>
      <div class="glass-card stat-card p-4 border-l-4 border-l-navy"><p class="text-xs text-gray-500">Jumlah PMT</p><p class="text-2xl font-bold text-navy mt-1">${machines.length}</p></div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <div class="glass-card p-6">
        <h3 class="font-bold text-base mb-4">📋 Pendaftaran JKKP</h3>
        <div class="space-y-3 text-sm">
          <div class="flex justify-between py-2 border-b border-gray-100"><span class="text-gray-600">Nama Syarikat</span><span class="font-semibold">${c.name}</span></div>
          <div class="flex justify-between py-2 border-b border-gray-100"><span class="text-gray-600">No. Pendaftaran JKKP</span><span class="font-semibold text-navy">JKKP/PP/2024/00456</span></div>
          <div class="flex justify-between py-2 border-b border-gray-100"><span class="text-gray-600">Kategori</span><span class="badge badge-blue">Kilang & Jentera</span></div>
          <div class="flex justify-between py-2 border-b border-gray-100"><span class="text-gray-600">Status</span><span class="badge badge-green">Aktif</span></div>
          <div class="flex justify-between py-2"><span class="text-gray-600">Tarikh Daftar</span><span class="font-semibold">15 Jan 2024</span></div>
        </div>
      </div>
      <div class="glass-card p-6">
        <h3 class="font-bold text-base mb-4">📨 Status Submission</h3>
        <div class="space-y-3">
          <div class="flex items-center gap-3 p-3 rounded-xl border border-green-100 bg-green-50"><div class="w-8 h-8 rounded-full bg-green-200 text-green-700 flex items-center justify-center text-xs font-bold">✓</div><div class="flex-grow"><p class="text-sm font-medium">JKKP 6 — Notifikasi Kemalangan</p><p class="text-xs text-gray-500">10 Mac 2024</p></div><span class="badge badge-green">Diterima</span></div>
          <div class="flex items-center gap-3 p-3 rounded-xl border border-green-100 bg-green-50"><div class="w-8 h-8 rounded-full bg-green-200 text-green-700 flex items-center justify-center text-xs font-bold">✓</div><div class="flex-grow"><p class="text-sm font-medium">JKKP 8 — Pendaftaran Jentera</p><p class="text-xs text-gray-500">5 Feb 2024</p></div><span class="badge badge-green">Diterima</span></div>
          <div class="flex items-center gap-3 p-3 rounded-xl border border-yellow-100 bg-yellow-50"><div class="w-8 h-8 rounded-full bg-yellow-200 text-yellow-700 flex items-center justify-center text-xs font-bold">⏳</div><div class="flex-grow"><p class="text-sm font-medium">JKKP 7 — Pembaharuan CF</p><p class="text-xs text-gray-500">20 Apr 2024</p></div><span class="badge badge-yellow">Dalam Proses</span></div>
          <div class="flex items-center gap-3 p-3 rounded-xl border border-blue-100 bg-blue-50"><div class="w-8 h-8 rounded-full bg-blue-200 text-blue-700 flex items-center justify-center text-xs font-bold">📝</div><div class="flex-grow"><p class="text-sm font-medium">JKKP 2 — Laporan Tahunan OSH</p><p class="text-xs text-gray-500">Akhir: 31 Dis 2024</p></div><span class="badge badge-blue">Belum Hantar</span></div>
        </div>
      </div>
    </div>
    <div class="glass-card overflow-hidden mb-6">
      <div class="bg-gray-50 px-5 py-4 border-b font-bold text-sm flex justify-between items-center"><span>📑 Senarai Pendaftaran Jentera (PMT)</span>
        <button onclick="openModal('Daftar Jentera Baru','<div class=\\'text-center py-8 text-gray-500\\'>Borang pendaftaran jentera JKKP.<br><br><a href=\\'https://mykkp.dosh.gov.my\\' target=\\'_blank\\' class=\\'bg-navy text-white px-6 py-2 rounded-lg text-sm inline-block mt-3\\'>Buka MyKKP ↗</a></div>')" class="bg-navy text-white px-3 py-1.5 rounded text-xs font-medium">+ Daftar Baru</button>
      </div>
      <div class="overflow-x-auto"><table class="w-full text-sm"><thead class="bg-gray-50 text-left"><tr><th class="px-5 py-3 text-xs text-gray-500 font-semibold">Mesin</th><th class="px-5 py-3 text-xs text-gray-500 font-semibold">No. PMT</th><th class="px-5 py-3 text-xs text-gray-500 font-semibold">Jenis</th><th class="px-5 py-3 text-xs text-gray-500 font-semibold">Tamat CF</th><th class="px-5 py-3 text-xs text-gray-500 font-semibold">Status</th></tr></thead>
        <tbody class="divide-y">${machines.map(m=>`<tr class="hover:bg-gray-50"><td class="px-5 py-3 font-medium">${m.name}</td><td class="px-5 py-3 text-gray-600">${m.pmt}</td><td class="px-5 py-3 text-gray-600">${m.type}</td><td class="px-5 py-3 ${m.status==='expired'?'text-danger font-semibold':m.status==='expiring'?'text-warning font-semibold':'text-gray-600'}">${m.cfExpiry}</td><td class="px-5 py-3"><span class="badge ${m.status==='valid'?'badge-green':m.status==='expired'?'badge-red':'badge-yellow'}">${m.status==='valid'?'Sah':m.status==='expired'?'Tamat':'Akan Tamat'}</span></td></tr>`).join('')}</tbody></table></div>
    </div>
    <div class="glass-card p-6">
      <h3 class="font-bold text-base mb-4">🔗 Pautan Pantas JKKP</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        ${[['https://mykkp.dosh.gov.my','MyKKP Portal','Portal utama JKKP','🏛️'],['https://www.dosh.gov.my','DOSH Official','Laman web rasmi JKKP','🌐'],['https://www.dosh.gov.my/index.php/legislation/acts','Akta & Peraturan','OSHA 1994, FMA 1967','📖'],['https://www.dosh.gov.my/index.php/factory-machinery/certificate-of-fitness','Certificate of Fitness','Maklumat CF & pembaharuan','📜'],['https://www.niosh.com.my','NIOSH Malaysia','Keselamatan & Kesihatan','🎓'],['https://www.cidb.gov.my','CIDB Portal','Industri Pembinaan','🏗️']].map(([url,title,desc,icon])=>`
        <a href="${url}" target="_blank" class="flex items-center gap-3 p-3 rounded-xl border border-gray-100 hover:border-navy hover:shadow-md transition cursor-pointer group"><div class="text-2xl">${icon}</div><div><p class="text-sm font-semibold group-hover:text-navy transition">${title}</p><p class="text-xs text-gray-500">${desc}</p></div></a>`).join('')}
      </div>
    </div>
  </div>`;
}

function renderDocuments() {
  const docs = APP_DATA.documents;
  const typeColors = {HIRARC:'blue',CHRA:'green',NRA:'yellow',Policy:'navy',ERP:'red'};
  return `<div class="max-w-6xl mx-auto h-full flex flex-col">
    <div class="flex justify-between items-center mb-5 flex-shrink-0">
      <h2 class="text-2xl font-bold text-gray-800">Pusat Dokumen</h2>
      <button onclick="openAddDoc()" class="bg-navy text-white px-4 py-2 rounded-lg text-sm font-medium">+ Muat Naik</button>
    </div>
    <div class="flex flex-col md:flex-row gap-5 flex-grow overflow-hidden">
      <div class="w-full md:w-1/3 bg-white border border-gray-200 rounded-2xl flex flex-col overflow-hidden shadow-sm" style="max-height:500px">
        <div class="bg-navy text-white p-4 flex-shrink-0"><h2 class="font-bold text-sm">📁 Senarai Dokumen</h2></div>
        <div class="overflow-y-auto flex-grow">
          ${docs.map((d,i)=>`<div class="doc-item border-b border-gray-100 p-4 cursor-pointer hover:bg-gray-50 transition flex items-start ${i===0?'doc-active':''}" onclick="selectDoc(${i},this)">
            <div class="bg-blue-50 text-navy rounded p-2 mr-3">📄</div>
            <div><h4 class="font-medium text-gray-900 text-sm">${d.name}</h4>
            <div class="flex gap-2 mt-1"><span class="badge badge-${typeColors[d.type]||'blue'}">${d.type}</span><span class="text-xs text-gray-400">${d.date}</span></div></div>
          </div>`).join('')}
        </div>
      </div>
      <div class="w-full md:w-2/3 bg-white border border-gray-200 rounded-2xl flex flex-col overflow-hidden shadow-sm flex-grow">
        <div class="bg-gray-50 border-b border-gray-200 p-4 flex justify-between items-center">
          <h3 id="doc-viewer-title" class="font-semibold text-gray-800 text-sm">${docs[0]?.name||'Tiada dokumen'}</h3>
          <button class="text-xs text-navy hover:text-safety font-medium">Buka Tab Baru ↗</button>
        </div>
        <div id="doc-viewer" class="flex-grow flex items-center justify-center bg-gray-50 p-6">
          <div class="text-center max-w-md">
            <div class="text-6xl mb-4">📋</div>
            <h3 class="font-bold text-lg text-gray-800 mb-2">${docs[0]?.name||''}</h3>
            <p class="text-sm text-gray-500 mb-4">Jenis: ${docs[0]?.type||''} | Tarikh: ${docs[0]?.date||''}</p>
            <div class="bg-white border-2 border-dashed border-gray-200 rounded-xl p-8 text-gray-400 text-sm">
              <p class="mb-2">Pratonton Dokumen</p>
              <div class="space-y-2 text-left text-xs text-gray-300">
                <div class="h-3 bg-gray-200 rounded w-full"></div>
                <div class="h-3 bg-gray-200 rounded w-5/6"></div>
                <div class="h-3 bg-gray-200 rounded w-4/6"></div>
                <div class="h-3 bg-gray-200 rounded w-full"></div>
                <div class="h-3 bg-gray-200 rounded w-3/6"></div>
              </div>
            </div>
            <div class="flex gap-3 justify-center mt-4">
              <button class="bg-navy text-white px-4 py-2 rounded-lg text-sm">📥 Muat Turun</button>
              <button class="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm">🖨️ Cetak</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>`;
}

function renderReports() {
  const reports = APP_DATA.reports;
  const machines = APP_DATA.machines;
  const types = [...new Set(reports.map(r=>r.type))];
  return `<div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Laporan Servis & Pemeriksaan</h2>
      <button onclick="openAddReport()" class="bg-navy text-white px-4 py-2 rounded-lg text-sm font-medium">+ Tambah Laporan</button>
    </div>
    <div class="flex flex-wrap gap-3 mb-6">
      <button onclick="filterReports('all',this)" class="tab-btn tab-active report-filter-btn">Semua</button>
      ${types.map(t=>`<button onclick="filterReports('${t}',this)" class="tab-btn report-filter-btn">${t}</button>`).join('')}
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="glass-card p-5">
        <h3 class="font-bold text-sm mb-4">📋 Senarai Laporan</h3>
        <div id="reports-list" class="space-y-3 max-h-[500px] overflow-y-auto">
          ${reports.map(r=>{const m=machines.find(x=>x.id===r.machineId);return `
          <div class="report-item flex items-center gap-3 p-3 rounded-xl border border-gray-100 hover:border-gray-300 cursor-pointer transition" data-type="${r.type}" onclick="showReportDetail('${r.id}')">
            <div class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${r.status==='completed'?'bg-green-100 text-green-700':r.status==='pending'?'bg-yellow-100 text-yellow-700':'bg-red-100 text-red-700'}">${r.status==='completed'?'✓':r.status==='pending'?'⏳':'!'}</div>
            <div class="flex-grow">
              <p class="text-sm font-semibold">${r.type}</p>
              <p class="text-xs text-gray-500">${m?m.name:'N/A'} · ${r.date} · ${r.tech}</p>
            </div>
            <span class="badge ${r.status==='completed'?'badge-green':r.status==='pending'?'badge-yellow':'badge-red'}">${r.status}</span>
          </div>`}).join('')}
        </div>
      </div>
      <div class="glass-card p-5">
        <h3 class="font-bold text-sm mb-4">📊 Timeline Laporan</h3>
        <div class="space-y-0">
          ${reports.sort((a,b)=>new Date(b.date)-new Date(a.date)).map(r=>{const m=machines.find(x=>x.id===r.machineId);return `
          <div class="timeline-item ${r.status}">
            <div class="flex justify-between items-start">
              <div><p class="text-sm font-semibold">${r.type}</p><p class="text-xs text-gray-500">${m?m.name:''}</p></div>
              <span class="text-xs text-gray-400">${r.date}</span>
            </div>
            <p class="text-xs text-gray-500 mt-1">Teknisyen: ${r.tech}</p>
          </div>`}).join('')}
        </div>
      </div>
    </div>
  </div>`;
}

function renderTraining() {
  const training = APP_DATA.training;
  const courses = ['OSHA Awareness','HIRARC Workshop','First Aid & CPR','Fire Safety Drill','Ergonomics','Chemical Safety'];
  return `<div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Latihan & Permintaan</h2>
      <button onclick="openAddTraining()" class="bg-safety text-white px-4 py-2 rounded-lg text-sm font-medium">+ Mohon Latihan</button>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
      ${courses.map(c=>`<div class="glass-card p-4 hover:shadow-md transition cursor-pointer" onclick="openAddTraining('${c}')">
        <div class="text-2xl mb-2">${c.includes('Fire')?'🔥':c.includes('First')?'🩹':c.includes('OSHA')?'🛡️':c.includes('HIRARC')?'⚠️':c.includes('Ergo')?'🧘':'☣️'}</div>
        <h4 class="font-semibold text-sm">${c}</h4>
        <p class="text-xs text-gray-500 mt-1">Klik untuk mohon</p>
      </div>`).join('')}
    </div>
    <div class="glass-card overflow-hidden">
      <div class="bg-gray-50 px-5 py-4 border-b font-bold text-sm">📋 Status Permohonan</div>
      <div class="divide-y">
        ${training.map(t=>{
          const steps=['requested','approved','scheduled','completed'];
          const stLabels=['Dimohon','Diluluskan','Dijadualkan','Selesai'];
          const ci=steps.indexOf(t.status);
          return `<div class="p-5">
            <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-3 mb-3">
              <div><h4 class="font-semibold">${t.course}</h4><p class="text-xs text-gray-500">${t.date} · ${t.participants} peserta</p></div>
              <span class="badge ${t.status==='completed'?'badge-green':t.status==='approved'?'badge-blue':'badge-yellow'}">${t.status}</span>
            </div>
            <div class="pipeline rounded-lg overflow-hidden">
              ${stLabels.map((s,i)=>`<div class="pipe-step ${i<ci?'done':i===ci?'active':''}">${s}</div>`).join('')}
            </div>
          </div>`}).join('')}
      </div>
    </div>
  </div>`;
}

function renderSettings() {
  const u = APP_DATA.user;
  const n = APP_DATA.notifications;
  return `<div class="max-w-3xl mx-auto">
    <h2 class="text-2xl font-bold text-gray-800 mb-6">⚙️ Tetapan Akaun</h2>
    <div class="space-y-6">
      <!-- Profile -->
      <div class="glass-card p-6">
        <h3 class="font-bold text-base mb-4">👤 Profil Pengguna</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div><label class="text-xs text-gray-500 block mb-1">Nama Penuh</label><input id="st-name" class="form-input" value="${u.name}"></div>
          <div><label class="text-xs text-gray-500 block mb-1">Jawatan</label><input id="st-pos" class="form-input" value="${u.position}"></div>
          <div><label class="text-xs text-gray-500 block mb-1">Email</label><input id="st-email" class="form-input" value="${u.email}"></div>
          <div><label class="text-xs text-gray-500 block mb-1">No Telefon</label><input id="st-phone" class="form-input" value="${u.phone}"></div>
        </div>
        <button onclick="saveUserSettings()" class="bg-navy text-white px-6 py-2 rounded-lg text-sm font-medium mt-4">💾 Simpan Profil</button>
      </div>
      <!-- Password -->
      <div class="glass-card p-6">
        <h3 class="font-bold text-base mb-4">🔒 Tukar Kata Laluan</h3>
        <div class="space-y-3 max-w-sm">
          <div><label class="text-xs text-gray-500 block mb-1">Kata Laluan Semasa</label><input type="password" class="form-input" placeholder="••••••••"></div>
          <div><label class="text-xs text-gray-500 block mb-1">Kata Laluan Baru</label><input type="password" class="form-input" placeholder="••••••••"></div>
          <div><label class="text-xs text-gray-500 block mb-1">Sahkan Kata Laluan</label><input type="password" class="form-input" placeholder="••••••••"></div>
        </div>
        <button onclick="showToast('Kata laluan berjaya dikemaskini!')" class="bg-gray-800 text-white px-6 py-2 rounded-lg text-sm font-medium mt-4">Tukar Kata Laluan</button>
      </div>
      <!-- Notifications -->
      <div class="glass-card p-6">
        <h3 class="font-bold text-base mb-4">🔔 Keutamaan Notifikasi</h3>
        <div class="space-y-4">
          ${[['cfExpiry','Peringatan Tamat CF','3 bulan sebelum tamat'],['calibration','Peringatan Kalibrasi','Tarikh kalibrasi hampir tiba'],['missingDoc','Dokumen Tidak Lengkap','Dokumen penting belum dimuat naik'],['trainingReminder','Peringatan Latihan','Latihan yang akan datang']].map(([k,t,d])=>`
          <div class="flex items-center justify-between py-2">
            <div><p class="text-sm font-medium">${t}</p><p class="text-xs text-gray-500">${d}</p></div>
            <div class="toggle ${n[k]?'on':''}" onclick="toggleNotifPref('${k}',this)"></div>
          </div>`).join('')}
        </div>
      </div>
      <!-- Account -->
      <div class="glass-card p-6">
        <h3 class="font-bold text-base mb-4">📦 Maklumat Akaun</h3>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div><p class="text-gray-500 text-xs">Pelan</p><p class="font-semibold">${u.plan}</p></div>
          <div><p class="text-gray-500 text-xs">Status</p><p class="font-semibold text-success">Aktif</p></div>
          <div><p class="text-gray-500 text-xs">Organisasi</p><p class="font-semibold">${APP_DATA.company.name}</p></div>
          <div><p class="text-gray-500 text-xs">Ahli Sejak</p><p class="font-semibold">Januari 2024</p></div>
        </div>
      </div>
    </div>
  </div>`;
}
