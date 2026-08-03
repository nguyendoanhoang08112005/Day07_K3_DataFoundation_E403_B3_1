# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Doãn Hoàng
**Nhóm:** Nhóm B3_1 - K3
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần bằng 1.0) nghĩa là hai vector embedding của hai đoạn văn bản hướng về cùng một phía trong không gian vector đa chiều. Điều này biểu thị rằng hai đoạn văn bản có độ tương đồng ngữ nghĩa rất lớn, chia sẻ nhiều ngữ cảnh hoặc ý nghĩa tương đương nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Quy định đăng ký môn học của trường rất rõ ràng."
- Câu B: "Hướng dẫn đăng ký học phần của trường rất cụ thể."
- Tại sao tương đồng: Cả hai câu đều nói về tính rõ ràng và chi tiết của quy chế đăng ký học tập của nhà trường. Chúng chia sẻ các khái niệm ngữ nghĩa tương tự như "đăng ký môn học/học phần" và "rõ ràng/cụ thể".

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Học phí học kỳ này tăng nhẹ."
- Câu B: "Chú mèo nhà em thích ngủ trên ghế sofa."
- Tại sao khác: Hai câu đề cập đến hai chủ đề hoàn toàn khác nhau không liên quan gì nhau (một bên là vấn đề tài chính học vụ, một bên là thói quen của thú cưng). Không có từ ngữ hay ý nghĩa ngữ nghĩa nào chia sẻ chung.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài của văn bản (văn bản dài hơn sẽ có vector dài hơn, dẫn đến khoảng cách Euclid lớn dù cùng chủ đề). Ngược lại, độ tương tự cosine chỉ đo góc giữa hai vector, đã được chuẩn hóa theo độ dài, giúp so sánh thuần túy về mặt ngữ nghĩa (hướng của vector) mà không bị thiên vị bởi độ dài ngắn của văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> Áp dụng công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
> `số lượng chunk = ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Trình bày phép tính mới:* `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25`.
> *Thay đổi:* Số lượng chunk tăng từ 23 lên 25 chunks.
> *Lý do muốn độ chồng chéo nhiều hơn:* Tăng độ chồng chéo giúp bảo toàn thông tin ngữ cảnh xung quanh ranh giới cắt của các chunk, tránh việc một câu hoặc một ý nghĩa quan trọng bị cắt đôi nửa chừng ở ranh giới giữa hai chunk kế tiếp, giúp mô hình ngôn ngữ (LLM) hiểu ngữ cảnh trọn vẹn hơn khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy (regex) `r'(\.\n|\. |! |\? )'` làm dấu phân tách câu để bảo toàn cả dấu câu kết thúc của mỗi câu (thông qua capture group). Sau đó, ghép phần nội dung câu với dấu câu tương ứng, làm sạch khoảng trắng thừa bằng `.strip()`, loại bỏ các câu rỗng, và nhóm các câu lại theo số lượng tối đa `max_sentences_per_chunk` trước khi ghép chúng bằng khoảng trắng để tạo thành một chunk hoàn chỉnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo cơ chế chia để trị đệ quy. Trường hợp cơ sở (base case) là khi văn bản ngắn hơn `chunk_size`, nó sẽ trả về chính nó. Nếu không, tôi lấy dấu phân tách có độ ưu tiên cao nhất, tách văn bản ra và đệ quy xử lý các phần con có độ dài lớn hơn `chunk_size` với các dấu phân tách tiếp theo. Cuối cùng, tôi tiến hành gom nhóm (merge) các phần con này lại với nhau sao cho độ dài của chunk kết quả được ghép bằng dấu phân tách không vượt quá giới hạn `chunk_size`. Nếu không còn dấu phân tách nào, tôi tự động cắt theo số ký tự cố định.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Đối với ChromaDB, tôi gọi phương thức `.add()` của collection. Đối với in-memory fallback, các tài liệu được lưu trong danh sách dưới dạng từ điển chứa `id`, `content`, `metadata` và `embedding` được tạo từ hàm nhúng. Khi tìm kiếm, tôi tính độ tương tự cosine giữa vector truy vấn và tất cả vector trong store thông qua `compute_similarity`, sắp xếp giảm dần theo điểm số similarity và trả về top-k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Trong `search_with_filter`, tôi lọc trước (pre-filtering) danh sách chunks trong store dựa trên `metadata_filter` bằng cách so khớp tất cả các cặp khóa-giá trị, sau đó tiến hành chạy tìm kiếm similarity trên tập hợp con đã lọc. Đối với `delete_document`, tôi loại bỏ tất cả các record có trường `metadata['doc_id']` bằng `doc_id`, hoặc có record `id` khớp chính xác hoặc có định dạng tiền tố dạng chunk của tài liệu cần xóa (`doc_id::chunk_`).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tác tử thực hiện truy xuất top-k chunk liên quan nhất từ vector store qua `self.store.search`. Sau đó ghép nội dung văn bản của các chunk này lại với nhau bằng ký tự xuống dòng kép `\n\n` để tạo thành ngữ cảnh (`context`). Ngữ cảnh này cùng câu hỏi được đưa vào prompt mẫu có cấu trúc rõ ràng và chuyển tới `llm_fn` để sinh ra câu trả lời cuối cùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.10.6, pytest-9.1.1, pluggy-1.6.0 -- D:\laragon\www\Day07Vinuni\Day07_-2A202601119_NguyenDoanHoang\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\laragon\www\Day07Vinuni\Day07_-2A202601119_NguyenDoanHoang
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.11s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Quy định đăng ký môn học của trường rất rõ ràng. | Hướng dẫn đăng ký học phần của trường rất cụ thể. | Cao | 0.040 | Sai |
| 2 | Tôi đi mua một cây bút máy ở cửa hàng. | Cây bút máy của tôi không viết được nữa vì hết mực. | Cao | -0.059 | Sai |
| 3 | Trời hôm nay nắng nóng gay gắt. | Hôm nay trời đổ mưa lạnh buốt. | Thấp/Âm | -0.225 | Đúng |
| 4 | Học phí học kỳ này tăng nhẹ. | Chú mèo nhà em thích ngủ trên ghế sofa. | Thấp/Gần 0 | -0.077 | Đúng |
| 5 | Sinh viên được phép gia hạn sách thư viện. | Sinh viên không được phép gia hạn sách thư viện. | Cao | 0.131 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điểm số tương đồng giữa các câu đồng nghĩa (như cặp 1 và 2) đều rất thấp (gần 0) tương tự các câu khác chủ đề (như cặp 4) làm tôi khá bất ngờ. Điều này xảy ra do `MockEmbedder` chỉ là bộ giả lập băm chuỗi MD5 thành vector ngẫu nhiên để phục vụ unit test, không hề có học ngữ nghĩa thực sự. Khi sử dụng các mô hình embeddings thật (như OpenAI hay SBERT), cách vector biểu diễn ý nghĩa sẽ bám sát ngữ cảnh hơn, giúp các câu có từ đồng nghĩa đạt điểm similarity cao hơn bất chấp việc từ vựng khác nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thư viện yêu cầu gì khi mượn tài liệu? | library-services.md: > Khối metadata phía trên là **template mẫu**... | 0.082 | Có | [DEMO LLM] Generated answer from prompt preview: Use... |
| 2 | Sinh viên đăng ký học phần ở đâu? | library-services.md: > Khối metadata phía trên là **template mẫu**... | 0.210 | Không | [DEMO LLM] Generated answer from prompt preview: Use... |
| 3 | Phải làm gì khi đăng ký học phần bị trùng lịch? | library-services.md: > Khối metadata phía trên là **template mẫu**... | 0.130 | Không | [DEMO LLM] Generated answer from prompt preview: Use... |
| 4 | Đối tượng nào có thể sử dụng không gian học tập của thư viện? | course-registration.md: trước khi xác nhận đăng ký... | 0.031 | Không | [DEMO LLM] Generated answer from prompt preview: Use... |
| 5 | Yêu cầu ngoại lệ về đăng ký học phần cần gửi qua đâu? | library-services.md: > Khối metadata phía trên là **template mẫu**... | 0.063 | Không | [DEMO LLM] Generated answer from prompt preview: Use... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 1 / 5 (do mock embedder sinh vector ngẫu nhiên)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua phần chạy thử nghiệm, tôi học được rằng việc sử dụng các mô hình embedding thật (`EMBEDDING_PROVIDER=local`) là cực kỳ thiết yếu cho việc đánh giá chất lượng truy xuất RAG ngữ nghĩa tiếng Việt. Trình nhúng mock chỉ có tác dụng kiểm thử cấu trúc chương trình chứ hoàn toàn không phản ánh chất lượng chunking ngữ nghĩa. Ngoài ra, việc thiết kế pre-filtering bằng siêu dữ liệu (metadata) giúp tăng mạnh độ chính xác truy xuất bằng cách loại trừ các nguồn tài liệu ngoài đối tượng mục tiêu trước khi thực hiện tìm kiếm.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
