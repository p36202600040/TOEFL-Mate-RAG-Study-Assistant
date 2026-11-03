# Publikasi GitHub Desktop dan pembaruan VPS

## 1. Apa yang masuk repositori?

Source code, tests, requirements, `.env.example`, dokumentasi, dataset pertanyaan, laporan final, dan salinan evaluasi pada `evaluation/public/`.

Jangan unggah `.env`, secrets, PDF sumber tanpa izin, `chroma_db/`, virtual environment, cache, dan ZIP proyek. `.gitignore` tidak menghapus berkas yang terlanjur tracked atau tersimpan pada commit lama. Periksa history sebelum menjadikan repositori publik. Jika kredensial pernah masuk history, cabut/rotasi kredensial dahulu; jangan menganggap menghapus berkas sudah cukup.

Berkas V2 asli tetap lokal karena salah satunya memuat metadata akun pada error provider. `scripts/export_public_results.py` membuat salinan JSON publik tanpa pesan error mentah; metrik tidak diubah. Fingerprint dalam laporan final mengacu pada artefak asli, bukan salinan tersanitasi.

Dokumen utama untuk presentasi: `reports/methodology_evaluation_final_uts_20261103.pdf`. Laporan lama adalah arsip historis, bukan acuan terbaru.

## 2. GitHub Desktop: commit dan publish

1. Buka GitHub Desktop dan login ke akunmu.
2. Pilih **File > Add local repository**, lalu pilih folder proyek ini. Folder ini sudah merupakan repositori Git; tidak perlu membuat repository baru di dalamnya.
3. Pada tab **Changes**, periksa daftar dan diff. Pastikan tidak ada `.env`, PDF buku, database, ZIP, atau data akun. Berkas yang diabaikan normalnya tidak tampil sebagai perubahan baru.
4. Pilih perubahan yang memang ingin dikumpulkan. Pertahankan arsip jika dibutuhkan, tetapi jangan mengunggah berkas yang tidak dipahami isinya. Laporan PDF lama tetap ada; nyatakan PDF final sebagai rujukan.
5. Isi summary, misalnya `Siapkan prototipe TOEFL Mate dan laporan UTS`, lalu klik **Commit to ...** sesuai branch aktif.
6. Jika belum ada remote, klik **Publish repository**. Disarankan private dahulu untuk pemeriksaan isi dan history; tambahkan akses teman/dosen jika dibutuhkan. Jika sudah ada remote, gunakan **Push origin** setelah memastikan remote benar.
7. Buka **View on GitHub**; periksa source code, README, PDF final, dan akses repository. Jangan menempel token pada URL atau screenshot.

GitHub menyimpan source code; push repository belum membuat aplikasi berjalan di domain.

## 3. VPS aaPanel: clone pertama kali

Contoh Linux berikut menggunakan direktori `/www/wwwroot/toefl-mate`. Sesuaikan pengguna, path, dan branch; jangan menjalankan pemasangan sebagai root bila tidak diperlukan. Pengguna service harus dapat membaca proyek dan menulis data Chroma.

```bash
cd /www/wwwroot
git clone https://github.com/USERNAME/REPOSITORY.git toefl-mate
cd /www/wwwroot/toefl-mate
git branch --show-current
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
chmod 600 .env
```

Ganti USERNAME/REPOSITORY dengan URL repository kamu. Untuk repository private, gunakan autentikasi GitHub dengan SSH deploy key read-only atau metode kredensial yang sesuai; jangan masukkan token ke URL clone. Isi `.env` di server melalui editor yang aman. Jangan kirim isi `.env` ke chat atau GitHub.

Dependency belum dikunci versinya secara penuh. Perbedaan versi ChromaDB dan PyTorch dapat menyebabkan masalah; simpan versi lingkungan yang berhasil setelah diuji. CPU, RAM, ruang disk, dan waktu download model perlu diperiksa sebelum pemasangan.

## 4. Menyediakan indeks dan menjalankan smoke test

Git clone tidak membawa PDF sumber, model cache, `.env`, atau database vektor. Aplikasi belum siap menjawab hanya dengan clone.

- Pilihan yang disarankan: unggah dokumen yang diizinkan melalui saluran privat ke `data/`, lalu bangun indeks pada VPS menggunakan model yang sesuai. Proses ini dapat mengunduh model dan memerlukan waktu/RAM; lakukan setelah kapasitas dan izin dokumen diperiksa.
- Jalankan `python scripts/ingest_pdf.py` hanya saat memang siap membangun kandidat. Verifikasi hasil dan manifest, lalu atur `CHROMA_COLLECTION` pada `.env` ke nama kandidat. Kandidat tidak aktif otomatis.
- Jika memindahkan database lokal, hentikan penulisan dan buat backup terlebih dahulu; perhatikan kompatibilitas ChromaDB, permission, kelengkapan manifest, dan model. Menyalin database Windows ke Linux tidak dijamin berhasil; pembangunan ulang sering lebih jelas provenance-nya.

Uji lokal di VPS tanpa membuka port Streamlit ke internet:

```bash
source /www/wwwroot/toefl-mate/.venv/bin/activate
cd /www/wwwroot/toefl-mate
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
```

Perintah ini berjalan foreground dan berhenti saat terminal ditutup. Untuk produksi demo gunakan pengelola proses aaPanel seperti Supervisor/Python manager, dengan working directory proyek dan perintah absolut `.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true`. Jangan memasang API key pada command line. Aktifkan restart otomatis dan log lokal yang tidak dipublikasikan.

## 5. Domain dan reverse proxy

1. Arahkan DNS A `webnyaadam.my.id` ke IP VPS; pastikan tidak konflik dengan website yang sudah ada.
2. Tambahkan website di aaPanel dan konfigurasi reverse proxy menuju `http://127.0.0.1:8501`.
3. Pastikan reverse proxy meneruskan WebSocket; Streamlit membutuhkannya. Aktifkan sertifikat HTTPS pada aaPanel dan sesuaikan timeout proxy untuk respons model.
4. Jangan membuka port 8501 publik jika reverse proxy sudah digunakan. Jangan mematikan proteksi CORS/XSRF sebagai solusi awal.
5. Uji dari perangkat lain: halaman terbuka, chat tersambung, jawaban muncul, dan reload bekerja.

Sebelum dibagikan, batasi akses demo (misalnya autentikasi pada reverse proxy), pantau kuota Groq, dan batasi pengguna serentak. Aplikasi belum memiliki kuota pengguna atau proteksi biaya publik yang lengkap. Jangan mengekspos panel aaPanel atau API key.

## 6. Pembaruan berikutnya: pull, bukan clone ulang

Setelah commit dan **Push origin** di GitHub Desktop:

```bash
cd /www/wwwroot/toefl-mate
git status --short
git pull --ff-only
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Jika status memperlihatkan perubahan source code lokal VPS atau pull menolak divergensi, berhenti dan periksa; jangan memakai `git reset --hard` untuk menghilangkannya. `.env` yang ignored tidak ikut pull. Restart proses melalui Supervisor/Python manager setelah update dan lakukan smoke test. Perubahan source tidak berarti harus membangun ulang indeks; lakukan hanya jika perubahan embedding/ingestion memang memerlukannya, dengan kandidat dan backup.

## 7. Bukti sebelum rekam video

- Repository dan PDF final dapat diakses pihak yang dituju.
- Domain HTTPS berfungsi dari perangkat teman; tidak sekadar localhost.
- Indeks terisi, model sesuai, dan kuota API tersedia.
- Coba pertanyaan faktual, sitasi, klarifikasi follow-up, dan pertanyaan di luar dokumen.
- Jangan tampilkan `.env`, dashboard rahasia, token, atau pesan error provider mentah.
- Nyatakan metrik V2 sebagai hasil historis, bukan hasil evaluasi server VPS.
