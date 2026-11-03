# Optimasi integritas dan UI

Status: perbaikan parsial; belum memenuhi seluruh penerimaan PRD. Tidak ada API live, re-scoring, replay retrieval, build indeks, atau PDF baru pada pekerjaan ini. Artefak dan indeks lama tidak ditimpa.

## Perubahan

- Evaluator menerima label `relevant_sources` berisi pasangan `source` dan `page`. Label lama `relevant_pages` diberi `SOURCE_UNKNOWN`, tidak ditebak dan tidak ikut agregasi source-aware. Hit menghitung query berlabel dengan minimal satu chunk sesuai; precision menghitung jumlah chunk yang cocok dibagi k, termasuk duplikat; retrieval gagal dikecualikan. Ketiadaan label dinyatakan eksplisit. Kesesuaian label sitasi terpisah dari validitas lokasi sitasi, dan keduanya bukan bukti dukungan klaim.
- Coverage memakai jawaban in-scope yang berhasil sebagai denominator. Indikator frasa OOS bukan akurasi dan mencakup item OOS gagal dalam denominator; review manusia tetap `NOT_RATED`. Model efektif, fingerprint item dataset, parameter generasi dan metadata konteks direkam; dimensi dan manifest evaluasi dicatat `UNKNOWN` jika belum ditelusuri.
- Build baru mencatat dimensi dan versi skema manifest. Retrieval memeriksa model dan dimensi bila metadata tersedia serta tidak lagi melakukan fallback diam-diam setelah kegagalan query. Indeks lama tanpa manifest lengkap tetap `UNKNOWN` dan masih dapat dipakai; ini bukan verifikasi kompatibilitas.
- UI tidak lagi membuat koleksi saat dibuka; status manifest tidak lengkap ditampilkan, klaim daftar dokumen statis dihapus, dan konteks retrieval dibedakan dari bukti. Pertanyaan ordinal ambigu meminta klarifikasi; pendekatan konservatif ini juga dapat meminta klarifikasi pada pertanyaan yang sebenarnya sudah cukup jelas.
- Test mencakup salah sumber dengan halaman sama, label historis, mismatch manifest, error query tanpa fallback, dan AppTest klarifikasi tanpa API.

## Hasil pengujian

`python -m pytest tests/ -q`: **67 passed, 1 warning** (plugin anyio, `PytestRemovedIn10Warning`). Test tidak membuktikan jawaban benar atau grounded. Tidak ada perubahan metrik generation; hasil V2 tetap historis dan tidak dibandingkan langsung dengan definisi source-aware baru.

## Belum selesai

- Checkpoint atomik, resume terverifikasi, fingerprint manifest aktual dalam metadata run, dan pengujian concurrency output belum tersedia.
- Dataset historis belum mempunyai label sumber terverifikasi; perlu membuat dataset terpisah dengan bukti pemetaan dan review manusia. Tidak ada hasil re-scoring baru.
- Penyempurnaan laporan PDF, template review manusia, dan audit narasi laporan lainnya belum selesai; PDF baru belum dibuat.
- Peringatan dan klarifikasi follow-up bukan pemahaman semantik lengkap. UI belum diuji visual pada browser/mobile atau deploy bersih.
- Indeks lama belum terbukti cocok dengan model aktif. Metadata manifest bukan bukti bahwa vektor benar-benar dibangun dengan model tersebut; provenance dan integritas data memerlukan audit.
- Penilaian manusia correctness, groundedness, dukungan sitasi dan OOS; video dan uji deploy masih terbuka.
