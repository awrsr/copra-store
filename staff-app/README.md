# Copra Staff

## Run the local test environment

1. Start the Flask store from the repository root:

   ```powershell
   python app.py
   ```

2. In `staff-app`, install dependencies and start Vite:

   ```powershell
   npm install
   npm run dev
   ```

3. Open `http://127.0.0.1:5173/staff/`. The development server proxies `/api`
   requests to Flask. Sign in with `STAFF_PASSWORD` (or `ADMIN_PASSWORD`); the
   local-only default is `copra-admin-123`.

4. In another tab, open the shop at `http://127.0.0.1:5000`, place a cash-on-
   delivery order, and watch it appear in the staff queue. The staff feed uses
   authenticated Server-Sent Events; the customer tracking link uses a random
   per-order token.

## Build and serve with Flask

```powershell
npm run build
```

Flask serves the generated app at `/staff`. Deploy the `staff-app/dist` build
with the Flask service. Set `STAFF_PASSWORD` and `SECRET_KEY` in the hosting
provider before exposing the service.

## Firestore and push notifications

The local test mode uses SQLite and works without cloud credentials. To mirror
users, orders, messages, inventory and server events to Firestore, enable
Firestore in Firebase, deploy the root `firestore.rules`, and set
`FIREBASE_SERVICE_ACCOUNT_JSON` to the service-account JSON as a private server
environment variable. Do not put this credential in `staff-app`, source
control, or a Capacitor client bundle. FCM delivery also requires Firebase Admin
credentials and registered staff devices.

The Capacitor app registration is in `capacitor.config.ts`. Add the native
platforms with `npx cap add android` / `npx cap add ios`, then run
`npx cap sync`. For Android, add the Firebase Android app and place its
`google-services.json` in `android/app`. iOS push builds require a Mac, the
Firebase iOS app configuration, and APNs credentials. Set
`CAPACITOR_SERVER_URL=https://your-domain.example/staff/` when building a
wrapper that loads the deployed staff app; use HTTPS.

This repository does not include Firebase project identifiers, service-account
credentials, Android/iOS signing keys, or APNs credentials. Push notifications
are enabled only after those Firebase and platform settings are supplied.
