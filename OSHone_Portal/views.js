// ===== VIEW RENDERERS (Part 1: Dashboard, Organisasi, Assets) =====

function renderDashboard() {
  const d = APP_DATA;
  const totalM = d.machines.length;
  const valid = d.machines.filter(m=>m.status==='valid').length;
  const rate = Math.round((valid/totalM)*100);
  const alerts = d.machines.filter(m=>m.status!=='valid').length;
  return `<div class="max-w-6xl mx-auto">
    <h2 class="text-2xl font-bold font-display text-gray-800 mb-6">Ringkasan Sistem</h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      <div class="glass-card stat-card p-5 border-l-4 border-l-navy cursor-pointer" onclick="switchView('view-assets',document.querySelectorAll('.nav-item')[2])">
        <p class="text-xs text-gray-500 font-medium">Jumlah Mesin</p>
        <p class="text-3xl font-bold text-gray-800 mt-2">${totalM}</p>
      </div>
      <div class="glass-card stat-card p-5 border-l-4 border-l-success">
        <p class="text-xs text-gray-500 font-medium">Pematuhan CF</p>
        <p class="text-3xl font-bold text-success mt-2">${rate}%</p>
        <div class="w-full bg-gray-100 rounded-full h-2 mt-3"><div class="bg-success h-2 rounded-full" style="width:${rate}%"></div></div>
      </div>
      <div class="glass-card stat-card p-5 border-l-4 border-l-danger">
        <p class="text-xs text-gray-500 font-medium">Alert</p>
        <p class="text-3xl font-bold text-danger mt-2">${alerts}</p>
      </div>
      <div class="glass-card stat-card p-5 border-l-4 border-l-warning cursor-pointer" onclick="switchView('view-documents',document.querySelectorAll('.nav-item')[3])">
        <p class="text-xs text-gray-500 font-medium">Dokumen</p>
        <p class="text-3xl font-bold text-gray-800 mt-2">${d.documents.length}</p>
      </div>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div class="glass-card overflow-hidden">
        <div class="bg-gray-50 px-5 py-4 border-b font-bold text-sm flex items-center">🔔 Peringatan</div>
        <div class="p-4 space-y-3">
          ${d.machines.filter(m=>m.status!=='valid').map(m=>`
          <div class="flex items-start p-3 rounded-xl border ${m.status==='expired'?'border-red-100 bg-red-50':'border-orange-100 bg-orange-50'} cursor-pointer" onclick="switchView('view-assets',document.querySelectorAll('.nav-item')[2])">
            <div class="text-lg mr-3">${m.status==='expired'?'🔴':'🟡'}</div>
            <div><h4 class="font-semibold text-sm">${m.name} <span class="text-xs text-gray-500 ml-1">(${m.pmt})</span></h4>
            <p class="text-xs mt-1 font-medium ${m.status==='expired'?'text-danger':'text-warning'}">${m.status==='expired'?'Telah Tamat Tempoh!':'Akan Tamat Tempoh'} (${m.cfExpiry})</p></div>
          </div>`).join('')}
          ${alerts===0?'<p class="text-center text-gray-400 text-sm py-4">Tiada peringatan</p>':''}
        </div>
      </div>
      <div class="glass-card overflow-hidden">
        <div class="bg-gray-50 px-5 py-4 border-b font-bold text-sm">📊 Aktiviti Terkini</div>
        <div class="p-4 space-y-3">
          ${d.reports.slice(0,4).map(r=>{const m=d.machines.find(x=>x.id===r.machineId);return `
          <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50">
            <div class="w-8 h-8 rounded-full ${r.status==='completed'?'bg-green-100 text-green-600':r.status==='pending'?'bg-yellow-100 text-yellow-600':'bg-red-100 text-red-600'} flex items-center justify-center text-xs font-bold">${r.status==='completed'?'✓':r.status==='pending'?'⏳':'!'}</div>
            <div class="flex-grow"><p class="text-sm font-medium">${r.type}</p><p class="text-xs text-gray-500">${m?m.name:''} · ${r.date}</p></div>
            <span class="badge ${r.status==='completed'?'badge-green':r.status==='pending'?'badge-yellow':'badge-red'}">${r.status}</span>
          </div>`}).join('')}
        </div>
      </div>
    </div>
    <div class="glass-card p-5">
      <h3 class="font-bold text-sm mb-4">⚡ Tindakan Pantas</h3>
      <div class="flex flex-wrap gap-3">
        <button onclick="openAddMachine()" class="bg-navy text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-900 transition">+ Tambah Mesin</button>
        <button onclick="openAddDoc()" class="bg-brandGreen text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition">+ Muat Naik Dokumen</button>
        <button onclick="openAddTraining()" class="bg-safety text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-orange-600 transition">+ Mohon Latihan</button>
      </div>
    </div>
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
