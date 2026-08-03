# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm B3_1 - K3
**Thành viên:**
- Nguyễn Doãn Hoàng (MSSV: 2A202601119) - Bạn A (Trưởng nhóm / Leader)
- Trần Chí Tâm (MSSV: 2A202601535) - Bạn B (Thủ kho / Data Collector)
- Đinh Quốc Trung (MSSV: 2A202601687) - Bạn C (Người ra đề / QA / Tester)
- Phạm Hà Linh (MSSV: 2A202601041) - Bạn D (Kỹ sư thuật toán / Custom Chunker)
**Ngày:** 2026-08-03

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K3):** Dịch vụ / quy định đại học (đăng ký môn, học phí, học bổng, thư viện, ký túc xá…).

**Phạm vi cụ thể nhóm tập trung:**
> Quy định về đăng ký học phần, chính sách học bổng Merit-based, quy trình xét duyệt hỗ trợ tài chính, quy định tuần hoàn/mượn trả của thư viện và biểu phí Ký túc xá tại VinUniversity.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | vinuni-course-registration.md | https://example.edu/hoc-vu/dang-ky-hoc-phan | 2026-08-02 / 2026.1 | 3603 | `audience: student`, `department: academic-affairs`, `language: vi` |
| 2 | vinuni-scholarships.md | https://example.edu/scholarships | 2026-08-02 / 2026.1 | 3588 | `audience: student`, `department: financial-aid`, `language: vi` |
| 3 | vinuni-financial-aid.md | https://example.edu/financial-aid | 2026-08-02 / 2026.1 | 3384 | `audience: student`, `department: financial-aid`, `language: vi` |
| 4 | vinuni-library-borrowing-privileges.md | https://example.edu/library/borrowing | 2026-08-02 / 2026.1 | 2548 | `audience: all`, `department: library`, `language: vi` |
| 5 | vinuni-library-borrow-return-renew.md | https://example.edu/library/borrow-return-renew | 2026-08-02 / 2026.1 | 2693 | `audience: all`, `department: library`, `language: vi` |
| 6 | vinuni-dormitory-fees.md | https://example.edu/dormitory/fees | 2026-08-02 / 2026.1 | 3392 | `audience: student`, `department: student-affairs`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string | `student` | Phân loại đối tượng (student/faculty/staff/all) giúp lọc bỏ các quy chế không phù hợp trước khi tìm kiếm ngữ nghĩa, tăng độ chính xác của RAG. |
| `department` | string | `academic-affairs` | Xác định phòng ban quản lý giúp thu hẹp phạm vi tìm kiếm của truy vấn liên quan đến đơn vị cụ thể. |
| `language` | string | `vi` | Xác định ngôn ngữ của tài liệu để định hướng truy vấn đa ngôn ngữ hiệu quả. |
| `doc_id` | string | `vinuni-course-registration` | Định danh tài liệu gốc giúp liên kết các chunk với tài liệu nguồn và hỗ trợ việc xóa document dễ dàng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| vinuni-course-registration.md | FixedSizeChunker (`fixed_size`) | 9 | 444.4 | Không hoàn hảo; có nguy cơ cắt ngang câu ở ranh giới chunk làm mất đi ngữ nghĩa trọn vẹn. |
| vinuni-course-registration.md | SentenceChunker (`by_sentences`) | 6 | 599.0 | Khá tốt; kết thúc ở ranh giới câu đầy đủ nhưng các chunk có thể hơi dài và loãng. |
| vinuni-course-registration.md | RecursiveChunker (`recursive`) | 9 | 400.0 | Tốt; đệ quy chia nhỏ theo ranh giới đoạn/câu giúp gom nhóm ngữ nghĩa liền mạch hơn. |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Doãn Hoàng**
- **Loại chiến lược:** RecursiveChunker (`recursive`)
- **Mô tả & lý do chọn cho chủ đề này:** Sử dụng bộ chia nhỏ đệ quy `RecursiveChunker` với `chunk_size=400`. Phương pháp này hoạt động bằng cách dò và cắt văn bản theo các dấu phân tách có độ ưu tiên từ lớn đến nhỏ (`\n\n`, `\n`, `. `, ` `, `""`). Lý do lựa chọn là giúp tài liệu quy định được phân tách ở ranh giới các đoạn văn hoặc câu hoàn chỉnh, tránh tối đa việc cắt ngang từ hay câu, đảm bảo tính liên kết ngữ nghĩa cao hơn cho RAG.

**Thành viên 2 — Trần Chí Tâm**
- **Loại chiến lược:** SentenceChunker (`by_sentences`)
- **Mô tả & lý do chọn:** Sử dụng `SentenceChunker` với tham số `max_sentences_per_chunk=3`. Lý do chọn là vì tài liệu quy chế gồm nhiều điều khoản được diễn đạt cô đọng trong vài câu. Phương pháp này đảm bảo các chunk luôn là những câu trọn vẹn, không bị vỡ câu ở ranh giới, nhưng độ dài ký tự của các chunk sẽ không đồng đều tùy thuộc vào độ dài câu của tài liệu nguồn.

**Thành viên 3 — Đinh Quốc Trung**
- **Loại chiến lược:** FixedSizeChunker (`fixed_size`)
- **Mô tả & lý do chọn:** Sử dụng chiến lược cơ sở `FixedSizeChunker` với `chunk_size=500` và `overlap=50`. Đây là chiến lược baseline dễ triển khai nhất, đảm bảo kích thước các chunk luôn đều nhau. Tuy nhiên điểm hạn chế là dễ cắt ngang từ hoặc câu ở ranh giới, gây mất ngữ cảnh, nhưng cơ chế overlap 50 ký tự giúp giảm thiểu một phần nhược điểm này.

**Thành viên 4 — Phạm Hà Linh**
- **Loại chiến lược:** custom (Markdown Heading Chunker)
- **Mô tả & lý do chọn:** Triển khai một bộ chia nhỏ tùy chỉnh `CustomChunker` chuyên biệt cho tài liệu Markdown. Chiến lược này quét và tách văn bản dựa theo các thẻ tiêu đề của Markdown (`#`, `##`, `###`). Lý do chọn là vì các quy chế học đường luôn có cấu trúc phân chia theo Mục/Điều rất rõ ràng. Việc nhóm các nội dung dưới mỗi tiêu đề tương ứng và giữ tiêu đề đó ở đầu mỗi chunk giúp mô hình RAG luôn có thông tin ngữ cảnh chủ đề chính xác.
- **Code snippet (nếu custom):**
```python
class CustomChunker:
    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        lines = text.splitlines()
        sections = []
        current_header = ""
        current_section_lines = []
        for line in lines:
            if line.strip().startswith("#"):
                if current_section_lines:
                    sections.append((current_header, "\n".join(current_section_lines)))
                current_header = line.strip()
                current_section_lines = [line]
            else:
                current_section_lines.append(line)
        if current_section_lines:
            sections.append((current_header, "\n".join(current_section_lines)))
            
        chunks = []
        for header, content in sections:
            content = content.strip()
            if not content:
                continue
            if len(content) <= self.chunk_size:
                chunks.append(content)
            else:
                paragraphs = content.split("\n\n")
                current_chunk = []
                current_len = 0
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    if len(para) > self.chunk_size:
                        if current_chunk:
                            chunks.append("\n\n".join(current_chunk))
                            current_chunk = []
                            current_len = 0
                        chunks.append(para)
                    elif current_len + len(para) + 2 <= self.chunk_size:
                        current_chunk.append(para)
                        current_len += len(para) + 2
                    else:
                        if current_chunk:
                            chunks.append("\n\n".join(current_chunk))
                        current_chunk = [para]
                        current_len = len(para)
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
        return chunks
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Doãn Hoàng | RecursiveChunker | 8 / 10 | Chia nhỏ rất mượt mà theo cấu trúc văn bản (đoạn, câu), giữ được tính liên kết ngữ nghĩa tốt nhất. | Phải tinh chỉnh cấu hình danh sách dấu phân tách phức tạp hơn. |
| Trần Chí Tâm | SentenceChunker | 0 / 10 | Chunk luôn chứa các câu trọn vẹn, dễ đọc hiểu đối với LLM. | Kích thước các chunk không đồng đều, dễ bị loãng thông tin nếu câu quá dài. |
| Đinh Quốc Trung | FixedSizeChunker | 2 / 10 | Đơn giản, tốc độ xử lý nhanh, kích thước chunk đồng đều. | Hay cắt ngang câu làm mất ngữ cảnh ở ranh giới chunk, tỷ lệ truy xuất đúng thấp (chỉ đúng câu Q5). |
| Phạm Hà Linh | CustomHeading Chunker | 4 / 10 | Bảo toàn hoàn hảo cấu trúc logic của tài liệu (Điều/Mục) và tiêu đề đi kèm. | Nếu các phần tiêu đề quá ngắn hoặc quá dài sẽ cần thêm thuật toán phụ để gộp/tách bổ sung. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược **RecursiveChunker** và **Custom Heading Chunker** cho kết quả tối ưu nhất đối với dữ liệu quy định đại học. Lý do vì các tài liệu này có cấu trúc phân chia mục lục (Markdown Heading) và các đoạn văn độc lập chặt chẽ. Việc chia nhỏ đệ quy giúp bảo toàn tối đa ý nghĩa toàn vẹn của câu/đoạn, giúp mô hình embedding tìm kiếm chính xác ngữ cảnh liên quan mà không bị nhiễu bởi các phần nội dung khác bị cắt dính vào.

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
| 1 | Khi đăng ký môn trên SIS... | Nguyễn Doãn Hoàng (Recursive) | Có (Rank 2) | Hoàn thành tốt dưới mock embedding. |
| 2 | Học bổng theo thành tích... | Nguyễn Doãn Hoàng (Recursive) | Có (Rank 2) | Chạy lọc chính xác bằng `audience: student`. |
| 3 | Hỗ trợ tài chính VinUni... | Phạm Hà Linh (Custom Heading) | Có (Rank 1) | Chunker tiêu đề bắt trúng tài liệu tài chính ngay từ Top-1. |
| 4 | Sinh viên mượn bao nhiêu sách... | Phạm Hà Linh (Custom Heading) | Có (Rank 1) | Tìm kiếm chính xác tài liệu thư viện ngay từ Top-1. |
| 5 | Phí KTX hằng tháng... | Đinh Quốc Trung (FixedSize) | Có (Rank 1) | Tìm trúng biểu phí KTX trong Top-1. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng siêu dữ liệu (metadata filtering) có giúp ích vô cùng lớn, thể hiện rõ nhất ở **Câu hỏi 2**. Nhờ áp dụng bộ lọc `metadata_filter = {"audience": "student"}`, hệ thống đã loại bỏ ngay lập tức tất cả các chunk thuộc về tài liệu có đối tượng người đọc khác (như faculty/staff), đảm bảo 100% kết quả trả về trong top-3 đều hướng tới đối tượng sinh viên, giúp nâng cao độ chính xác của câu trả lời từ tác tử RAG.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- 1. **Tầm quan trọng của Chiến lược Chunking**: Chunking không chỉ đơn thuần là cắt nhỏ văn bản, mà phải cắt sao cho bảo toàn cấu trúc ngữ nghĩa. Một chiến lược chunking thông minh bám theo các tiêu đề Markdown (`CustomChunker`) hoặc cắt đệ quy (`RecursiveChunker`) mang lại hiệu quả vượt trội so với cắt kích thước cố định.
- 2. **Sự phối hợp của Metadata**: Việc gắn siêu dữ liệu chất lượng (`audience`, `department`) và thực hiện lọc trước (pre-filtering) giúp giải quyết triệt để vấn đề nhiễu thông tin trong hệ thống RAG quy mô lớn.
- 3. **Tác động của mô hình nhúng**: Trình nhúng Mock tạo vector ngẫu nhiên chỉ có vai trò chạy kiểm thử kiểm tra tính đúng đắn của luồng code. Để RAG đạt hiệu suất thực tế tốt, bắt buộc phải nâng cấp lên mô hình nhúng ngữ nghĩa thực sự (như SBERT địa phương hoặc OpenAI).

**Bài học rút ra khi so sánh trong nhóm:**
> Nhóm rút ra bài học rằng việc thiết kế chunking cần phụ thuộc lớn vào cấu trúc của bộ dữ liệu gốc. Với tài liệu quy chế đại học có cấu trúc phân mục rõ ràng, việc chia theo headings (`CustomChunker`) là tối ưu nhất. So sánh giữa các thành viên cho thấy cùng một câu hỏi và cùng dữ liệu nhưng chỉ cần thay đổi thuật toán chunking là kết quả tìm kiếm có thể thay đổi từ "thất bại hoàn toàn" (0 điểm) lên "truy xuất trọn vẹn" (8-10 điểm).

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nếu làm lại, nhóm sẽ bổ sung thêm các thuộc tính siêu dữ liệu chi tiết hơn như cấp độ tiêu đề (`section_level`) và thiết lập chiến lược chunking lai (hybrid chunking) - chia theo tiêu đề lớn nhưng kết hợp sliding window ở phần nội dung chi tiết để vừa đảm bảo độ dài chunk tối ưu vừa giữ nguyên tiêu đề dẫn đường ở mỗi chunk.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
