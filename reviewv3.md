# Review V3 — Pengujian Ulang Hasil Perbaikan TOEFL Mate

**Tanggal:** 30 Oktober 2026  
**Landasan:** PRD, `reviewv2.md`, `planning_perbaikan_v2.md`, dan `reports/perbaikan_v2.md`.  
**Kesimpulan:** perbaikan menghasilkan kemajuan nyata, tetapi sebagian klaim penyelesaian masih terlalu luas. Kualitas retrieval, evaluasi multi-dokumen, konsistensi sitasi, dan penanganan error belum sepenuhnya tuntas.

## 1. Nilai dan keputusan

**Skor reviewer: 77/100**, naik dari 72/100. Estimasi progres menuju MVP tervalidasi sekitar **85%**, bukan persentase akurasi atau nilai resmi dosen.

| Aspek | Bobot | V2 | V3 | Dasar |
|---|---:|---:|---:|---|
| Arsitektur dan ingestion | 20 | 18 | 18 | Build kandidat lebih aman; manifest, validasi model indeks, dan alur aktivasi masih parsial. |
| Retrieval dan grounded generation | 20 | 12 | 14 | Peningkatan retrieval direproduksi, tetapi follow-up gagal dan 11/25 query masih miss pada top-5. |
| UI dan SOP | 15 | 13 | 13 | Kontrol berjalan; format sitasi output belum konsisten dan penanganan retrieval gagal masih membingungkan. |
| Evaluasi dan validitas eksperimen | 20 | 9 | 12 | Ada 59 jawaban berhasil dari dua run tersimpan, tetapi label sumber, metrik OOS, model efektif, dan audit konteks belum lengkap. |
| Pengujian dan reproduksibilitas | 10 | 8 | 8 | 59 test lulus, tetapi pengujian tambahan menemukan gap yang belum dicakup suite. |
| Dokumentasi, laporan, dan demo | 10 | 8 | 8 | Laporan baru tersedia, tetapi PDF masih memuat narasi hardcode yang salah. |
| Rahasia dan copyright | 5 | 4 | 4 | Tidak ada kebocoran key nyata yang diuji; jalur constructor error masih mengembalikan exception mentah pada fixture. |
| **Total** | **100** | **72** | **77** | Kemajuan nyata, belum acceptance penuh. |

**Keputusan:** cukup baik untuk demo prototipe dengan batasan yang dijelaskan, tetapi belum layak disebut MVP tervalidasi penuh. Tidak ada nilai correctness atau groundedness yang boleh diklaim sebelum penilaian manusia dilakukan.

## 2. Cakupan pengujian ulang

Pengujian ini tidak mengubah implementasi, dataset, indeks aktif, atau hasil evaluasi yang sudah ada. Hanya dokumen review ini yang ditambahkan.

Pemeriksaan yang benar-benar dilakukan:

1. Menjalankan ulang seluruh test dan dependency check.
2. Mengulang retrieval seluruh 25 query berlabel pada indeks yang sama: enrichment dimatikan sementara di memori, lalu diaktifkan, masing-masing top-k 5 dan 3.
3. Memeriksa kecocokan sumber Official Guide saat menghitung ulang retrieval; tidak hanya nomor halaman.
4. Mengaudit dua JSON hasil V2 dan teks PDF laporan.
5. Menjalankan empat request generation nyata melalui Streamlit AppTest: regression case Indonesia, follow-up, OOS tahun 2026, dan pertanyaan Inggris dengan kontrol bahasa/gaya/kesulitan.
6. Menguji kegagalan retrieval UI, metrik salah sumber, pelaporan model efektif, dan constructor error memakai fixture/mock tanpa request API.
7. Menguji kegagalan embedding pada build kandidat menggunakan PDF sintetis dan database sementara, bukan indeks pengguna.

**Batas:** tidak mengulang batch 60 request API karena artefak sudah tersedia; tidak ada audit manusia seluruh jawaban, pengujian visual Chrome/mobile, instalasi bersih, atau rekaman video. Analisis semantik jawaban di dokumen ini merupakan penilaian model/reviewer AI, bukan penilaian manusia.

## 3. Hasil yang terkonfirmasi

### 3.1 Test, dependensi, dan layanan

| Pemeriksaan | Hasil |
|---|---|
| `python -m pytest tests/ -q` | **59 passed, 1 warning**, 16,87 detik |
| `python -m pip check` | `No broken requirements found.` |
| HTTP aplikasi / health | Keduanya **200** |
| Indeks aktif | **4.156 chunk**: Official Guide 3.911, CFLT 245 |
| Hapus percakapan | Snapshot segera setelah klik: `messages=0`, `sources=0` |
| UI saat retrieval exception fixture | Tidak ada exception Streamlit; pesan pemulihan tampil, tetapi jawaban akhir menyebut konteks tidak ditemukan |
| Build kandidat saat embedding fixture gagal | Koleksi aktif fixture tetap berisi **1 item** |

Database sementara pada pengujian embedding menimbulkan `WinError 32` ketika cleanup otomatis karena file Chroma masih terkunci. Assertion preservasi indeks telah tercapai sebelum cleanup gagal; karena itu pengujian ad hoc ini **bukan run proses bersih tanpa error**. Indeks aktif proyek tidak disentuh. Ini juga mengingatkan perlunya pengelolaan resource Windows pada test integrasi.

### 3.2 Retrieval sebelum–sesudah pada indeks dan dataset identik

| Mode | Top-k | Query hit / 25 | Hit@K | Precision@K |
|---|---:|---:|---:|---:|
| Tanpa enrichment | 5 | 8 | 0,3200 | 0,1040 |
| Dengan enrichment | 5 | 14 | **0,5600** | **0,1920** |
| Tanpa enrichment | 3 | 6 | 0,2400 | 0,1333 |
| Dengan enrichment | 3 | 11 | **0,4400** | **0,2000** |

Hasil ini mendukung bahwa enrichment memang memberi manfaat pada development set, bukan sekadar perubahan API atau artefak historis. Tidak ditemukan kecocokan halaman palsu dari dokumen CFLT pada replay ini. Namun, kemampuan evaluator secara umum tetap bermasalah untuk kasus salah sumber, seperti dibuktikan fixture di bawah.

Pada top-k 5, 11 query masih gagal menemukan halaman berlabel, termasuk `fact_01`, `fact_04`, `fact_05`, `fact_06`, `concept_02`, `concept_03`, `concept_04`, `concept_09`, `cite_01`, `cite_04`, dan `cite_05`.

Catatan penting: regression case empat bagian TOEFL berhasil, tetapi pertanyaan berlabel `fact_01` yang menanyakan rentang skor dengan susunan kalimat berbeda **masih miss**. Perbaikannya belum robust terhadap parafrasa. Label halaman juga mungkin belum lengkap, sehingga miss bukan bukti otomatis semua jawabannya salah.

### 3.3 AppTest dengan API aktual

| Skenario | Hasil | Keputusan |
|---|---|---|
| Empat bagian TOEFL dan rentang skor, Indonesia | Jawaban menyebut Reading/Listening/Speaking/Writing masing-masing 0–30 dan total 0–120. Sitasi `[eBook_TOEFL_Official_Guide_4e.pdf, Halaman 35]` terbaca dan ada pada konteks. Waktu rerun sekitar 3,543 detik, termasuk cold start. | **Lulus untuk satu regression case.** |
| Langsung dilanjutkan `Jelaskan bagian kedua tadi.` | Menafsirkan sebagai **Konteks 2**, membahas Reading to Learn halaman 25, bukan Listening sebagai bagian kedua daftar sebelumnya. Waktu rerun sekitar 2,600 detik. | **Gagal secara semantik**, meskipun tidak ada exception dan sitasinya valid secara lokasi. |
| `Berapa biaya TOEFL tahun 2026 di Jakarta?`, sesi bersih | Tidak mengarang angka; menjelaskan tidak ada biaya spesifik, merujuk halaman 49. Sumber ditulis sebagai teks biasa, bukan sitasi kanonis. | **Penolakan cukup baik**, format sitasi belum patuh. |
| Inggris, ringkas, tingkat dasar; durasi Independent Speaking Q1 | Menjawab 15 detik persiapan dan 45 detik respons. Sumber halaman 183 ditulis tanpa tanda kurung sitasi kanonis. | **Kontrol dan generation berjalan**, dukungan halaman belum diaudit penuh dan parser tidak membaca sumber teks biasa. |

Keempat request selesai tanpa exception AppTest. Tidak adanya exception tidak berarti jawaban benar; follow-up membuktikan perbedaannya.

## 4. Temuan prioritas yang masih harus dibereskan

### F-01 — P1: metrik masih menganggap halaman benar walau dokumennya salah

**Lokasi:** `src/evaluation.py:250-269`.

Fixture retrieval `other.pdf` halaman 35 dan jawaban `[other.pdf, Halaman 35]`, dengan label dataset hanya halaman 35, menghasilkan **recall=1,0 dan citation_accuracy_micro=1,0**. Ini menunjukkan label/metrik belum source-aware, meskipun parser sudah menghasilkan sumber.

Selain itu, flag `in_retrieved_context` tidak digunakan untuk menghitung citation accuracy. Sitasi sumber yang salah atau format bermasalah tetap bisa memperoleh nilai dari kecocokan angka halaman saja.

**Perbaikan:** gunakan label pasangan sumber-halaman, laporkan lokasi-valid versus sesuai-label secara terpisah, dan jangan menyamakan keduanya dengan groundedness.

### F-02 — P1: kontrak sitasi belum ditegakkan pada jawaban UI

**Lokasi:** `src/evaluation.py:72-87`, `app.py:215-230`.

UI tidak menjalankan validator sitasi sebelum menampilkan jawaban. Parser hanya dipakai dalam evaluasi. Dua jawaban live terbaru menyertakan nama file/halaman sebagai teks biasa sehingga tidak bisa diparse.

Artefak V2 juga memiliki jawaban in-scope yang menyebut `.pdf` tetapi tidak memiliki sitasi terbaca: **9 pada top-k 5** dan **12 pada top-k 3**. Angka tersebut bukan seluruh jawaban tanpa sitasi, hanya subset yang jelas menyebut nama sumber dalam teks.

**Perbaikan:** buat renderer/validator bersama untuk UI dan evaluator. Flag jawaban faktual tanpa sitasi; jangan otomatis menciptakan sitasi yang tidak didukung konteks.

### F-03 — P1: normalisasi Unicode sumber belum lengkap

**Lokasi:** `src/evaluation.py:78-82, 112-120`.

Semua **3 sitasi invalid** pada run top-k 5 dan **1 sitasi invalid** pada run top-k 3 memiliki `U+200B` (zero-width space) di awal nama file. Setelah karakter tersebut dihapus pada pemeriksaan ad hoc, pasangan sumber-halamannya cocok dengan konteks tersimpan.

Artinya, angka 37/40 dan 36/37 tidak boleh langsung disebut jumlah sitasi halusinasi. Pada kasus ini penyebabnya normalisasi identitas sumber. NFKC dan `.strip()` saja tidak menghilangkan zero-width space.

**Perbaikan:** normalisasi konservatif karakter format pada identitas sumber, uji dengan contoh nyata, dan pertahankan nilai mentah untuk audit.

### F-04 — P1: skor OOS otomatis tidak dapat dipakai sebagai akurasi final

**Lokasi:** `src/evaluation.py:124-146, 271-280`.

Pembacaan jawaban artefak menunjukkan false negative:

- Top-k 5 `oos_02` menolak IELTS/kursus Yogyakarta, tetapi diberi `False` karena frasa tidak cocok.
- Top-k 3 `oos_01` jelas menyatakan informasi tidak terdapat pada sumber, tetapi diberi `False`.
- Top-k 3 `oos_05` menolak kunci UTBK, tetapi diberi `False`.

Sebaliknya, fixture `Informasi tidak ditemukan, tetapi biaya tes adalah Rp 3.000.000.` menghasilkan `True`, meskipun mengandung klaim biaya yang seharusnya diperiksa.

Dengan demikian, **0,8 versus 0,6 tidak membuktikan top-k 5 lebih baik dalam OOS**. Sebut metrik tersebut indikator frasa penolakan sampai tersedia review berbasis rubrik. Review AI ini tidak menggantikan review manusia.

### F-05 — P1: constructor error masih mengembalikan exception mentah

**Lokasi:** `src/generator.py:65-74`.

Fixture constructor `Groq` yang melempar `ValueError` berisi token palsu `FAKE_TEST_SECRET` menghasilkan error yang masih memuat token tersebut. Tidak ada key nyata digunakan atau dibocorkan dalam pengujian ini.

Sanitasi pada blok request tidak melindungi blok constructor. Test rate-limit yang ada hanya mencakup blok request.

**Perbaikan:** satu jalur pemetaan error aman untuk constructor dan request; tambahkan test credential tidak ada tanpa bergantung pada `.env` pengguna. Test rate-limit sekarang memanggil loader `.env` asli dan tidak benar-benar memalsukan proses load/key, sehingga belum hermetik.

### F-06 — P1: PDF V2 masih berisi angka dan narasi lama yang salah

**Lokasi:** `scripts/build_report.py:332, 429`; terkonfirmasi pada teks PDF V2.

PDF menyebut **“Recall naik signifikan (+33% relatif)”** dan **“hanya mencakup satu dokumen sumber”**. Padahal tabel V2 membandingkan 0,56 versus 0,44, yaitu kenaikan sekitar **27,3% relatif** atau **12 poin persentase**, dan indeks aktif berisi dua dokumen. “Signifikan” juga belum didukung uji statistik.

Status evaluasi parsial di awal PDF sudah benar. Masalahnya adalah narasi hardcode di bagian lain masih bertentangan.

**Perbaikan:** hitung narasi dari data run, tampilkan sumber dari manifest, dan uji teks laporan terhadap konfigurasi aktual.

### F-07 — P1: reproduksibilitas dan proteksi artefak masih parsial

**Lokasi:** `src/evaluation.py:181-192, 232-248`; `scripts/evaluate.py:99-102`.

- `dataset_version` selalu `historical_test_questions`, walaupun CLI menerima dataset lain.
- Tidak ada hash dataset, manifest/identitas koleksi, dimensi embedding, versi enrichment, atau snapshot konteks pada hasil run.
- Fixture generation yang mengembalikan model efektif berbeda tidak menyimpan nama model tersebut di hasil; evaluator hanya mencatat config awal.
- Menjalankan CLI tanpa `--output` masih menimpa `evaluation/results.json` historis setelah batch selesai.
- Tidak ada checkpoint/resume; hasil baru disimpan setelah semua item selesai.
- Dataset kosong diberi `run_status=COMPLETE` karena `all([])` bernilai benar.

**Perbaikan:** output unik default dengan penolakan overwrite, identitas konfigurasi aktual, checkpoint atomik, dan validasi dataset kosong. Jangan menyebut auditabilitas lengkap sebelum item ini selesai.

### F-08 — P1: aman terhadap penghapusan indeks, tetapi belum aman terhadap mismatch embedding

**Lokasi:** `scripts/ingest_pdf.py:57-90`; `src/retriever.py:156-170`.

Build kandidat memperbaiki risiko penghapusan indeks aktif dan uji failure fixture mendukung klaim itu. Namun, query belum membaca manifest untuk menolak perbedaan model embedding. Jika model baru memiliki dimensi sama, pencarian berpotensi tetap berjalan dengan representasi vektor yang tidak kompatibel tanpa error dimensi.

Manifest belum memuat dimensi, dan aktivasi/rollback masih berupa perubahan manual `CHROMA_COLLECTION`. Panduan error UI hanya menyuruh ingestion; pada instalasi pertama, kandidat yang selesai dibangun belum otomatis aktif sehingga pengguna perlu mengikuti langkah manual README.

**Perbaikan:** validasi model/dimensi/manifes ketika membuka koleksi serta sediakan aktivasi kandidat yang eksplisit dan tervalidasi. Bukan dengan menghapus koleksi aktif.

### F-09 — P2: follow-up dan pesan retrieval error masih membingungkan

**Lokasi:** `app.py:55-63, 190-206`.

Follow-up menggabungkan pertanyaan sebelumnya, tetapi tidak menyelesaikan rujukan pada jawaban sebelumnya. Kasus “bagian kedua” nyata diinterpretasikan sebagai Konteks 2. Untuk pertanyaan ambigu, meminta klarifikasi lebih baik daripada memberikan penjelasan yang melenceng.

Saat retrieval fixture gagal, UI memang memberi error aman, tetapi tetap menyimpan jawaban “tidak menemukan konteks yang relevan”. Kegagalan teknis dan kurangnya relevansi seharusnya dibedakan.

### F-10 — P2: template review dan validasi konfigurasi perlu dirapikan

`evaluation/human_review_template.csv` memiliki header **10 kolom**, tetapi baris instruksi hanya **1 kolom**. Pembaca CSV dapat menganggap instruksi sebagai data. Jadikan CSV hanya header/data dan pindahkan instruksi ke Markdown.

Validasi konfigurasi belum dipanggil pada startup UI dan belum mencakup seluruh parameter generation/angka non-finite. Daftar dokumen sidebar juga masih statis, bukan berasal dari koleksi aktif.

## 5. Prioritas pekerjaan berikutnya

1. **Benahi evaluator terlebih dahulu:** label sumber-halaman, model efektif, identitas dataset/indeks, proteksi overwrite, dan status dataset kosong.
2. **Satukan sitasi UI/evaluator:** normalisasi Unicode, cek lokasi, dan flag jawaban tanpa format sitasi yang dapat dibaca.
3. **Perbaiki keamanan error constructor** dan buat test tanpa ketergantungan key nyata.
4. **Perbaiki PDF:** angka perbandingan harus dihitung dan sumber tidak boleh hardcode satu dokumen.
5. **Lakukan penilaian manusia:** correctness, groundedness, OOS; jangan mengulang batch API hanya untuk memperbaiki metrik yang dapat dihitung ulang dari jawaban tersimpan.
6. **Lanjutkan eksperimen retrieval terkontrol**, terutama parafrasa dan follow-up; 0,56 masih di bawah target internal 0,70.
7. **Verifikasi manifest embedding saat query**, kemudian instalasi bersih dan demo final.

## 6. Kesimpulan akhir

Perbaikan sebelumnya **bukan sekadar kosmetik**: kenaikan retrieval direproduksi pada indeks yang sama, regression case utama berhasil, generation sudah memiliki hasil aktual, dan build kandidat tidak menghapus koleksi aktif ketika gagal.

Namun, **59 test lulus belum membuktikan seluruh acceptance criteria selesai**. Pengujian tambahan menemukan error metrik, ketidakpatuhan sitasi, constructor error mentah, PDF hardcode, dan follow-up salah sasaran yang belum dicakup test.

**Status rekomendasi: lanjut stabilisasi, bukan klaim selesai penuh. Skor 77/100; progres estimasi sekitar 85%.** Fokus sprint berikutnya pada integritas evaluasi dan sitasi sebelum menambah fitur atau mengejar angka retrieval semata.
