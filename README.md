<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&height=130&color=0:0ea5e9,100:22c55e&text=IT%20Support%20Automation%20Toolkit&fontSize=34&fontColor=ffffff&animation=fadeIn&fontAlignY=55" />
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=14&duration=2200&pause=700&color=22C55E&center=true&vCenter=true&width=860&lines=CLI+tool+untuk+health+check%2C+log+parsing%2C+dan+export+laporan;Disk+dan+RAM+dan+service+status+hingga+ringkasan+temuan;Output+CSV+atau+XLSX+untuk+monitoring+dan+ticketing" />
  <br/>
  <img src="https://skillicons.dev/icons?i=python&perline=1" />
</div>

---

## Deskripsi
**IT Support Automation Toolkit** adalah **CLI (Command Line Interface)** untuk mengecek kesehatan PC (**disk, RAM, CPU, service**), melakukan **parsing log** (filter error/keyword), dan mengekspor laporan ke **Excel (XLSX)** atau **CSV** agar dokumentasi troubleshooting lebih konsisten. Tool ini dipakai teknisi dengan alur: **pilih mode → ambil metrik sistem & status service → baca log & filter keyword → rangkum temuan → export CSV/XLSX → tampilkan ringkasan di terminal**, sehingga output bisa disimpan dan dilampirkan ke tiket atau arsip monitoring rutin.

---

## Lokasi Folder (sesuai permintaan)
Folder proyek disimpan dan dinamai **sesuai bahasa pemrograman**:
- **Windows**: `C:\Users\ASUS\Desktop\proyek\python`
- **Nama folder root**: `python`

> Catatan: Walau nama folder root menjadi `python`, modul CLI tetap dijalankan dengan `python -m toolkit` karena package-nya bernama `toolkit/`.

---

## Struktur Proyek
```text
python/
├─ main.py
├─ requirements.txt
├─ README.md
├─ sample_logs/
│  └─ app.log
└─ toolkit/
   ├─ __init__.py
   ├─ __main__.py
   ├─ cli.py
   ├─ system_health.py
   ├─ log_parser.py
   ├─ report.py
   └─ utils.py
```

---

## 🎯 Fitur Utama
- ✅ **System Health Check**: disk usage, RAM, CPU *(best-effort + fallback → `N/A` jika metrik tidak tersedia)*.
- ✅ **Service Check**:
  - **Windows**: via `psutil.win_service_get`
  - **Linux (systemd)**: via `systemctl is-active`
  - **Fallback**: jika tidak didukung, status = `unknown` *(tanpa crash)*.
- ✅ **Log Parsing**: streaming line-by-line, filter keyword (default `error`), simpan sample baris yang match.
- ✅ **Export**:
  - **XLSX**: 1 file multi-sheet *(Summary, SystemHealth, Services, LogFindings)*
  - **CSV**: beberapa file *(`summary.csv`, `system_health.csv`, `services.csv`, `log_findings.csv`)*
- ✅ **Aman dipakai**: validasi input path/file, handle file tidak ditemukan, permission error, dan error tak terduga.

---

## 🖼️ Preview
> Taruh file preview ini di repo kamu (mis. folder `assets/`) supaya README bisa menampilkan hasilnya.

- Terminal output (contoh): `assets/terminal_preview.png`  
- Contoh laporan: `assets/preview_report.xlsx`

```text
assets/
├─ terminal_preview.png
└─ preview_report.xlsx
```

Jika file sudah ada, tampilkan di README:
```md
![Terminal Preview](assets/terminal_preview.png)
```

---

## ✅ Requirements
- **Python 3.9+** (disarankan)
- **Dependencies**:
  - `psutil`
  - `openpyxl`

---

## 🛠️ Instalasi
Jalankan di folder root `python/` *(bukan `toolkit/`)*.

---

## Windows (PowerShell)
```powershell
cd C:\Users\ASUS\Desktop\proyek\python
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Linux/Mac
```bash
cd python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ✅ Cek berhasil
```bash
python -c "import psutil, openpyxl; print('OK')"
```

---

## ▶️ Cara Pakai (yang teknisi lakukan)

---

## 1) Jalankan menu (interaktif)
```bash
python -m toolkit
```

---

## 2) Langkah di menu (mode → cek → parse → export)
- Pilih mode
- (opsional) input nama service
- input file log
- input keyword (default `error`)
- export CSV / XLSX
- hasil laporan disimpan untuk dilampirkan ke tiket

---

## 3) Mode cepat (non-interaktif)

---

## A) Full workflow (health + log + export)
```bash
python -m toolkit run --log "sample_logs/app.log" --keywords error,failed,exception --out reports --export xlsx
```

---

## B) Cek health saja
```bash
python -m toolkit health --services "Spooler,wuauserv" --out reports --export xlsx
```

---

## C) Parse log saja
```bash
python -m toolkit parse-log --log "sample_logs/app.log" --keywords error,failed,exception --out reports --export csv
```

---

## 📥 Langkah Lengkap dari ZIP (Download → Extract → Run)

---

## 1) Download & Extract
- Download file ZIP: `it_support_automation_toolkit.zip` lalu extract.
- Contoh lokasi extract:
  - Windows: `C:\Projects\it_support_automation_toolkit`
  - Linux/Mac: `~/it_support_automation_toolkit`

---

## 2) Rename folder jadi `python` dan pindahkan
- Setelah extract, rename folder root menjadi `python`
- Pindahkan ke: `C:\Users\ASUS\Desktop\proyek\python`

---

## 3) Masuk folder proyek

---

## Windows (PowerShell)
```powershell
cd C:\Users\ASUS\Desktop\proyek\python
```

---

## Linux/Mac
```bash
cd ~/it_support_automation_toolkit
# atau path tempat kamu menyimpan folder "python"
```

---

## 4) Buat virtual environment + install dependency

---

## Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Linux/Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 5) Jalankan toolkit
```bash
python -m toolkit
```

---

## 6) Menu yang muncul
- Check system health
- Parse log
- Full workflow (health + log + export)
- Exit

---

## 7) Contoh alur teknisi (paling umum)
- Pilih **3 (Full workflow)**
- Export: `xlsx` (atau `csv`)
- Output folder: `./reports`
- Service (optional):
  - Windows: `Spooler,wuauserv`
  - Linux: `ssh,cron`
- Path log: `sample_logs/app.log`
- Keywords: `error,failed,exception`
- Output laporan otomatis masuk ke folder `reports/`.

---

## 📦 Output (Di mana hasil laporan tersimpan?)

---

## Jika `--export xlsx`
File `.xlsx` ada di folder output, contoh:
```text
reports/it_support_report_YYYYMMDD_HHMMSS.xlsx
```

---

## Jika `--export csv`
Dibuat folder run otomatis, misalnya:
```text
reports/it_support_report_YYYYMMDD_HHMMSS/
├─ summary.csv
├─ system_health.csv
├─ services.csv
└─ log_findings.csv
```

---

## 🧠 Alur Kerja
- User memilih mode
- Aplikasi mengambil metrik sistem & status service
- Membaca file log dan memfilter error/keyword
- Merangkum temuan (jumlah match & sample baris)
- Menyimpan hasil ke CSV atau XLSX
- Menampilkan ringkasan di terminal

---

## 🧯 Troubleshooting (Error umum & solusi)

---

## “python is not recognized” (Windows)
Install Python dan centang **Add Python to PATH**, atau gunakan:
```powershell
py -m venv .venv
py -m toolkit
```

---

## “openpyxl not available”
Dependency belum terinstall:
```bash
pip install -r requirements.txt
```

---

## Log file tidak ketemu
Pastikan path benar. Contoh aman:
```bash
python -m toolkit parse-log --log "sample_logs/app.log" --out reports --export xlsx
```

Jika path ada spasi (Windows):
```powershell
python -m toolkit parse-log --log "C:\Logs\app log.txt" --out reports --export xlsx
```

---

## 🧩 Catatan Teknis (Best-Effort & Fallback)
Tool ini dibuat agar tidak crash:
- Jika metrik tidak bisa diambil → nilai jadi `N/A`
- Jika service check tidak didukung → status `unknown`
- Jika file log tidak ditemukan → muncul error yang jelas *(File not found)* dan program berhenti dengan aman

---
