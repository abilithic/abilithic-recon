# 🚀 Panduan Push & Update ke GitHub — Abilithic Recon

> Jalankan semua perintah dari folder proyek:
> `cd "D:\Lab Kantor 2025\Github-Me\Project_1-Recon\abilithic-recon"`

---

## 0. Sekali saja: siapkan repo di GitHub
1. Buka https://github.com/new
2. Repository name: **abilithic-recon**
3. Visibility: **Public**
4. JANGAN centang "Add a README / .gitignore / license" (biar tidak bentrok).
5. Klik **Create repository**, lalu salin URL-nya
   (mis. `https://github.com/USERNAME/abilithic-recon.git`).

> Ganti `USERNAME` di perintah-perintah di bawah dengan username GitHub kamu.

---

## 1. Sekali saja: inisialisasi git lokal & push pertama
```bash
cd "D:\Lab Kantor 2025\Github-Me\Project_1-Recon\abilithic-recon"

git init
git add .
git commit -m "feat: Abilithic Recon v1.0.0 - initial release"
git branch -M main
git remote add origin https://github.com/USERNAME/abilithic-recon.git
git push -u origin main
```
Jika diminta login: izinkan popup browser Git Credential Manager, atau pakai
Personal Access Token (Settings > Developer settings > Tokens) sebagai password.

---

## 2. Sekali saja: rapikan tampilan repo (opsional tapi profesional)
- Buka repo > ⚙️ (samping "About") > isi Description + Website (LinkedIn) >
  tambahkan **Topics**:
  `cybersecurity, security-tools, osint, recon, subdomain-enumeration,
   attack-surface, shadow-it, windows, desktop-app, python`

---

## 3. Rilis v1.0.0 -> GitHub otomatis build .exe
Tag versi memicu workflow `.github/workflows/build.yml` (build .exe di runner
Windows, bikin checksum SHA-256, dan tempel ke halaman Releases).
```bash
git tag v1.0.0
git push origin v1.0.0
```
Lalu pantau di tab **Actions**. Setelah hijau, cek tab **Releases** -> file
`AbilithicRecon.exe` + `AbilithicRecon.exe.sha256.txt` sudah terlampir.

---

## 4. Alur UPDATE rutin (setiap ada perubahan)
```bash
cd "D:\Lab Kantor 2025\Github-Me\Project_1-Recon\abilithic-recon"

git add -A
git commit -m "fix: perbaiki X" 
git push
```

## 5. Merilis versi baru (mis. v1.1.0)
1. Update nomor versi di `abilithic_recon/__init__.py` (`__version__ = "1.1.0"`)
   dan di `version_info.txt` (filevers/prodvers + FileVersion/ProductVersion).
2. Catat perubahan di `CHANGELOG.md`.
3. Commit + push, lalu tag rilis:
```bash
git add -A
git commit -m "release: v1.1.0"
git push
git tag v1.1.0
git push origin v1.1.0
```

---

## Catatan penting
- **Folder `build/`, `dist/`, `.venv/` TIDAK ikut ter-push** (sudah di `.gitignore`).
  File `.exe` dikirim ke pengguna lewat **Releases** (hasil GitHub Actions), bukan via commit.
- **Jangan commit database GeoIP `.mmdb`** (sudah di-ignore; ukurannya besar/berlisensi).
- Pastikan link di README/aplikasi memakai path repo kamu. Kalau username/nama repo
  beda dari `abilithic/abilithic-recon`, cari-ganti dengan perintah ini (PowerShell):
  ```powershell
  Get-ChildItem -Recurse -Include *.md,*.py,*.yml |
    ForEach-Object { (Get-Content $_ -Raw) -replace 'abilithic/abilithic-recon','USERNAME/abilithic-recon' | Set-Content $_ }
  ```

## Perintah git harian yang berguna
```bash
git status            # lihat perubahan
git log --oneline -10 # riwayat commit
git pull              # tarik perubahan dari GitHub
git tag               # lihat daftar tag/rilis
```
