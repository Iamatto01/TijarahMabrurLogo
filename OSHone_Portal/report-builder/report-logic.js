// ===== REPORT BUILDER LOGIC =====
// Connected to CMS data via cms-data.js

let uploadedImages = [];

// ===== AUTO REPORT NUMBER SYSTEM =====
const REPORT_STORAGE_KEY = 'oshone_submitted_reports';

function getSubmittedReports() {
  try {
    return JSON.parse(localStorage.getItem(REPORT_STORAGE_KEY) || '[]');
  } catch { return []; }
}

function saveSubmittedReports(reports) {
  localStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(reports));
}

function generateNextReportNo() {
  const year = new Date().getFullYear();
  const reports = getSubmittedReports();

  // Extract all numbers from this year's reports
  const yearReports = reports
    .map(r => r.reportNo)
    .filter(no => no && no.includes(`MIT-${year}-`))
    .map(no => parseInt(no.split('-')[2], 10))
    .filter(n => !isNaN(n));

  // Find next available number (fills gaps from deleted reports)
  let nextNum = 1;
  if (yearReports.length > 0) {
    yearReports.sort((a, b) => a - b);
    // Check for gaps
    for (let i = 1; i <= yearReports[yearReports.length - 1] + 1; i++) {
      if (!yearReports.includes(i)) {
        nextNum = i;
        break;
      }
    }
    // If no gaps found, use max + 1
    if (yearReports.includes(nextNum)) {
      nextNum = yearReports[yearReports.length - 1] + 1;
    }
  }

  return `MIT-${year}-${nextNum}`;
}

function registerReport(reportNo) {
  const reports = getSubmittedReports();
  if (!reports.find(r => r.reportNo === reportNo)) {
    reports.push({
      reportNo,
      submittedAt: new Date().toISOString()
    });
    saveSubmittedReports(reports);
  }
}

function deleteReport(reportNo) {
  let reports = getSubmittedReports();
  reports = reports.filter(r => r.reportNo !== reportNo);
  saveSubmittedReports(reports);
  // Refresh the report number field
  document.getElementById('f-reportNo').value = generateNextReportNo();
  showToast(`🗑️ Report ${reportNo} deleted. Number available for reuse.`);
}

function renderSubmittedReports() {
  const container = document.getElementById('submitted-list');
  if (!container) return;
  const reports = getSubmittedReports();
  if (reports.length === 0) {
    container.innerHTML = '<p class="text-gray-400 text-xs">Belum ada laporan dihantar.</p>';
    return;
  }
  container.innerHTML = reports.map(r => `
    <div class="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 text-sm">
      <div>
        <span class="font-semibold text-navy">${r.reportNo}</span>
        <span class="text-gray-400 text-xs ml-2">${new Date(r.submittedAt).toLocaleDateString('ms-MY')}</span>
      </div>
      <button onclick="deleteReport('${r.reportNo}')" class="text-red-400 hover:text-red-600 text-xs font-medium">🗑️ Delete</button>
    </div>`).join('');
}

// ----- POPULATE CLIENT DROPDOWN (reusable for live refresh) -----
function populateClientDropdown() {
  const clientSelect = document.getElementById('f-client');
  const currentVal = clientSelect.value; // preserve selection
  clientSelect.innerHTML = '<option value="">-- Pilih Syarikat --</option>';

  const clients = getClients();
  clients.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name;
    opt.textContent = c.name;
    clientSelect.appendChild(opt);
  });

  // Add "Tambah Baru" option
  const newOpt = document.createElement('option');
  newOpt.value = '__NEW__';
  newOpt.textContent = '➕ Tambah Client Baru...';
  clientSelect.appendChild(newOpt);

  // Restore previous selection if still exists
  if (currentVal && [...clientSelect.options].some(o => o.value === currentVal)) {
    clientSelect.value = currentVal;
  }

  // Update source badge
  const badge = document.getElementById('data-source-badge');
  if (badge) {
    const src = getCMSSource();
    const labels = { wix: '🟢 Live Wix', csv: '📁 CSV', fallback: '⚠️ Fallback', none: '⏳ Loading...' };
    badge.textContent = labels[src] || src;
    badge.className = 'text-xs font-semibold px-2 py-0.5 rounded-full ' +
      (src === 'wix' ? 'bg-green-100 text-green-700' :
       src === 'csv' ? 'bg-blue-100 text-blue-700' :
       'bg-yellow-100 text-yellow-700');
  }
}

// ----- INIT: Load CMS data & populate dropdowns -----
document.addEventListener('DOMContentLoaded', async () => {
  // Set today's date as default
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('f-reportDate').value = today;
  document.getElementById('f-serviceDate').value = today;

  // Auto-generate report number
  document.getElementById('f-reportNo').value = generateNextReportNo();
  renderSubmittedReports();

  // Register refresh callback — when Wix sends live data, refresh dropdowns
  onCMSDataRefresh = () => {
    console.log('🔄 Refreshing dropdowns with new CMS data...');
    populateClientDropdown();
    // If a client is selected, refresh machine dropdown too
    const currentClient = document.getElementById('f-client').value;
    if (currentClient && currentClient !== '__NEW__') {
      onClientSelect();
    }
  };

  // Load CMS data (CSV fallback — will be overridden if Wix sends postMessage)
  await loadCMSData('../CMS');

  // Populate client dropdown
  populateClientDropdown();

  // Hide loading bar
  document.getElementById('loading-bar').style.display = 'none';
});

// ----- CLIENT DROPDOWN HANDLER -----
function onClientSelect() {
  const clientName = document.getElementById('f-client').value;

  if (clientName === '__NEW__') {
    const newName = prompt('Masukkan nama syarikat baru:');
    if (newName) {
      const opt = document.createElement('option');
      opt.value = newName;
      opt.textContent = newName;
      const select = document.getElementById('f-client');
      select.insertBefore(opt, select.querySelector('[value="__NEW__"]'));
      select.value = newName;
      document.getElementById('f-address').value = '';
      document.getElementById('f-address').readOnly = false;
      document.getElementById('f-clientEmail').value = '';
      document.getElementById('f-clientEmail').readOnly = false;
      document.getElementById('f-clientImage').value = '';
      updateClientImagePreview('');
    } else {
      document.getElementById('f-client').value = '';
    }
    updateMachineDropdown('');
    return;
  }

  // Auto-fill client details
  const client = getClientByName(clientName);
  if (client) {
    document.getElementById('f-address').value = client.address || '';
    document.getElementById('f-clientEmail').value = client.email || '';
    document.getElementById('f-clientImage').value = client.image || '';
    updateClientImagePreview(client.image || '');
  } else {
    document.getElementById('f-address').value = '';
    document.getElementById('f-clientEmail').value = '';
    document.getElementById('f-clientImage').value = '';
    updateClientImagePreview('');
  }

  // Update machine dropdown for this client
  updateMachineDropdown(clientName);
}

function onClientImageInput() {
  const val = document.getElementById('f-clientImage').value.trim();
  updateClientImagePreview(val);
}

function updateClientImagePreview(src) {
  const img = document.getElementById('f-clientImagePreview');
  const empty = document.getElementById('f-clientImageEmpty');
  if (!img || !empty) return;

  if (!src) {
    img.classList.add('hidden');
    img.removeAttribute('src');
    empty.classList.remove('hidden');
    return;
  }

  img.src = src;
  img.classList.remove('hidden');
  empty.classList.add('hidden');
}

// ----- MACHINE DROPDOWN -----
function updateMachineDropdown(clientName) {
  const machineSelect = document.getElementById('f-machine');
  machineSelect.innerHTML = '<option value="">-- Pilih Mesin --</option>';

  if (!clientName || clientName === '__NEW__') {
    machineSelect.innerHTML = '<option value="">-- Pilih syarikat dahulu --</option>';
    clearMachineFields();
    return;
  }

  const machines = getMachinesByClient(clientName);

  if (machines.length === 0) {
    machineSelect.innerHTML = '<option value="">Tiada mesin untuk client ini</option>';
  }

  machines.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m.serialNo;
    opt.textContent = `${m.name} (${m.serialNo})`;
    machineSelect.appendChild(opt);
  });

  // Add "Tambah Baru" option
  const newOpt = document.createElement('option');
  newOpt.value = '__NEW_MACHINE__';
  newOpt.textContent = '➕ Tambah Mesin Baru...';
  machineSelect.appendChild(newOpt);

  clearMachineFields();
}

function clearMachineFields() {
  ['f-machineName', 'f-serialNo', 'f-location', 'f-nextCF'].forEach(id => {
    const el = document.getElementById(id);
    el.value = '';
    el.readOnly = true;
  });
}

// ----- MACHINE DROPDOWN HANDLER -----
function onMachineSelect() {
  const serialNo = document.getElementById('f-machine').value;

  if (serialNo === '__NEW_MACHINE__') {
    // Unlock fields for manual entry
    ['f-machineName', 'f-serialNo', 'f-location', 'f-nextCF'].forEach(id => {
      const el = document.getElementById(id);
      el.value = '';
      el.readOnly = false;
      el.placeholder = 'Masukkan secara manual';
    });
    return;
  }

  const machine = getMachineBySerial(serialNo);
  if (machine) {
    document.getElementById('f-machineName').value = machine.name;
    document.getElementById('f-serialNo').value = machine.serialNo;
    document.getElementById('f-location').value = machine.location || '';
    document.getElementById('f-nextCF').value = machine.nextCFDate || '';
    // Auto-set CF Expiry
    document.getElementById('f-cfExpiry').value = machine.nextCFDate || 'N/A';
  } else {
    clearMachineFields();
  }
}

// ----- COMMENTS -----
function addComment() {
  const container = document.getElementById('comments-container');
  const count = container.querySelectorAll('.comment-row').length + 1;
  const row = document.createElement('div');
  row.className = 'comment-row flex gap-3 items-start';
  row.innerHTML = `
    <span class="comment-num">${count}</span>
    <textarea class="comment-input" rows="2" placeholder="Enter comment or recommendation..."></textarea>
    <button onclick="removeComment(this)" class="text-red-400 hover:text-red-600 text-lg mt-1">✕</button>`;
  container.appendChild(row);
}

function removeComment(btn) {
  btn.closest('.comment-row').remove();
  renumberComments();
}

function renumberComments() {
  document.querySelectorAll('#comments-container .comment-num').forEach((el, i) => {
    el.textContent = i + 1;
  });
}

// ----- IMAGES -----
function handleImages(files) {
  Array.from(files).forEach(file => {
    const reader = new FileReader();
    reader.onloadend = () => {
      uploadedImages.push({ base64: reader.result, caption: file.name });
      renderImages();
    };
    reader.readAsDataURL(file);
  });
}

function renderImages() {
  const grid = document.getElementById('image-grid');
  grid.innerHTML = uploadedImages.map((img, i) => `
    <div class="image-thumb">
      <img src="${img.base64}" alt="${img.caption}">
      <div class="img-caption">
        <input type="text" value="${img.caption}" onchange="uploadedImages[${i}].caption=this.value" placeholder="Caption...">
      </div>
      <button class="img-remove" onclick="removeImage(${i})">✕</button>
    </div>`).join('');
}

function removeImage(idx) {
  uploadedImages.splice(idx, 1);
  renderImages();
}

// ----- COLLECT ALL DATA -----
function collectFormData() {
  const client = {
    name:       document.getElementById('f-client').value,
    address:    document.getElementById('f-address').value,
    email:      document.getElementById('f-clientEmail').value,
    image:      document.getElementById('f-clientImage').value,
    reportDate: document.getElementById('f-reportDate').value,
    reportNo:   document.getElementById('f-reportNo').value,
    serviceDate:document.getElementById('f-serviceDate').value,
    serviceBy:  document.getElementById('f-serviceBy').value,
    cfExpiry:   document.getElementById('f-cfExpiry').value,
    clientPIC:  document.getElementById('f-clientPIC').value,
  };

  const machine = {
    pmtNo:       document.getElementById('f-pmtNo').value,
    machineName: document.getElementById('f-machineName').value,
    manufacturer:document.getElementById('f-manufacturer').value,
    vesselType:  document.getElementById('f-vesselType').value,
    svSize:      document.getElementById('f-svSize').value,
    volume:      document.getElementById('f-volume').value,
    serialNo:    document.getElementById('f-serialNo').value,
    yearBuilt:   document.getElementById('f-yearBuilt').value,
    mawp:        document.getElementById('f-mawp').value,
    location:    document.getElementById('f-location').value,
    nextCFDate:  document.getElementById('f-nextCF').value,
  };

  const scope = [];
  document.querySelectorAll('#scope-table tbody tr').forEach(row => {
    const idx = row.querySelector('.scope-check').dataset.idx;
    scope.push({
      item: parseInt(idx),
      description: row.querySelectorAll('td')[1].textContent.trim(),
      checked: row.querySelector('.scope-check').checked,
      remark: row.querySelector('.remark-input').value,
    });
  });

  const comments = [];
  document.querySelectorAll('#comments-container .comment-input').forEach(ta => {
    if (ta.value.trim()) comments.push(ta.value.trim());
  });

  const summary = document.getElementById('f-summary').value;
  const images = uploadedImages.map(img => ({ caption: img.caption, base64: img.base64 }));

  const signoff = {
    inspector1: {
      name:   document.getElementById('f-sign1Name').value,
      title:  document.getElementById('f-sign1Title').value,
      mobile: document.getElementById('f-sign1Mobile').value,
      email:  document.getElementById('f-sign1Email').value,
    },
    inspector2: {
      name:   document.getElementById('f-sign2Name').value,
      title:  document.getElementById('f-sign2Title').value,
      mobile: document.getElementById('f-sign2Mobile').value,
      email:  document.getElementById('f-sign2Email').value,
    },
  };

  return {
    tag: 'PMT_SERVICE_REPORT',
    wixCollection: 'sv-report-2',
    client,
    machine,
    scope,
    comments,
    summary,
    images,
    signoff,
    submittedAt: new Date().toISOString(),
  };
}

// ----- CSV EXPORT -----
function exportCSV() {
  const data = collectFormData();
  let rows = [['Field', 'Value']];

  Object.entries(data.client).forEach(([k, v]) => rows.push([`Client.${k}`, v]));
  Object.entries(data.machine).forEach(([k, v]) => rows.push([`Machine.${k}`, v]));
  data.scope.forEach(s => {
    rows.push([`Scope.Item${s.item}.Checked`, s.checked ? 'YES' : 'NO']);
    rows.push([`Scope.Item${s.item}.Remark`, s.remark]);
  });
  data.comments.forEach((c, i) => rows.push([`Comment.${i + 1}`, c]));
  rows.push(['Summary', data.summary]);
  rows.push(['ImagesCount', data.images.length.toString()]);
  Object.entries(data.signoff.inspector1).forEach(([k, v]) => rows.push([`Signoff.Inspector1.${k}`, v]));
  Object.entries(data.signoff.inspector2).forEach(([k, v]) => rows.push([`Signoff.Inspector2.${k}`, v]));

  const csvContent = rows.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${data.client.reportNo || 'report'}_service_report.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  showToast('📥 CSV exported!');
}

// ----- SUBMIT TO WIX -----
function submitToWix() {
  const data = collectFormData();

  // Validation
  if (!data.client.name) { showToast('⚠️ Sila pilih client dahulu!'); return; }
  if (!data.machine.serialNo) { showToast('⚠️ Sila pilih mesin dahulu!'); return; }

  // Register report number
  registerReport(data.client.reportNo);

  if (window.parent !== window) {
    // Inside Wix iframe
    window.parent.postMessage({
      type: 'REPORT_SUBMISSION',
      tag: data.tag,
      collection: data.wixCollection,
      payload: data
    }, '*');
    showToast('✅ Report submitted to Wix CMS!');
  } else {
    // Standalone - log
    console.log('📋 Report Payload:', JSON.stringify(data, null, 2));
    showToast('⚡ Test mode — data logged to console (F12). Embed in Wix to submit.');
  }

  // Generate next report number for the next report
  document.getElementById('f-reportNo').value = generateNextReportNo();
  renderSubmittedReports();
}

// ----- TOAST -----
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 3000);
}
