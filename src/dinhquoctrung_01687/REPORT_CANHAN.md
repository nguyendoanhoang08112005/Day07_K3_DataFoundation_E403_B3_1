# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đinh Quốc Trung
**Nhóm:** Nhóm B3_1 - K3
**Ngày:** 03/08/2026

> **Trạng thái bằng chứng:** Phần code và test đã được chạy trong môi trường local. Phần retrieval competition vẫn cần corpus, 5 benchmark queries và gold answers thống nhất của nhóm; không có số liệu nào được bịa.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Hai vector embedding tạo một góc nhỏ và hướng gần giống nhau; vì vậy model xem hai đoạn văn có pattern ngữ nghĩa tương đồng. Giá trị gần `1` biểu thị cùng hướng, gần `0` biểu thị ít liên quan và gần `-1` biểu thị hướng đối lập trong không gian vector.

**Ví dụ có độ tương tự CAO:**

- Câu A: “Sinh viên cần hoàn tất đăng ký học phần trước hạn.”
- Câu B: “Người học phải đăng ký môn đúng thời hạn.”
- Tại sao tương đồng: cùng actor, cùng hành động và cùng ràng buộc thời gian dù dùng từ khác nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: “Học phí phải được thanh toán trước ngày quy định.”
- Câu B: “Ký túc xá có giờ đóng cổng.”
- Tại sao khác: hai câu thuộc hai dịch vụ đại học khác nhau và không chia sẻ ý định chính.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**

Cosine tập trung vào hướng của vector thay vì độ lớn tuyệt đối, nên ít bị ảnh hưởng bởi scale hoặc độ dài biểu diễn. Với embedding đã normalize, cosine cũng tương đương dot product và thuận tiện để xếp hạng retrieval.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

\[
N = \left\lceil \frac{10{,}000 - 50}{500 - 50} \right\rceil
= \left\lceil \frac{9{,}950}{450} \right\rceil
= 23
\]

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100:**

\[
N = \left\lceil \frac{10{,}000 - 100}{500 - 100} \right\rceil
= \left\lceil \frac{9{,}900}{400} \right\rceil
= 25
\]

Số chunk tăng từ 23 lên 25 vì bước trượt giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ context ở biên chunk, nhưng làm tăng redundancy, storage và chi phí embedding/search.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm Chunking

**`SentenceChunker.chunk`**

Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu kết thúc câu nhưng vẫn giữ lại dấu câu. Sau đó chuẩn hóa khoảng trắng, bỏ phần rỗng và group tối đa `max_sentences_per_chunk`; input rỗng trả `[]`, còn văn bản không có dấu kết thúc vẫn tạo một chunk.

**`RecursiveChunker.chunk` / `_split`**

Thuật toán thử separator từ coarse đến fine: đoạn văn → dòng → câu → từ → ký tự. Base case là đoạn đã không vượt `chunk_size`; khi separator hiện tại không tách được thì chuyển sang separator tiếp theo, còn khi hết separator thì hard-split theo số ký tự. Tôi nối lại separator vào các unit để hạn chế làm mất nội dung khi chia.

**`compute_similarity` và `ChunkingStrategyComparator`**

Cosine similarity được tính bằng dot product chia cho tích hai magnitude, trả `0.0` nếu có zero vector và báo lỗi nếu số chiều không khớp. Comparator chạy cả FixedSize, Sentence và Recursive rồi trả count, average/min/max length và chunks để phục vụ phân tích.

### Lớp EmbeddingStore

**`add_documents` + `search`**

Mỗi `Document` được copy metadata, tự bổ sung `doc_id`, tạo embedding và lưu thành record có storage ID duy nhất. Search embed query, tính dot product với toàn bộ candidate, sort giảm dần và chỉ trả các field public gồm `id`, `content`, `metadata`, `score`; in-memory store là nguồn dữ liệu deterministic, còn Chroma được mirror khi thư viện khả dụng.

**`search_with_filter` + `delete_document`**

Metadata được pre-filter trước similarity search để giảm candidate set và bảo đảm tất cả kết quả thỏa điều kiện. `delete_document` xóa mọi chunk có `metadata['doc_id']` tương ứng, trả `True` nếu có phần tử bị xóa và đồng bộ xóa sang Chroma khi backend khả dụng.

### Tác tử KnowledgeBaseAgent

**`answer`**

Agent retrieve top-k chunks, gắn số thứ tự, source và score vào context, rồi tạo prompt buộc LLM chỉ dùng evidence được cung cấp. Prompt yêu cầu nói rõ khi context không đủ và khuyến khích tham chiếu `[1]`, `[2]`; input rỗng, `top_k <= 0` hoặc LLM trả sai kiểu đều được validation.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

```text
============================= test session starts ==============================
collected 42 items
...
============================== 42 passed in 0.05s ==============================
```

Lệnh tái lập:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. pytest tests/ -v
```

**Số lượng bài test vượt qua:** **42 / 42**.

> Test được chạy với Python 3.13 trong môi trường hiện tại để xác minh logic. Repository quy định Python 3.11 là môi trường chuẩn khi nộp, nên cần chạy lại cùng lệnh bằng Python 3.11 trên máy học viên trước khi push cuối.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                                             | Câu B                                                      | Dự đoán trước khi chạy | Điểm thực tế với `_mock_embed` | Đúng theo ngưỡng minh họa 0.30? |
| --: | ------------------------------------------------- | ---------------------------------------------------------- | ---------------------- | -----------------------------: | ------------------------------- |
|   1 | Sinh viên cần đăng ký học phần trước hạn.         | Người học phải hoàn tất đăng ký môn đúng thời hạn.         | Cao                    |                      -0.053898 | Không                           |
|   2 | Thư viện cho phép gia hạn sách trực tuyến.        | Sinh viên có thể kéo dài thời gian mượn sách qua hệ thống. | Cao                    |                      -0.094500 | Không                           |
|   3 | Học phí phải được thanh toán trước ngày quy định. | Ký túc xá có giờ đóng cổng.                                | Thấp                   |                       0.019872 | Có                              |
|   4 | Học bổng yêu cầu điểm trung bình tối thiểu.       | Điều kiện nhận học bổng bao gồm GPA tối thiểu.             | Cao                    |                       0.039894 | Không                           |
|   5 | Quy trình đăng ký môn học.                        | Thời tiết hôm nay có mưa.                                  | Thấp                   |                       0.126604 | Có                              |

**Kết quả bất ngờ nhất và bài học:**

Ba cặp tương đồng về ngữ nghĩa lại có score gần 0 hoặc âm. Đây không phải bằng chứng cosine similarity thất bại; `_mock_embed` sinh vector deterministic gần như ngẫu nhiên theo toàn bộ chuỗi, chỉ phù hợp unit test. Trước khi kết luận chiến lược retrieval, phải chạy lại bằng `LocalEmbedder` đa ngữ như README yêu cầu.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Chiến lược cá nhân đề xuất:** `HeadingSectionChunker(max_chars=900)` kết hợp metadata filter, vì tài liệu quy định/FAQ thường có heading phản ánh đúng đơn vị ngữ nghĩa mà người dùng hỏi.

|   # | Câu hỏi chung của nhóm | Top-1 Chunk | Score | Relevant? | Agent answer |
| --: | ---------------------- | ----------- | ----: | --------- | ------------ |
|   1 | CẦN NHÓM THỐNG NHẤT    | Chưa chạy   |     — | —         | —            |
|   2 | CẦN NHÓM THỐNG NHẤT    | Chưa chạy   |     — | —         | —            |
|   3 | CẦN NHÓM THỐNG NHẤT    | Chưa chạy   |     — | —         | —            |
|   4 | CẦN NHÓM THỐNG NHẤT    | Chưa chạy   |     — | —         | —            |
|   5 | CẦN NHÓM THỐNG NHẤT    | Chưa chạy   |     — | —         | —            |

**Bao nhiêu câu hỏi có chunk liên quan trong top-3:** Chưa đánh giá — cần cùng corpus, local embedder và gold answers của nhóm.

**Bằng chứng cần bổ sung trước khi nộp:**

1. 5–10 tài liệu thật có `source_url`, `retrieved_at`, `document_version`, `audience` và metadata hữu ích khác.
2. Đúng 5 benchmark queries; ít nhất một câu dùng `metadata_filter={"audience": "student"}`.
3. JSON output từ `scripts/run_group_benchmark.py` với `EMBEDDING_PROVIDER=local`.
4. Human relevance label và tóm tắt Agent answer cho từng query.

---

## Tự đánh giá tạm thời

| Tiêu chí                   | Điểm tự đánh giá |
| -------------------------- | ---------------: |
| Khởi động                  |            5 / 5 |
| Hướng tiếp cận             |          10 / 10 |
| Hoàn thiện code            |          30 / 30 |
| Dự đoán độ tương tự        |            5 / 5 |
| Kết quả retrieval          |   Chưa chấm / 10 |
| **Tạm tính trước Phase 2** |      **50 / 60** |
