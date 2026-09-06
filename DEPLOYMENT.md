# Deployment Guide — Real-World Daily Production Setup

This guide provides step-by-step instructions to deploy the **Staff Attendance, GPS Location & Selfie Portal** for real-world daily use by employees and administrators on their smartphones, tablets, and computers.

---

## ⚠️ Mandatory Prerequisite: HTTPS (SSL)
All modern mobile browsers (Google Chrome on Android, Apple Safari on iOS) **strictly block Camera and GPS Geolocation access on non-HTTPS websites**. 
Therefore, your production deployment must run over **HTTPS (`https://`)**. All options below include **100% free SSL certificates** (via Let's Encrypt, Cloudflare, or Vercel).

---

## Architecture Overview

```
Mobile / Desktop Device (Staff & Admin)
         │
         ▼ (HTTPS)
   Nginx / Cloud CDN (Port 443)
   ┌─────┴────────────────────────┐
   │                              │
   ▼                              ▼
React Single Page App        Flask Backend (Gunicorn)
(/var/www/.../dist)          (127.0.0.1:5000)
                                  │
                                  ▼
                             MySQL 8.0
                      (logistics_attendance)
```

---

## Option 1: Dedicated Linux Cloud VPS (Recommended for Companies)
*Providers: DigitalOcean Droplet ($4–$6/mo), AWS Lightsail ($3.50/mo), Hetzner (€3.50/mo), or Hostinger VPS.*

This is the cleanest and most cost-effective solution for a single company:
- Fixed, predictable monthly price.
- Everything runs on one server (MySQL + Flask + React + Nginx + Let's Encrypt).
- Uploaded selfie photos stay safely on your server's local disk.
- Fast, low-latency database queries.

### Step 1: Provision a Server
Create an **Ubuntu 22.04 or 24.04 LTS** server and connect via SSH:
```bash
ssh root@your-server-ip
```

### Step 2: Install System Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv mysql-server nginx certbot python3-certbot-nginx git nodejs npm
```

### Step 3: Configure MySQL Database
1. Run secure installation:
   ```bash
   sudo mysql_secure_installation
   ```
2. Log into MySQL:
   ```bash
   sudo mysql -u root -p
   ```
3. Create database and production user:
   ```sql
   CREATE DATABASE logistics_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'logistics_user'@'localhost' IDENTIFIED BY 'YourStrongPassword123!';
   GRANT ALL PRIVILEGES ON logistics_attendance.* TO 'logistics_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

### Step 4: Clone Code and Setup Database Schema
```bash
sudo mkdir -p /var/www/logistics-attendance
sudo chown -R $USER:$USER /var/www/logistics-attendance
cd /var/www/logistics-attendance

# Clone your project repository here or upload the files
# Import schema and initial seed data:
mysql -u logistics_user -p logistics_attendance < database/schema.sql
mysql -u logistics_user -p logistics_attendance < database/seed.sql
```

### Step 5: Setup Python Backend Environment
```bash
cd /var/www/logistics-attendance/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create production .env file:
cat << 'EOF' > .env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=logistics_attendance
DB_USER=logistics_user
DB_PASSWORD=YourStrongPassword123!
JWT_SECRET=generate_a_random_64_character_secret_key_here
TIMEZONE=Asia/Kolkata
STANDARD_WORK_MINUTES=480
FLASK_ENV=production
EOF
```

### Step 6: Configure Systemd Background Service
Copy the provided service file:
```bash
sudo cp /var/www/logistics-attendance/deploy/attendance-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now attendance-backend
sudo systemctl status attendance-backend
```

### Step 7: Build React Frontend
```bash
cd /var/www/logistics-attendance/frontend
npm install
npm run build
```

### Step 8: Setup Nginx and Let's Encrypt SSL
1. Point your domain (e.g., `attendance.yourcompany.com`) to `your-server-ip` in your DNS manager (GoDaddy, Cloudflare, Namecheap, etc.) by creating an **A Record**.
2. Copy the Nginx configuration:
   ```bash
   sudo cp /var/www/logistics-attendance/deploy/nginx.conf /etc/nginx/sites-available/attendance
   # Edit domain name inside the file:
   sudo nano /etc/nginx/sites-available/attendance
   sudo ln -s /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo nginx -t
   sudo systemctl restart nginx
   ```
3. Generate 100% Free SSL Certificate:
   ```bash
   sudo certbot --nginx -d attendance.yourcompany.com
   ```

**Done!** Your staff can now open `https://attendance.yourcompany.com` from any mobile browser (Chrome/Safari), install it to their home screen as a Web App, and check in with live selfie camera & GPS.

---

## Option 2: Managed Cloud Platform (Render + Vercel + Aiven)
*Best if you do not want to manage a Linux server.*

1. **Database**: Create a free MySQL database on [Aiven.io](https://aiven.io/) or [Railway.app](https://railway.app/).
   - Import `database/schema.sql` and `database/seed.sql` using MySQL Workbench or DBeaver.
2. **Backend**: Deploy `backend/` to [Render.com](https://render.com/) (Web Service).
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()"`
   - Set Environment Variables: `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`, `JWT_SECRET`, `TIMEZONE=Asia/Kolkata`.
3. **Frontend**: Deploy `frontend/` to [Vercel](https://vercel.com/) (React / Vite).
   - Set Environment Variable: `VITE_API_URL=https://your-backend.onrender.com/api`
   - The included `vercel.json` will automatically handle SPA routing.

---

## Option 3: Free Instant Test on Real Devices (Cloudflare Tunnel)
If you want your employees to test the portal on their real devices **right now** without purchasing a server yet:
1. Run this command on your machine:
   ```powershell
   npx -y cloudflared tunnel --url http://localhost:5173
   ```
2. Cloudflare will give you a public secure URL (e.g. `https://random-name.trycloudflare.com`).
3. Share that URL with your staff. It has valid HTTPS, so Camera and GPS will work on any iPhone and Android phone anywhere in the world!
