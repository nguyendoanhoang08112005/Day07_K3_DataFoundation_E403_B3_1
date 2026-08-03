# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Chí Tâm
**Nhóm:** B3_1
**Ngày:** 03.08.2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần 1) nghĩa là hai vector có hướng gần như giống nhau trong không gian nhiều chiều, tức là hai văn bản có ngữ nghĩa và ngữ cảnh tương tự nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Machine learning is a subset of artificial intelligence"
- Câu B: "AI includes machine learning as one of its branches"
- Tại sao tương đồng: Cả hai câu đều nói về mối quan hệ giữa Machine Learning và AI, sử dụng các từ và khái niệm liên quan

**Ví dụ có độ tương tự THẤP:**
- Câu A: "The weather is sunny today"
- Câu B: "I am reading a book about quantum physics"
- Tại sao khác: Hai câu hoàn toàn thuộc các lĩnh vực khác nhau (thời tiết vs vật lý lượng tử), không có từ vựng hay ngữ nghĩa chung

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến hướng của vector (góc) chứ không phải độ lớn, phù hợp hơn với việc so sánh ý nghĩa văn bản. Hai văn bản dài ngắn khác nhau nhưng cùng chủ đề sẽ có cosine similarity cao, trong khi Euclidean distance sẽ cho kết quả khác biệt do ảnh hưởng của độ dài vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Kích thước bước nhảy (step) = chunk_size - overlap = 500 - 50 = 450
> - Số chunks = ceil(10000 / 450) = ceil(22.22) = 23 chunks
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, step = 500 - 100 = 400, số chunks = ceil(10000 / 400) = 25 chunks. Overlap nhiều hơn giúp giữ nguyên ngữ cảnh ở ranh giới chunk, tránh mất thông tin quan trọng khi chia cắt, đặc biệt hữu ích với các câu hoặc đoạn văn bị cắt ngang.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng regex `r'(?<=[.!?])\s*(?=[A-Z])|\.\n'` để phát hiện ranh giới câu. Regex này tách tại các dấu `.`, `!`, `?` theo sau là khoảng trắng và chữ hoa, hoặc dấu chấm trước xuống dòng. Sau khi tách thành danh sách câu, tôi nhóm chúng theo `max_sentences_per_chunk` và nối lại bằng khoảng trắng. Edge case được xử lý: text rỗng trả về list rỗng, câu quá dài vẫn giữ nguyên.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử từng separator theo thứ tự ưu tiên (`\n\n`, `\n`, `. `, ` `, `""`). Base case: khi hết separator hoặc text đã nhỏ hơn chunk_size thì trả về. Khi một phần văn bản vẫn lớn hơn chunk_size sau khi split, gọi đệ quy với separator tiếp theo. Nếu separator không tìm thấy trong text, chuyển sang separator kế tiếp.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi document được embed thành vector bằng `_embedding_fn`, sau đó lưu vào `_store` (in-memory) hoặc ChromaDB collection. Record bao gồm: id, content, embedding, và metadata (đã copy và thêm doc_id). Khi search, query được embed, tính dot product với tất cả vectors đã lưu, sắp xếp giảm dần theo score, trả về top_k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc trước (pre-filter) các records theo metadata_filter trước khi tính similarity. Với in-memory store, dùng list comprehension kiểm tra `all(record['metadata'].get(k) == v for k, v in metadata_filter.items())`. `delete_document` xóa tất cả records có `doc_id` trong metadata, trả về True nếu có record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tôi sử dụng pattern RAG: (1) Search top_k chunks từ store, (2) Build prompt với context được đánh số `[1]`, `[2]`, ... để dễ tham chiếu, (3) Gọi `llm_fn(prompt)` để generate answer. Prompt template có cấu trúc rõ ràng: phần "Context:" chứa các chunks, "Question:" chứa câu hỏi, "Answer:" là nơi LLM trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.12, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: D:\Hoc_voi_cha_hanh\AIInAction\Day07_-2A202601119_NguyenDoanHoang
plugins: anyio-4.14.2, langsmith-0.10.10, asyncio-1.4.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
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
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
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

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-------|-------|---------|--------------|-------|
| 1 | "How to register for courses online" | "Online course registration process" | cao | Mock (ngẫu nhiên) | Không xác định |
| 2 | "What is the library opening hours?" | "The library closes at 9 PM daily" | cao | Mock (ngẫu nhiên) | Không xác định |
| 3 | "Scholarship application deadline" | "The weather forecast for tomorrow" | thấp | Mock (ngẫu nhiên) | Không xác định |
| 4 | "Pay tuition fees by bank transfer" | "Bank transfer for tuition payment" | cao | Mock (ngẫu nhiên) | Không xác định |
| 5 | "Library card renewal procedures" | "How to renew your library card" | cao | Mock (ngẫu nhiên) | Không xác định |

*Lưu ý: Với mock embedder, điểm thực tế gần như ngẫu nhiên, không phản ánh chất lượng ngữ nghĩa thật. Cần dùng local embedder hoặc OpenAI embedder để có kết quả đáng tin cậy.*

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Với mock embedder, kết quả không đáng tin cậy vì nó chỉ tạo vectors dựa trên hash của text. Điều này cho thấy tầm quan trọng của việc chọn embedder phù hợp — mock chỉ dùng để test, không phản ánh semantic similarity thật. Với embedder thật, embeddings biểu diễn ý nghĩa qua việc học từ ngữ cảnh trong training data.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> *Phần này cần được hoàn thành sau khi nhóm thống nhất 5 câu hỏi đánh giá trong REPORT_NHOM.md*

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | [Câu hỏi 1 từ nhóm] | | | | |
| 2 | [Câu hỏi 2 từ nhóm] | | | | |
| 3 | [Câu hỏi 3 từ nhóm] | | | | |
| 4 | [Câu hỏi 4 từ nhóm] | | | | |
| 5 | [Câu hỏi 5 từ nhóm] | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> [Cần hoàn thành sau phần demo nhóm]

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
