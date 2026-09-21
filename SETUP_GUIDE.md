# 💻 TubePulse US — Laptop Setup & Running Guide

Complete step-by-step instructions to run TubePulse US on your **Windows**, **Mac**, or **Linux** laptop with **100% full autonomous automation**.

---

## ⚡ Quick Start (Under 3 Minutes)

### 1. Prerequisites
Make sure you have installed on your laptop:
* **Python 3.10 or higher**: [Download from python.org](https://www.python.org/downloads/) (Make sure to check *"Add Python to PATH"* during Windows installation).
* **Git**: [Download from git-scm.com](https://git-scm.com/)

---

### 2. Download the Code

Open your terminal or command prompt:

```bash
git clone https://github.com/shivyse/auto-reply.git
cd auto-reply
git checkout arena/01a0c218-auto-reply
```

---

### 3. Create a Virtual Environment & Install Dependencies

#### On macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### On Windows (PowerShell or Command Prompt):
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

*(Note: `imageio-ffmpeg` is included in `requirements.txt`, meaning a high-performance FFmpeg binary is automatically provided—no complex manual FFmpeg installation required!)*

---

### 4. Start the 100% Autonomous Studio

Run one command:

```bash
python app.py
```

You will see:
```text
INFO:TubePulseDaemon:🚀 Autonomous Autopilot Daemon thread started!
INFO:TubePulseDaemon:Autopilot daemon successfully launched with 60m interval.
🤖 24/7 Fully Autonomous Autopilot Daemon Active! (Zero Manual Work Required)
Starting TubePulse US Web Dashboard on http://0.0.0.0:5000...
```

Now open your web browser and go to:
👉 **`http://localhost:5000`**

---

## 🤖 How the Automation Works on Your Laptop

Once `python app.py` is running:
1. **Zero Work Required**:
   * The background worker thread (`engine/daemon.py`) runs automatically every hour (or scheduled drops at 12:00 PM & 5:30 PM EDT).
   * It automatically:
     - Researches high-curiosity macroeconomic/mystery topics.
     - Writes open-loop retention scripts.
     - Synthesizes the 20–25yo conversational voiceover.
     - Renders the hand-drawn stick figure animation & kinetic text in 1080p MP4.
     - Generates high-CTR thumbnails.
     - Packages complete SEO tags and pushes to the scheduled YouTube queue.
2. **Channel Evolution (Shorts ➔ Hybrid)**:
   * **Phase 1 (Days 1–5 / <500 subscribers)**: Uploads only rapid YouTube Shorts (9:16).
   * **Phase 2 (500+ subscribers reached)**: Automatically switches to uploading **both Shorts and Long-Form Videos (16:9 deep dives)**.

---

## 🖥️ Running in the Background (Close Terminal & Let It Run)

If you want the automation to run silently on your laptop even when you close the terminal window:

### On macOS / Linux (using `nohup` or `screen`):
```bash
nohup python3 app.py > tubepulse.log 2>&1 &
```
*To stop it later:* `pkill -f "python3 app.py"`

### On Windows (Run in Background via PowerShell):
```powershell
Start-Process python -ArgumentList "app.py" -WindowStyle Hidden
```
*To stop it later:* In Task Manager or PowerShell: `Stop-Process -Name python`

---

## 🔑 Direct YouTube Auto-Posting (Optional)

If you want videos automatically uploaded directly to your YouTube channel rather than saved locally:

1. Create a free Google Cloud project and enable the **YouTube Data API v3**.
2. Create an **OAuth 2.0 Client ID** (Desktop Application).
3. Create a file named `youtube_credentials.json` in the project root:
```json
{
  "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
  "client_secret": "YOUR_CLIENT_SECRET",
  "refresh_token": "YOUR_REFRESH_TOKEN"
}
```
*Once this file exists, the background daemon will automatically publish directly to your YouTube channel!*

---

## 🛠️ Handy CLI Commands

* **Check current channel growth phase & stats:**
  ```bash
  python app.py --status
  ```
* **Trigger an immediate autonomous production drop:**
  ```bash
  python app.py --autopilot
  ```
* **Advance to the next day:**
  ```bash
  python app.py --advance-day
  ```
* **Generate a single custom video manually:**
  ```bash
  python app.py --cli --topic "The (Greatest) Financial Hack in History" --niche finance --format shorts
  ```
