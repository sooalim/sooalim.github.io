"""
Azure Cognitive Services Processor for RAG Agent

This module integrates with Azure Cognitive Services to provide advanced
document analysis, OCR, and natural language processing capabilities.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Container for cognitive services analysis results."""
    content: str
    confidence_scores: Dict[str, float]
    entities: List[Dict[str, Any]]
    key_phrases: List[str]
    sentiment: Dict[str, Any]
    language: str
    tables: List[Dict[str, Any]]
    layout_elements: List[Dict[str, Any]]
    custom_fields: Dict[str, Any]


class FormRecognizerProcessor:
    """Processor for Azure Form Recognizer service."""
    
    def __init__(self, endpoint: str, api_key: Optional[str] = None):
        """Initialize Form Recognizer client."""
        self.endpoint = endpoint
        
        if api_key:
            self.credential = AzureKeyCredential(api_key)
        else:
            self.credential = DefaultAzureCredential()
        
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
    
    async def analyze_document(self, document_path: str, model_id: str = "prebuilt-document") -> Dict[str, Any]:
        """Analyze document using Form Recognizer."""
        try:
            logger.info(f"Analyzing document with Form Recognizer: {document_path}")
            
            with open(document_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    model_id=model_id,
                    document=f
                )
                
            result = poller.result()
            
            # Extract content and structure
            content_parts = []
            tables = []
            key_value_pairs = []
            
            # Process pages
            for page in result.pages:
                page_content = []
                
                # Extract lines of text
                for line in page.lines:
                    page_content.append(line.content)
                
                if page_content:
                    content_parts.append('\n'.join(page_content))
            
            # Process tables
            for table in result.tables:
                table_data = []
                for cell in table.cells:
                    if len(table_data) <= cell.row_index:
                        table_data.extend([[] for _ in range(cell.row_index + 1 - len(table_data))])
                    
                    if len(table_data[cell.row_index]) <= cell.column_index:
                        table_data[cell.row_index].extend(['' for _ in range(cell.column_index + 1 - len(table_data[cell.row_index]))])
                    
                    table_data[cell.row_index][cell.column_index] = cell.content
                
                tables.append({
                    'data': table_data,
                    'row_count': table.row_count,
                    'column_count': table.column_count,
                    'confidence': table.confidence if hasattr(table, 'confidence') else 1.0
                })
            
            # Process key-value pairs
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    key_value_pairs.append({
                        'key': kv_pair.key.content,
                        'value': kv_pair.value.content,
                        'confidence': kv_pair.confidence
                    })
            
            return {
                'content': '\n\n'.join(content_parts),
                'tables': tables,
                'key_value_pairs': key_value_pairs,
                'page_count': len(result.pages),
                'confidence_scores': {
                    'overall': getattr(result, 'confidence', 1.0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document with Form Recognizer: {str(e)}")
            raise
    
    async def analyze_layout(self, document_path: str) -> Dict[str, Any]:
        """Analyze document layout and structure."""
        try:
            logger.info(f"Analyzing document layout: {document_path}")
            
            with open(document_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    model_id="prebuilt-layout",
                    document=f
                )
                
            result = poller.result()
            
            layout_elements = []
            
            # Process paragraphs
            for paragraph in result.paragraphs:
                layout_elements.append({
                    'type': 'paragraph',
                    'content': paragraph.content,
                    'role': paragraph.role,
                    'bounding_regions': [
                        {
                            'page_number': region.page_number,
                            'polygon': [(point.x, point.y) for point in region.polygon]
                        }
                        for region in paragraph.bounding_regions
                    ]
                })
            
            # Process selection marks
            for page in result.pages:
                for selection_mark in page.selection_marks:
                    layout_elements.append({
                        'type': 'selection_mark',
                        'state': selection_mark.state,
                        'confidence': selection_mark.confidence,
                        'bounding_box': {
                            'x': selection_mark.polygon[0].x,
                            'y': selection_mark.polygon[0].y,
                            'width': selection_mark.polygon[2].x - selection_mark.polygon[0].x,
                            'height': selection_mark.polygon[2].y - selection_mark.polygon[0].y
                        }
                    })
            
            return {
                'layout_elements': layout_elements,
                'page_count': len(result.pages)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing document layout: {str(e)}")
            raise
    
    async def analyze_receipts(self, document_path: str) -> Dict[str, Any]:
        """Analyze receipts using prebuilt receipt model."""
        try:
            logger.info(f"Analyzing receipt: {document_path}")
            
            with open(document_path, "rb") as f:
                poller = self.client.begin_analyze_document(
                    model_id="prebuilt-receipt",
                    document=f
                )
                
            result = poller.result()
            
            receipts = []
            for document in result.documents:
                receipt_data = {}
                
                for field_name, field in document.fields.items():
                    if field.value is not None:
                        receipt_data[field_name] = {
                            'value': field.value,
                            'confidence': field.confidence
                        }
                
                receipts.append(receipt_data)
            
            return {
                'receipts': receipts,
                'document_count': len(result.documents)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing receipt: {str(e)}")
            raise


class TextAnalyticsProcessor:
    """Processor for Azure Text Analytics service."""
    
    def __init__(self, endpoint: str, api_key: Optional[str] = None):
        """Initialize Text Analytics client."""
        self.endpoint = endpoint
        
        if api_key:
            self.credential = AzureKeyCredential(api_key)
        else:
            self.credential = DefaultAzureCredential()
        
        self.client = TextAnalyticsClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
    
    async def analyze_text(self, text: str, language: str = "en") -> Dict[str, Any]:
        """Perform comprehensive text analysis."""
        try:
            logger.info(f"Analyzing text with Text Analytics (length: {len(text)})")
            
            # Prepare documents
            documents = [{"id": "1", "language": language, "text": text}]
            
            # Detect language
            language_result = self.client.detect_language(documents=[{"id": "1", "text": text}])
            detected_language = language_result[0].primary_language.iso6391_name
            
            # Update documents with detected language
            documents[0]["language"] = detected_language
            
            # Sentiment analysis
            sentiment_result = self.client.analyze_sentiment(documents=documents)
            sentiment_scores = sentiment_result[0]
            
            # Key phrase extraction
            key_phrases_result = self.client.extract_key_phrases(documents=documents)
            key_phrases = key_phrases_result[0].key_phrases
            
            # Named entity recognition
            entities_result = self.client.recognize_entities(documents=documents)
            entities = []
            for entity in entities_result[0].entities:
                entities.append({
                    'text': entity.text,
                    'category': entity.category,
                    'subcategory': entity.subcategory,
                    'confidence_score': entity.confidence_score,
                    'offset': entity.offset,
                    'length': entity.length
                })
            
            # PII entity recognition
            pii_result = self.client.recognize_pii_entities(documents=documents)
            pii_entities = []
            for entity in pii_result[0].entities:
                pii_entities.append({
                    'text': entity.text,
                    'category': entity.category,
                    'subcategory': entity.subcategory,
                    'confidence_score': entity.confidence_score,
                    'offset': entity.offset,
                    'length': entity.length
                })
            
            return {
                'language': detected_language,
                'sentiment': {
                    'overall': sentiment_scores.sentiment,
                    'positive_score': sentiment_scores.confidence_scores.positive,
                    'neutral_score': sentiment_scores.confidence_scores.neutral,
                    'negative_score': sentiment_scores.confidence_scores.negative
                },
                'key_phrases': key_phrases,
                'entities': entities,
                'pii_entities': pii_entities,
                'text_length': len(text)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            raise
    
    async def extract_summary(self, text: str, language: str = "en", max_sentences: int = 3) -> Dict[str, Any]:
        """Extract text summary using extractive summarization."""
        try:
            logger.info(f"Extracting summary from text (length: {len(text)})")
            
            documents = [{"id": "1", "language": language, "text": text}]
            
            # Extractive summarization
            poller = self.client.begin_extract_summary(
                documents=documents,
                max_sentence_count=max_sentences
            )
            
            summary_result = poller.result()
            
            summary_sentences = []
            for sentence in summary_result[0].sentences:
                summary_sentences.append({
                    'text': sentence.text,
                    'rank_score': sentence.rank_score,
                    'offset': sentence.offset,
                    'length': sentence.length
                })
            
            summary_text = ' '.join([s['text'] for s in summary_sentences])
            
            return {
                'summary': summary_text,
                'sentences': summary_sentences,
                'original_length': len(text),
                'summary_length': len(summary_text),
                'compression_ratio': len(summary_text) / len(text) if len(text) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error extracting summary: {str(e)}")
            raise
    
    async def analyze_healthcare_text(self, text: str) -> Dict[str, Any]:
        """Analyze healthcare-related text for medical entities."""
        try:
            logger.info(f"Analyzing healthcare text (length: {len(text)})")
            
            documents = [text]
            
            poller = self.client.begin_analyze_healthcare_entities(documents)
            result = poller.result()
            
            healthcare_entities = []
            for doc in result:
                for entity in doc.entities:
                    healthcare_entities.append({
                        'text': entity.text,
                        'category': entity.category,
                        'subcategory': entity.subcategory,
                        'confidence_score': entity.confidence_score,
                        'offset': entity.offset,
                        'length': entity.length,
                        'normalized_text': entity.normalized_text
                    })
            
            return {
                'healthcare_entities': healthcare_entities,
                'entity_count': len(healthcare_entities)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing healthcare text: {str(e)}")
            raise


class CognitiveServicesProcessor:
    """Main processor that orchestrates all cognitive services."""
    
    def __init__(self, 
                 form_recognizer_endpoint: str,
                 text_analytics_endpoint: str,
                 form_recognizer_key: Optional[str] = None,
                 text_analytics_key: Optional[str] = None):
        """Initialize cognitive services processor."""
        
        self.form_recognizer = FormRecognizerProcessor(
            endpoint=form_recognizer_endpoint,
            api_key=form_recognizer_key
        )
        
        self.text_analytics = TextAnalyticsProcessor(
            endpoint=text_analytics_endpoint,
            api_key=text_analytics_key
        )
    
    async def process_document(self, 
                             document_path: str, 
                             analysis_types: List[str] = None) -> AnalysisResult:
        """Process document with specified analysis types."""
        
        if analysis_types is None:
            analysis_types = ['document', 'text_analytics']
        
        try:
            logger.info(f"Processing document with cognitive services: {document_path}")
            
            # Initialize result components
            content = ""
            confidence_scores = {}
            entities = []
            key_phrases = []
            sentiment = {}
            language = "en"
            tables = []
            layout_elements = []
            custom_fields = {}
            
            # Form Recognizer analysis
            if 'document' in analysis_types:
                form_result = await self.form_recognizer.analyze_document(document_path)
                content = form_result['content']
                tables = form_result['tables']
                confidence_scores.update(form_result['confidence_scores'])
                custom_fields['key_value_pairs'] = form_result['key_value_pairs']
                custom_fields['page_count'] = form_result['page_count']
            
            # Layout analysis
            if 'layout' in analysis_types:
                layout_result = await self.form_recognizer.analyze_layout(document_path)
                layout_elements = layout_result['layout_elements']
            
            # Receipt analysis
            if 'receipt' in analysis_types:
                receipt_result = await self.form_recognizer.analyze_receipts(document_path)
                custom_fields['receipts'] = receipt_result['receipts']
            
            # Text Analytics analysis
            if 'text_analytics' in analysis_types and content:
                text_result = await self.text_analytics.analyze_text(content)
                entities = text_result['entities']
                key_phrases = text_result['key_phrases']
                sentiment = text_result['sentiment']
                language = text_result['language']
                
                # Add PII entities to custom fields
                custom_fields['pii_entities'] = text_result['pii_entities']
            
            # Summary extraction
            if 'summary' in analysis_types and content:
                summary_result = await self.text_analytics.extract_summary(content)
                custom_fields['summary'] = summary_result
            
            # Healthcare analysis
            if 'healthcare' in analysis_types and content:
                healthcare_result = await self.text_analytics.analyze_healthcare_text(content)
                custom_fields['healthcare_entities'] = healthcare_result['healthcare_entities']
            
            return AnalysisResult(
                content=content,
                confidence_scores=confidence_scores,
                entities=entities,
                key_phrases=key_phrases,
                sentiment=sentiment,
                language=language,
                tables=tables,
                layout_elements=layout_elements,
                custom_fields=custom_fields
            )
            
        except Exception as e:
            logger.error(f"Error processing document with cognitive services: {str(e)}")
            raise
    
    async def process_text_only(self, text: str, analysis_types: List[str] = None) -> AnalysisResult:
        """Process text content without document analysis."""
        
        if analysis_types is None:
            analysis_types = ['text_analytics']
        
        try:
            logger.info(f"Processing text with cognitive services (length: {len(text)})")
            
            # Initialize result components
            confidence_scores = {}
            entities = []
            key_phrases = []
            sentiment = {}
            language = "en"
            custom_fields = {}
            
            # Text Analytics analysis
            if 'text_analytics' in analysis_types:
                text_result = await self.text_analytics.analyze_text(text)
                entities = text_result['entities']
                key_phrases = text_result['key_phrases']
                sentiment = text_result['sentiment']
                language = text_result['language']
                custom_fields['pii_entities'] = text_result['pii_entities']
            
            # Summary extraction
            if 'summary' in analysis_types:
                summary_result = await self.text_analytics.extract_summary(text)
                custom_fields['summary'] = summary_result
            
            # Healthcare analysis
            if 'healthcare' in analysis_types:
                healthcare_result = await self.text_analytics.analyze_healthcare_text(text)
                custom_fields['healthcare_entities'] = healthcare_result['healthcare_entities']
            
            return AnalysisResult(
                content=text,
                confidence_scores=confidence_scores,
                entities=entities,
                key_phrases=key_phrases,
                sentiment=sentiment,
                language=language,
                tables=[],
                layout_elements=[],
                custom_fields=custom_fields
            )
            
        except Exception as e:
            logger.error(f"Error processing text with cognitive services: {str(e)}")
            raise


# Factory function for easy initialization
def create_cognitive_processor(config: Dict[str, str]) -> CognitiveServicesProcessor:
    """Create cognitive services processor from configuration."""
    
    return CognitiveServicesProcessor(
        form_recognizer_endpoint=config['form_recognizer_endpoint'],
        text_analytics_endpoint=config['text_analytics_endpoint'],
        form_recognizer_key=config.get('form_recognizer_key'),
        text_analytics_key=config.get('text_analytics_key')
    )


# Example usage
async def main():
    """Example usage of the cognitive services processor."""
    
    # Configuration
    config = {
        'form_recognizer_endpoint': os.getenv('FORM_RECOGNIZER_ENDPOINT', 'https://your-form-recognizer.cognitiveservices.azure.com/'),
        'text_analytics_endpoint': os.getenv('TEXT_ANALYTICS_ENDPOINT', 'https://your-text-analytics.cognitiveservices.azure.com/'),
        'form_recognizer_key': os.getenv('FORM_RECOGNIZER_KEY'),
        'text_analytics_key': os.getenv('TEXT_ANALYTICS_KEY')
    }
    
    # Create processor
    processor = create_cognitive_processor(config)
    
    # Example: Process a document
    try:
        result = await processor.process_document(
            document_path="sample.pdf",
            analysis_types=['document', 'text_analytics', 'summary']
        )
        
        print(f"Content length: {len(result.content)}")
        print(f"Language: {result.language}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Key phrases: {result.key_phrases[:5]}")  # First 5 key phrases
        print(f"Entities found: {len(result.entities)}")
        print(f"Tables found: {len(result.tables)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
