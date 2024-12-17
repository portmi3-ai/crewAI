from pathlib import Path
from typing import Iterator, List, Union
from urllib.parse import urlparse

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
from docling_core.types.doc.document import DoclingDocument
from pydantic import Field

from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from crewai.utilities.constants import KNOWLEDGE_DIRECTORY
from crewai.utilities.logger import Logger


class DoclingSource(BaseKnowledgeSource):
    """Utility package for converting documents to markdown or json
    This will auto support PDF, DOCX, and TXT, XLSX, files without any additional dependencies.
    """

    _logger: Logger = Logger(verbose=True)

    file_path: List[str] = Field(default=None)
    file_paths: List[str] = Field(default_factory=list)
    document_converter: DocumentConverter = Field(default_factory=DocumentConverter)
    chunks: List[str] = Field(default_factory=list)
    safe_file_paths: List[Union[Path, str]] = Field(default_factory=list)
    content: List[DoclingDocument] = Field(default_factory=list)

    def model_post_init(self, _) -> None:
        if self.file_path:
            self._logger.log(
                "warning",
                "The 'file_path' attribute is deprecated and will be removed in a future version. Please use 'file_paths' instead.",
                color="yellow",
            )
            self.file_paths = self.file_path
        self.safe_file_paths = self._process_file_paths()
        self.document_converter = DocumentConverter(
            allowed_formats=[
                InputFormat.MD,
                InputFormat.ASCIIDOC,
                InputFormat.PDF,
                InputFormat.DOCX,
                InputFormat.HTML,
                InputFormat.IMAGE,
                InputFormat.XLSX,
                InputFormat.PPTX,
            ]
        )
        self.content = self.load_content()

    def load_content(self) -> List[DoclingDocument]:  # type: ignore
        try:
            return self.convert_source_to_docling_documents()
        except Exception as e:
            self._logger.log("error", f"Error loading content: {e}")
            return []

    def add(self) -> None:
        if self.content is None:
            return
        for doc in self.content:
            new_chunks = self._chunk_text(doc)
            self.chunks.extend(new_chunks)
        self._save_documents()

    def convert_source_to_docling_documents(self) -> List[DoclingDocument]:
        conv_results_iter = self.document_converter.convert_all(self.safe_file_paths)
        return [result.document for result in conv_results_iter]

    def _chunk_text(self, doc: DoclingDocument) -> Iterator[str]:  # type: ignore[override]
        chunker = HierarchicalChunker()
        for chunk in chunker.chunk(doc):
            yield chunk.text

    def _process_file_paths(self) -> List[Union[Path, str]]:
        processed_paths: List[Union[Path, str]] = []
        for path in self.file_paths:
            if isinstance(path, str):
                if path.startswith(("http://", "https://")):
                    try:
                        if self._validate_url(path):
                            processed_paths.append(path)
                        else:
                            raise ValueError(f"Invalid URL format: {path}")
                    except Exception as e:
                        raise ValueError(f"Invalid URL: {path}. Error: {str(e)}")
                else:
                    local_path = Path(KNOWLEDGE_DIRECTORY + "/" + path)
                    if local_path.exists():
                        processed_paths.append(local_path)
                    else:
                        raise FileNotFoundError(f"File not found: {local_path}")
            else:
                # this is an instance of Path
                processed_paths.append(path)
        return processed_paths

    def _validate_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all(
                [
                    result.scheme in ("http", "https"),
                    result.netloc,
                    len(result.netloc.split(".")) >= 2,  # Ensure domain has TLD
                ]
            )
        except Exception:
            return False
