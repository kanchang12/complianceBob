#!/usr/bin/env python3
"""
RAG System Initialization Script
Processes all regulatory PDFs and populates the vector database
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import traceback

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.pdf_processor import PDFProcessor
from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore


# Configure logging
def setup_logging(log_file: str = "data/rag_init.log"):
    """Setup logging configuration"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


class RAGInitializer:
    """Handles RAG system initialization"""
    
    def __init__(self, regulations_dir: str = "regulations", 
                 db_path: str = "compliance-guardian/database/compliance.db",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50):
        """
        Initialize RAG system
        
        Args:
            regulations_dir: Directory containing PDF files
            db_path: Path to SQLite database
            chunk_size: Size of text chunks in tokens (approximate characters)
            chunk_overlap: Overlap between chunks in tokens
        """
        self.logger = logging.getLogger(__name__)
        self.regulations_dir = regulations_dir
        self.db_path = db_path
        self.chunk_size = chunk_size * 4  # Approximate: 1 token ≈ 4 characters
        self.chunk_overlap = chunk_overlap * 4
        
        # Initialize components
        self.logger.info("Initializing RAG components...")
        self.pdf_processor = PDFProcessor()
        self.embedder = Embedder(model_name='text-embedding-3-small')
        self.vector_store = VectorStore(db_path=db_path)
        
        # Statistics
        self.stats = {
            'total_pdfs': 0,
            'processed_pdfs': 0,
            'failed_pdfs': 0,
            'total_chunks': 0,
            'total_embeddings': 0,
            'errors': []
        }
    
    def get_pdf_files(self) -> List[str]:
        """
        Get list of PDF files from regulations directory
        
        Returns:
            List of PDF file paths
        """
        pdf_files = []
        regulations_path = Path(self.regulations_dir)
        
        if not regulations_path.exists():
            self.logger.error(f"Regulations directory not found: {self.regulations_dir}")
            return pdf_files
        
        for file_path in regulations_path.glob("*.pdf"):
            pdf_files.append(str(file_path))
        
        self.logger.info(f"Found {len(pdf_files)} PDF files")
        return sorted(pdf_files)
    
    def process_pdf(self, pdf_path: str) -> Tuple[int, int]:
        """
        Process a single PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (chunks_created, embeddings_stored)
        """
        try:
            pdf_name = os.path.basename(pdf_path)
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing: {pdf_name}")
            self.logger.info(f"{'='*60}")
            
            # Extract text by pages
            self.logger.info("Extracting text from PDF...")
            pages_data = self.pdf_processor.extract_text_by_pages(pdf_path)
            self.logger.info(f"Extracted {len(pages_data)} pages")
            
            # Process each page and create chunks
            all_chunks = []
            chunk_metadata = []
            
            for page_data in pages_data:
                page_num = page_data['page_number']
                page_text = page_data['text']
                
                if not page_text.strip():
                    self.logger.warning(f"Page {page_num} is empty, skipping...")
                    continue
                
                # Chunk the page text
                chunks = self.pdf_processor.chunk_text(
                    page_text,
                    chunk_size=self.chunk_size,
                    overlap=self.chunk_overlap
                )
                
                # Store chunks with metadata
                for chunk_idx, chunk in enumerate(chunks):
                    if chunk.strip():  # Only store non-empty chunks
                        all_chunks.append(chunk)
                        chunk_metadata.append({
                            'source': pdf_name,
                            'page_number': page_num,
                            'chunk_index': chunk_idx,
                            'total_chunks_in_page': len(chunks)
                        })
            
            self.logger.info(f"Created {len(all_chunks)} chunks from {len(pages_data)} pages")
            
            if not all_chunks:
                self.logger.warning(f"No valid chunks created from {pdf_name}")
                return 0, 0
            
            # Generate embeddings
            self.logger.info("Generating embeddings...")
            embeddings = self.embedder.embed_batch(all_chunks, batch_size=32)
            self.logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Prepare data for batch storage
            embeddings_data = []
            document_id = pdf_name.replace('.pdf', '')
            
            for i, (chunk, embedding, metadata) in enumerate(zip(all_chunks, embeddings, chunk_metadata)):
                embeddings_data.append((
                    document_id,
                    chunk,
                    embedding,
                    metadata
                ))
            
            # Store embeddings in database
            self.logger.info("Storing embeddings in database...")
            self.vector_store.store_embeddings_batch(embeddings_data)
            self.logger.info(f"✓ Successfully stored {len(embeddings_data)} embeddings for {pdf_name}")
            
            return len(all_chunks), len(embeddings_data)
        
        except Exception as e:
            error_msg = f"Error processing {pdf_path}: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append({
                'file': pdf_path,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return 0, 0
    
    def verify_embeddings(self) -> bool:
        """
        Verify that embeddings were created successfully
        
        Returns:
            True if verification passed
        """
        try:
            self.logger.info("\n" + "="*60)
            self.logger.info("Verifying embeddings...")
            self.logger.info("="*60)
            
            cursor = self.vector_store.conn.cursor()
            
            # Count total embeddings
            cursor.execute("SELECT COUNT(*) as count FROM embeddings")
            total_count = cursor.fetchone()['count']
            
            # Count unique documents
            cursor.execute("SELECT COUNT(DISTINCT document_id) as count FROM embeddings")
            doc_count = cursor.fetchone()['count']
            
            # Get sample embedding to verify structure
            cursor.execute("SELECT * FROM embeddings LIMIT 1")
            sample = cursor.fetchone()
            
            self.logger.info(f"✓ Total embeddings in database: {total_count}")
            self.logger.info(f"✓ Unique documents: {doc_count}")
            
            if sample:
                self.logger.info(f"✓ Sample embedding verified:")
                self.logger.info(f"  - Document ID: {sample['document_id']}")
                self.logger.info(f"  - Chunk length: {len(sample['chunk_text'])} characters")
                self.logger.info(f"  - Embedding size: {len(sample['embedding'])} bytes")
            
            return total_count > 0
        
        except Exception as e:
            self.logger.error(f"Verification failed: {str(e)}")
            return False
    
    def print_statistics(self):
        """Print processing statistics"""
        self.logger.info("\n" + "="*60)
        self.logger.info("PROCESSING STATISTICS")
        self.logger.info("="*60)
        self.logger.info(f"Total PDFs found: {self.stats['total_pdfs']}")
        self.logger.info(f"Successfully processed: {self.stats['processed_pdfs']}")
        self.logger.info(f"Failed: {self.stats['failed_pdfs']}")
        self.logger.info(f"Total chunks created: {self.stats['total_chunks']}")
        self.logger.info(f"Total embeddings stored: {self.stats['total_embeddings']}")
        
        if self.stats['errors']:
            self.logger.info(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                self.logger.error(f"  - {error['file']}: {error['error']}")
        
        success_rate = (self.stats['processed_pdfs'] / self.stats['total_pdfs'] * 100) if self.stats['total_pdfs'] > 0 else 0
        self.logger.info(f"\nSuccess rate: {success_rate:.1f}%")
        self.logger.info("="*60)
    
    def run(self):
        """Run the RAG initialization process"""
        start_time = datetime.now()
        self.logger.info("\n" + "="*60)
        self.logger.info("RAG SYSTEM INITIALIZATION")
        self.logger.info("="*60)
        self.logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Regulations directory: {self.regulations_dir}")
        self.logger.info(f"Database path: {self.db_path}")
        self.logger.info(f"Chunk size: {self.chunk_size} characters (~{self.chunk_size//4} tokens)")
        self.logger.info(f"Chunk overlap: {self.chunk_overlap} characters (~{self.chunk_overlap//4} tokens)")
        
        # Get PDF files
        pdf_files = self.get_pdf_files()
        self.stats['total_pdfs'] = len(pdf_files)
        
        if not pdf_files:
            self.logger.error("No PDF files found. Exiting.")
            return False
        
        # Process each PDF
        for idx, pdf_path in enumerate(pdf_files, 1):
            self.logger.info(f"\n[{idx}/{len(pdf_files)}] Processing {os.path.basename(pdf_path)}...")
            
            chunks_created, embeddings_stored = self.process_pdf(pdf_path)
            
            if embeddings_stored > 0:
                self.stats['processed_pdfs'] += 1
                self.stats['total_chunks'] += chunks_created
                self.stats['total_embeddings'] += embeddings_stored
            else:
                self.stats['failed_pdfs'] += 1
        
        # Verify embeddings
        verification_passed = self.verify_embeddings()
        
        # Print statistics
        self.print_statistics()
        
        # Calculate duration
        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info(f"\nEnd time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Total duration: {duration}")
        
        # Close database connection
        self.vector_store.close()
        
        if verification_passed and self.stats['processed_pdfs'] > 0:
            self.logger.info("\n✓ RAG system initialization completed successfully!")
            return True
        else:
            self.logger.error("\n✗ RAG system initialization completed with errors.")
            return False


def main():
    """Main entry point"""
    # Setup logging
    logger = setup_logging()
    
    try:
        # Initialize and run
        initializer = RAGInitializer(
            regulations_dir="regulations",
            db_path="database/compliance.db",
            chunk_size=512,  # tokens
            chunk_overlap=50  # tokens
        )
        
        success = initializer.run()
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("\n\nProcess interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n\nFatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob