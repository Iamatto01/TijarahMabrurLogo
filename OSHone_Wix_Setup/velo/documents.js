import wixData from 'wix-data';
import { getCurrentUserCompany } from 'backend/oshoneData';

$w.onReady(async function () {
    const htmlComponent = $w("#htmlDocuments");
    let docsDataReady = null;

    // 1. Terima mesej dari HTML
    htmlComponent.onMessage((event) => {
        const message = event.data;
        if (message.type === 'HTML_READY') {
            if (docsDataReady !== null) {
                htmlComponent.postMessage({
                    type: "DOCS_DATA",
                    documents: docsDataReady
                });
            }
        }
    });

    // 2. Ambil data dari CMS
    try {
        const company = await getCurrentUserCompany();
        
        if (company) {
            const docsQuery = await wixData.query("Documents")
                .eq("company", company._id)
                .find();
                
            docsDataReady = docsQuery.items;
            
            // Backup tembak terus
            htmlComponent.postMessage({
                type: "DOCS_DATA",
                documents: docsDataReady
            });
            
        }
    } catch (err) {
        console.error("Ralat:", err);
    }
});
