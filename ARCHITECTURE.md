# OSHone Architecture

The workspace is now portal-first:

## 1. `OSHone_Portal/`
Main application.

- Handles login, portal views, and the admin CMS detail screen.
- Uses the shared local data model in `data.js` for the mock CMS content.
- This is the primary UI that Netlify serves.

## 2. Root `index.html`
Netlify entrypoint.

- Prevents a 404 at the site root.
- Redirects users into `OSHone_Portal/index.html`.

## Data Flow

```text
Netlify domain
  -> root index.html
  -> OSHone_Portal/index.html
  -> login
  -> portal views
  -> CMS Detail view inside the portal
```

## Why the setup folder was removed

The separate Wix setup area was folded into the portal so admins can inspect CMS data without leaving the app. That keeps the structure simpler and makes the deployment target obvious: the portal is the product.