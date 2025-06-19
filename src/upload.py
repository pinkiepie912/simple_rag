import os
from pathlib import Path

from clients.elasticsearch.es import ElasticsearchWriter
from clients.elasticsearch.dto import DocumentDTO

from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import PDFReader


class DocUploader:
    def __init__(self, es_writer: ElasticsearchWriter):
        self.es_writer = es_writer

    def upload(
        self,
        pdf_file_path: Path,
        chunk_size: int = 512,
        chunk_overlap_ratio: float = 0.2,
    ):
        # Use llama_index PDFReader
        reader = PDFReader()
        documents = reader.load_data(file=pdf_file_path)

        chunk_overlap = max(0, int(chunk_size * chunk_overlap_ratio))

        splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        nodes = splitter.get_nodes_from_documents(documents)

        indexed_doc_ids = []
        for i, node in enumerate(nodes):
            doc = DocumentDTO(
                doc_id=f"{os.path.basename(pdf_file_path)}_chunk_{i}",
                content=node.get_content(),
                metadata={"source": os.path.basename(pdf_file_path), "chunk_index": i},
            )
            self.es_writer.index_doc(doc)
            indexed_doc_ids.append(doc.doc_id)

        return indexed_doc_ids
