import wixData from 'wix-data';
import { getCurrentUserCompany } from 'backend/oshoneData';
import wixLocation from 'wix-location';

$w.onReady(async function () {
    const htmlComponent = $w("#htmlAssets");
    let assetsDataReady = null;

    // 1. Terima mesej dari HTML
    htmlComponent.onMessage((event) => {
        const message = event.data;
        
        // Bila HTML dah sedia nak terima data
        if (message.type === 'HTML_READY') {
            if (assetsDataReady !== null) {
                htmlComponent.postMessage({
                    type: "ASSETS_DATA",
                    assets: assetsDataReady
                });
            }
        }
        // Bila user klik "Lihat Detail Penuh"
        else if (message.type === 'NAVIGATE') {
            wixLocation.to(message.url);
        }
    });

    // 2. Ambil data dari CMS
    try {
        const company = await getCurrentUserCompany();
        
        if (company) {
            const assetsQuery = await wixData.query("Assets")
                .eq("company", company._id)
                .find();
                
            assetsDataReady = assetsQuery.items;
            
            // Backup tembak je, in case HTML dah load sebelum JS sedia
            htmlComponent.postMessage({
                type: "ASSETS_DATA",
                assets: assetsDataReady
            });
        }
    } catch (err) {
        console.error("Ralat:", err);
    }
});
