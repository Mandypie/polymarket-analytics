# Deploy Polymarket Analytics to Cloud

## Option 1: Streamlit Cloud (Easiest - Free)

1. Push your code to GitHub:
   ```bash
   cd "C:\Users\DALLAS COMPUTERS\polymarket-analytics"
   git init
   git add .
   git commit -m "Polymarket Analytics Demo"
   # Create repo on GitHub.com, then:
   git remote add origin YOUR_GITHUB_URL
   git push -u origin main
   ```

2. Go to https://streamlit.io/cloud
3. Click "New app"
4. Connect your GitHub repo
5. Select `demo_app.py` as main file
6. Click "Deploy"

**Result:** https://your-app.streamlit.app (FREE!)

---

## Option 2: Render.com (Also Free)

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Use these settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run demo_app.py --server.port $PORT --server.address 0.0.0.0`

**Result:** https://your-app.onrender.com (FREE!)

---

## Option 3: Railway.app (Free Tier)

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repo
4. Railway auto-detects Streamlit
5. Click "Deploy"

**Result:** https://your-app.railway.app (FREE!)

---

## Option 4: ngrok (Manual Download)

1. Download ngrok from https://ngrok.com/download
2. Extract and run: `ngrok http 8502`
3. Share the URL it gives you

---

## Option 5: Use the HTML (Fastest)

1. The HTML on your Desktop: `polymarket-demo.html`
2. Upload to https://app.netlify.com/drop
3. Share the URL

---

## Recommendation: Streamlit Cloud

**Why it's best:**
- ✅ Free hosting
- ✅ No setup needed
- ✅ Your actual working app (not HTML simulation)
- ✅ Professional URL (yourname.streamlit.app)
- ✅ Always available
- ✅ No tunneling needed

**Time to deploy: 5 minutes**