# QR-Based Cow Digital Passport

A working demo module of a larger Smart Farm Management System. It lets a
farmer register a cow, generates a unique QR tag for it, and lets anyone
scan that tag with a normal phone camera to open the cow's digital
passport — its health, vaccination, and ownership record — straight in
the browser.

This demo is scoped to **QR-based cow identification only**. There is no
AI/ML, IoT, payment gateway, or login system — keeping the project simple,
explainable, and easy to demo in a panel review.

---

## 1. Features

- **Register a cow** — full profile form (identity, owner, health,
  vaccination, production, photo).
- **Auto-generated QR tag** — encodes only the cow's profile URL / ID,
  never the full report, and can be viewed, downloaded, or printed.
- **Camera-based scanner** — works on desktop and mobile browsers, no
  app install required.
- **Cow Digital Passport** — a mobile-friendly page organized into
  clear sections (basic info, registration, health, vaccination,
  production).
- **Lost cow recovery** — a public "Found This Cow?" flow that lets a
  finder submit their contact details without exposing the owner's
  private information.
- **Admin dashboard** — total count, search by ID/name, view profile,
  view/print QR, delete cow.
- **Sample data** — 3 cows preloaded so the demo works immediately.

---

## 2. Technology Stack

| Layer      | Technology                          |
|------------|--------------------------------------|
| Frontend   | HTML, CSS, JavaScript (no framework) |
| Backend    | Python 3, Flask                      |
| Database   | MySQL                                |
| QR Codes   | `qrcode` (Python) for generation, `html5-qrcode` (JS, via CDN) for scanning |

---

## 3. Folder Structure

```
cow_qr_demo/
│
├── app.py                  # Flask application (all routes)
├── requirements.txt
├── README.md
├── .env.example             # Sample environment variables
├── database/
│   └── schema.sql           # Tables + sample data
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── register_cow.html
│   ├── qr.html
│   ├── scan.html
│   ├── cow_profile.html
│   ├── report_found.html
│   └── 404.html
├── static/
│   ├── css/style.css
│   ├── js/scanner.js
│   ├── images/              # (optional, for logos etc.)
│   └── qr_codes/            # QR PNGs are generated here at runtime
└── uploads/                 # Cow photos are stored here at runtime
```

---

## 4. Prerequisites

- Python 3.9+
- MySQL Server 8.0+ (or MariaDB) running locally
- pip

---

## 5. MySQL Setup

1. Log in to MySQL:
   ```bash
   mysql -u root -p
   ```
2. Run the schema file — it creates the database, both tables, and
   inserts 3 sample cows:
   ```bash
   mysql -u root -p < database/schema.sql
   ```
   Or from inside the MySQL shell:
   ```sql
   SOURCE database/schema.sql;
   ```

---

## 6. Python Environment Setup

```bash
cd cow_qr_demo

# create a virtual environment
python -m venv venv

# activate it
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

---

## 7. Configure Environment Variables

Copy `.env.example` to `.env` (or set these in your shell / VS Code
launch settings):

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=cow_qr_demo
SECRET_KEY=change-this-secret-key
SITE_BASE_URL=http://localhost:5000
```

If you're running Flask with `python-dotenv` installed it will pick up
`.env` automatically; otherwise export the variables manually before
running the app, e.g. on macOS/Linux:

```bash
export DB_PASSWORD=your_mysql_password
```

> **Important for live demos:** `SITE_BASE_URL` is what gets embedded
> inside every QR code. If you plan to scan the QR tag with a **phone**
> while the Flask server runs on your **laptop**, `localhost` will not
> work from the phone. Set `SITE_BASE_URL` to your laptop's LAN IP
> instead, e.g. `http://192.168.1.10:5000`, and make sure the phone is
> on the same Wi-Fi network.

---

## 8. Running the Flask Server

```bash
python app.py
```

The server starts at `http://localhost:5000` (and is also reachable on
your LAN IP on port 5000, since it binds to `0.0.0.0`).

---

## 9. Using the Application

### Access
Open `http://localhost:5000` in a browser.

### Register a Cow
1. Go to **Register Cow** from the navigation bar.
2. Fill in the required fields (marked with `*`) and optionally upload
   a photo.
3. Submit — you're redirected straight to the generated QR tag page.

### Generate / View a QR Tag
- Every registration automatically generates a QR PNG saved under
  `static/qr_codes/<COW_ID>.png`.
- From the dashboard, click **QR** next to any cow to view, download,
  or print its tag.

### Test QR Scanning
1. Go to **Scan QR** from the navigation bar.
2. Allow camera access when prompted.
3. Point the camera at a printed or on-screen QR tag.
4. The browser automatically redirects to that cow's digital passport.

> If testing on the same laptop, you can simply open the printed QR's
> profile URL in a new tab, or point a second device's camera at the
> screen showing the QR from the `/qr/<COW_ID>` page.

---

## 10. Demo Instructions for Presentation

Suggested live-demo flow for the panel:

1. Open the **Admin Dashboard** — show the 3 preloaded cows.
2. Click **Register New Cow** — fill in a new cow's details live.
3. Submit — the **QR tag** appears immediately.
4. Show the QR **on the laptop screen**.
5. On a **phone**, open **Scan QR**, allow camera access, and scan the
   tag on the laptop screen.
6. The phone opens the **Cow Digital Passport** — walk through the
   health, vaccination, and production sections.
7. Tap **Found This Cow?** to show the lost-cow recovery flow, and
   submit a sample "found" report.
8. Return to the dashboard to show the total count updated and the
   new cow listed.

---

## 11. How the QR Flow Works

1. When a cow is registered, the server creates a QR image using the
   Python `qrcode` library.
2. The QR code encodes **only** the cow's public profile URL, e.g.
   `http://<host>:5000/cow/COW004` — never the full health report, and
   never the owner's private contact number.
3. Anyone who scans that QR code (with the app's own camera scanner,
   or any generic phone QR reader) is taken straight to `/cow/COW004`.
4. The Flask route `/cow/<cow_id>` looks up the cow in MySQL and
   renders the **Cow Digital Passport** page with live data — so the
   passport is always up to date, even if the underlying details
   change after the QR tag was printed.
5. The **Found This Cow?** section only reveals the registered
   location (not the owner's home address) and routes any finder
   contact information through a stored `found_reports` entry, rather
   than exposing the owner's number publicly.

---

## 12. Security Notes (Demo-Appropriate)

- All SQL queries use parameterized statements (`%s` placeholders) —
  no string-formatted SQL.
- Uploaded images are validated by extension (`png`, `jpg`, `jpeg`)
  and saved under a randomly generated filename.
- Database credentials are read from environment variables, never
  hard-coded or exposed to the frontend.
- The public cow profile never shows the owner's phone number
  directly.

This is a demo project and intentionally does not include user
authentication, HTTPS, or rate limiting — call this out if asked by
the panel, and mention these as "future scope" for the full Smart Farm
Management System.

---

## 13. Troubleshooting

| Problem | Likely Cause |
|---|---|
| `Access denied for user 'root'@'localhost'` | Wrong `DB_PASSWORD` in your environment. |
| `Unknown database 'cow_qr_demo'` | You haven't run `schema.sql` yet. |
| QR scan doesn't open the passport on a phone | `SITE_BASE_URL` is set to `localhost`, which the phone can't resolve — use your laptop's LAN IP instead. |
| Camera doesn't start on `/scan` | Most browsers require HTTPS or `localhost` for camera access; if testing over LAN IP from a phone, use Chrome and allow camera permission, or test on the same machine via `localhost`. |
