# Klik Indomaret – Web Automation (Selenium + Python)

Automation test untuk Klik Indomaret **tanpa login (guest)** menggunakan
Selenium, Python, dan pytest.

## Skenario

1. Akses https://www.klikindomaret.com/
2. Tutup popup QR (jika muncul)
3. Buka menu Kategori, pilih meta kategori **Makanan**
4. Pilih kategori **Madu**
5. Pilih salah satu produk Madu
6. Masuk ke halaman produk detail
7. Klik tombol **+ Keranjang**
8. Verifikasi: guest diminta login (popup login muncul)

## Prasyarat

- Python 3.12+
- Google Chrome (versi terbaru)
- Koneksi internet

## Instalasi

```bash
git clone https://github.com/salmahadiatna/edts-automation
cd edts-automation

python -m venv .venv
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Menjalankan test

```bash
python -m pytest -v -s
```

> Gunakan flag `-s` agar log langkah dan pesan interaktif tampil di terminal.

### Mode attach ke Chrome yang sudah terbuka (direkomendasikan)

Situs dilindungi Cloudflare, jadi Chrome dijalankan dulu secara manual:

1. Tutup semua jendela Chrome.
2. Jalankan Chrome dengan remote debugging:
   ```powershell
   & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenium_profile"
   ```
3. Di Chrome tersebut, buka https://www.klikindomaret.com/ dan selesaikan
   verifikasi Cloudflare secara manual (cukup sekali).
4. Di terminal lain (venv aktif), jalankan:
   ```bash
   python -m pytest -v -s
   ```

### Mode launch (Chrome dibuka oleh Selenium)

```powershell
$env:ATTACH_CHROME = "0"
python -m pytest -v -s
```

[Sesuaikan: jelaskan di sini kalau kamu memakai profil yang sudah "dipanaskan"
atau SeleniumBase UC mode.]

## Catatan Cloudflare

Situs ini memakai Cloudflare untuk mendeteksi bot. Akibatnya:

- Challenge verifikasi bisa muncul di homepage maupun saat membuka halaman
  kategori (`/xpress/category/...`).
- Script **tidak mem-bypass** Cloudflare. Jika challenge muncul, test menunggu
  verifikasi diselesaikan secara manual, lalu melanjutkan otomatis.
- Cookie hasil verifikasi tersimpan di profil Chrome lokal (tidak di-commit).
- Test dijalankan **tanpa headless mode** karena headless lebih mudah diblokir.
- Hasil bisa bervariasi tergantung jaringan, IP, dan kebijakan Cloudflare saat itu.

## Struktur project

```
├── conftest.py            # fixture driver, hook screenshot saat gagal
├── helpers.py             # helper wait, klik, Cloudflare, popup
├── pytest.ini
├── requirements.txt
├── tests/
│   └── test_edts.py       # skenario utama
└── docs/evidence/         # contoh screenshot hasil run
```

## Teknik yang dipakai

- Explicit wait (`WebDriverWait`), tanpa `time.sleep`
- Screenshot otomatis saat test gagal
- Assertion di tiap tahap penting dan di hasil akhir
- Deteksi challenge Cloudflare dengan jeda manual yang eksplisit

## Hasil

Test dijalankan pada Windows, Python 3.12, Chrome 152: **PASSED**.
Contoh bukti ada di folder `docs/evidence/`.

## Keterbatasan

- Bergantung pada struktur HTML Klik Indomaret saat ini; perubahan UI dapat
  memerlukan penyesuaian selector.
- Challenge Cloudflare dapat memerlukan intervensi manual.
- Perilaku "+ Keranjang" untuk guest (popup login atau pilih lokasi) mengikuti
  kebijakan situs saat test dijalankan.

  ## Troubleshooting

Jika test gagal menemukan menu kategori atau tersangkut di Cloudflare:

1. Tutup semua proses `chrome.exe` (Task Manager).
2. Buka Chrome debugging dan hapus cache (Ctrl+Shift+Del, pilih
   "Cached images and files").
3. Buka klikindomaret.com secara manual, lewati verifikasi Cloudflare,
   lalu jalankan ulang test.