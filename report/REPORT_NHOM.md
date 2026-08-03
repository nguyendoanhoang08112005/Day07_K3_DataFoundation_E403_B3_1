# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> *1 câu — ví dụ: thư viện + đăng ký môn học.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| | | | |
| | | | |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Khi đăng ký môn trên SIS, trạng thái nào xác nhận đăng ký thành công, và hệ thống xử lý thế nào nếu sinh viên chưa đủ điều kiện tiên quyết hoặc chọn hai môn trùng lịch? | Đăng ký chỉ thành công khi môn có trạng thái **“Registered”**; trạng thái **“Selected”** nghĩa là chưa đăng ký thành công. SIS tự động chặn đăng ký nếu sinh viên không đáp ứng điều kiện tiên quyết và không cho phép đăng ký các môn có thời gian trùng nhau. | `vinuni-course-registration` — “Bước 4: Thêm vào giỏ và đăng ký”, “Điều kiện tiên quyết”, “Môn học trùng lịch” |
| 2 | Học bổng theo thành tích của VinUniversity dành cho đối tượng nào và bốn loại học bổng chính có mức hỗ trợ ra sao? **Bắt buộc lọc `audience: student`.** | Học bổng dành cho thí sinh có thành tích học tập xuất sắc và phẩm chất cá nhân nổi bật. Bốn loại chính gồm: **President's Excellence Scholarship:** 100% học phí và chi phí sinh hoạt; **Provost's Merit Scholarship:** 90%–100% học phí; **Dean's Distinction Scholarship:** 80% học phí; **Discipline's Honor Scholarship:** 50%, 60% hoặc 70% tùy chương trình. | `vinuni-scholarships` — “Học bổng theo thành tích (Merit-based Scholarship)”, “Các loại học bổng chính” |
| 3 | Hỗ trợ tài chính của VinUniversity dựa trên nhu cầu hay thành tích, hạn nộp hằng tháng và thời điểm thông báo kết quả là khi nào? Hồ sơ nộp muộn được xử lý ra sao? | Hỗ trợ tài chính là chương trình **dựa trên nhu cầu (need-based)**, không phải học bổng dựa trên thành tích. Hồ sơ phải nộp trước **23:59 ngày 15 hằng tháng** và kết quả được thông báo vào **ngày 15 tháng tiếp theo**; hồ sơ nộp sau hạn được chuyển sang chu kỳ xét duyệt tiếp theo. | `vinuni-financial-aid` — “Tổng quan”, “Thời gian xét duyệt”, “Lưu ý quan trọng” |
| 4 | Sinh viên đại học được mượn tối đa bao nhiêu sách, trong bao lâu, và chỉ được gia hạn khi đáp ứng những điều kiện nào? | Sinh viên đại học được mượn tối đa **3 cuốn trong 2 tuần** và gia hạn **1 lần**. Thời gian gia hạn bằng một nửa thời gian mượn ban đầu; tài liệu phải chưa quá hạn và không có người khác yêu cầu mượn. | `vinuni-library-borrowing-privileges` — “Đặc quyền mượn sách theo nhóm người dùng”, “Quy định gia hạn”; `vinuni-library-borrow-return-renew` — “Điều kiện gia hạn” |
| 5 | Phí KTX hằng tháng cho phòng 4–8 người, phòng 2 người và KTX ngoài khuôn viên là bao nhiêu? Sinh viên phải đặt cọc bao nhiêu? | Mức phí lần lượt là **3.200.000 VND/tháng/sinh viên** cho phòng 4–8 người, **4.000.000 VND/tháng/sinh viên** cho phòng 2 người và **4.500.000 VND/tháng/sinh viên** cho KTX ngoài khuôn viên. Tiền đặt cọc bằng **1 tháng tiền thuê** và được thanh toán cùng phí KTX. | `vinuni-dormitory-fees` — “Phí KTX trong khuôn viên”, “Phí KTX ngoài khuôn viên”, “Tiền đặt cọc (Security Deposit)” |

**Cấu hình benchmark bắt buộc cho câu 2:**

```python
metadata_filter = {"audience": "student"}
results = store.search_with_filter(query_2, top_k=3, metadata_filter=metadata_filter)
```

Câu 2 được dùng để so sánh trực tiếp `search()` với `search_with_filter()`. Kết quả lọc hợp lệ khi mọi chunk trả về đều có `metadata["audience"] == "student"`; các câu còn lại chạy không lọc để giữ độ bao phủ của bộ tài liệu.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
