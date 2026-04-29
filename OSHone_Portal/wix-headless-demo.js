// CONTOH KOD PENGGUNAAN WIX HEADLESS SDK UNTUK UPDATE & DELETE DATA
// Sesuai digunakan untuk Pilihan 1: Custom Admin Portal

import { createClient, OAuthStrategy } from '@wix/sdk';
import { items } from '@wix/data';

const wixClient = createClient({
  modules: { items },
  auth: OAuthStrategy({ clientId: '13c286fe-a77c-47ee-9165-a0f896986e93' })
});

/**
 * 1. MENGEMASKINI DATA (UPDATE)
 * Fungsi ini digunakan untuk mengemaskini maklumat sedia ada dalam CMS.
 * Memerlukan _id bagi item tersebut.
 */
export async function updateCMSData(collectionName, itemId, updatedFields) {
    try {
        // Dapatkan data asal dahulu
        const existingItem = await wixClient.items.getDataItem(itemId, { dataCollectionId: collectionName });
        
        // Gabungkan data lama dengan data baru
        const newData = {
            ...existingItem.data,
            ...updatedFields
        };

        // Simpan semula ke Wix CMS
        const result = await wixClient.items.updateDataItem(itemId, {
            dataCollectionId: collectionName,
            data: newData
        });

        console.log("Berjaya dikemaskini:", result);
        return result;
    } catch (error) {
        console.error("Gagal mengemaskini data:", error);
        throw error;
    }
}

/**
 * 2. MEMADAM DATA (DELETE)
 * Fungsi ini digunakan untuk membuang rekod dari Wix CMS berdasarkan _id.
 */
export async function deleteCMSData(collectionName, itemId) {
    try {
        await wixClient.items.removeDataItem(itemId, { dataCollectionId: collectionName });
        console.log(`Item ${itemId} telah berjaya dipadam dari ${collectionName}`);
        return true;
    } catch (error) {
        console.error("Gagal memadam data:", error);
        throw error;
    }
}

/**
 * 3. MENAMBAH DATA BARU (INSERT)
 * Fungsi tambahan untuk masukkan rekod baru.
 */
export async function insertCMSData(collectionName, itemData) {
    try {
        const result = await wixClient.items.insertDataItem({
            dataCollectionId: collectionName,
            data: itemData
        });
        console.log("Data baru berjaya ditambah:", result);
        return result;
    } catch (error) {
        console.error("Gagal menambah data:", error);
        throw error;
    }
}

// ==========================================
// CONTOH CARA GUNA (Di dalam fail UI anda):
// ==========================================
/*
  // Update lokasi mesin
  updateCMSData('Assets', '12345-abcde', {
      location: 'Gudang Utama',
      status: 'valid'
  });

  // Delete laporan yang salah
  deleteCMSData('Reports', '98765-zyxwv');

  // Insert laporan baru (Untuk user "Report")
  insertCMSData('Reports', {
      machineId: '12345-abcde',
      type: 'PMT Service',
      date: '2024-12-01',
      tech: 'En. Rahman',
      status: 'pending'
  });
*/
