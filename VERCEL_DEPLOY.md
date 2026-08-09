# Deploying JobSwipe to Vercel (quick version)

This is the fast path: get it live on Vercel with minimal changes. Important
trade-off — **Vercel's filesystem resets on every cold start**, so:

- The SQLite database (`/tmp/jobswipe.db`) is wiped periodically → accounts,
  saves, and applications will occasionally disappear.
- Uploaded resumes/photos (`/tmp/uploads/`) are wiped the same way.

This is fine for a demo/prototype. For anything real, migrate to a hosted
Postgres (e.g. Vercel Postgres, Neon, Supabase) and object storage (e.g.
Vercel Blob, S3) — ask me and I'll wire that up.

## Steps

1. **Push this folder to a GitHub repo** (Vercel deploys from Git).
   ```
   cd JobSwipeVercel
   git init
   git add .
   git commit -m "JobSwipe for Vercel"
   git branch -M main
   git remote add origin https://github.com/<you>/jobswipe.git
   git push -u origin main
   ```

2. **Import the repo in Vercel**
   - Go to https://vercel.com/new
   - Select your repo
   - Framework preset: choose **Other** (this is a plain Python/Flask app)
   - Leave build/output settings as default — `vercel.json` handles routing

3. **Set an environment variable** (recommended)
   - In the Vercel project settings → Environment Variables, add:
     - `SECRET_KEY` = any long random string (used to sign session cookies)
   - Without this, sessions still work but reset on every deploy.

4. **Deploy.** Vercel will pick up `vercel.json` and `api/index.py`
   automatically as the Python entrypoint.

## What changed from the local version

- `db.py` and `app.py` now write to `/tmp` when the `VERCEL` env var is set
  (Vercel sets this automatically), instead of the project folder — Vercel's
  filesystem is read-only outside `/tmp`.
- `api/index.py` — the serverless entrypoint Vercel's Python runtime expects.
- `vercel.json` — routes all requests to the Flask app.
- `/static/<file>` is now served explicitly through Flask rather than relying
  on Vercel's static file detection, since the whole app is one function.

## Known limitations of this quick path

- Data resets periodically (see above).
- Cold starts: first request after inactivity will be slower (~1-2s) while
  the function spins up.
- `pdfplumber` (used for resume parsing) has some native dependencies —
  if the deploy fails on size limits, let me know and I'll swap in a lighter
  PDF text extractor.
