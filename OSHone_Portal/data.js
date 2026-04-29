// ===== SAMPLE DATA (localStorage backed) =====
const DEFAULT_DATA = {
  company: {
    name: 'Tijarah Mabrur Sdn Bhd',
    address: '123 Jalan Ampang, Kuala Lumpur',
    phone: '03-1234 5678',
    email: 'admin@tijarah.com',
    website: 'www.tijarah.com',
    logo: 'TM'
  },
  user: {
    name: 'Ahmad Faizal',
    email: 'admin@tijarah.com',
    phone: '012-345 6789',
    position: 'Safety Manager',
    plan: 'Pro Plan'
  },
  machines: [
    {id:'M001',name:'Boiler Unit A',pmt:'PMT-001',serial:'BLR-2019-001',location:'Loji Utama',cfExpiry:'2026-12-01',type:'Boiler',status:'valid'},
    {id:'M002',name:'Overhead Crane',pmt:'PMT-002',serial:'CRN-2018-003',location:'Warehouse B',cfExpiry:'2022-01-01',type:'Crane',status:'expired'},
    {id:'M003',name:'Pressure Vessel',pmt:'PMT-003',serial:'PV-2020-007',location:'Chemical Store',cfExpiry:'2024-08-15',type:'Pressure Vessel',status:'expiring'},
    {id:'M004',name:'Passenger Lift',pmt:'PMT-004',serial:'LFT-2021-002',location:'Bangunan Utama',cfExpiry:'2025-06-30',type:'Lift',status:'valid'},
    {id:'M005',name:'Steam Boiler B',pmt:'PMT-005',serial:'BLR-2020-004',location:'Loji Utama',cfExpiry:'2025-03-20',type:'Boiler',status:'valid'},
    {id:'M006',name:'Forklift Toyota',pmt:'PMT-006',serial:'FLK-2022-001',location:'Gudang C',cfExpiry:'2024-11-10',type:'Forklift',status:'expiring'}
  ],
  documents: [
    {id:'D001',name:'HIRARC Loji Utama',type:'HIRARC',date:'2024-01-15',status:'active'},
    {id:'D002',name:'CHRA Chemical Store',type:'CHRA',date:'2023-11-20',status:'active'},
    {id:'D003',name:'NRA Warehouse B',type:'NRA',date:'2024-03-10',status:'active'},
    {id:'D004',name:'Safety Policy 2024',type:'Policy',date:'2024-01-01',status:'active'},
    {id:'D005',name:'Emergency Response Plan',type:'ERP',date:'2023-09-15',status:'review'}
  ],
  reports: [
    {id:'R001',machineId:'M001',type:'PMT Service',date:'2024-06-15',status:'completed',tech:'En. Rahman'},
    {id:'R002',machineId:'M002',type:'Load Test',date:'2023-12-01',status:'overdue',tech:'En. Azman'},
    {id:'R003',machineId:'M003',type:'Hydrostatic Test',date:'2024-07-20',status:'completed',tech:'En. Hafiz'},
    {id:'R004',machineId:'M001',type:'UT Thickness',date:'2024-08-01',status:'pending',tech:'En. Rahman'},
    {id:'R005',machineId:'M004',type:'PMT Service',date:'2024-05-10',status:'completed',tech:'En. Azman'},
    {id:'R006',machineId:'M005',type:'PMA Calibration',date:'2024-09-01',status:'pending',tech:'Pn. Siti'}
  ],
  training: [
    {id:'T001',course:'OSHA Awareness',date:'2024-03-15',participants:25,status:'completed'},
    {id:'T002',course:'HIRARC Workshop',date:'2024-06-20',participants:15,status:'completed'},
    {id:'T003',course:'First Aid & CPR',date:'2024-10-05',participants:30,status:'approved'},
    {id:'T004',course:'Fire Safety Drill',date:'2024-12-01',participants:50,status:'requested'}
  ],
  certificates: [
    {id:'C001',title:'Occupational Safety & Health Coordinator',abbr:'OSHC',holder:'Ahmad Faizal bin Mohd',ic:'880515-14-5523',regNo:'JKKP/OSHC/2024/1234',validUntil:'2026-12-31',issuer:'JKKP Malaysia'},
    {id:'C002',title:'Safety & Health Officer',abbr:'SHO',holder:'Siti Aminah binti Abdullah',ic:'900820-10-6634',regNo:'JKKP/SHO/2023/5678',validUntil:'2025-08-15',issuer:'JKKP Malaysia'},
    {id:'C003',title:'Fire Safety Coordinator',abbr:'FSC',holder:'Mohd Rizal bin Hassan',ic:'850310-14-7789',regNo:'BOMBA/FSC/2024/0091',validUntil:'2026-06-30',issuer:'Jabatan Bomba dan Penyelamat'},
    {id:'C004',title:'Certified First Aider',abbr:'FA',holder:'Nurul Huda binti Yusof',ic:'920115-08-4456',regNo:'SJA/FA/2024/2345',validUntil:'2025-12-31',issuer:'St. John Ambulance Malaysia'}
  ],
  notifications: {
    cfExpiry: true,
    calibration: true,
    missingDoc: true,
    trainingReminder: true
  }
};

function loadData() {
  const saved = localStorage.getItem('oshone_data');
  if (saved) return JSON.parse(saved);
  return JSON.parse(JSON.stringify(DEFAULT_DATA));
}

function saveData(data) {
  localStorage.setItem('oshone_data', JSON.stringify(data));
}

let APP_DATA = loadData();
