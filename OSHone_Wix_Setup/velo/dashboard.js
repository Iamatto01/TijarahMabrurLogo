import { getCurrentUserCompany } from 'backend/oshoneData';

$w.onReady(async function () {
    const htmlComponent = $w("#htmlDashboard");
    let companyDataReady = null;

    // 1. Terima mesej dari HTML
    htmlComponent.onMessage((event) => {
        const message = event.data;
        if (message.type === 'HTML_READY') {
            if (companyDataReady !== null) {
                htmlComponent.postMessage({
                    type: "COMPANY_INFO",
                    company: companyDataReady
                });
            }
        }
    });

    // 2. Ambil data syarikat dari CMS
    try {
        const company = await getCurrentUserCompany();
        
        if (company) {
            // Kita assume field-field ini wujud dalam Collection 'Companies'
            companyDataReady = {
                title: company.title,
                alamat: company.alamat || '',
                noPejabat: company.noPejabat || '',
                email: company.email || '',
                lamanWeb: company.lamanWeb || '',
                logo: company.logo || null // URL gambar dari Wix
            };
            
            // Backup hantar terus
            htmlComponent.postMessage({
                type: "COMPANY_INFO",
                company: companyDataReady
            });
            
        } else {
            console.error("Data syarikat tidak dijumpai.");
        }
    } catch (err) {
        console.error("Ralat memuat turun data:", err);
    }
});
