// ===== VIEW RENDERERS (Part 1: Dashboard, Organisasi, Assets) =====

function renderDashboard() {
  const d = APP_DATA;
  const totalM = d.machines.length;
  const valid = d.machines.filter(m=>m.status==='valid').length;
  const rate = totalM ? Math.round((valid/totalM)*100) : 0;
  const alerts = d.machines.filter(m=>m.status!=='valid').length;
  const pendingReports = d.reports.filter(r => r.status !== 'completed').length;
  const trainingOpen = d.training.filter(t => t.status !== 'completed').length;
  const priorityItems = d.machines.filter(m => m.status !== 'valid').slice(0, 5);

  return `<div class="dashboard-shell max-w-7xl mx-auto space-y-6">
    <section class="dashboard-hero">
      <div class="flex items-start gap-4 flex-1 min-w-0">
        <button onclick="toggleSidebar()" class="md:hidden mt-1 text-white/90 text-2xl leading-none">☰</button>
        <div class="min-w-0">
          <p class="dashboard-kicker">Overview</p>
          <h2 class="text-2xl md:text-3xl font-bold font-display text-white tracking-tight">OSHone Portal</h2>
          <p class="mt-2 text-white/78 text-sm max-w-2xl">Pantau mesin, dokumen, laporan dan latihan dalam satu ruang kerja yang lebih kemas.</p>
          <div class="flex flex-wrap items-center gap-3 mt-4">
            <span class="hero-pill">Aktif</span>
            <span class="hero-pill hero-pill-soft">${rate}% Pematuhan</span>
          </div>
        </div>
      </div>
      <div class="flex flex-wrap gap-3">
        <button onclick="switchView('view-reports',document.querySelectorAll('.nav-item')[5])" class="hero-action-btn">📊 Laporan</button>
        <button onclick="openAddMachine()" class="hero-action-btn hero-action-btn-solid">+ Tambah Mesin</button>
      </div>
    </section>

    <section class="grid grid-cols-2 xl:grid-cols-4 gap-4">
      <div class="summary-tile cursor-pointer" onclick="switchView('view-assets',document.querySelectorAll('.nav-item')[2])">
        <p class="summary-tile-label">Jumlah Mesin</p>
        <p class="summary-tile-value">${totalM}</p>
        <p class="summary-tile-meta">${valid} masih sah</p>
      </div>
      <div class="summary-tile">
        <p class="summary-tile-label">Pematuhan CF</p>
        <p class="summary-tile-value text-indigo-600">${rate}%</p>
        <div class="compliance-meter"><span style="width:${rate}%"></span></div>
      </div>
      <div class="summary-tile">
        <p class="summary-tile-label">Alert Aktif</p>
        <p class="summary-tile-value text-rose-600">${alerts}</p>
        <p class="summary-tile-meta">${alerts===0?'Tiada risiko segera':'Perlu tindakan'}</p>
      </div>
      <div class="summary-tile cursor-pointer" onclick="switchView('view-documents',document.querySelectorAll('.nav-item')[3])">
        <p class="summary-tile-label">Dokumen</p>
        <p class="summary-tile-value">${d.documents.length}</p>
        <p class="summary-tile-meta">${pendingReports} laporan terbuka</p>
      </div>
    </section>

    <section class="grid xl:grid-cols-[minmax(0,1.7fr)_minmax(320px,1fr)] gap-6 items-start">
      <div class="space-y-6">
        <article class="glass-card p-5">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-slate-400 font-semibold">Priority Queue</p>
              <h3 class="text-lg font-bold text-slate-900">Peringatan & Tindakan Segera</h3>
            </div>
            <button onclick="switchView('view-assets',document.querySelectorAll('.nav-item')[2])" class="text-sm font-semibold text-indigo-600 hover:text-indigo-700">Lihat semua</button>
          </div>
          <div class="space-y-3">
            ${priorityItems.length ? priorityItems.map(m => `
              <div class="queue-item ${m.status==='expired'?'border-rose-200 bg-rose-50':'border-amber-200 bg-amber-50'} cursor-pointer" onclick="switchView('view-assets',document.querySelectorAll('.nav-item')[2])">
                <div class="queue-icon ${m.status==='expired'?'bg-rose-100 text-rose-600':'bg-amber-100 text-amber-600'}">${m.status==='expired'?'🔴':'🟡'}</div>
                <div class="queue-copy">
                  <p class="queue-title">${m.name}</p>
                  <p class="queue-subtitle">${m.pmt} · ${m.type} · CF ${m.cfExpiry}</p>
                  <p class="queue-subtitle mt-2 font-medium ${m.status==='expired'?'text-rose-600':'text-amber-600'}">${m.status==='expired'?'Telah Tamat Tempoh':'Akan Tamat Tempoh'}</p>
                </div>
                <span class="badge ${m.status==='expired'?'badge-red':'badge-yellow'} queue-badge">${m.status==='expired'?'Expired':'Expiring'}</span>
              </div>`).join('') : '<div class="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">Tiada alert aktif</div>'}
          </div>
        </article>

        <article class="glass-card p-5">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-slate-400 font-semibold">Activity Feed</p>
              <h3 class="text-lg font-bold text-slate-900">Aktiviti Terkini</h3>
            </div>
            <span class="badge badge-blue">Live</span>
          </div>
          <div class="space-y-3">
            ${d.reports.slice(0,4).map(r => { const m = d.machines.find(x => x.id === r.machineId); return `
              <div class="queue-item">
                <div class="queue-icon ${r.status==='completed'?'bg-emerald-100 text-emerald-600':r.status==='pending'?'bg-amber-100 text-amber-600':'bg-rose-100 text-rose-600'}">${r.status==='completed'?'✓':r.status==='pending'?'⏳':'!'}</div>
                <div class="queue-copy">
                  <p class="queue-title">${r.type}</p>
                  <p class="queue-subtitle">${m ? m.name : 'N/A'} · ${r.date}</p>
                </div>
                <span class="badge ${r.status==='completed'?'badge-green':r.status==='pending'?'badge-yellow':'badge-red'} queue-badge">${r.status}</span>
              </div>`; }).join('')}
          </div>
        </article>
      </div>

      <aside class="space-y-6">
        <div class="snapshot-panel">
          <div class="flex items-center justify-between mb-4 gap-3">
            <div>
              <p class="text-xs uppercase tracking-[0.24em] text-slate-400 font-semibold">Project Information</p>
              <h3 class="text-lg font-bold text-slate-900">Compliance Snapshot</h3>
            </div>
            <div class="badge badge-blue">OSH</div>
          </div>
          <div class="rounded-3xl bg-white border border-indigo-100 p-4 shadow-sm">
            <div class="flex items-center justify-between text-sm gap-3">
              <span class="text-slate-500">Organisasi</span>
              <span class="font-semibold text-slate-900 text-right">${d.company.name}</span>
            </div>
            <div class="flex items-center justify-between text-sm mt-2 gap-3">
              <span class="text-slate-500">Pematuhan</span>
              <span class="font-semibold text-indigo-600">${rate}%</span>
            </div>
            <div class="compliance-meter mt-4"><span style="width:${rate}%"></span></div>
            <div class="grid grid-cols-2 gap-3 mt-4">
              <div class="mini-metric">
                <p class="mini-metric-label">Latihan</p>
                <p class="mini-metric-value">${trainingOpen}</p>
                <p class="text-xs text-slate-500 mt-1">Permohonan terbuka</p>
              </div>
              <div class="mini-metric">
                <p class="mini-metric-label">Laporan</p>
                <p class="mini-metric-value">${pendingReports}</p>
                <p class="text-xs text-slate-500 mt-1">Perlu semakan</p>
              </div>
            </div>
          </div>
        </div>

        <div class="glass-card p-5">
          <div class="flex items-center justify-between mb-4 gap-3">
            <h3 class="text-lg font-bold text-slate-900">Tindakan Pantas</h3>
            <span class="badge badge-yellow">4</span>
          </div>
          <div class="space-y-3">
            <button onclick="openAddMachine()" class="w-full rounded-2xl border border-indigo-100 bg-gradient-to-r from-indigo-50 to-sky-50 px-4 py-3 text-left text-sm font-semibold text-indigo-700 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200">+ Tambah Mesin</button>
            <button onclick="openAddDoc()" class="w-full rounded-2xl border border-sky-100 bg-gradient-to-r from-sky-50 to-white px-4 py-3 text-left text-sm font-semibold text-sky-700 shadow-sm transition hover:-translate-y-0.5 hover:border-sky-200">+ Muat Naik Dokumen</button>
            <button onclick="openAddTraining()" class="w-full rounded-2xl border border-amber-100 bg-gradient-to-r from-amber-50 to-white px-4 py-3 text-left text-sm font-semibold text-amber-700 shadow-sm transition hover:-translate-y-0.5 hover:border-amber-200">+ Mohon Latihan</button>
            <button onclick="switchView('view-mykkp',document.querySelectorAll('.nav-item')[4])" class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-semibold text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-indigo-50">Buka MyKKP</button>
          </div>
        </div>
      </aside>
    </section>
  </div>`;
}

function renderOrganisasi() {
  const c = APP_DATA.company;
  const certs = APP_DATA.certificates;
  return `<div class="relative w-full font-display">
    <div class="header-slant"></div>
    <div class="max-w-6xl mx-auto relative z-10 pt-2 md:pt-6">
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center">
        <div class="flex items-center mb-4 md:mb-0">
          <div class="w-20 h-20 md:w-28 md:h-28 rounded-full profile-ring flex items-center justify-center bg-white"><span class="text-2xl md:text-3xl font-bold text-navy">${c.logo||'TM'}</span></div>
          <div class="bg-white rounded-r-full pl-6 pr-4 py-2 ml-[-20px] flex items-center shadow-md z-0"><span class="text-blue-700 font-semibold text-xs md:text-sm mr-3">Welcome to OSHONE</span><div class="w-7 h-7 bg-black rounded-full flex items-center justify-center text-white text-xs">👷</div></div>
        </div>
        <div class="flex flex-wrap gap-2">
          <button onclick="toggleEditProfile()" id="btn-edit-profile" class="bg-white px-4 py-2 rounded-full text-blue-800 text-xs font-semibold shadow hover:bg-gray-50">✏️ Update Profile</button>
          <a href="https://mykkp.dosh.gov.my" target="_blank" class="bg-white px-4 py-2 rounded-full text-blue-800 text-xs font-semibold shadow hover:bg-gray-50">MyKKP ↗</a>
        </div>
      </div>
      <div class="flex items-center gap-3 mt-6 pl-2">
        <div class="h-10 bg-white rounded shadow px-3 flex items-center justify-center font-bold text-blue-800 text-xs">JKKP</div>
        <div class="h-10 bg-white rounded shadow px-3 flex items-center justify-center font-bold text-blue-800 text-xs">NIOSH</div>
        <div class="h-10 bg-white rounded shadow px-3 flex items-center justify-center font-bold text-blue-800 text-xs">CIDB</div>
      </div>
      <h1 class="text-2xl md:text-3xl font-bold mt-8 mb-6 text-gray-900">Maklumat Organisasi</h1>
      <div class="flex overflow-x-auto gap-2 mb-6 border-b border-gray-300 pb-2 hide-scrollbar">
        <button onclick="switchOrgTab('otab-org',this)" class="tab-btn tab-active">Organisasi</button>
        <button onclick="switchOrgTab('otab-policy',this)" class="tab-btn">Safety Policy</button>
        <button onclick="switchOrgTab('otab-committee',this)" class="tab-btn">Safety Committee</button>
        <button onclick="switchOrgTab('otab-person',this)" class="tab-btn">Competent Person</button>
        <button onclick="switchOrgTab('otab-layout',this)" class="tab-btn">Layout</button>
      </div>
      <!-- TAB: Organisasi -->
      <div id="otab-org" class="org-tab bg-white p-5 md:p-8 rounded-xl shadow-sm border border-gray-200">
        <div id="profile-actions" class="hidden flex gap-2 mb-4 justify-end">
          <button onclick="saveProfile()" class="bg-success text-white px-4 py-2 rounded-lg text-sm font-medium">💾 Simpan</button>
          <button onclick="cancelEditProfile()" class="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium">Batal</button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div class="md:col-span-3 flex flex-col gap-2">
            <h3 class="text-xs font-semibold text-gray-600 mb-1">Sijil Syarikat</h3>
            <button class="bg-[#113C4A] text-white py-2 rounded font-medium hover:bg-opacity-90 shadow text-sm">SSM</button>
            <button class="bg-[#113C4A] text-white py-2 rounded font-medium hover:bg-opacity-90 shadow text-sm">SLK</button>
            <button class="bg-[#113C4A] text-white py-2 rounded font-medium hover:bg-opacity-90 shadow text-sm">CIDB</button>
          </div>
          <div class="md:col-span-4 flex flex-col items-center">
            <h3 class="text-xs font-semibold text-gray-600 text-center mb-2">Logo</h3>
            <div class="w-full h-40 border border-gray-200 rounded-xl flex items-center justify-center bg-gray-50 shadow-inner p-4">
              <div class="text-3xl font-black text-blue-600 flex items-center"><div class="w-10 h-10 bg-blue-500 mr-2 rounded text-white flex items-center justify-center text-2xl italic">T</div> TIJARAH</div>
            </div>
          </div>
          <div class="md:col-span-5 flex flex-col justify-center gap-4">
            <div><label class="text-xs font-medium text-gray-500">Nama Organisasi:</label><input id="pf-name" type="text" value="${c.name}" class="input-line profile-field text-gray-800 font-medium" readonly></div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div><label class="text-xs font-medium text-gray-500">Alamat:</label><input id="pf-addr" type="text" value="${c.address}" class="input-line profile-field text-gray-800" readonly></div>
              <div><label class="text-xs font-medium text-gray-500">No Pejabat:</label><input id="pf-phone" type="text" value="${c.phone}" class="input-line profile-field text-gray-800" readonly></div>
              <div><label class="text-xs font-medium text-gray-500">Email:</label><input id="pf-email" type="text" value="${c.email}" class="input-line profile-field text-gray-800" readonly></div>
              <div><label class="text-xs font-medium text-gray-500">Laman Web:</label><input id="pf-web" type="text" value="${c.website}" class="input-line profile-field text-gray-800" readonly></div>
            </div>
          </div>
        </div>
      </div>
      <!-- TAB: Safety Policy -->
      <div id="otab-policy" class="org-tab hidden bg-white p-8 rounded-xl shadow-sm border border-gray-200 min-h-[300px] flex flex-col items-center justify-center">
        <div class="text-4xl mb-3">📜</div>
        <p class="text-gray-500 text-sm mb-4">Polisi Keselamatan & Kesihatan Pekerjaan</p>
        <button onclick="openModal('Muat Naik Safety Policy','<p class=\\'text-center text-gray-500 py-8\\'>Seret fail PDF ke sini atau<br><br><button class=\\'bg-navy text-white px-6 py-2 rounded-lg text-sm\\'>Pilih Fail</button></p>')" class="bg-navy text-white px-6 py-2 rounded-lg text-sm font-medium">Muat Naik</button>
      </div>
      <!-- TAB: Safety Committee -->
      <div id="otab-committee" class="org-tab hidden bg-white p-6 rounded-xl shadow-sm border border-gray-200 overflow-x-auto">
        <h2 class="text-center font-bold text-lg mb-6">Safety Committee Members</h2>
        <div class="flex flex-col items-center min-w-[500px] pb-4">
          <div class="w-40 bg-[#9CB2A9] rounded-t-lg p-3 flex flex-col items-center shadow border-b-4 border-gray-300"><div class="w-20 h-20 bg-white rounded-full mb-3 shadow-inner flex items-center justify-center text-2xl">👨‍💼</div><div class="bg-white w-[115%] text-center py-1.5 font-medium text-sm shadow-md rounded border">Chairman</div></div>
          <div class="org-line-vertical"></div>
          <div class="flex w-full justify-center relative left-16 mb-4"><div class="w-24 border-t-2 border-[#ccc] absolute left-[-30px] top-[50%]"></div><div class="w-36 bg-[#E6DACB] rounded-t-lg p-3 flex flex-col items-center shadow border-b-4 border-gray-300 relative z-10"><div class="w-16 h-16 bg-white rounded-full mb-2 shadow-inner flex items-center justify-center text-xl">👩‍💼</div><div class="bg-white w-[115%] text-center py-1.5 font-medium text-xs shadow-md rounded border">Secretary</div></div></div>
          <div class="org-line-vertical h-6"></div>
          <div class="org-line-horizontal w-full max-w-2xl"></div>
          <div class="flex justify-center gap-4 mt-4 flex-wrap max-w-2xl">
            ${['Member 1','Member 2','Member 3'].map(n=>`<div class="w-32 bg-[#DCE4EC] rounded-t-lg p-3 flex flex-col items-center shadow border-b-4 border-gray-300 relative"><div class="absolute w-1 h-4 bg-[#ccc] top-[-16px]"></div><div class="w-14 h-14 bg-white rounded-full mb-2 shadow-inner flex items-center justify-center">👷</div><div class="bg-white w-[115%] text-center py-1.5 font-medium text-xs shadow-md rounded border">${n}</div></div>`).join('')}
          </div>
        </div>
      </div>
      <!-- TAB: Competent Person + Certificate Buttons -->
      <div id="otab-person" class="org-tab hidden">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          ${certs.map(ct=>`<div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition">
            <div class="h-36 bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center border-b"><span class="text-5xl">🏅</span></div>
            <div class="p-4 flex justify-between items-center">
              <div><h4 class="font-medium text-sm">${ct.title}</h4><p class="text-xs text-gray-500 mt-1">${ct.holder}</p></div>
              <button onclick="showCertificate('${ct.id}')" class="bg-[#113C4A] text-white text-xs px-4 py-2 rounded font-semibold hover:bg-opacity-90">📜 Sijil</button>
            </div>
          </div>`).join('')}
        </div>
      </div>
      <!-- TAB: Layout -->
      <div id="otab-layout" class="org-tab hidden bg-white p-8 rounded-xl shadow-sm border border-gray-200 min-h-[300px] flex flex-col items-center justify-center">
        <div class="text-4xl mb-3">🗺️</div>
        <p class="text-gray-500 text-sm mb-4">Pelan Susun Atur Premis</p>
        <button class="bg-navy text-white px-6 py-2 rounded-lg text-sm font-medium">Muat Naik Pelan</button>
      </div>
    </div>
  </div>`;
}

function renderAssets() {
  const machines = APP_DATA.machines;
  return `<div class="max-w-6xl mx-auto">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold text-gray-800">Senarai Mesin & Aset</h2>
      <button onclick="openAddMachine()" class="bg-navy text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-900">+ Tambah Mesin</button>
    </div>
    <div class="flex flex-col md:flex-row gap-4 bg-white p-4 rounded-xl shadow-sm border border-gray-100 mb-6">
      <input id="search-machine" type="text" oninput="filterMachines()" class="flex-grow border border-gray-300 rounded-lg px-4 py-2 text-sm" placeholder="🔍 Cari mesin / PMT...">
      <select id="filter-status" onchange="filterMachines()" class="border border-gray-300 rounded-lg px-4 py-2 text-sm">
        <option value="all">Semua Status</option><option value="valid">Sah (Valid)</option><option value="expired">Tamat Tempoh</option><option value="expiring">Akan Tamat</option>
      </select>
    </div>
    <div id="machines-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      ${machines.map(m=>machineCard(m)).join('')}
    </div>
  </div>`;
}

function machineCard(m) {
  const colors = {valid:'green',expired:'red',expiring:'orange'};
  const labels = {valid:'🟢 Sah',expired:'🔴 Tamat Tempoh',expiring:'🟡 Akan Tamat'};
  const c = colors[m.status]||'gray';
  return `<div class="machine-card bg-white rounded-2xl overflow-hidden hover:shadow-lg transition border border-gray-100 flex flex-col" data-name="${m.name.toLowerCase()}" data-pmt="${m.pmt.toLowerCase()}" data-status="${m.status}">
    <div class="p-5 border-b border-gray-100 flex-grow">
      <div class="flex justify-between items-start mb-3"><span class="badge badge-${c}">${labels[m.status]}</span><span class="text-xs text-gray-400">${m.type}</span></div>
      <h3 class="text-lg font-bold text-gray-900 mb-1">${m.name}</h3>
      <div class="space-y-1.5 mt-3 text-sm">
        <div class="flex"><span class="text-gray-500 w-24">No PMT:</span><span class="font-medium">${m.pmt}</span></div>
        <div class="flex"><span class="text-gray-500 w-24">Serial:</span><span class="font-medium">${m.serial}</span></div>
        <div class="flex"><span class="text-gray-500 w-24">Lokasi:</span><span class="font-medium">${m.location}</span></div>
        <div class="flex"><span class="text-gray-500 w-24">Tamat CF:</span><span class="font-medium text-${c}-600">${m.cfExpiry}</span></div>
      </div>
    </div>
    <div class="bg-gray-50 px-5 py-3 flex justify-between">
      <button onclick="showMachineDetail('${m.id}')" class="text-sm font-medium text-navy hover:text-safety">Lihat Detail →</button>
      <button onclick="openEditMachine('${m.id}')" class="text-sm font-medium text-gray-400 hover:text-navy">✏️</button>
    </div>
  </div>`;
}
