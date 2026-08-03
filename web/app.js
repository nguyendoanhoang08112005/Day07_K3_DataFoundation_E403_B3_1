document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const queryInput = document.getElementById("query-input");
    const chatMessages = document.getElementById("chat-messages");
    const clearChatBtn = document.getElementById("clear-chat");
    const strategySelect = document.getElementById("strategy-select");
    const filterAudience = document.getElementById("filter-audience");
    const filterDept = document.getElementById("filter-dept");
    const chunksCount = document.getElementById("chunks-count");
    const retrievalTime = document.getElementById("retrieval-time");
    const retrievedChunksList = document.getElementById("retrieved-chunks-list");

    // Fetch initial status
    async function updateStatus() {
        try {
            const res = await fetch("/api/status?strategy=" + strategySelect.value);
            if (res.ok) {
                const data = await res.json();
                chunksCount.textContent = data.chunks_count + " chunks";
            }
        } catch (e) {
            console.error("Failed to fetch initial status:", e);
        }
    }

    strategySelect.addEventListener("change", updateStatus);
    updateStatus();

    // Suggestion items click handler
    document.querySelectorAll(".suggestion-item").forEach(item => {
        item.addEventListener("click", () => {
            queryInput.value = item.textContent.replace(" (Bật lọc student)", "");
            if (item.getAttribute("data-filter") === "student") {
                filterAudience.checked = true;
            }
            queryInput.focus();
        });
    });

    // Form submission
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        // Append user message
        appendMessage(query, "user");
        queryInput.value = "";

        // Show typing indicator
        const typingMsg = appendMessage("Đang truy xuất dữ liệu và xử lý câu trả lời...", "assistant typing");

        // Build request payload
        const metadataFilter = {};
        if (filterAudience.checked) {
            metadataFilter["audience"] = "student";
        }
        if (filterDept.value !== "none") {
            metadataFilter["department"] = filterDept.value;
        }

        const start = performance.now();

        try {
            const res = await fetch("/api/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    strategy: strategySelect.value,
                    metadata_filter: Object.keys(metadataFilter).length > 0 ? metadataFilter : null
                })
            });

            const duration = (performance.now() - start) / 1000;
            retrievalTime.textContent = duration.toFixed(2) + "s";

            // Remove typing message
            typingMsg.remove();

            if (res.ok) {
                const data = await res.json();
                
                // Append assistant message
                appendMessage(data.answer, "assistant");
                
                // Update inspector
                chunksCount.textContent = data.total_chunks + " chunks";
                renderRetrievedChunks(data.chunks);
            } else {
                appendMessage("Lỗi: Không thể nhận được câu trả lời từ máy chủ.", "assistant");
            }
        } catch (err) {
            typingMsg.remove();
            appendMessage("Lỗi kết nối đến máy chủ. Vui lòng kiểm tra lại.", "assistant");
            console.error(err);
        }
    });

    // Clear chat
    clearChatBtn.addEventListener("click", () => {
        chatMessages.innerHTML = `
            <div class="message assistant welcome">
                <div class="message-content">
                    Xin chào! Tôi là trợ lý học vụ thông minh của VinUniversity. Bạn có câu hỏi nào về quy chế đăng ký học phần, chính sách học bổng, hỗ trợ tài chính, mượn sách thư viện hoặc ký túc xá không?
                    <br><br>
                    <strong>Một số câu gợi ý từ bộ benchmark của nhóm:</strong>
                    <ul class="suggestions">
                        <li class="suggestion-item">Khi đăng ký môn trên SIS, trạng thái nào xác nhận đăng ký thành công, và hệ thống xử lý thế nào nếu sinh viên chưa đủ điều kiện tiên quyết hoặc chọn hai môn trùng lịch?</li>
                        <li class="suggestion-item" data-filter="student">Học bổng theo thành tích của VinUniversity dành cho đối tượng nào và bốn loại học bổng chính có mức hỗ trợ ra sao? (Bật lọc student)</li>
                        <li class="suggestion-item">Hỗ trợ tài chính của VinUniversity dựa trên nhu cầu hay thành tích, hạn nộp hằng tháng và thời điểm thông báo kết quả là khi nào?</li>
                        <li class="suggestion-item">Sinh viên đại học được mượn tối đa bao nhiêu sách, trong bao lâu, và chỉ được gia hạn khi đáp ứng những điều kiện nào?</li>
                    </ul>
                </div>
            </div>
        `;
        retrievedChunksList.innerHTML = `<p class="empty-text">Chưa thực hiện truy vấn nào. Hãy gửi câu hỏi để xem chi tiết các đoạn văn bản được vector store lọc ra.</p>`;
        retrievalTime.textContent = "-";
        
        // Re-attach suggestion click handlers
        document.querySelectorAll(".suggestion-item").forEach(item => {
            item.addEventListener("click", () => {
                queryInput.value = item.textContent.replace(" (Bật lọc student)", "");
                if (item.getAttribute("data-filter") === "student") {
                    filterAudience.checked = true;
                }
                queryInput.focus();
            });
        });
    });

    // Helper functions
    function appendMessage(text, senderClass) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${senderClass}`;
        
        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";
        contentDiv.innerHTML = text.replace(/\n/g, "<br>");
        
        msgDiv.appendChild(contentDiv);
        chatMessages.appendChild(msgDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return msgDiv;
    }

    function renderRetrievedChunks(chunks) {
        if (!chunks || chunks.length === 0) {
            retrievedChunksList.innerHTML = `<p class="empty-text">Không tìm thấy đoạn văn bản nào phù hợp.</p>`;
            return;
        }

        retrievedChunksList.innerHTML = "";
        chunks.forEach((chunk, index) => {
            const card = document.createElement("div");
            card.className = "chunk-card";
            
            const docId = chunk.metadata.doc_id || "unknown";
            const chunkIdx = chunk.metadata.chunk_index !== undefined ? chunk.metadata.chunk_index : "?";
            const audience = chunk.metadata.audience || "all";
            const score = chunk.score !== undefined ? chunk.score.toFixed(3) : "0.000";

            card.innerHTML = `
                <div class="chunk-header">
                    <span class="chunk-tag">Doc ID: ${docId}</span>
                    <span class="chunk-score">Similarity: ${score}</span>
                </div>
                <div class="chunk-body">
                    "${escapeHtml(chunk.content)}"
                </div>
                <div class="chunk-footer">
                    <span>Chunk Index: ${chunkIdx}</span>
                    <span>Audience: ${audience}</span>
                </div>
            `;
            retrievedChunksList.appendChild(card);
        });
    }

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
