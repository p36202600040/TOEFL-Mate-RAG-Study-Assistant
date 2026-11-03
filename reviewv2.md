# Review V2 — TOEFL Mate RAG Study Assistant

**Tanggal review:** 30 Oktober 2026  
**Landasan:** `PRD — TOEFL Mate RAG Study Assistant.md`  
**Objek:** implementasi di workspace, indeks lokal, artefak evaluasi, laporan PDF, dan pengujian interaktif aplikasi.  
**Kesimpulan:** fondasi MVP sudah kuat dan pipeline benar-benar berjalan, tetapi kualitas retrieval dan kelengkapan validasi belum memenuhi seluruh kriteria penerimaan PRD.

## 1. Ringkasan nilai dan progres

| Indikator | Penilaian | Makna |
|---|---:|---|
| **Skor keseluruhan** | **72/100** | Penilaian reviewer berbasis rubrik di bawah, bukan nilai resmi dosen atau skor akurasi model. |
| **Estimasi progres menuju MVP yang diterima PRD** | **sekitar 80%** | Mayoritas komponen dan deliverable sudah ada; validasi kualitas, konsistensi dokumentasi, serta video masih perlu dituntaskan. Ini estimasi milestone, bukan persentase baris kode. |
| Kesiapan demo terbatas | Cukup siap, dengan catatan | Aplikasi aktif dan beberapa interaksi berhasil; skenario utama berbahasa Indonesia masih dapat gagal menemukan materi dasar. |
| Kesiapan klaim kualitas akademik | Belum lengkap | Evaluasi jawaban LLM tersimpan belum berhasil, penilaian manusia belum dilakukan, dan retrieval masih rendah. |
| Kesiapan produksi | Di luar lingkup | PRD memang tidak mewajibkan autentikasi, deployment produksi, atau multi-user. Tidak dikurangi karena fitur tersebut belum ada. |

**Penilaian singkat:** ini bukan sekadar mockup chatbot. Ingestion, embedding lokal, ChromaDB, prompt, Groq, UI, dan evaluasi retrieval sudah nyata. Namun, “pipeline berjalan” belum sama dengan “asisten belajar sudah andal”. Pekerjaan terpenting sekarang bukan menambah fitur, melainkan meningkatkan keberhasilan pencarian materi dan membuktikan kualitas jawaban.

### Rubrik skor

| Aspek | Bobot | Skor | Alasan |
|---|---:|---:|---|
| Arsitektur dan ingestion | 20 | 18 | Modul terpisah, metadata halaman terpelihara, indeks persisten dan multi-dokumen tersedia; rebuild belum aman terhadap kegagalan. |
| Retrieval dan grounded generation | 20 | 12 | Alur nyata dan Groq aktif, tetapi Recall@5 hanya 32% dan pertanyaan inti Indonesia mengalami penolakan keliru. |
| UI dan kontrol SOP | 15 | 13 | Kontrol bahasa, gaya, kesulitan, top-k, sumber, riwayat, dan hapus percakapan tersedia; akses halaman dan pemulihan error belum lengkap. |
| Evaluasi dan validitas eksperimen | 20 | 9 | Dataset serta perbandingan retrieval tersedia; seluruh jawaban pada dua run tersimpan kosong, metrik manual belum dinilai, parser sitasi belum konsisten. |
| Pengujian dan reproduksibilitas | 10 | 8 | 49 test lulus dan dependency check bersih; belum ada bukti instalasi bersih, versi tidak dikunci, pengujian integrasi masih terbatas. |
| Dokumentasi, laporan, dan demo | 10 | 8 | README, PDF, dan outline tersedia, tetapi sebagian klaim/config sudah tidak mengikuti kondisi aktual. Video final belum ditemukan dalam workspace. |
| Rahasia dan copyright | 5 | 4 | `.env` serta PDF sumber tidak tercatat pada pemeriksaan Git saat ini; masih perlu penguatan sanitasi error dan pembatasan reproduksi panjang. |
| **Total** | **100** | **72** | Skor dibatasi terutama oleh bukti kualitas dan validasi, bukan oleh kelengkapan tampilan. |

## 2. Metode dan batas pemeriksaan

Review dilakukan melalui:

1. Pembacaan PRD, README, `review.md`, source code, test, dataset, dan generator laporan.
2. Menjalankan ulang `python -m pytest tests/ -q` dan `python -m pip check`.
3. Memeriksa HTTP aplikasi lokal dan endpoint kesehatan Streamlit.
4. Menggunakan `streamlit.testing.v1.AppTest` untuk menjalankan aplikasi, mengirim tiga pertanyaan, mengganti pengaturan, dan menghapus percakapan. Pengujian ini memakai indeks serta Groq aktual, bukan mock jawaban.
5. Menjalankan ulang retrieval atas 25 pertanyaan berlabel untuk top-k 5 dan 3, tanpa generasi massal dan tanpa menimpa hasil evaluasi lama.
6. Memeriksa jumlah chunk, sumber dalam ChromaDB, beberapa halaman PDF sumber, teks laporan PDF, daftar file Git saat ini, dan daftar nama file dalam ZIP pengumpulan.

**Batas penting:** alat kendali Chrome tidak tersedia. Karena itu, tidak ada klaim telah menguji browser secara visual, responsivitas mobile, atau screenshot. HTTP 200 hanya membuktikan layanan merespons; bukti interaksi berasal dari AppTest. Instalasi bersih, audit seluruh riwayat Git, verifikasi manusia seluruh dataset, dan penilaian semua jawaban belum dilakukan. Tidak ada source aplikasi atau hasil evaluasi lama yang diubah untuk review ini.

## 3. Bukti pengujian aktual

### 3.1 Lingkungan dan layanan

| Pemeriksaan | Hasil |
|---|---|
| Python | `3.13.6` pada Windows; berbeda dari rekomendasi Python 3.11 di PRD, tetapi didokumentasikan di README. |
| Unit test | **49 passed, 2 warnings**, selesai dalam **13,98 detik**. |
| Dependensi | `No broken requirements found.` |
| `http://localhost:8501` | HTTP **200**. |
| `http://localhost:8501/_stcore/health` | HTTP **200**, respons `ok`. |
| Inisialisasi AppTest | Tidak ada exception; indeks dan konfigurasi API terbaca. |
| Model aktif yang ditampilkan | `openai/gpt-oss-120b`. |
| Indeks aktual | **4.156 chunk**: 3.911 dari Official Guide dan 245 dari modul CFLT. |
| PDF aktual di `data/` | Official Guide **668 halaman**, modul CFLT **70 halaman**. |

Dua warning test berasal dari perubahan API pytest/AnyIO dan penamaan metode Sentence Transformers. Keduanya tidak menggagalkan tes, tetapi perlu diperhatikan saat memperbarui dependensi.

### 3.2 Skenario interaktif

Ketiga pertanyaan dikirim berurutan dalam satu sesi. Skenario ketiga memakai bahasa jawaban `English` dan gaya `ringkas`.

| Skenario | Hasil aktual | Penilaian |
|---|---|---|
| `Apa saja 4 bagian tes TOEFL iBT dan berapa rentang skornya?` | Menjawab: `Informasi ini tidak ditemukan dalam dokumen sumber yang tersedia.` Retrieval mengambil halaman 526, 525, 476, 346, 544. Waktu keseluruhan rerun sekitar 2,910 detik, termasuk pemuatan awal embedding. | **Gagal membantu pertanyaan inti.** Jawaban tersedia di halaman PDF 35, tetapi konteks tersebut tidak ditemukan. Ini penolakan keliru karena retrieval, bukan bukti bahwa isi buku tidak memuat jawabannya. |
| `Berapa biaya pendaftaran tes TOEFL tahun 2025 di Jakarta dalam Rupiah?` | Menjawab bahwa informasi tidak ditemukan. Waktu rerun sekitar 1,135 detik. | **Berhasil untuk satu contoh out-of-scope.** Tidak boleh digeneralisasi menjadi OOS handling 100%. |
| `What is the preparation time and response time for Independent Speaking Question 1 in the 2012 guide?` | Menjawab **15 seconds** persiapan dan **45 seconds** respons; menyertakan rujukan halaman 183 dengan tanda kurung Unicode. | **Berhasil secara fungsional**, jawaban sejalan dengan acuan durasi pada dataset. Validitas dukungan setiap klaim pada halaman 183 belum dinilai penuh. Format sitasinya tidak terbaca parser evaluasi saat ini. |
| Ganti bahasa dan gaya | Pergantian selectbox berhasil tanpa exception; jawaban berikutnya berbahasa Inggris. | Kontrol dasar berjalan; belum membuktikan seluruh kombinasi tingkat kesulitan. |
| Hapus percakapan | `messages` dan `sources` kembali menjadi daftar kosong, tanpa exception. | **Lulus.** |

Waktu AppTest di atas bukan latency murni Groq dan bukan benchmark browser. Hanya tiga contoh generation yang diuji; tidak dihitung sebagai akurasi keseluruhan aplikasi.

### 3.3 Evaluasi retrieval yang dapat direproduksi

| Konfigurasi | Pertanyaan berlabel | Query dengan minimal satu halaman target | Recall/Hit@K | Precision@K |
|---|---:|---:|---:|---:|
| `top_k=5` | 25 | 8 | **0,3200** | **0,1040** |
| `top_k=3` | 25 | 6 | **0,2400** | **0,1333** |

Angka tersebut berhasil direproduksi pada indeks aktual dan cocok dengan ringkasan hasil tersimpan. Dengan definisi proyek, Recall@5 adalah proporsi query yang menemukan sedikitnya satu halaman target, lebih dekat dengan **Hit Rate@5** daripada recall atas seluruh item relevan. Definisi ini diperbolehkan oleh PRD selama dijelaskan.

Interpretasi yang tepat:

- Top-k 5 menambah keberhasilan sebanyak **2 dari 25 query**, atau **8 poin persentase** dibanding top-k 3; kenaikan relatifnya sekitar **33,3%**.
- Namun, **17 dari 25 query** belum menemukan halaman berlabel pada top-5. Ini kelemahan substantif untuk asisten belajar.
- Label halaman belum tentu mencakup semua lokasi jawaban yang valid. Karena itu, retrieval miss menurut label tidak otomatis membuktikan jawaban pasti salah.
- Precision saat ini menggunakan kecocokan nomor halaman untuk setiap chunk, bukan relevansi semantik chunk yang dinilai manusia. Angka 10,4% bukan probabilitas kebenaran jawaban.
- Kenaikan dua query belum cukup untuk menyebut perbedaan “signifikan” secara statistik.

### 3.4 Status evaluasi generation yang tersimpan

`evaluation/results.json` dan `evaluation/results_k3.json` mencatat run tanggal **28 Oktober 2026**, dengan model konfigurasi `llama-3.1-8b-instant`.

Pada **masing-masing** berkas:

- Ada 30 pertanyaan, tetapi **0 jawaban nonkosong**.
- Seluruh 30 item mencatat `GROQ_API_KEY tidak dikonfigurasi di file .env`.
- Citation accuracy, OOS handling, dan latency belum menghasilkan angka generation yang valid.
- Seluruh item berstatus `NOT_RATED` untuk answer correctness dan groundedness.

**Maknanya:** API yang aktif sekarang tidak membuat run lama otomatis valid. Bukti terkini menunjukkan generation dapat berjalan pada beberapa interaksi, sedangkan artefak evaluasi massal masih berstatus retrieval-only secara praktis. Hasil lama cukup transparan tentang kendalanya, tetapi belum memenuhi bukti kualitas end-to-end.

## 4. Kesesuaian terhadap PRD

| Persyaratan | Status | Bukti dan sisa pekerjaan |
|---|---|---|
| FR-01 — ingestion terpisah, metadata, halaman | Sebagian besar terpenuhi | `scripts/ingest_pdf.py`, `src/ingestion.py`, dan indeks aktual tersedia; halaman 1-based dipertahankan. Rebuild perlu dibuat aman sebelum dianggap andal. |
| FR-02 — retrieval, generation, top-k, threshold | Terimplementasi, kualitas belum memadai | ChromaDB dan Groq nyata; konfigurasi tersedia; retrieval pada pertanyaan Indonesia masih rendah. |
| FR-03 — UI Indonesia, proses, sumber, error | Sebagian besar terpenuhi | UI, spinner, expander sumber, serta validasi indeks/key ada. Belum ada pembuka halaman PDF langsung, dan exception retrieval belum ditangani di UI. |
| FR-04 — bahasa, gaya, kesulitan, grounding, label AI | Implementasi tersedia, validasi parsial | Semua kontrol ada; aturan grounding dan label latihan ada di prompt. Konsistensi seluruh perilaku belum diuji. |
| FR-05 — rahasia dan copyright | Sebagian besar terpenuhi | Ignore file dan disclaimer tersedia; perlu sanitasi error menyeluruh serta batas output untuk permintaan reproduksi panjang. |
| Dataset 30 pertanyaan sesuai komposisi | Struktur terpenuhi | 10 faktual, 10 konseptual, 5 sitasi, 5 OOS; ada jawaban acuan, halaman, catatan. Bukti siapa/kapan memverifikasi manusia belum tercatat eksplisit. |
| Metrik retrieval aktual | Terpenuhi dengan batas definisi | Hasil tersimpan dan pengulangan cocok; label masih tingkat halaman. |
| Metrik citation, OOS, latency generation | Belum lengkap | Run tersimpan gagal pada seluruh generation. Tiga interaksi review bukan pengganti full evaluation. |
| Answer correctness dan groundedness | Belum terpenuhi sebagai hasil | Field tersedia tetapi seluruhnya belum dinilai; rubrik groundedness perlu dipertegas. |
| Unit test | Terpenuhi | 49 test lulus; belum menguji seluruh jalur error/integrasi. |
| Laporan metodologi PDF | Ada, belum final | PDF empat halaman dapat dibaca dan memuat status metrik belum tersedia, tetapi narasi sumber/config tidak mengikuti aplikasi aktual. |
| README Windows dan reproduksibilitas | Sebagian besar terpenuhi | Perintah utama lengkap; belum dibuktikan di lingkungan bersih dan ada ketidaksinkronan model/jumlah chunk. |
| Outline demo maksimal 5 menit | Terpenuhi sebagai panduan | `reports/demo_outline.md` tersedia; `review.md` juga berupa panduan presentasi, bukan review kualitas. |
| Video demo final | Belum terverifikasi | Tidak ditemukan dalam workspace; bisa saja tersedia di luar proyek. |
| Tidak ada secret di source control | Pemeriksaan saat ini mendukung, bukan audit penuh | `.env`, PDF sumber, dan indeks tidak muncul dalam hasil `git ls-files` untuk target tersebut. Riwayat Git belum diaudit. |

**Keputusan penerimaan:** belum layak dinyatakan memenuhi seluruh acceptance criteria. Hambatan utamanya adalah validasi, keandalan retrieval, dan konsistensi bukti, bukan kekurangan komponen dasar.

## 5. Temuan prioritas

### P0-1 — Retrieval Indonesia belum andal untuk materi paling dasar

**Bukti:** skenario empat bagian TOEFL ditolak, padahal halaman PDF 35 memuat empat bagian beserta skornya. `fact_01` pada artefak lama juga gagal mengambil halaman target. Recall@5 hasil pengulangan tetap 32%.

**Lokasi:** `src/embeddings.py`, `src/retriever.py`, `src/ingestion.py`.

**Hipotesis:** model `all-MiniLM-L6-v2` kurang cocok untuk pencarian lintas bahasa Indonesia–dokumen Inggris; chunk 500 karakter dapat memutus konteks. Ini penjelasan yang masuk akal, belum hasil eksperimen kausal.

**Rekomendasi:** bandingkan satu perubahan terkendali terlebih dahulu: model embedding multibahasa atau penerjemahan query ke Inggris. Bangun indeks eksperimen terpisah jika mengganti embedding. Setelah itu, pertimbangkan chunk berbatas paragraf/kalimat, hybrid search, atau reranking bila masih diperlukan. Jangan hanya memperbesar top-k tanpa pengukuran.

### P0-2 — Full evaluation generation belum selesai

**Bukti:** kedua run tersimpan memiliki 30 error API key dan nol jawaban, walaupun Groq bekerja saat review.

**Rekomendasi:** jalankan baseline dan variasi baru dengan konfigurasi aktual, simpan sebagai berkas baru agar hasil lama tetap dapat diaudit. Catat model efektif, jumlah request berhasil/gagal, tanggal, kondisi indeks, bahasa, prompt, serta parameter generation. Lanjutkan penilaian manusia dan bangun ulang laporan dari run baru.

### P0-3 — Format sitasi prompt, output model, dan parser tidak sinkron

**Lokasi:** `src/prompts.py:43-46`, `src/evaluation.py:70-75`.

Prompt mengizinkan `[Halaman X]` maupun `[Nama Dokumen, Halaman X]`, sedangkan parser hanya mengenali `[Halaman X]` atau `[Page X]`. Pada review, jawaban aktual memakai `【Halaman 183】` dengan spasi Unicode. Pengujian parser terhadap format bernama dokumen dan bentuk Unicode tersebut menghasilkan daftar kosong.

**Dampak:** sitasi yang terlihat oleh pengguna dapat tidak terhitung. Sebaliknya, pencocokan halaman saja tidak membuktikan klaim didukung teks. Karena ada dua dokumen, nomor halaman tanpa identitas sumber juga ambigu.

**Rekomendasi:** tentukan format sitasi kanonis yang menyertakan `source` dan `page`, normalisasi output, uji parser terhadap variasi nyata, serta verifikasi pasangan sumber-halaman terhadap konteks retrieval. Laporkan citation validity, citation coverage, dan pemeriksaan dukungan klaim secara terpisah jika memungkinkan.

### P0-4 — Rebuild indeks menghapus koleksi aktif sebelum input tervalidasi

**Lokasi:** `scripts/ingest_pdf.py:79-100`.

Koleksi lama dihapus sebelum seluruh PDF berhasil dibaca dan di-embed. Path PDF yang tidak ada atau kegagalan ingestion dapat meninggalkan indeks kosong/parsial. Error per file dicetak lalu proses berlanjut; tidak ada exit code gagal yang konsisten untuk kondisi seluruh dokumen gagal.

**Rekomendasi:** validasi input terlebih dahulu, bangun koleksi sementara, verifikasi jumlah chunk, lalu alihkan koleksi aktif setelah sukses. Pertahankan indeks lama bila build gagal. Temuan ini berasal dari alur kode; ingestion destruktif tidak dijalankan saat review.

### P1-1 — Agregasi metrik dan definisi latency perlu diperbaiki

**Lokasi:** `src/evaluation.py:166-175, 193-250`.

- Citation accuracy agregat adalah rata-rata skor per jawaban yang memiliki sitasi, bukan rasio seluruh sitasi benar terhadap seluruh sitasi diperiksa seperti definisi ringkasan. Pilih dan dokumentasikan macro atau micro secara konsisten.
- Jawaban tanpa sitasi tidak masuk denominator citation agregat; akurasi dapat tampak baik meski cakupan sitasi buruk.
- `has_generation` hanya memeriksa apakah ada satu jawaban nonkosong. Pada run campuran sukses/gagal, angka ringkasan perlu denominator dan status error yang lebih jelas.
- Latency bersumber dari `generate_answer`, bukan keseluruhan retrieval sampai jawaban. Cold start embedding tidak ikut; tahap error tertentu bernilai nol.
- Deteksi OOS berbasis frasa dapat menandai jawaban sebagai benar walaupun jawaban juga memberikan fakta yang tidak didukung.

**Rekomendasi:** pisahkan latency retrieval, generation, dan end-to-end; laporkan sukses/gagal serta cold/warm. Tambahkan penilaian OOS berbasis rubrik, bukan hanya frasa. Simpan konteks/snapshot indeks agar groundedness bisa diaudit setelah indeks berubah.

### P1-2 — Konfigurasi model dan dokumentasi tidak konsisten

**Lokasi:** `config.py:41`, `app.py:203`, `src/generator.py:53`, `README.md`, `review.md`, `scripts/build_report.py`.

- Default config/UI menyebut `qwen/qwen3.8-27b`, fallback generator `openai/gpt-oss-120b`, README dan run lama `llama-3.1-8b-instant`; diagram README juga menyebut keluarga model lain.
- Model aktif saat review adalah `openai/gpt-oss-120b`; ini tidak memverifikasi ketersediaan semua nama fallback.
- README dan panduan demo menyebut 3.911 chunk/satu buku, sedangkan indeks aktif sudah 4.156 chunk/dua dokumen.
- PDF dan generator laporan menyebut keterbatasan “satu dokumen”, tidak sesuai implementasi multi-dokumen saat ini.
- Klaim inferensi “sub-detik” pada `review.md` tidak didukung benchmark end-to-end yang memadai. Embedding lokal juga tidak berarti tidak ada isi dokumen yang dikirim keluar: chunk retrieval memang dikirim ke Groq.

**Rekomendasi:** gunakan satu resolusi konfigurasi model untuk UI, generator, dan evaluasi; catat model efektif dari hasil generation. Sinkronkan README, laporan, dan naskah dengan sumber serta angka hasil run yang digunakan. Bedakan “embedding lokal” dari “generation melalui API eksternal”.

### P1-3 — Pemulihan error UI dan perlindungan output masih parsial

**Lokasi:** `app.py:177-204`, `src/retriever.py:109-124`, `src/generator.py:65-74, 105-117`.

Pemanggilan retrieval di UI belum dibungkus penanganan error. Kegagalan embedding atau query kedua setelah fallback dapat keluar sebagai exception Streamlit, bukan pesan pemulihan yang terarah. Penanganan error pembuatan client mengembalikan `str(e)` langsung, sedangkan sanitasi error request hanya memakai key dari config, bukan selalu key aktif yang baru dibaca.

**Rekomendasi:** tampilkan pesan pengguna yang aman untuk kegagalan model, koneksi, rate limit, dan indeks; simpan detail teknis yang sudah disanitasi secara terpisah. Tambahkan aturan dan batas kutipan untuk permintaan reproduksi materi panjang. Ini gap penguatan berdasarkan kode, bukan bukti kebocoran secret yang teramati.

### P2 — Penyempurnaan setelah validasi inti selesai

- Tambahkan pembuka PDF pada halaman yang dirujuk atau preview halaman lokal yang mematuhi batas akses dan copyright.
- Labeli expander sebagai “konteks yang diambil” jika belum dapat dipastikan seluruh chunk benar-benar digunakan mendukung jawaban.
- Perjelas nomor halaman PDF versus nomor cetak buku langsung di UI.
- Tambahkan contoh pertanyaan awal dan indikator sumber aktif yang berasal dari indeks, bukan daftar statis.
- Pin versi dependensi atau sediakan lock file/lingkungan yang sudah diuji.
- Uji follow-up percakapan: retrieval saat ini memakai pertanyaan terakhir saja, sehingga rujukan seperti “jelaskan bagian kedua tadi” berpotensi tidak menemukan konteks yang tepat.
- Jangan mendahulukan login, Telegram, WhatsApp, atau deployment produksi sebelum P0 selesai.

## 6. Kualitas dataset, laporan, dan pengumpulan

### Dataset

Struktur dataset sudah memenuhi komposisi PRD dan berisi catatan halaman yang berguna. Spot-check halaman 35, 137, 180, 210, dan 223 menemukan materi skor, listening, penilaian speaking, waktu membaca integrated writing, dan rubrik writing yang sejalan dengan topik label.

Namun, spot-check bukan pengesahan semua 30 pertanyaan. Catat `verified_by`, `verified_at`, identitas dokumen, dan status verifikasi untuk setiap item atau lembar verifikasi terpisah. Karena indeks sekarang multi-dokumen, ubah label relevansi menjadi pasangan sumber-halaman atau chunk ID yang terikat versi indeks. Siapkan subset uji terpisah bila pertanyaan yang sama dipakai berulang untuk tuning.

### Laporan PDF

`reports/methodology_evaluation.pdf` ada dan dapat diekstrak sebagai empat halaman. Tabel masih menandai kebutuhan API key/manual review; ini lebih baik daripada mengarang hasil. Tetapi status di awal sebaiknya tegas: **“evaluasi retrieval selesai; evaluasi generation dan manual belum selesai”**. Saat ini keberadaan `results.json` saja membuat generator menganggap ada hasil, walaupun semua generation gagal. Kesimpulan tentang generation yang dapat direproduksi terlalu kuat untuk artefak tersebut.

Rubrik correctness sudah memiliki kategori, tetapi pemetaan kategori parsial ke skor agregat belum tegas. Rubrik groundedness perlu unit klaim, cara menghitung dukungan, identitas penilai, jumlah sampel, dan cara menangani jawaban kosong/penolakan.

### Keamanan paket pengumpulan

Pemeriksaan daftar nama file `TOEFL_Mate_RAG_Study_Assistant_UTS.zip` menemukan 37 entri. Tidak ditemukan `.env`, direktori `chroma_db`, atau PDF sumber; PDF yang terdeteksi hanya dua laporan di `reports/`. Ini mendukung praktik packaging yang baik, tetapi bukan audit seluruh isi file atau riwayat Git. ZIP masih untracked saat pemeriksaan dan tidak diubah oleh review ini.

## 7. Rencana penyelesaian yang disarankan

| Urutan | Tindakan | Kriteria selesai |
|---|---|---|
| 1 | Perbaiki retrieval lintas bahasa dengan satu eksperimen terkendali | Pertanyaan dasar Indonesia mengambil bukti yang tepat; hasil baseline dan variasi pada dataset yang sama terdokumentasi. |
| 2 | Samakan konfigurasi dan format sitasi | UI/evaluasi memakai model efektif yang sama; sitasi nyata berhasil diparse dan cocok dengan sumber serta konteks. |
| 3 | Jalankan ulang evaluasi generation | Ada jawaban/error aktual untuk 30 item, jumlah sukses/gagal jelas, hasil baru tidak menimpa bukti lama. |
| 4 | Lakukan penilaian manusia | Correctness dan groundedness dinilai dengan rubrik, identitas penilai, jumlah sampel, dan catatan; tidak lagi seluruhnya `NOT_RATED`. |
| 5 | Perkuat ingestion dan error handling | Build gagal tidak menghilangkan indeks aktif; kegagalan retrieval/API memberi pesan yang aman dan dapat ditindaklanjuti. |
| 6 | Sinkronkan README, PDF, dan naskah demo | Model, sumber, jumlah chunk, status eksperimen, dan angka metrik konsisten. |
| 7 | Rekam demo dan uji di lingkungan bersih | Video maksimal lima menit tersedia; instalasi Windows dari README terbukti berhasil. |

Contoh perintah untuk run lanjutan, **belum dijalankan dalam review ini**:

```powershell
python scripts/evaluate.py --top_k 5 --output evaluation/results_v2_k5.json
python scripts/evaluate.py --top_k 3 --output evaluation/results_v2_k3.json
python scripts/build_report.py --results evaluation/results_v2_k5.json --comparison evaluation/results_v2_k3.json --output reports/methodology_evaluation_v2.pdf
```

Untuk target internal, bukan ketentuan resmi PRD, tetapkan ambang retrieval sebelum eksperimen, misalnya Hit@5 minimal 0,70 pada label yang sudah diaudit. Target tersebut belum tercapai dan tidak boleh dipresentasikan sebagai hasil.

## 8. Kesimpulan akhir

**Nilai review: 72/100, dengan estimasi progres MVP sekitar 80%.** Proyek memiliki fondasi teknis yang baik, struktur yang mudah diikuti, 49 unit test lulus, indeks nyata, dan integrasi Groq yang terbukti berjalan saat interaksi.

Hambatan utama menuju hasil UTS yang lebih kuat adalah:

1. Retrieval Indonesia belum menemukan cukup banyak bukti relevan, termasuk materi TOEFL paling dasar.
2. Evaluasi generation tersimpan masih gagal seluruhnya dan penilaian manusia belum diisi.
3. Sitasi, model, sumber dokumen, dan narasi laporan belum konsisten dari UI sampai evaluasi.

**Rekomendasi keputusan:** lanjutkan ke tahap stabilisasi dan validasi, bukan ekspansi fitur. Setelah tiga hambatan tersebut dibereskan dengan bukti run baru, proyek akan jauh lebih layak dipertahankan sebagai MVP RAG akademik yang jujur dan dapat diuji ulang.
