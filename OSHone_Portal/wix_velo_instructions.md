# Wix Velo Integration Guide — OSHone Report Builder (DYNAMIC)

## Architecture
```
[Wix Page Load] → Velo queries CMS → postMessage('CMS_SYNC') → [iframe: Report Builder]
[iframe: Submit] → postMessage('REPORT_SUBMISSION') → Velo saves to CMS
[Wix CMS Change] → afterInsert/afterRemove hooks → postMessage('CMS_ADD/DELETE') → iframe updates
```

## Wix CMS Collections

| Collection | Slug | Key Fields |
|---|---|---|
| Personal Detail | `personal-detail` | Client Name, Address, email, Image |
| Machinery List | `machinery-list` | Serial Number, Machine Name, Client, Location, Next_CF_Date |
| Report SV | `sv-report-2` | Certificate Number, Customer, Instrument, Calibration Data |
| Report OSHWA | `report-oshwa` | Nama Organisasi, Alamat, compliance fields |

> **DYNAMIC**: Bila tambah collection baru, hanya perlu tambah 1 query dalam Step 1 dan 1 handler dalam Step 2.

---

## Step 1: Page Code — Send Live CMS Data ke iframe

Letak kod ini di page yang ada HtmlComponent (`#html1`):

```javascript
import wixData from 'wix-data';
import { saveServiceReport, saveMachine } from 'backend/reportBackend';

$w.onReady(async function () {

  // ========================================
  // 1) SYNC: Send all CMS data to iframe on load
  // ========================================
  try {
    const [clientResult, machineResult] = await Promise.all([
      wixData.query("personal-detail").limit(1000).find(),
      wixData.query("machinery-list").limit(1000).find()
    ]);

    // Send to iframe
    $w("#html1").postMessage({
      type: 'CMS_SYNC',
      clients: clientResult.items,
      machines: machineResult.items
    });

    console.log(`Synced ${clientResult.items.length} clients, ${machineResult.items.length} machines`);
  } catch (err) {
    console.error("CMS sync failed:", err);
  }

  // ========================================
  // 2) RECEIVE: Listen for report submissions from iframe
  // ========================================
  $w("#html1").onMessage(async (event) => {
    const msg = event.data;
    if (!msg || !msg.type) return;

    // --- Save Service Report ---
    if (msg.type === 'REPORT_SUBMISSION') {
      console.log("Report received:", msg.payload.client.reportNo);
      const response = await saveServiceReport(msg.payload);

      if (response.success) {
        $w("#html1").postMessage({ type: 'SAVE_OK', id: response.item._id });
        console.log("Saved:", response.item._id);
      } else {
        $w("#html1").postMessage({ type: 'SAVE_ERROR', error: response.error });
      }
    }

    // --- Save New Machine ---
    if (msg.type === 'NEW_MACHINE') {
      const response = await saveMachine(msg.machine);
      if (response.success) {
        // Send the new machine back to iframe so dropdown updates
        $w("#html1").postMessage({ type: 'CMS_ADD_MACHINE', machine: response.item });
      }
    }
  });
});
```

---

## Step 2: Backend Module (`reportBackend.jsw`)

```javascript
import wixData from 'wix-data';

// ---- Save Service Report ----
export async function saveServiceReport(payload) {
  try {
    const toInsert = {
      certificateNumber: payload.client.reportNo,
      customer:          payload.client.name,
      address:           payload.client.address,
      dateOfIssue:       payload.client.reportDate,
      serialNumber:      payload.machine.serialNo,
      instrumentName:    payload.machine.machineName,
      manufacturerModel: payload.machine.manufacturer,
      calibrationDate:   payload.client.serviceDate,
      calibrationLocation: payload.machine.location,
      reportData:        JSON.stringify(payload),
      tag:               payload.tag || 'PMT_SERVICE_REPORT',
    };
    const result = await wixData.insert("sv-report-2", toInsert);
    return { success: true, item: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ---- Save New Machine ----
export async function saveMachine(machineData) {
  try {
    const toInsert = {
      serialNumber: machineData.serialNo,
      machineName:  machineData.name,
      client:       machineData.client,
      location:     machineData.location,
      next_Cf_Date: machineData.nextCFDate,
      priority:     machineData.priority || 'Medium',
      workStatus:   'Active',
    };
    const result = await wixData.insert("machinery-list", toInsert);
    return { success: true, item: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ---- Generic Query (for any collection) ----
export async function queryCollection(collectionName, filters = {}) {
  try {
    let query = wixData.query(collectionName);
    Object.entries(filters).forEach(([field, value]) => {
      query = query.eq(field, value);
    });
    const result = await query.limit(1000).find();
    return { success: true, items: result.items, totalCount: result.totalCount };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

---

## Step 3: Data Hooks (Auto-sync on CMS changes)

Buat fail `data.js` dalam Backend untuk auto-notify iframe bila ada perubahan:

```javascript
// backend/data.js (Wix Data Hooks)
import wixData from 'wix-data';

// When a new client is added to Personal Detail
export function personal_detail_afterInsert(item, context) {
  // The page code will re-sync on next load
  // For real-time: use wix-realtime or polling
  return item;
}

// When a new machine is added
export function machinery_list_afterInsert(item, context) {
  return item;
}
```

> **Nota**: Wix Data Hooks berjalan di backend dan tidak boleh terus postMessage ke iframe.
> Untuk real-time sync selepas CMS berubah, iframe boleh poll data setiap 30 saat,
> atau gunakan butang "🔄 Refresh" dalam Report Builder.

---

## Step 4: HtmlComponent Setup

1. Dalam Wix Editor, tambah **HtmlComponent** (`#html1`)
2. Set source URL: `https://your-app.netlify.app/report-builder/`
3. Paste page code dari Step 1 ke page code panel

---

## Aliran Data (Dynamic)

```
┌─────────────┐     CMS_SYNC      ┌──────────────────┐
│  Wix CMS    │ ──────────────►   │  Report Builder   │
│  (Database) │                    │  (iframe/Netlify) │
│             │ ◄──────────────   │                   │
│             │  REPORT_SUBMISSION │                   │
└─────────────┘                    └──────────────────┘
      │                                    │
      │ afterInsert                        │ onCMSDataRefresh
      ▼                                    ▼
   Auto-sync                        Dropdown refresh
   (next load)                      (instant)
```

## Menambah Collection Baru

Untuk sambung collection baru (contoh: `training-records`):

1. **Page Code** — Tambah 1 query:
```javascript
const trainingResult = await wixData.query("training-records").limit(1000).find();
// Add to CMS_SYNC message
$w("#html1").postMessage({
  type: 'CMS_SYNC',
  clients: clientResult.items,
  machines: machineResult.items,
  training: trainingResult.items  // ← baru
});
```

2. **cms-data.js** — Tambah handler dalam `CMS_SYNC`:
```javascript
if (msg.training && Array.isArray(msg.training)) {
  CMS_DATA.training = msg.training;
}
```

Itu sahaja! Tidak perlu ubah backend atau HTML.
