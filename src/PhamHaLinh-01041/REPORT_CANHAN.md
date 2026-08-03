# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Hà Linh  
**Mã sinh viên:** 2A202601041  
**Nhóm:** Chưa cập nhật  
**Ngày:** 03/08/2026

> Nộp 1 bản / sinh viên. Phần nhóm nộp chung trong `REPORT_NHOM.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) - Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**  
Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau, tức là hai đoạn văn bản có nội dung hoặc ý nghĩa gần nhau. Trong bài toán truy xuất văn bản, điểm cosine cao thường cho thấy chunk có khả năng liên quan đến câu hỏi.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên cần đăng ký học phần theo lịch của từng học kỳ.
- Câu B: Người học phải đăng ký môn học đúng thời gian nhà trường công bố.
- Tại sao tương đồng: Hai câu cùng nói về việc sinh viên đăng ký học phần/môn học theo lịch.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên cần kiểm tra học phần tiên quyết trước khi đăng ký.
- Câu B: Trời hôm nay có mưa lớn vào buổi chiều.
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau, một câu về học vụ và một câu về thời tiết.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**  
Cosine similarity tập trung vào hướng của vector, nên phù hợp để so sánh ý nghĩa văn bản ngay cả khi độ lớn vector khác nhau. Euclidean distance phụ thuộc nhiều vào khoảng cách tuyệt đối, nên có thể kém ổn định hơn khi so sánh embedding văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**  
Công thức:

```text
số chunk = ceil((độ dài tài liệu - overlap) / (chunk_size - overlap))
         = ceil((10000 - 50) / (500 - 50))
         = ceil(9950 / 450)
         = ceil(22.11)
         = 23 chunks
```

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**  
Khi `overlap=100`:

```text
số chunk = ceil((10000 - 100) / (500 - 100))
         = ceil(9900 / 400)
         = ceil(24.75)
         = 25 chunks
```

Số chunk tăng từ 23 lên 25 vì bước nhảy giữa hai chunk nhỏ hơn. Tăng overlap giúp giữ lại ngữ cảnh ở ranh giới giữa các chunk, giảm nguy cơ câu trả lời bị cắt mất thông tin quan trọng.

---

## 2. Hướng tiếp cận của tôi (My Approach) - Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` - hướng tiếp cận:**  
Tôi dùng regex `(?<=[.!?])\s+|(?<=\.)\n+` để tách văn bản theo ranh giới câu như dấu chấm, chấm hỏi, chấm than và xuống dòng sau dấu chấm. Sau khi tách, tôi loại bỏ khoảng trắng thừa và gom tối đa `max_sentences_per_chunk` câu vào một chunk. Nếu văn bản rỗng hoặc không có câu hợp lệ thì trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split` - hướng tiếp cận:**  
Tôi triển khai chia đệ quy theo thứ tự separator ưu tiên: đoạn văn, dòng, câu, khoảng trắng, rồi cuối cùng là cắt theo ký tự. Base case là khi đoạn hiện tại có độ dài nhỏ hơn hoặc bằng `chunk_size`, lúc đó trả về đoạn đó luôn. Nếu một đoạn vẫn quá dài sau khi split bằng separator hiện tại, hàm tiếp tục gọi `_split` với separator tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search` - hướng tiếp cận:**  
Mỗi `Document` được chuyển thành một record gồm `id`, `content`, `metadata` và `embedding`. Hàm `add_documents` nhúng nội dung bằng `embedding_fn` rồi lưu vào danh sách trong bộ nhớ. Khi search, query cũng được embed, sau đó tính score bằng dot product giữa query embedding và từng document embedding, rồi sắp xếp giảm dần để lấy top-k.

**`search_with_filter` + `delete_document` - hướng tiếp cận:**  
Với `search_with_filter`, tôi lọc metadata trước để chỉ giữ các record có đủ cặp key-value yêu cầu, sau đó mới search trên tập đã lọc. Với `delete_document`, tôi xóa tất cả record có `metadata["doc_id"]` trùng với `doc_id` được truyền vào. Hàm trả về `True` nếu có record bị xóa và `False` nếu không tìm thấy.

### Tác tử KnowledgeBaseAgent

**`answer` - hướng tiếp cận:**  
Agent nhận câu hỏi, gọi `store.search()` để lấy top-k chunk liên quan, rồi ghép các chunk đó thành phần `Context` trong prompt. Prompt yêu cầu mô hình trả lời dựa trên context đã truy xuất. Cuối cùng agent gọi `llm_fn(prompt)` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) - Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-9.1.1
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

======================== 42 passed, 1 warning in 0.15s ========================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) - Cá nhân (5 điểm)

Backend dùng để lấy điểm thực tế: `MockEmbedder`. Lưu ý: mock embedder tạo vector xác định nhưng không thật sự hiểu ngữ nghĩa, nên điểm số có thể không giống trực giác ngôn ngữ.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên cần đăng ký học phần đúng lịch học kỳ. | Người học phải đăng ký môn học theo thời gian nhà trường công bố. | cao | -0.0270 | Không |
| 2 | Thư viện cung cấp không gian học tập cho sinh viên. | Sinh viên có thể sử dụng thư viện để học tập và mượn tài liệu. | cao | -0.1993 | Không |
| 3 | Học phần có thể yêu cầu môn tiên quyết. | Trời hôm nay có mưa lớn vào buổi chiều. | thấp | -0.1704 | Có |
| 4 | Người dùng cần mang thẻ định danh khi mượn tài liệu. | Cần xuất trình thẻ hợp lệ khi sử dụng dịch vụ mượn sách. | cao | 0.0562 | Tương đối |
| 5 | Vector store dùng để tìm kiếm theo độ tương tự. | Bánh mì là món ăn phổ biến vào buổi sáng. | thấp | 0.1024 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**  
Kết quả bất ngờ nhất là các cặp câu có ý nghĩa gần nhau lại có điểm thấp hoặc âm. Điều này xảy ra vì `MockEmbedder` chỉ dùng để test kỹ thuật, tạo vector giả lập từ chuỗi chứ không học quan hệ ngữ nghĩa thật. Nếu dùng local multilingual embedder hoặc OpenAI embedder, điểm similarity sẽ phản ánh ý nghĩa văn bản tốt hơn.

---

## 5. Kết quả truy xuất của tôi (Competition Results) - Cá nhân (10 điểm)

Tôi chạy 5 câu hỏi đánh giá mẫu trên dữ liệu `data/k3_university`. Khi nhóm có bộ câu hỏi chính thức, phần này có thể thay bằng đúng 5 câu hỏi chung của nhóm.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên đăng ký học phần ở đâu? | Chunk từ `k3-course-registration`, nói về đăng ký học phần trong cổng học vụ theo lịch từng học kỳ. | 0.1166 | Có | Agent trả lời dựa trên chunk đăng ký học phần được truy xuất. |
| 2 | Khi bị trùng lịch học phần thì sinh viên cần làm gì? | Chunk từ `k3-course-registration`, có nội dung về lỗi trùng lịch và điều chỉnh lớp học phần trước hạn. | 0.1072 | Có | Agent dùng context về điều chỉnh lớp học phần để trả lời. |
| 3 | Học phần có thể yêu cầu điều kiện gì trước khi đăng ký? | Chunk từ `k3-course-registration`, nhắc đến học phần tiên quyết và kiểm tra điều kiện trước khi xác nhận. | 0.0271 | Có | Agent trả lời dựa trên thông tin học phần tiên quyết. |
| 4 | Ai có thể sử dụng dịch vụ thư viện? | Chunk từ `k3-library-services`, nói thư viện phục vụ sinh viên, giảng viên và nhân viên. | -0.0013 | Có | Agent trả lời dựa trên context dịch vụ thư viện. |
| 5 | Khi mượn tài liệu thư viện cần mang gì? | Chunk từ `k3-library-services`, nói người dùng cần mang thẻ định danh hợp lệ khi mượn tài liệu. | 0.1208 | Có | Agent dùng context về thẻ định danh hợp lệ để trả lời. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**  
Cùng một bộ tài liệu nhưng chiến lược chunking khác nhau có thể làm kết quả retrieval thay đổi rõ rệt. Chunk quá dài giữ được nhiều ngữ cảnh nhưng dễ nhiễu, còn chunk quá ngắn có thể mất ý. Metadata cũng rất hữu ích khi câu hỏi cần giới hạn theo phòng ban, đối tượng hoặc loại tài liệu.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation - tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
