# Perbaikan V3 — status parsial

Implementasi ini belum menyelesaikan sprint. Hasil historis, PDF V2, indeks aktif, dan `.env` tidak diubah. Tidak ada request API baru, replay retrieval, pembangunan indeks, atau pengunduhan model pada pekerjaan ini.

## Perubahan dan batasnya

- Error constructor dan request generation dipetakan ke pesan aman; respons kosong dinyatakan gagal. Nama model dari respons disimpan pada hasil generation bila tersedia. Pengklasifikasian rate limit juga memeriksa teks exception secara internal, tanpa menampilkannya.
- Validator lokasi sitasi yang sama kini dipakai UI dan evaluator. Karakter format Unicode diabaikan saat mencocokkan identitas sumber, sementara nama mentah dalam sitasi dipertahankan. UI memperingatkan sitasi tidak terbaca atau di luar konteks; daftar konteks tidak diklaim sebagai bukti dukungan klaim. Peringatan tanpa sitasi memakai heuristik OOS sehingga bukan penilaian semantik yang andal.
- Dataset kosong ditolak; CLI memilih nama output unik dan menolak file yang sudah ada sebelum generation. Pembuatan output memakai mode eksklusif, tetapi pasangan JSON/CSV belum merupakan transaksi atomik dan belum ada checkpoint/resume.
- Error retrieval di UI dibedakan dari konteks kosong.
- Dua narasi hardcode pada generator laporan diperbaiki. Generator laporan lainnya belum diaudit menyeluruh; PDF baru belum dibuat.

## Temuan review

| Temuan | Status | Keterangan |
|---|---|---|
| F-01 | Belum | Metrik evaluator masih berbasis nomor halaman, bukan sumber-halaman. Jangan gunakan sebagai metrik source-aware. |
| F-02 | Sebagian | UI memakai validator bersama dan memberi peringatan; belum ada pengujian UI regresi khusus atau klasifikasi faktual andal. |
| F-03 | Sebagian | Normalisasi karakter format pada pencocokan lokasi dan fixture tersedia; artefak V2 belum dihitung ulang. |
| F-04 | Belum | Heuristik OOS dan nama metrik evaluator masih menyesatkan; perlu dipisahkan dari review manusia. |
| F-05 | Sebagian | Constructor/request dan respons kosong ditangani aman, test baru memakai fixture; test lama belum sepenuhnya hermetik dan seluruh kategori belum diuji. |
| F-06 | Sebagian | Dua klaim hardcode dihapus atau dihitung; laporan belum diuji lengkap dan PDF baru belum dibuat. |
| F-07 | Sebagian | Output unik, proteksi overwrite, dataset kosong; metadata, checkpoint dan resume belum lengkap. |
| F-08 | Belum | Validasi manifest model dan dimensi embedding belum diterapkan. |
| F-09 | Sebagian | Error retrieval dibedakan; resolusi follow-up belum diperbaiki. |
| F-10 | Belum | Template review dan validasi konfigurasi belum dirapikan. |

## Pengujian dan metrik

`python -m pytest tests/ -q`: 63 lulus, satu warning `PytestRemovedIn10Warning` dari plugin anyio. Test baru mencakup error constructor dengan token palsu, respons kosong, zero-width/sumber salah, dan dataset kosong. Test lulus tidak membuktikan correctness atau groundedness.

Tidak ada re-scoring atau generation baru. Nilai V2 tetap historis: Hit@5 0,56 dan Precision@5 0,192 pada 25 pertanyaan berlabel halaman; Hit@3 0,44 dan Precision@3 0,20. Precision menghitung chunk yang cocok per k, termasuk chunk duplikat. Metrik ini bukan metrik source-aware yang telah diimplementasikan, dan label belum diverifikasi manusia. Jawaban V2 top-k 5: 29 sukses dan satu gagal; top-k 3: 30 sukses. Correctness, groundedness, dan OOS berbasis rubrik tetap belum dinilai manusia.

## Penerimaan PRD dan pekerjaan berikutnya

- [ ] Evaluasi source-aware, metadata aktual lengkap, checkpoint dan resume.
- [ ] Validasi manifest embedding–indeks dan uji mismatch.
- [ ] Audit laporan dinamis, PDF baru dan review manusia correctness/groundedness/OOS.
- [ ] Pengujian follow-up, UI, instalasi bersih, dan demo/video.

Prioritas berikutnya adalah menyelesaikan F-01 dan F-07 sebelum menjalankan batch API, lalu F-04, F-06, dan F-08. Jangan mengklaim acceptance penuh berdasarkan hasil test ini.
