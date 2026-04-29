# OSHone Architecture

This workspace is split into two parts because it serves two different jobs:

## 1. `OSHone_Portal/`
User-facing portal.

- Main web app for login and day-to-day portal usage.
- Deployed through the root Netlify site.
- The root `index.html` redirects here so the site opens the portal first.

## 2. `OSHone_Wix_Setup/`
Wix / headless CMS side.

- Contains CMS-related pages and Velo helpers.
- Used for managing organizational data, assets, and documents.
- The admin menu inside the portal opens the CMS hub from here.

## 3. Root `index.html`
Netlify entrypoint.

- Keeps the site from showing a 404 on the domain root.
- Redirects to `OSHone_Portal/index.html`.

## Data Flow

```text
Netlify domain
  -> root index.html
  -> OSHone_Portal/index.html
  -> login
  -> portal views
  -> admin CMS link
  -> OSHone_Wix_Setup/page/cms.html
```

## Why there are two folders

The portal and the CMS are intentionally separated so the user experience stays simple while the data-management side stays isolated. That makes it easier to deploy the portal on Netlify while keeping Wix-specific pages and headless CMS helpers in their own area.