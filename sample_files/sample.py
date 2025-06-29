"""
RAG 시스템용 문서 적재 스크립트
이 스크립트는 텍스트 기반 문서를 SentenceSplitter를 사용하여 청킹하고,
Elasticsearch에 색인하는 기능을 제공합니다.
"""

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from elasticsearch import Elasticsearch, helpers
import uuid
import os
import time


def load_text_file(filepath: str) -> str:
    """파일에서 텍스트를 로드합니다."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def split_text_to_nodes(text: str, chunk_size: int = 512, chunk_overlap: int = 50) -> list[TextNode]:
    """텍스트를 SentenceSplitter로 분할하여 노드 생성"""
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.get_nodes_from_documents([text])


def create_doc_id() -> str:
    return str(uuid.uuid4())


def build_index_documents(nodes: list[TextNode], doc_id: str) -> list[dict]:
    """Elasticsearch 색인용 문서 변환"""
    return [
        {
            "_index": "rag-index",
            "_id": f"{doc_id}_{i}",
            "_source": {
                "doc_id": doc_id,
                "order": i,
                "content": node.text,
                "metadata": {
                    "length": len(node.text),
                    "node_id": node.id_,
                    "created_at": time.time()
                }
            }
        }
        for i, node in enumerate(nodes)
    ]


def store_documents_to_elasticsearch(docs: list[dict]):
    """Elasticsearch에 문서 색인"""
    client = Elasticsearch("http://localhost:9200")
    helpers.bulk(client, docs)
    print(f"{len(docs)}개의 청크를 Elasticsearch에 적재했습니다.")


def index_file(filepath: str):
    """단일 파일 색인 전체 플로우"""
    print(f"파일 로드 중: {filepath}")
    text = load_text_file(filepath)
    doc_id = create_doc_id()
    nodes = split_text_to_nodes(text)
    docs = build_index_documents(nodes, doc_id)
    store_documents_to_elasticsearch(docs)
    print("색인이 완료되었습니다.")


if __name__ == "__main__":
    path = "sample.txt"  # 여기에 적재할 파일 경로를 지정
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            for _ in range(300):  # 예시 텍스트 300개 줄 생성
                sentence = ''.join(random.choices(string.ascii_lowercase + ' ', k=100))
                f.write(sentence + "\n")
    index_file(path)