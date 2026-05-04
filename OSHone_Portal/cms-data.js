// ===== CMS DATA LOADER (DYNAMIC) =====
// Priority: 1) Live Wix postMessage  2) CSV files  3) Hardcoded fallback
// When embedded in Wix, data auto-updates from CMS.
// When running standalone, reads from CSV exports.

const CMS_DATA = {
  clients: [],
  machines: [],
  loaded: false,
  source: 'none' // 'wix', 'csv', or 'fallback'
};

// Callback for when data is refreshed (set by report-logic.js)
let onCMSDataRefresh = null;

function resolveImageValue(value) {
  if (!value) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'object') {
    return value.src || value.url || value.fileUrl || '';
  }
  return '';
}

// ---- CSV PARSER (lightweight, handles quoted fields) ----
function parseCSV(text) {
  const lines = text.split('\n').filter(l => l.trim());
  if (lines.length < 2) return [];
  
  function parseLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        if (inQuotes && line[i + 1] === '"') { current += '"'; i++; }
        else { inQuotes = !inQuotes; }
      } else if (ch === ',' && !inQuotes) {
        result.push(current.trim());
        current = '';
      } else {
        current += ch;
      }
    }
    result.push(current.trim());
    return result;
  }

  const headers = parseLine(lines[0]);
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const vals = parseLine(lines[i]);
    if (vals.length < 2) continue;
    const obj = {};
    headers.forEach((h, idx) => { obj[h] = vals[idx] || ''; });
    rows.push(obj);
  }
  return rows;
}

// ========================================
// 1) LIVE WIX DATA (via postMessage)
// ========================================
// Wix Velo page code sends CMS data to iframe on load.
// This listener catches it and replaces CSV/fallback data.

window.addEventListener('message', (event) => {
  const msg = event.data;
  if (!msg || !msg.type) return;

  // --- Receive full CMS sync from Wix ---
  if (msg.type === 'CMS_SYNC') {
    console.log('📡 Live CMS data received from Wix!');

    if (msg.clients && Array.isArray(msg.clients)) {
      CMS_DATA.clients = msg.clients.map(c => ({
        id:      c._id || c.id || '',
        name:    c.clientName || c['Client Name'] || c.title || '',
        address: c.address || c['Address'] || '',
        email:   c.email || '',
        image:   resolveImageValue(c.image || c.Image),
      })).filter(c => c.name);
    }

    if (msg.machines && Array.isArray(msg.machines)) {
      CMS_DATA.machines = msg.machines.map(m => ({
        id:         m._id || m.id || '',
        serialNo:   m.serialNumber || m['Serial Number'] || '',
        name:       m.machineName || m['Machine Name'] || '',
        client:     m.client || m['Client'] || '',
        location:   m.location || m['Location'] || '',
        nextCFDate: m.next_Cf_Date || m['Next_CF_Date'] || '',
        priority:   m.priority || m['Priority'] || '',
        workStatus: m.workStatus || m['Work Status'] || '',
        remarks:    m.latestRemarks || m['Latest Remarks'] || '',
      })).filter(m => m.serialNo);
    }

    CMS_DATA.loaded = true;
    CMS_DATA.source = 'wix';
    console.log(`✅ CMS synced: ${CMS_DATA.clients.length} clients, ${CMS_DATA.machines.length} machines`);

    // Notify report-logic to refresh dropdowns
    if (typeof onCMSDataRefresh === 'function') {
      onCMSDataRefresh();
    }
  }

  // --- Receive confirmation after saving ---
  if (msg.type === 'SAVE_OK') {
    console.log('✅ Wix saved report:', msg.id);
  }
  if (msg.type === 'SAVE_ERROR') {
    console.error('❌ Wix save failed:', msg.error);
  }

  // --- Receive single new item (real-time add) ---
  if (msg.type === 'CMS_ADD_CLIENT' && msg.client) {
    const c = msg.client;
    CMS_DATA.clients.push({
      id: c._id || '', name: c.clientName || '', address: c.address || '', email: c.email || '', image: resolveImageValue(c.image || c.Image)
    });
    if (typeof onCMSDataRefresh === 'function') onCMSDataRefresh();
    console.log('➕ New client added from Wix:', c.clientName);
  }

  if (msg.type === 'CMS_UPDATE_CLIENT' && msg.client) {
    const c = msg.client;
    const idx = CMS_DATA.clients.findIndex(x => x.id === (c._id || c.id || ''));
    const next = {
      id: c._id || c.id || '',
      name: c.clientName || c['Client Name'] || c.title || '',
      address: c.address || c['Address'] || '',
      email: c.email || '',
      image: resolveImageValue(c.image || c.Image)
    };
    if (idx >= 0) {
      CMS_DATA.clients[idx] = next;
    } else if (next.name) {
      CMS_DATA.clients.push(next);
    }
    if (typeof onCMSDataRefresh === 'function') onCMSDataRefresh();
    console.log('✏️ Client updated from Wix:', next.name || next.id);
  }

  if (msg.type === 'CMS_ADD_MACHINE' && msg.machine) {
    const m = msg.machine;
    CMS_DATA.machines.push({
      id: m._id || '', serialNo: m.serialNumber || '', name: m.machineName || '',
      client: m.client || '', location: m.location || '', nextCFDate: m.next_Cf_Date || '',
      priority: m.priority || ''
    });
    if (typeof onCMSDataRefresh === 'function') onCMSDataRefresh();
    console.log('➕ New machine added from Wix:', m.machineName);
  }

  // --- Receive delete notification ---
  if (msg.type === 'CMS_DELETE_CLIENT' && msg.clientId) {
    CMS_DATA.clients = CMS_DATA.clients.filter(c => c.id !== msg.clientId);
    if (typeof onCMSDataRefresh === 'function') onCMSDataRefresh();
    console.log('🗑️ Client removed:', msg.clientId);
  }

  if (msg.type === 'CMS_DELETE_MACHINE' && msg.machineId) {
    CMS_DATA.machines = CMS_DATA.machines.filter(m => m.id !== msg.machineId);
    if (typeof onCMSDataRefresh === 'function') onCMSDataRefresh();
    console.log('🗑️ Machine removed:', msg.machineId);
  }
});

// ========================================
// 2) CSV FILE LOADER (fallback for standalone)
// ========================================
async function loadCMSData(basePath) {
  // If already loaded from Wix, don't overwrite
  if (CMS_DATA.source === 'wix') {
    console.log('⏭️ Skipping CSV — already using live Wix data');
    return CMS_DATA;
  }

  const base = basePath || '../CMS';
  try {
    const [clientRes, machineRes] = await Promise.all([
      fetch(`${base}/Personal Detail.csv`),
      fetch(`${base}/Machinery List.csv`)
    ]);

    if (clientRes.ok) {
      const clientText = await clientRes.text();
      CMS_DATA.clients = parseCSV(clientText).map(row => ({
        id:      row['ID'] || '',
        name:    row['Client Name'] || '',
        address: row['Address'] || '',
        email:   row['email'] || '',
        image:   row['Image'] || '',
        status:  row['Status'] || 'PUBLISHED'
      })).filter(c => c.name && c.status === 'PUBLISHED');
    }

    if (machineRes.ok) {
      const machineText = await machineRes.text();
      CMS_DATA.machines = parseCSV(machineText).map(row => ({
        id:         row['ID'] || '',
        serialNo:   row['Serial Number'] || '',
        name:       row['Machine Name'] || '',
        client:     row['Client'] || '',
        location:   row['Location'] || '',
        nextCFDate: row['Next_CF_Date'] || '',
        priority:   row['Priority'] || '',
        workStatus: row['Work Status'] || '',
        remarks:    row['Latest Remarks'] || ''
      })).filter(m => m.serialNo);
    }

    CMS_DATA.loaded = true;
    CMS_DATA.source = 'csv';
    console.log(`📁 CSV loaded: ${CMS_DATA.clients.length} clients, ${CMS_DATA.machines.length} machines`);
    return CMS_DATA;
  } catch (err) {
    console.warn('CSV load failed, using fallback:', err);
    loadFallbackData();
    return CMS_DATA;
  }
}

// ========================================
// 3) HARDCODED FALLBACK
// ========================================
function loadFallbackData() {
  CMS_DATA.clients = [
    { id: '1', name: 'IIUM10',                   address: 'IIUM199',                                                                                           email: 'syifaputrixez@gmail.com' },
    { id: '2', name: 'IIUM 3',                    address: 'IIUM 32',                                                                                           email: 'businessatto001@gmail.com' },
    { id: '3', name: 'Tijarah Mabrur Sdn Bhd',    address: 'F-6-8, PUSAT KOMERSIAL SETAPAK POINT, (STARPARC POINT) JALAN TAMAN IBU KOTA, TAMAN DANAU KOTA, 53100, KUALA LUMPUR', email: 'shalihinidris@gmail.com' },
    { id: '4', name: 'Daikin (M) Sdn Bhd',        address: '',                                                                                                  email: '' },
    { id: '5', name: 'COMPANY SENDIRI',            address: 'kat mana2',                                                                                        email: 'iamatto01@gmail.com' },
    { id: '6', name: 'rumahhijau',                 address: 'ausdhbajkhsf',                                                                                     email: 'asim.elmo@gmail.com' },
    { id: '7', name: 'IIUMd',                      address: 'IIUd',                                                                                             email: 'muhammadsaifudinmj@gmail.com' },
    { id: '8', name: 'TIJARAH',                    address: '',                                                                                                  email: '' },
  ];

  CMS_DATA.machines = [
    { id: 'M001', serialNo: 'A17071205',     name: 'Air Receiver Tank 1000L',         client: 'IIUM10',                   location: 'Block A - Ground Floor',    nextCFDate: '2026-09-15', priority: 'High' },
    { id: 'M002', serialNo: 'SB-2024-0012',  name: 'Steam Boiler 500HP',              client: 'IIUM10',                   location: 'Utility Building',          nextCFDate: '2026-06-30', priority: 'Urgent' },
    { id: 'M003', serialNo: 'CR-KT-001',     name: 'Overhead Crane 10 Ton',           client: 'IIUM10',                   location: 'Workshop Bay 1',            nextCFDate: '2026-12-01', priority: 'Medium' },
    { id: 'M004', serialNo: 'PV-HZ-2019',    name: 'Horizontal Pressure Vessel 2000L',client: 'Tijarah Mabrur Sdn Bhd',   location: 'HQ - Level 1',              nextCFDate: '2027-01-15', priority: 'Low' },
    { id: 'M005', serialNo: 'CP-ATL-005',    name: 'Atlas Copco Compressor GA37',     client: 'Tijarah Mabrur Sdn Bhd',   location: 'HQ - Compressor Room',      nextCFDate: '2026-08-20', priority: 'Medium' },
    { id: 'M006', serialNo: 'HT-CHN-003',    name: 'Chain Hoist 5 Ton',               client: 'Tijarah Mabrur Sdn Bhd',   location: 'Workshop',                  nextCFDate: '2026-11-30', priority: 'Low' },
    { id: 'M007', serialNo: 'AR-TG-F31-001', name: 'Air Receiver Tank 500L',          client: 'Daikin (M) Sdn Bhd',       location: 'Plant 1 - Section A',       nextCFDate: '2026-07-20', priority: 'High' },
    { id: 'M008', serialNo: 'CP-IR-008',     name: 'Ingersoll Rand Compressor R55',   client: 'Daikin (M) Sdn Bhd',       location: 'Plant 1 - Compressor Room', nextCFDate: '2026-10-15', priority: 'Medium' },
    { id: 'M009', serialNo: 'PV-VT-2020',    name: 'Vertical Pressure Vessel 800L',   client: 'Daikin (M) Sdn Bhd',       location: 'Plant 2 - Utility',         nextCFDate: '2026-05-30', priority: 'Urgent' },
    { id: 'M010', serialNo: 'LF-PSG-001',    name: 'Passenger Lift - KONE MonoSpace', client: 'IIUM 3',                   location: 'Building C',                nextCFDate: '2026-08-01', priority: 'High' },
    { id: 'M011', serialNo: 'SB-MIS-002',    name: 'Miura Steam Boiler EI-2056',      client: 'IIUM 3',                   location: 'Boiler Room',               nextCFDate: '2026-04-15', priority: 'Urgent' },
    { id: 'M012', serialNo: 'GC-LBG-001',    name: 'Gantry Crane 20 Ton',             client: 'rumahhijau',               location: 'Factory Floor',             nextCFDate: '2027-02-28', priority: 'Low' },
    { id: 'M013', serialNo: 'FLT-TYT-001',   name: 'Toyota Forklift 8FBN25',          client: 'rumahhijau',               location: 'Warehouse',                 nextCFDate: '2026-09-01', priority: 'Medium' },
    { id: 'M014', serialNo: 'CP-KSR-010',    name: 'Kaeser Compressor CSD 75',        client: 'COMPANY SENDIRI',           location: 'Workshop A',                nextCFDate: '2026-11-01', priority: 'Medium' },
    { id: 'M015', serialNo: 'AR-VT-500',     name: 'Vertical Air Receiver 500L',      client: 'COMPANY SENDIRI',           location: 'Workshop A - Corner',       nextCFDate: '2026-12-15', priority: 'Low' },
    { id: 'M016', serialNo: 'BLR-YRK-001',   name: 'York Chiller YCIV',               client: 'Daikin (M) Sdn Bhd',       location: 'Plant 1 - Chiller Room',    nextCFDate: '2026-06-01', priority: 'High' },
  ];

  CMS_DATA.loaded = true;
  CMS_DATA.source = 'fallback';
}

// ---- HELPER FUNCTIONS ----
function getClients() {
  return CMS_DATA.clients;
}

function getMachinesByClient(clientName) {
  if (!clientName) return CMS_DATA.machines;
  return CMS_DATA.machines.filter(m =>
    m.client.toLowerCase() === clientName.toLowerCase()
  );
}

function getClientByName(name) {
  return CMS_DATA.clients.find(c =>
    c.name.toLowerCase() === name.toLowerCase()
  );
}

function getMachineBySerial(serial) {
  return CMS_DATA.machines.find(m => m.serialNo === serial);
}

function getCMSSource() {
  return CMS_DATA.source;
}
