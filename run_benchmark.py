import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
load_dotenv(override=False)

from ingest import build_knowledge_base, load_documents, chunk_document
from src import (
    _mock_embed,
    LocalEmbedder,
    OpenAIEmbedder,
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
    CustomChunker,
    EmbeddingStore
)

# Select embedder
def get_embedder():
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder()
        except Exception as e:
            print(f"Failed to load LocalEmbedder: {e}. Falling back to mock.")
            return _mock_embed
    return _mock_embed

embedder = get_embedder()
print(f"Using embedder: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")

# Define the 4 chunkers matching the team members' strategies
chunkers = {
    "Đinh Quốc Trung (FixedSize)": FixedSizeChunker(chunk_size=500, overlap=50),
    "Trần Chí Tâm (Sentence)": SentenceChunker(max_sentences_per_chunk=3),
    "Nguyễn Doãn Hoàng (Recursive)": RecursiveChunker(chunk_size=400),
    "Phạm Hà Linh (Custom Heading)": CustomChunker(chunk_size=500)
}

queries = [
    ("Q1", "Khi đăng ký môn trên SIS, trạng thái nào xác nhận đăng ký thành công, và hệ thống xử lý thế nào nếu sinh viên chưa đủ điều kiện tiên quyết hoặc chọn hai môn trùng lịch?"),
    ("Q2", "Học bổng theo thành tích của VinUniversity dành cho đối tượng nào và bốn loại học bổng chính có mức hỗ trợ ra sao?"),
    ("Q3", "Hỗ trợ tài chính của VinUniversity dựa trên nhu cầu hay thành tích, hạn nộp hằng tháng và thời điểm thông báo kết quả là khi nào? Hồ sơ nộp muộn được xử lý ra sao?"),
    ("Q4", "Sinh viên đại học được mượn tối đa bao nhiêu sách, trong bao lâu, và chỉ được gia hạn khi đáp ứng những điều kiện nào?"),
    ("Q5", "Phí KTX hằng tháng cho phòng 4–8 người, phòng 2 người và KTX ngoài khuôn viên là bao nhiêu? Sinh viên phải đặt cọc bao nhiêu?")
]

data_dir = Path("data/vinuni-services")
if not data_dir.exists():
    print(f"Data directory {data_dir} does not exist!")
    sys.exit(1)

# Run benchmark for each strategy
for name, chunker in chunkers.items():
    print(f"\n==================================================")
    print(f"Strategy: {name}")
    print(f"==================================================")
    
    # Ingest documents using the specific chunker
    try:
        store = build_knowledge_base(data_dir, embedding_fn=embedder, chunker=chunker, collection_name=f"benchmark_{name.replace(' ', '_')}")
    except Exception as e:
        print(f"Failed to build knowledge base: {e}")
        continue
        
    print(f"Total chunks in store: {store.get_collection_size()}")
    
    # Execute the 5 queries
    for q_code, q_text in queries:
        print(f"\n[{q_code}] Query: {q_text}")
        
        # Determine filter
        metadata_filter = None
        if q_code == "Q2":
            metadata_filter = {"audience": "student"}
            
        if metadata_filter:
            results = store.search_with_filter(q_text, top_k=3, metadata_filter=metadata_filter)
            print(f"   (Ran with metadata filter: {metadata_filter})")
        else:
            results = store.search(q_text, top_k=3)
            
        if not results:
            print("   No results retrieved.")
            continue
            
        for idx, res in enumerate(results, 1):
            meta = res.get("metadata") or {}
            source = Path(meta.get("source", "unknown")).name
            doc_id = meta.get("doc_id", "unknown")
            chunk_idx = meta.get("chunk_index", "unknown")
            score = res.get("score", 0.0)
            content = res.get("content", "").strip().replace("\n", " ")[:90] + "..."
            audience = meta.get("audience", "none")
            
            print(f"   {idx}. Score={score:.3f} | doc={doc_id} (chunk {chunk_idx}) | audience={audience} | content: {content}")
