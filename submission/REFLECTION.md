# Reflection — Lab 20 (Personal Report)

> **Đây là báo cáo cá nhân.** Mỗi học viên chạy lab trên laptop của mình, với spec của mình. Số liệu của bạn không so sánh được với bạn cùng lớp — chỉ so sánh **before vs after trên chính máy bạn**. Grade rubric tính theo độ rõ ràng của setup + tuning của bạn, không phải tốc độ tuyệt đối.

---

**Họ Tên:** _Nguyen Van A_
**Cohort:** _A20-K1_
**Ngày submit:** _2026-05-06_

---

## 1. Hardware spec (từ `00-setup/detect-hardware.py`)

> Paste output của `python 00-setup/detect-hardware.py` vào đây, hoặc điền thủ công:

- **OS:** _Windows 10 (AMD64)_
- **CPU:** _12th Gen Intel(R) Core(TM) i5-12450HX_
- **Cores:** _8 physical / 12 logical_
- **CPU extensions:** _AVX2_
- **RAM:** _23.7 GB_
- **Accelerator:** _NVIDIA GeForce RTX 3050 Laptop GPU 6GB_
- **llama.cpp backend đã chọn:** _CPU fallback on Windows native_
- **Recommended model tier:** _Qwen2.5-1.5B-Instruct_

**Setup story** (≤ 80 chữ): những gì cần thay đổi để lab chạy được trên máy bạn (vd: dùng WSL2, install CUDA Toolkit, fall back sang Vulkan vì ROCm phiên bản kén, tắt antivirus để pip install nhanh hơn, v.v.):

Native CUDA path was not available (missing CUDA toolkit/toolchain constraints on this machine), so I used CPU fallback on Windows to complete all core tracks with reproducible artifacts.

---

## 2. Track 01 — Quickstart numbers (từ `benchmarks/01-quickstart-results.md`)

> Paste bảng từ `benchmarks/01-quickstart-results.md` xuống đây (auto-generated bởi `python 01-llama-cpp-quickstart/benchmark.py`).

| Model | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode rate (tok/s) |
|---|--:|--:|--:|--:|--:|
| qwen2.5-1.5b-instruct-q4_k_m.gguf | 406 | 229 / 257 | 125.5 / 127.8 | 8130 / 8291 / 8373 | 8.0 |
| qwen2.5-1.5b-instruct-q2_k.gguf   | 443 | 231 / 254 | 122.5 / 123.6 | 7945 / 8036 / 8048 | 8.2 |

**Một quan sát** (≤ 50 chữ): Q4_K_M vs Q2_K trên máy bạn — số liệu nói gì? Quality đáng đánh đổi không?

On this CPU fallback setup, Q2_K is only slightly faster than Q4_K_M, while Q4_K_M still gives better answer quality. I used Q4_K_M as primary for serving and Q2_K as comparison baseline.

---

## 3. Track 02 — llama-server load test

> Chạy 2 lần locust ở concurrency 10 và 50, paste tóm tắt bên dưới.

| Concurrency | Total RPS | TTFB P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 0.66 | 12000 | 17000 | 18000 | 0 |
| 50 | 0.64 | 25000 | 32000 | 32000 | 17 |

**KV-cache observation** (từ `record-metrics.py`): peak `llamacpp:kv_cache_usage_ratio` ở concurrency 50 = _<0.XX>_, nghĩa là …

`llamacpp:kv_cache_usage_ratio` không thu được vì fallback server (`python -m llama_cpp.server`) không expose endpoint `/metrics` trên phiên bản đang dùng. Thay thế bằng quan sát từ locust: ở concurrency 50 xuất hiện timeout và latency tăng mạnh, cho thấy hệ thống bão hòa CPU.

---

## 4. Track 03 — Milestone integration

- **N16 (Cloud/IaC):** _stub: localhost only_
- **N17 (Data pipeline):** _stub: in-memory retrieval_
- **N18 (Lakehouse):** _stub: in-memory docs_
- **N19 (Vector + Feature Store):** _stub: TOY_DOCS keyword overlap_

**Nơi tốn nhiều ms nhất** trong pipeline (đo bằng `time.perf_counter` trong `pipeline.py`):

- embed: _0.0 ms (not used in current stub pipeline)_
- retrieve: _0.0 ms_
- llama-server: _~7030-8712 ms_

**Reflection** (≤ 60 chữ): bottleneck nằm ở đâu? Có khớp với kỳ vọng không?

Bottleneck nằm ở llama-server inference (decode trên CPU), không phải retrieve. Điều này khớp kỳ vọng vì retrieve trong bản stub gần như tức thì.

---

## 5. Bonus — The single change that mattered most

> **Most important section.** Pick **một** thay đổi từ bonus track (build flag, thread sweep, quant pick, GPU offload, KV-cache quantization, speculative decoding, bất cứ challenge nào trong `BONUS-llama-cpp-optimization/CHALLENGES.md`) đã tạo ra speedup lớn nhất trên máy bạn.

**Change:** _Thread sweep on CPU fallback: giảm `n_threads` từ 8 xuống 2_

**Before vs after** (paste 2-3 dòng từ sweep output):

```
before: 8 threads -> 7.95 tok/s decode
after:  2 threads -> 14.92 tok/s decode
speedup: ~1.88× vs 8-thread setting (~1.21× vs 1-thread baseline)
```

**Tại sao nó work** (1–2 đoạn ngắn — đây là phần grader đọc kỹ nhất):

Kết quả ngược với trực giác "nhiều thread hơn là nhanh hơn". Với Qwen2.5-1.5B Q4_K_M trên CPU i5-12450HX, decode tốt nhất ở 2 threads; khi tăng lên 8 hoặc 12 threads, throughput giảm mạnh. Lý do hợp lý nhất là workload decode bị giới hạn bởi memory bandwidth/cache locality hơn là thiếu core compute thuần túy. Thêm thread làm scheduler và memory subsystem tranh chấp nhiều hơn, nên mỗi token chậm đi.

Điều này khớp bài học production tuning của lab: phải đo knob trên chính hardware của mình. Setting default theo physical cores (`8`) ổn để bắt đầu, nhưng không phải tối ưu cho decode trên máy này.

---

## 6. (Optional) Điều ngạc nhiên nhất

_(1–2 câu — không bắt buộc, nhưng người grader đọc tất cả)_

Điều bất ngờ nhất là chỉ cần giảm độ dài output cho workload benchmark đã thay đổi mạnh tỷ lệ request hoàn tất, dù model và phần cứng giữ nguyên.

---

## 7. Self-graded checklist

- [x] `hardware.json` đã commit
- [x] `models/active.json` đã commit (hoặc paste path snapshot vào section 1)
- [x] `benchmarks/01-quickstart-results.md` đã commit
- [x] `benchmarks/02-server-results.md` (hoặc CSV từ `record-metrics.py`) đã commit
- [x] `benchmarks/bonus-*.md` đã commit (ít nhất 1 sweep)
- [ ] Ít nhất 6 screenshots trong `submission/screenshots/` (xem `submission/screenshots/README.md`)
- [ ] `make verify` exit 0 (chạy ngay trước khi push)
- [ ] Repo trên GitHub ở chế độ **public**
- [ ] Đã paste public repo URL vào VinUni LMS

---

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.
