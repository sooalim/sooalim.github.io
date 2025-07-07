"""
Chunk Processor for RAG Agent

This module handles the intelligent chunking of documents for optimal
vector embedding and retrieval performance.
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

import nltk
import spacy
import tiktoken
from langdetect import detect

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChunkStrategy(Enum):
    """Enumeration of available chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SENTENCE_BASED = "sentence_based"
    PARAGRAPH_BASED = "paragraph_based"
    SEMANTIC_BASED = "semantic_based"
    RECURSIVE_CHARACTER = "recursive_character"
    TOKEN_BASED = "token_based"


@dataclass
class ChunkMetadata:
    """Metadata for document chunks."""
    chunk_id: str
    document_id: str
    chunk_index: int
    chunk_type: str
    start_position: int
    end_position: int
    token_count: int
    character_count: int
    sentence_count: int
    overlap_with_previous: int
    overlap_with_next: int
    language: str
    confidence_score: float = 1.0
    semantic_similarity: Optional[float] = None
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """Container for a document chunk with metadata."""
    content: str
    metadata: ChunkMetadata
    vector_embedding: Optional[List[float]] = None
    parent_content: Optional[str] = None
    child_chunks: List['DocumentChunk'] = field(default_factory=list)


class ChunkingStrategy(ABC):
    """Abstract base class for chunking strategies."""
    
    @abstractmethod
    def chunk(self, text: str, **kwargs) -> List[DocumentChunk]:
        """Chunk the input text according to the strategy."""
        pass
    
    @abstractmethod
    def get_optimal_chunk_size(self, text: str) -> int:
        """Get optimal chunk size for the given text."""
        pass


class FixedSizeChunker(ChunkingStrategy):
    """Fixed-size chunking strategy."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        """Initialize fixed-size chunker."""
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text into fixed-size segments."""
        try:
            logger.info(f"Chunking text with fixed size strategy (size: {self.chunk_size}, overlap: {self.overlap})")
            
            chunks = []
            document_id = kwargs.get('document_id', 'unknown')
            
            # Detect language
            try:
                language = detect(text[:1000])  # Use first 1000 chars for detection
            except:
                language = 'en'
            
            start = 0
            chunk_index = 0
            
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                
                # Adjust end to avoid cutting words
                if end < len(text):
                    # Find the last space before the end
                    last_space = text.rfind(' ', start, end)
                    if last_space > start:
                        end = last_space
                
                chunk_content = text[start:end].strip()
                
                if chunk_content:
                    # Calculate overlap
                    overlap_prev = min(self.overlap, start) if start > 0 else 0
                    overlap_next = min(self.overlap, len(text) - end) if end < len(text) else 0
                    
                    # Count tokens and sentences
                    token_count = len(chunk_content.split())
                    sentence_count = len(nltk.sent_tokenize(chunk_content))
                    
                    metadata = ChunkMetadata(
                        chunk_id=f"{document_id}_chunk_{chunk_index}",
                        document_id=document_id,
                        chunk_index=chunk_index,
                        chunk_type="fixed_size",
                        start_position=start,
                        end_position=end,
                        token_count=token_count,
                        character_count=len(chunk_content),
                        sentence_count=sentence_count,
                        overlap_with_previous=overlap_prev,
                        overlap_with_next=overlap_next,
                        language=language
                    )
                    
                    chunk = DocumentChunk(
                        content=chunk_content,
                        metadata=metadata
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Move start position considering overlap
                start = end - self.overlap if end < len(text) else len(text)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in fixed-size chunking: {str(e)}")
            raise
    
    def get_optimal_chunk_size(self, text: str) -> int:
        """Get optimal chunk size based on text characteristics."""
        avg_sentence_length = len(text) / max(len(nltk.sent_tokenize(text)), 1)
        avg_word_length = len(text) / max(len(text.split()), 1)
        
        # Adjust chunk size based on text characteristics
        if avg_sentence_length > 200:  # Long sentences
            return min(self.chunk_size * 2, 2000)
        elif avg_sentence_length < 50:  # Short sentences
            return max(self.chunk_size // 2, 500)
        
        return self.chunk_size


class SentenceBasedChunker(ChunkingStrategy):
    """Sentence-based chunking strategy."""
    
    def __init__(self, max_sentences: int = 10, overlap_sentences: int = 2):
        """Initialize sentence-based chunker."""
        self.max_sentences = max_sentences
        self.overlap_sentences = overlap_sentences
    
    def chunk(self, text: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text based on sentences."""
        try:
            logger.info(f"Chunking text with sentence-based strategy (max: {self.max_sentences}, overlap: {self.overlap_sentences})")
            
            chunks = []
            document_id = kwargs.get('document_id', 'unknown')
            
            # Detect language and tokenize sentences
            try:
                language = detect(text[:1000])
            except:
                language = 'en'
            
            sentences = nltk.sent_tokenize(text)
            
            if not sentences:
                return chunks
            
            chunk_index = 0
            i = 0
            
            while i < len(sentences):
                # Take up to max_sentences
                end_idx = min(i + self.max_sentences, len(sentences))
                chunk_sentences = sentences[i:end_idx]
                
                chunk_content = ' '.join(chunk_sentences).strip()
                
                if chunk_content:
                    # Calculate positions in original text
                    start_pos = text.find(sentences[i])
                    last_sentence = chunk_sentences[-1]
                    end_pos = text.find(last_sentence) + len(last_sentence)
                    
                    # Calculate overlap
                    overlap_prev = min(self.overlap_sentences, i) if i > 0 else 0
                    overlap_next = min(self.overlap_sentences, len(sentences) - end_idx) if end_idx < len(sentences) else 0
                    
                    # Count tokens
                    token_count = len(chunk_content.split())
                    
                    metadata = ChunkMetadata(
                        chunk_id=f"{document_id}_chunk_{chunk_index}",
                        document_id=document_id,
                        chunk_index=chunk_index,
                        chunk_type="sentence_based",
                        start_position=start_pos,
                        end_position=end_pos,
                        token_count=token_count,
                        character_count=len(chunk_content),
                        sentence_count=len(chunk_sentences),
                        overlap_with_previous=overlap_prev,
                        overlap_with_next=overlap_next,
                        language=language
                    )
                    
                    chunk = DocumentChunk(
                        content=chunk_content,
                        metadata=metadata
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Move to next chunk with overlap
                i = end_idx - self.overlap_sentences if end_idx < len(sentences) else len(sentences)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in sentence-based chunking: {str(e)}")
            raise
    
    def get_optimal_chunk_size(self, text: str) -> int:
        """Get optimal number of sentences per chunk."""
        sentences = nltk.sent_tokenize(text)
        avg_sentence_length = len(text) / max(len(sentences), 1)
        
        # Adjust based on average sentence length
        if avg_sentence_length > 100:  # Long sentences
            return max(self.max_sentences // 2, 3)
        elif avg_sentence_length < 30:  # Short sentences
            return min(self.max_sentences * 2, 20)
        
        return self.max_sentences


class TokenBasedChunker(ChunkingStrategy):
    """Token-based chunking using tiktoken for precise token counting."""
    
    def __init__(self, max_tokens: int = 1000, overlap_tokens: int = 100, model: str = "gpt-3.5-turbo"):
        """Initialize token-based chunker."""
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.model = model
        
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk(self, text: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text based on token count."""
        try:
            logger.info(f"Chunking text with token-based strategy (max: {self.max_tokens}, overlap: {self.overlap_tokens})")
            
            chunks = []
            document_id = kwargs.get('document_id', 'unknown')
            
            # Detect language
            try:
                language = detect(text[:1000])
            except:
                language = 'en'
            
            # Encode the entire text
            tokens = self.encoding.encode(text)
            
            if not tokens:
                return chunks
            
            chunk_index = 0
            start_token_idx = 0
            
            while start_token_idx < len(tokens):
                # Calculate end token index
                end_token_idx = min(start_token_idx + self.max_tokens, len(tokens))
                
                # Extract tokens for this chunk
                chunk_tokens = tokens[start_token_idx:end_token_idx]
                
                # Decode tokens back to text
                chunk_content = self.encoding.decode(chunk_tokens).strip()
                
                if chunk_content:
                    # Find positions in original text (approximate)
                    if start_token_idx == 0:
                        start_pos = 0
                    else:
                        start_text = self.encoding.decode(tokens[:start_token_idx])
                        start_pos = len(start_text)
                    
                    if end_token_idx >= len(tokens):
                        end_pos = len(text)
                    else:
                        end_text = self.encoding.decode(tokens[:end_token_idx])
                        end_pos = len(end_text)
                    
                    # Calculate overlap
                    overlap_prev = min(self.overlap_tokens, start_token_idx) if start_token_idx > 0 else 0
                    overlap_next = min(self.overlap_tokens, len(tokens) - end_token_idx) if end_token_idx < len(tokens) else 0
                    
                    # Count sentences
                    sentence_count = len(nltk.sent_tokenize(chunk_content))
                    
                    metadata = ChunkMetadata(
                        chunk_id=f"{document_id}_chunk_{chunk_index}",
                        document_id=document_id,
                        chunk_index=chunk_index,
                        chunk_type="token_based",
                        start_position=start_pos,
                        end_position=end_pos,
                        token_count=len(chunk_tokens),
                        character_count=len(chunk_content),
                        sentence_count=sentence_count,
                        overlap_with_previous=overlap_prev,
                        overlap_with_next=overlap_next,
                        language=language
                    )
                    
                    chunk = DocumentChunk(
                        content=chunk_content,
                        metadata=metadata
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Move to next chunk with overlap
                start_token_idx = end_token_idx - self.overlap_tokens if end_token_idx < len(tokens) else len(tokens)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in token-based chunking: {str(e)}")
            raise
    
    def get_optimal_chunk_size(self, text: str) -> int:
        """Get optimal token count per chunk."""
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)
        
        # Adjust based on total document size
        if total_tokens > 10000:  # Large document
            return min(self.max_tokens * 2, 2000)
        elif total_tokens < 500:  # Small document
            return max(self.max_tokens // 2, 250)
        
        return self.max_tokens


class SemanticChunker(ChunkingStrategy):
    """Semantic chunking using spaCy for linguistic analysis."""
    
    def __init__(self, similarity_threshold: float = 0.7, min_chunk_size: int = 100, max_chunk_size: int = 2000):
        """Initialize semantic chunker."""
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy English model not found. Using simple semantic chunking.")
            self.nlp = None
    
    def chunk(self, text: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text based on semantic similarity."""
        try:
            logger.info(f"Chunking text with semantic strategy (threshold: {self.similarity_threshold})")
            
            chunks = []
            document_id = kwargs.get('document_id', 'unknown')
            
            # Detect language
            try:
                language = detect(text[:1000])
            except:
                language = 'en'
            
            if not self.nlp:
                # Fallback to sentence-based chunking
                fallback_chunker = SentenceBasedChunker()
                return fallback_chunker.chunk(text, **kwargs)
            
            # Process text with spaCy
            doc = self.nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents]
            
            if not sentences:
                return chunks
            
            # Group sentences by semantic similarity
            current_chunk = [sentences[0]]
            chunk_index = 0
            
            for i in range(1, len(sentences)):
                current_text = ' '.join(current_chunk)
                candidate_text = current_text + ' ' + sentences[i]
                
                # Check if adding the sentence exceeds max size
                if len(candidate_text) > self.max_chunk_size:
                    # Finalize current chunk
                    if len(current_text) >= self.min_chunk_size:
                        chunk = self._create_semantic_chunk(
                            current_chunk, text, document_id, chunk_index, language
                        )
                        chunks.append(chunk)
                        chunk_index += 1
                    
                    # Start new chunk
                    current_chunk = [sentences[i]]
                else:
                    # Calculate semantic similarity
                    similarity = self._calculate_similarity(current_text, sentences[i])
                    
                    if similarity >= self.similarity_threshold:
                        current_chunk.append(sentences[i])
                    else:
                        # Finalize current chunk if it meets minimum size
                        if len(current_text) >= self.min_chunk_size:
                            chunk = self._create_semantic_chunk(
                                current_chunk, text, document_id, chunk_index, language
                            )
                            chunks.append(chunk)
                            chunk_index += 1
                        
                        # Start new chunk
                        current_chunk = [sentences[i]]
            
            # Handle remaining sentences
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunk = self._create_semantic_chunk(
                        current_chunk, text, document_id, chunk_index, language
                    )
                    chunks.append(chunk)
                elif chunks:
                    # Merge with last chunk if too small
                    chunks[-1].content += ' ' + chunk_text
                    chunks[-1].metadata.character_count = len(chunks[-1].content)
                    chunks[-1].metadata.token_count = len(chunks[-1].content.split())
                    chunks[-1].metadata.sentence_count += len(current_chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in semantic chunking: {str(e)}")
            raise
    
    def _create_semantic_chunk(self, sentences: List[str], full_text: str, 
                             document_id: str, chunk_index: int, language: str) -> DocumentChunk:
        """Create a semantic chunk from sentences."""
        
        chunk_content = ' '.join(sentences).strip()
        
        # Find positions in original text
        start_pos = full_text.find(sentences[0])
        last_sentence = sentences[-1]
        end_pos = full_text.find(last_sentence) + len(last_sentence)
        
        # Count tokens
        token_count = len(chunk_content.split())
        
        metadata = ChunkMetadata(
            chunk_id=f"{document_id}_chunk_{chunk_index}",
            document_id=document_id,
            chunk_index=chunk_index,
            chunk_type="semantic_based",
            start_position=start_pos,
            end_position=end_pos,
            token_count=token_count,
            character_count=len(chunk_content),
            sentence_count=len(sentences),
            overlap_with_previous=0,  # Semantic chunks don't have traditional overlap
            overlap_with_next=0,
            language=language
        )
        
        return DocumentChunk(
            content=chunk_content,
            metadata=metadata
        )
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between texts."""
        if not self.nlp:
            return 0.5  # Default similarity
        
        try:
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            
            return doc1.similarity(doc2)
        except:
            return 0.5  # Default similarity on error
    
    def get_optimal_chunk_size(self, text: str) -> int:
        """Get optimal chunk size for semantic chunking."""
        # For semantic chunking, size is determined by similarity
        return self.max_chunk_size


class RecursiveCharacterChunker(ChunkingStrategy):
    """Recursive character-based chunking with multiple separators."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 100, separators: List[str] = None):
        """Initialize recursive character chunker."""
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        if separators is None:
            self.separators = ["\n\n", "\n", ". ", " ", ""]
        else:
            self.separators = separators
    
    def chunk(self, text: str, **kwargs) -> List[DocumentChunk]:
        """Chunk text using recursive character splitting."""
        try:
            logger.info(f"Chunking text with recursive character strategy (size: {self.chunk_size})")
            
            document_id = kwargs.get('document_id', 'unknown')
            
            # Detect language
            try:
                language = detect(text[:1000])
            except:
                language = 'en'
            
            # Perform recursive splitting
            text_chunks = self._split_text_recursive(text, self.separators, self.chunk_size)
            
            # Convert to DocumentChunk objects
            chunks = []
            current_pos = 0
            
            for i, chunk_text in enumerate(text_chunks):
                if chunk_text.strip():
                    # Find actual position in original text
                    start_pos = text.find(chunk_text, current_pos)
                    if start_pos == -1:
                        start_pos = current_pos
                    end_pos = start_pos + len(chunk_text)
                    
                    # Count tokens and sentences
                    token_count = len(chunk_text.split())
                    sentence_count = len(nltk.sent_tokenize(chunk_text))
                    
                    # Calculate overlap
                    overlap_prev = self.overlap if i > 0 else 0
                    overlap_next = self.overlap if i < len(text_chunks) - 1 else 0
                    
                    metadata = ChunkMetadata(
                        chunk_id=f"{document_id}_chunk_{i}",
                        document_id=document_id,
                        chunk_index=i,
                        chunk_type="recursive_character",
                        start_position=start_pos,
                        end_position=end_pos,
                        token_count=token_count,
                        character_count=len(chunk_text),
                        sentence_count=sentence_count,
                        overlap_with_previous=overlap_prev,
                        overlap_with_next=overlap_next,
                        language=language
                    )
                    
                    chunk = DocumentChunk(
                        content=chunk_text.strip(),
                        metadata=metadata
                    )
                    
                    chunks.append(chunk)
                    current_pos = end_pos
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error in recursive character chunking: {str(e)}")
            raise
    
    def _split_text_recursive(self, text: str, separators: List[str], chunk_size: int) -> List[str]:
        """Recursively split text using different separators."""
        
        if not separators:
            return [text]
        
        separator = separators[0]
        new_separators = separators[1:]
        
        splits = text.split(separator)
        
        # Combine splits that are too small
        good_splits = []
        current_split = ""
        
        for split in splits:
            if len(current_split + separator + split) <= chunk_size:
                if current_split:
                    current_split += separator + split
                else:
                    current_split = split
            else:
                if current_split:
                    good_splits.append(current_split)
                current_split = split
        
        if current_split:
            good_splits.append(current_split)
        
        # Further split chunks that are still too large
        final_splits = []
        for split in good_splits:
            if len(split) > chunk_size and new_separators:
                final_splits.extend(self._split_text_recursive(split, new_separators, chunk_size))
            else:
                final_splits.append(split)
        
        return final_splits
    
    def get_optimal_chunk_size(self, text: str) -> int:
        """Get optimal chunk size for recursive chunking."""
        # Analyze text structure to determine optimal size
        paragraph_count = len(text.split('\n\n'))
        avg_paragraph_length = len(text) / max(paragraph_count, 1)
        
        if avg_paragraph_length > self.chunk_size:
            return min(self.chunk_size * 2, 2000)
        elif avg_paragraph_length < self.chunk_size / 2:
            return max(self.chunk_size // 2, 500)
        
        return self.chunk_size


class ChunkProcessor:
    """Main processor for document chunking operations."""
    
    def __init__(self):
        """Initialize chunk processor with available strategies."""
        self.strategies = {
            ChunkStrategy.FIXED_SIZE: FixedSizeChunker,
            ChunkStrategy.SENTENCE_BASED: SentenceBasedChunker,
            ChunkStrategy.TOKEN_BASED: TokenBasedChunker,
            ChunkStrategy.SEMANTIC_BASED: SemanticChunker,
            ChunkStrategy.RECURSIVE_CHARACTER: RecursiveCharacterChunker
        }
    
    def create_chunker(self, strategy: ChunkStrategy, **kwargs) -> ChunkingStrategy:
        """Create a chunker instance for the specified strategy."""
        
        if strategy not in self.strategies:
            raise ValueError(f"Unknown chunking strategy: {strategy}")
        
        chunker_class = self.strategies[strategy]
        return chunker_class(**kwargs)
    
    async def process_document(self, 
                             text: str, 
                             document_id: str,
                             strategy: ChunkStrategy = ChunkStrategy.RECURSIVE_CHARACTER,
                             **kwargs) -> List[DocumentChunk]:
        """Process a document using the specified chunking strategy."""
        
        try:
            logger.info(f"Processing document {document_id} with {strategy.value} strategy")
            
            # Create chunker
            chunker = self.create_chunker(strategy, **kwargs)
            
            # Perform chunking
            chunks = chunker.chunk(text, document_id=document_id, **kwargs)
            
            # Add hierarchical relationships
            for i, chunk in enumerate(chunks):
                if i > 0:
                    chunk.metadata.custom_metadata['previous_chunk_id'] = chunks[i-1].metadata.chunk_id
                if i < len(chunks) - 1:
                    chunk.metadata.custom_metadata['next_chunk_id'] = chunks[i+1].metadata.chunk_id
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            raise
    
    def get_strategy_recommendation(self, text: str, use_case: str = "general") -> Tuple[ChunkStrategy, Dict[str, Any]]:
        """Recommend the best chunking strategy and parameters for the given text."""
        
        text_length = len(text)
        sentence_count = len(nltk.sent_tokenize(text))
        avg_sentence_length = text_length / max(sentence_count, 1)
        
        # Analyze text structure
        paragraph_count = len(text.split('\n\n'))
        avg_paragraph_length = text_length / max(paragraph_count, 1)
        
        if use_case == "qa":
            # For Q&A, prefer sentence-based chunking
            return ChunkStrategy.SENTENCE_BASED, {
                'max_sentences': 8,
                'overlap_sentences': 2
            }
        elif use_case == "summarization":
            # For summarization, prefer larger semantic chunks
            return ChunkStrategy.SEMANTIC_BASED, {
                'similarity_threshold': 0.6,
                'min_chunk_size': 500,
                'max_chunk_size': 2000
            }
        elif use_case == "embedding":
            # For embeddings, prefer token-based chunking
            return ChunkStrategy.TOKEN_BASED, {
                'max_tokens': 512,
                'overlap_tokens': 50
            }
        elif avg_sentence_length > 150:
            # Long sentences - use recursive character splitting
            return ChunkStrategy.RECURSIVE_CHARACTER, {
                'chunk_size': 1500,
                'overlap': 150
            }
        elif sentence_count < 10:
            # Short documents - use fixed size
            return ChunkStrategy.FIXED_SIZE, {
                'chunk_size': 800,
                'overlap': 80
            }
        else:
            # Default - recursive character splitting
            return ChunkStrategy.RECURSIVE_CHARACTER, {
                'chunk_size': 1000,
                'overlap': 100
            }
    
    async def optimize_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Optimize chunks by merging small ones and splitting large ones."""
        
        optimized_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            
            # Check if chunk is too small
            if (current_chunk.metadata.character_count < 200 and 
                i < len(chunks) - 1):
                
                # Try to merge with next chunk
                next_chunk = chunks[i + 1]
                merged_content = current_chunk.content + " " + next_chunk.content
                
                if len(merged_content) <= 2000:  # Don't make chunks too large
                    # Create merged chunk
                    merged_metadata = ChunkMetadata(
                        chunk_id=current_chunk.metadata.chunk_id,
                        document_id=current_chunk.metadata.document_id,
                        chunk_index=current_chunk.metadata.chunk_index,
                        chunk_type=f"merged_{current_chunk.metadata.chunk_type}",
                        start_position=current_chunk.metadata.start_position,
                        end_position=next_chunk.metadata.end_position,
                        token_count=current_chunk.metadata.token_count + next_chunk.metadata.token_count,
                        character_count=len(merged_content),
                        sentence_count=current_chunk.metadata.sentence_count + next_chunk.metadata.sentence_count,
                        overlap_with_previous=current_chunk.metadata.overlap_with_previous,
                        overlap_with_next=next_chunk.metadata.overlap_with_next,
                        language=current_chunk.metadata.language
                    )
                    
                    merged_chunk = DocumentChunk(
                        content=merged_content,
                        metadata=merged_metadata
                    )
                    
                    optimized_chunks.append(merged_chunk)
                    i += 2  # Skip next chunk as it's been merged
                    continue
            
            optimized_chunks.append(current_chunk)
            i += 1
        
        return optimized_chunks


# Example usage
async def main():
    """Example usage of the chunk processor."""
    
    # Sample text
    sample_text = """
    Artificial Intelligence (AI) is transforming industries across the globe. Machine learning, a subset of AI, 
    enables computers to learn and improve from experience without being explicitly programmed. Deep learning, 
    a subset of machine learning, uses neural networks with multiple layers to model and understand complex patterns.
    
    Natural Language Processing (NLP) is another important branch of AI that focuses on the interaction between 
    computers and human language. It involves developing algorithms that can understand, interpret, and generate 
    human language in a valuable way.
    
    Computer vision is a field of AI that trains computers to interpret and understand the visual world. 
    Using digital images from cameras and videos and deep learning models, machines can accurately identify 
    and classify objects.
    """
    
    # Initialize processor
    processor = ChunkProcessor()
    
    # Get strategy recommendation
    strategy, params = processor.get_strategy_recommendation(sample_text, use_case="embedding")
    print(f"Recommended strategy: {strategy.value}")
    print(f"Recommended parameters: {params}")
    
    # Process document
    chunks = await processor.process_document(
        text=sample_text,
        document_id="sample_doc",
        strategy=strategy,
        **params
    )
    
    # Display results
    print(f"\nCreated {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"Chunk {chunk.metadata.chunk_index}:")
        print(f"  Content: {chunk.content[:100]}...")
        print(f"  Characters: {chunk.metadata.character_count}")
        print(f"  Tokens: {chunk.metadata.token_count}")
        print(f"  Sentences: {chunk.metadata.sentence_count}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
