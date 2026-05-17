**User:**

<task>
Create a RAG system test script at `compliance-guardian/scripts/test_rag.py` that verifies the RAG system works correctly.

The script should:

1. **Test Vector Store Connection**:
   - Connect to the SQLite database
   - Verify embeddings table exists and has data
   - Show count of stored embeddings

2. **Test Retrieval Functionality**:
   - Query the RAG system with sample compliance questions like:
     - "What are GDPR requirements for data processing?"
     - "What security controls does NIST recommend?"
     - "What are OWASP top security vulnerabilities?"
     - "What does EU AI Act say about high-risk AI systems?"
   
3. **Verify Results**:
   - For each query, retrieve top 5 most relevant chunks
   - Display: chunk text, source document, similarity score
   - Verify results are actually relevant to the query

4. **Test Edge Cases**:
   - Query with non-existent topic (should return low similarity scores)
   - Query with very specific regulation reference
   - Query with general security terms

5. **Performance Metrics**:
   - Measure query response time
   - Show average similarity scores
   - Verify retrieval speed is acceptable (<1 second per query)

6. **Output**:
   - Print test results in a clear format
   - Show PASS/FAIL for each test
   - Save detailed results to `data/rag_test_results.txt`

This will verify that the RAG system is properly initialized and can retrieve relevant compliance information before we integrate it with the compliance checker.
</task>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\init_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:05:33.238Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.00

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>


# Current Workspace Directory (c:/Users/kanch/Downloads/Bob) Files
doc.py
TECHNICAL_SPEC.md
compliance-guardian/
compliance-guardian/.gitignore
compliance-guardian/config.py
compliance-guardian/README.md
compliance-guardian/requirements.txt
compliance-guardian/data/
compliance-guardian/data/.gitkeep
compliance-guardian/database/
compliance-guardian/database/schema.sql
compliance-guardian/frontend/
compliance-guardian/frontend/index.html
compliance-guardian/frontend/script.js
compliance-guardian/frontend/styles.css
compliance-guardian/scripts/
compliance-guardian/scripts/init_rag.py
compliance-guardian/src/
compliance-guardian/src/__init__.py
compliance-guardian/src/analyzer/
compliance-guardian/src/analyzer/__init__.py
compliance-guardian/src/analyzer/file_parser.py
compliance-guardian/src/analyzer/repo_cloner.py
compliance-guardian/src/api/
compliance-guardian/src/api/__init__.py
compliance-guardian/src/api/app.py
compliance-guardian/src/checker/
compliance-guardian/src/checker/__init__.py
compliance-guardian/src/checker/deep_analyzer.py
compliance-guardian/src/checker/quick_scanner.py
compliance-guardian/src/checker/rules_engine.py
compliance-guardian/src/orchestrator/
compliance-guardian/src/orchestrator/__init__.py
compliance-guardian/src/orchestrator/workflow.py
compliance-guardian/src/rag/
compliance-guardian/src/rag/__init__.py
compliance-guardian/src/rag/embedder.py
compliance-guardian/src/rag/pdf_processor.py
compliance-guardian/src/rag/vector_store.py
compliance-guardian/src/reports/
compliance-guardian/src/reports/__init__.py
compliance-guardian/src/reports/detailed_report.py
compliance-guardian/src/reports/summary_generator.py
regulations/
regulations/CCPA_Full_Text.pdf
regulations/EU_AI_Act_2024.pdf
regulations/GDPR_2016.pdf
regulations/ISO27001_2022_Overview.pdf
regulations/Keeling_Schedule_for_UK_GDPR_-_DPDI_No2_Bill_as_introduced.pdf
regulations/NIST_AI_RMF_1.0.pdf
regulations/NIST_CSF_2.0.pdf
regulations/NIST_SP800_53_Rev5.pdf
regulations/owasp-top-10.pdf
regulations/privacysummary.pdf
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I'll create a comprehensive RAG system test script that verifies all aspects of the RAG system. Let me start by examining the existing RAG components to understand the structure.

<read_file>
<args>
<file>
<path>compliance-guardian/src/rag/vector_store.py</path>
</file>
<file>
<path>compliance-guardian/src/rag/embedder.py</path>
</file>
<file>
<path>compliance-guardian/scripts/init_rag.py</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'compliance-guardian/src/rag/vector_store.py', 'compliance-guardian/src/rag/embedder.py', 'compliance-guardian/scripts/init_rag.py'] Result:
<files>
<file><path>compliance-guardian/src/rag/vector_store.py</path>
<content lines="1-215">
  1 | """
  2 | Vector Store Module
  3 | SQLite-based vector storage with similarity search
  4 | """
  5 | 
  6 | import sqlite3
  7 | import numpy as np
  8 | from typing import List, Dict, Tuple
  9 | import json
 10 | import logging
 11 | 
 12 | logger = logging.getLogger(__name__)
 13 | 
 14 | 
 15 | class VectorStore:
 16 |     """Handles vector storage and similarity search using SQLite"""
 17 |     
 18 |     def __init__(self, db_path: str = "database/compliance.db"):
 19 |         """
 20 |         Initialize vector store
 21 |         
 22 |         Args:
 23 |             db_path: Path to SQLite database
 24 |         """
 25 |         self.db_path = db_path
 26 |         self.conn = None
 27 |         self._connect()
 28 |         self._create_tables()
 29 |     
 30 |     def _connect(self):
 31 |         """Establish database connection"""
 32 |         try:
 33 |             self.conn = sqlite3.connect(self.db_path)
 34 |             self.conn.row_factory = sqlite3.Row
 35 |             logger.info(f"Connected to database: {self.db_path}")
 36 |         except Exception as e:
 37 |             logger.error(f"Error connecting to database: {str(e)}")
 38 |             raise
 39 |     
 40 |     def _create_tables(self):
 41 |         """Create necessary tables if they don't exist"""
 42 |         try:
 43 |             cursor = self.conn.cursor()
 44 |             
 45 |             # Create embeddings table
 46 |             cursor.execute("""
 47 |                 CREATE TABLE IF NOT EXISTS embeddings (
 48 |                     id INTEGER PRIMARY KEY AUTOINCREMENT,
 49 |                     document_id TEXT NOT NULL,
 50 |                     chunk_text TEXT NOT NULL,
 51 |                     embedding BLOB NOT NULL,
 52 |                     metadata TEXT,
 53 |                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
 54 |                 )
 55 |             """)
 56 |             
 57 |             # Create index for faster lookups
 58 |             cursor.execute("""
 59 |                 CREATE INDEX IF NOT EXISTS idx_document_id 
 60 |                 ON embeddings(document_id)
 61 |             """)
 62 |             
 63 |             self.conn.commit()
 64 |             logger.info("Database tables created/verified")
 65 |         except Exception as e:
 66 |             logger.error(f"Error creating tables: {str(e)}")
 67 |             raise
 68 |     
 69 |     def store_embedding(self, document_id: str, chunk_text: str, 
 70 |                        embedding: np.ndarray, metadata: Dict = None):
 71 |         """
 72 |         Store an embedding in the database
 73 |         
 74 |         Args:
 75 |             document_id: Unique identifier for the document
 76 |             chunk_text: The text chunk
 77 |             embedding: The embedding vector
 78 |             metadata: Additional metadata as dictionary
 79 |         """
 80 |         try:
 81 |             cursor = self.conn.cursor()
 82 |             
 83 |             # Convert embedding to bytes
 84 |             embedding_bytes = embedding.tobytes()
 85 |             metadata_json = json.dumps(metadata) if metadata else None
 86 |             
 87 |             cursor.execute("""
 88 |                 INSERT INTO embeddings (document_id, chunk_text, embedding, metadata)
 89 |                 VALUES (?, ?, ?, ?)
 90 |             """, (document_id, chunk_text, embedding_bytes, metadata_json))
 91 |             
 92 |             self.conn.commit()
 93 |         except Exception as e:
 94 |             logger.error(f"Error storing embedding: {str(e)}")
 95 |             raise
 96 |     
 97 |     def store_embeddings_batch(self, embeddings_data: List[Tuple]):
 98 |         """
 99 |         Store multiple embeddings at once
100 |         
101 |         Args:
102 |             embeddings_data: List of tuples (document_id, chunk_text, embedding, metadata)
103 |         """
104 |         try:
105 |             cursor = self.conn.cursor()
106 |             
107 |             processed_data = []
108 |             for doc_id, text, embedding, metadata in embeddings_data:
109 |                 embedding_bytes = embedding.tobytes()
110 |                 metadata_json = json.dumps(metadata) if metadata else None
111 |                 processed_data.append((doc_id, text, embedding_bytes, metadata_json))
112 |             
113 |             cursor.executemany("""
114 |                 INSERT INTO embeddings (document_id, chunk_text, embedding, metadata)
115 |                 VALUES (?, ?, ?, ?)
116 |             """, processed_data)
117 |             
118 |             self.conn.commit()
119 |             logger.info(f"Stored {len(embeddings_data)} embeddings")
120 |         except Exception as e:
121 |             logger.error(f"Error storing batch embeddings: {str(e)}")
122 |             raise
123 |     
124 |     def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
125 |         """
126 |         Calculate cosine similarity between two vectors
127 |         
128 |         Args:
129 |             vec1: First vector
130 |             vec2: Second vector
131 |             
132 |         Returns:
133 |             Cosine similarity score
134 |         """
135 |         dot_product = np.dot(vec1, vec2)
136 |         norm1 = np.linalg.norm(vec1)
137 |         norm2 = np.linalg.norm(vec2)
138 |         return dot_product / (norm1 * norm2)
139 |     
140 |     def search_similar(self, query_embedding: np.ndarray, 
141 |                       top_k: int = 5, document_id: str = None) -> List[Dict]:
142 |         """
143 |         Search for similar embeddings
144 |         
145 |         Args:
146 |             query_embedding: Query embedding vector
147 |             top_k: Number of results to return
148 |             document_id: Optional filter by document ID
149 |             
150 |         Returns:
151 |             List of similar chunks with scores
152 |         """
153 |         try:
154 |             cursor = self.conn.cursor()
155 |             
156 |             # Fetch embeddings
157 |             if document_id:
158 |                 cursor.execute("""
159 |                     SELECT id, document_id, chunk_text, embedding, metadata
160 |                     FROM embeddings
161 |                     WHERE document_id = ?
162 |                 """, (document_id,))
163 |             else:
164 |                 cursor.execute("""
165 |                     SELECT id, document_id, chunk_text, embedding, metadata
166 |                     FROM embeddings
167 |                 """)
168 |             
169 |             results = []
170 |             for row in cursor.fetchall():
171 |                 # Convert bytes back to numpy array
172 |                 stored_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
173 |                 
174 |                 # Calculate similarity
175 |                 similarity = self.cosine_similarity(query_embedding, stored_embedding)
176 |                 
177 |                 results.append({
178 |                     'id': row['id'],
179 |                     'document_id': row['document_id'],
180 |                     'chunk_text': row['chunk_text'],
181 |                     'similarity': float(similarity),
182 |                     'metadata': json.loads(row['metadata']) if row['metadata'] else None
183 |                 })
184 |             
185 |             # Sort by similarity and return top_k
186 |             results.sort(key=lambda x: x['similarity'], reverse=True)
187 |             return results[:top_k]
188 |         
189 |         except Exception as e:
190 |             logger.error(f"Error searching similar embeddings: {str(e)}")
191 |             raise
192 |     
193 |     def delete_document_embeddings(self, document_id: str):
194 |         """
195 |         Delete all embeddings for a document
196 |         
197 |         Args:
198 |             document_id: Document identifier
199 |         """
200 |         try:
201 |             cursor = self.conn.cursor()
202 |             cursor.execute("DELETE FROM embeddings WHERE document_id = ?", (document_id,))
203 |             self.conn.commit()
204 |             logger.info(f"Deleted embeddings for document: {document_id}")
205 |         except Exception as e:
206 |             logger.error(f"Error deleting embeddings: {str(e)}")
207 |             raise
208 |     
209 |     def close(self):
210 |         """Close database connection"""
211 |         if self.conn:
212 |             self.conn.close()
213 |             logger.info("Database connection closed")
214 | 
215 | # Made with Bob
</content>
</file>
<file><path>compliance-guardian/src/rag/embedder.py</path>
<content lines="1-79">
 1 | """
 2 | Embedder Module
 3 | Creates embeddings using sentence-transformers
 4 | """
 5 | 
 6 | from sentence_transformers import SentenceTransformer
 7 | from typing import List
 8 | import numpy as np
 9 | import logging
10 | 
11 | logger = logging.getLogger(__name__)
12 | 
13 | 
14 | class Embedder:
15 |     """Handles text embedding generation"""
16 |     
17 |     def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
18 |         """
19 |         Initialize embedder with specified model
20 |         
21 |         Args:
22 |             model_name: Name of the sentence-transformer model to use
23 |         """
24 |         logger.info(f"Loading embedding model: {model_name}")
25 |         self.model = SentenceTransformer(model_name)
26 |         self.embedding_dimension = self.model.get_sentence_embedding_dimension()
27 |         logger.info(f"Model loaded. Embedding dimension: {self.embedding_dimension}")
28 |     
29 |     def embed_text(self, text: str) -> np.ndarray:
30 |         """
31 |         Create embedding for a single text
32 |         
33 |         Args:
34 |             text: Text to embed
35 |             
36 |         Returns:
37 |             Numpy array of embeddings
38 |         """
39 |         try:
40 |             embedding = self.model.encode(text, convert_to_numpy=True)
41 |             return embedding
42 |         except Exception as e:
43 |             logger.error(f"Error creating embedding: {str(e)}")
44 |             raise
45 |     
46 |     def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
47 |         """
48 |         Create embeddings for multiple texts
49 |         
50 |         Args:
51 |             texts: List of texts to embed
52 |             batch_size: Number of texts to process at once
53 |             
54 |         Returns:
55 |             Numpy array of embeddings
56 |         """
57 |         try:
58 |             logger.info(f"Creating embeddings for {len(texts)} texts")
59 |             embeddings = self.model.encode(
60 |                 texts,
61 |                 batch_size=batch_size,
62 |                 convert_to_numpy=True,
63 |                 show_progress_bar=True
64 |             )
65 |             return embeddings
66 |         except Exception as e:
67 |             logger.error(f"Error creating batch embeddings: {str(e)}")
68 |             raise
69 |     
70 |     def get_embedding_dimension(self) -> int:
71 |         """
72 |         Get the dimension of embeddings produced by this model
73 |         
74 |         Returns:
75 |             Embedding dimension
76 |         """
77 |         return self.embedding_dimension
78 | 
79 | # Made with Bob
</content>
</file>
<file><path>compliance-guardian/scripts/init_rag.py</path>
<content lines="1-336">
  1 | #!/usr/bin/env python3
  2 | """
  3 | RAG System Initialization Script
  4 | Processes all regulatory PDFs and populates the vector database
  5 | """
  6 | 
  7 | import os
  8 | import sys
  9 | import logging
 10 | from pathlib import Path
 11 | from datetime import datetime
 12 | from typing import List, Dict, Tuple
 13 | import traceback
 14 | 
 15 | # Add parent directory to path for imports
 16 | sys.path.insert(0, str(Path(__file__).parent.parent))
 17 | 
 18 | from src.rag.pdf_processor import PDFProcessor
 19 | from src.rag.embedder import Embedder
 20 | from src.rag.vector_store import VectorStore
 21 | 
 22 | 
 23 | # Configure logging
 24 | def setup_logging(log_file: str = "data/rag_init.log"):
 25 |     """Setup logging configuration"""
 26 |     os.makedirs(os.path.dirname(log_file), exist_ok=True)
 27 |     
 28 |     logging.basicConfig(
 29 |         level=logging.INFO,
 30 |         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
 31 |         handlers=[
 32 |             logging.FileHandler(log_file),
 33 |             logging.StreamHandler(sys.stdout)
 34 |         ]
 35 |     )
 36 |     return logging.getLogger(__name__)
 37 | 
 38 | 
 39 | class RAGInitializer:
 40 |     """Handles RAG system initialization"""
 41 |     
 42 |     def __init__(self, regulations_dir: str = "regulations", 
 43 |                  db_path: str = "compliance-guardian/database/compliance.db",
 44 |                  chunk_size: int = 512,
 45 |                  chunk_overlap: int = 50):
 46 |         """
 47 |         Initialize RAG system
 48 |         
 49 |         Args:
 50 |             regulations_dir: Directory containing PDF files
 51 |             db_path: Path to SQLite database
 52 |             chunk_size: Size of text chunks in tokens (approximate characters)
 53 |             chunk_overlap: Overlap between chunks in tokens
 54 |         """
 55 |         self.logger = logging.getLogger(__name__)
 56 |         self.regulations_dir = regulations_dir
 57 |         self.db_path = db_path
 58 |         self.chunk_size = chunk_size * 4  # Approximate: 1 token ≈ 4 characters
 59 |         self.chunk_overlap = chunk_overlap * 4
 60 |         
 61 |         # Initialize components
 62 |         self.logger.info("Initializing RAG components...")
 63 |         self.pdf_processor = PDFProcessor()
 64 |         self.embedder = Embedder(model_name='all-MiniLM-L6-v2')
 65 |         self.vector_store = VectorStore(db_path=db_path)
 66 |         
 67 |         # Statistics
 68 |         self.stats = {
 69 |             'total_pdfs': 0,
 70 |             'processed_pdfs': 0,
 71 |             'failed_pdfs': 0,
 72 |             'total_chunks': 0,
 73 |             'total_embeddings': 0,
 74 |             'errors': []
 75 |         }
 76 |     
 77 |     def get_pdf_files(self) -> List[str]:
 78 |         """
 79 |         Get list of PDF files from regulations directory
 80 |         
 81 |         Returns:
 82 |             List of PDF file paths
 83 |         """
 84 |         pdf_files = []
 85 |         regulations_path = Path(self.regulations_dir)
 86 |         
 87 |         if not regulations_path.exists():
 88 |             self.logger.error(f"Regulations directory not found: {self.regulations_dir}")
 89 |             return pdf_files
 90 |         
 91 |         for file_path in regulations_path.glob("*.pdf"):
 92 |             pdf_files.append(str(file_path))
 93 |         
 94 |         self.logger.info(f"Found {len(pdf_files)} PDF files")
 95 |         return sorted(pdf_files)
 96 |     
 97 |     def process_pdf(self, pdf_path: str) -> Tuple[int, int]:
 98 |         """
 99 |         Process a single PDF file
100 |         
101 |         Args:
102 |             pdf_path: Path to PDF file
103 |             
104 |         Returns:
105 |             Tuple of (chunks_created, embeddings_stored)
106 |         """
107 |         try:
108 |             pdf_name = os.path.basename(pdf_path)
109 |             self.logger.info(f"\n{'='*60}")
110 |             self.logger.info(f"Processing: {pdf_name}")
111 |             self.logger.info(f"{'='*60}")
112 |             
113 |             # Extract text by pages
114 |             self.logger.info("Extracting text from PDF...")
115 |             pages_data = self.pdf_processor.extract_text_by_pages(pdf_path)
116 |             self.logger.info(f"Extracted {len(pages_data)} pages")
117 |             
118 |             # Process each page and create chunks
119 |             all_chunks = []
120 |             chunk_metadata = []
121 |             
122 |             for page_data in pages_data:
123 |                 page_num = page_data['page_number']
124 |                 page_text = page_data['text']
125 |                 
126 |                 if not page_text.strip():
127 |                     self.logger.warning(f"Page {page_num} is empty, skipping...")
128 |                     continue
129 |                 
130 |                 # Chunk the page text
131 |                 chunks = self.pdf_processor.chunk_text(
132 |                     page_text,
133 |                     chunk_size=self.chunk_size,
134 |                     overlap=self.chunk_overlap
135 |                 )
136 |                 
137 |                 # Store chunks with metadata
138 |                 for chunk_idx, chunk in enumerate(chunks):
139 |                     if chunk.strip():  # Only store non-empty chunks
140 |                         all_chunks.append(chunk)
141 |                         chunk_metadata.append({
142 |                             'source': pdf_name,
143 |                             'page_number': page_num,
144 |                             'chunk_index': chunk_idx,
145 |                             'total_chunks_in_page': len(chunks)
146 |                         })
147 |             
148 |             self.logger.info(f"Created {len(all_chunks)} chunks from {len(pages_data)} pages")
149 |             
150 |             if not all_chunks:
151 |                 self.logger.warning(f"No valid chunks created from {pdf_name}")
152 |                 return 0, 0
153 |             
154 |             # Generate embeddings
155 |             self.logger.info("Generating embeddings...")
156 |             embeddings = self.embedder.embed_batch(all_chunks, batch_size=32)
157 |             self.logger.info(f"Generated {len(embeddings)} embeddings")
158 |             
159 |             # Prepare data for batch storage
160 |             embeddings_data = []
161 |             document_id = pdf_name.replace('.pdf', '')
162 |             
163 |             for i, (chunk, embedding, metadata) in enumerate(zip(all_chunks, embeddings, chunk_metadata)):
164 |                 embeddings_data.append((
165 |                     document_id,
166 |                     chunk,
167 |                     embedding,
168 |                     metadata
169 |                 ))
170 |             
171 |             # Store embeddings in database
172 |             self.logger.info("Storing embeddings in database...")
173 |             self.vector_store.store_embeddings_batch(embeddings_data)
174 |             self.logger.info(f"✓ Successfully stored {len(embeddings_data)} embeddings for {pdf_name}")
175 |             
176 |             return len(all_chunks), len(embeddings_data)
177 |         
178 |         except Exception as e:
179 |             error_msg = f"Error processing {pdf_path}: {str(e)}"
180 |             self.logger.error(error_msg)
181 |             self.logger.error(traceback.format_exc())
182 |             self.stats['errors'].append({
183 |                 'file': pdf_path,
184 |                 'error': str(e),
185 |                 'traceback': traceback.format_exc()
186 |             })
187 |             return 0, 0
188 |     
189 |     def verify_embeddings(self) -> bool:
190 |         """
191 |         Verify that embeddings were created successfully
192 |         
193 |         Returns:
194 |             True if verification passed
195 |         """
196 |         try:
197 |             self.logger.info("\n" + "="*60)
198 |             self.logger.info("Verifying embeddings...")
199 |             self.logger.info("="*60)
200 |             
201 |             cursor = self.vector_store.conn.cursor()
202 |             
203 |             # Count total embeddings
204 |             cursor.execute("SELECT COUNT(*) as count FROM embeddings")
205 |             total_count = cursor.fetchone()['count']
206 |             
207 |             # Count unique documents
208 |             cursor.execute("SELECT COUNT(DISTINCT document_id) as count FROM embeddings")
209 |             doc_count = cursor.fetchone()['count']
210 |             
211 |             # Get sample embedding to verify structure
212 |             cursor.execute("SELECT * FROM embeddings LIMIT 1")
213 |             sample = cursor.fetchone()
214 |             
215 |             self.logger.info(f"✓ Total embeddings in database: {total_count}")
216 |             self.logger.info(f"✓ Unique documents: {doc_count}")
217 |             
218 |             if sample:
219 |                 self.logger.info(f"✓ Sample embedding verified:")
220 |                 self.logger.info(f"  - Document ID: {sample['document_id']}")
221 |                 self.logger.info(f"  - Chunk length: {len(sample['chunk_text'])} characters")
222 |                 self.logger.info(f"  - Embedding size: {len(sample['embedding'])} bytes")
223 |             
224 |             return total_count > 0
225 |         
226 |         except Exception as e:
227 |             self.logger.error(f"Verification failed: {str(e)}")
228 |             return False
229 |     
230 |     def print_statistics(self):
231 |         """Print processing statistics"""
232 |         self.logger.info("\n" + "="*60)
233 |         self.logger.info("PROCESSING STATISTICS")
234 |         self.logger.info("="*60)
235 |         self.logger.info(f"Total PDFs found: {self.stats['total_pdfs']}")
236 |         self.logger.info(f"Successfully processed: {self.stats['processed_pdfs']}")
237 |         self.logger.info(f"Failed: {self.stats['failed_pdfs']}")
238 |         self.logger.info(f"Total chunks created: {self.stats['total_chunks']}")
239 |         self.logger.info(f"Total embeddings stored: {self.stats['total_embeddings']}")
240 |         
241 |         if self.stats['errors']:
242 |             self.logger.info(f"\nErrors encountered: {len(self.stats['errors'])}")
243 |             for error in self.stats['errors']:
244 |                 self.logger.error(f"  - {error['file']}: {error['error']}")
245 |         
246 |         success_rate = (self.stats['processed_pdfs'] / self.stats['total_pdfs'] * 100) if self.stats['total_pdfs'] > 0 else 0
247 |         self.logger.info(f"\nSuccess rate: {success_rate:.1f}%")
248 |         self.logger.info("="*60)
249 |     
250 |     def run(self):
251 |         """Run the RAG initialization process"""
252 |         start_time = datetime.now()
253 |         self.logger.info("\n" + "="*60)
254 |         self.logger.info("RAG SYSTEM INITIALIZATION")
255 |         self.logger.info("="*60)
256 |         self.logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
257 |         self.logger.info(f"Regulations directory: {self.regulations_dir}")
258 |         self.logger.info(f"Database path: {self.db_path}")
259 |         self.logger.info(f"Chunk size: {self.chunk_size} characters (~{self.chunk_size//4} tokens)")
260 |         self.logger.info(f"Chunk overlap: {self.chunk_overlap} characters (~{self.chunk_overlap//4} tokens)")
261 |         
262 |         # Get PDF files
263 |         pdf_files = self.get_pdf_files()
264 |         self.stats['total_pdfs'] = len(pdf_files)
265 |         
266 |         if not pdf_files:
267 |             self.logger.error("No PDF files found. Exiting.")
268 |             return False
269 |         
270 |         # Process each PDF
271 |         for idx, pdf_path in enumerate(pdf_files, 1):
272 |             self.logger.info(f"\n[{idx}/{len(pdf_files)}] Processing {os.path.basename(pdf_path)}...")
273 |             
274 |             chunks_created, embeddings_stored = self.process_pdf(pdf_path)
275 |             
276 |             if embeddings_stored > 0:
277 |                 self.stats['processed_pdfs'] += 1
278 |                 self.stats['total_chunks'] += chunks_created
279 |                 self.stats['total_embeddings'] += embeddings_stored
280 |             else:
281 |                 self.stats['failed_pdfs'] += 1
282 |         
283 |         # Verify embeddings
284 |         verification_passed = self.verify_embeddings()
285 |         
286 |         # Print statistics
287 |         self.print_statistics()
288 |         
289 |         # Calculate duration
290 |         end_time = datetime.now()
291 |         duration = end_time - start_time
292 |         self.logger.info(f"\nEnd time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
293 |         self.logger.info(f"Total duration: {duration}")
294 |         
295 |         # Close database connection
296 |         self.vector_store.close()
297 |         
298 |         if verification_passed and self.stats['processed_pdfs'] > 0:
299 |             self.logger.info("\n✓ RAG system initialization completed successfully!")
300 |             return True
301 |         else:
302 |             self.logger.error("\n✗ RAG system initialization completed with errors.")
303 |             return False
304 | 
305 | 
306 | def main():
307 |     """Main entry point"""
308 |     # Setup logging
309 |     logger = setup_logging()
310 |     
311 |     try:
312 |         # Initialize and run
313 |         initializer = RAGInitializer(
314 |             regulations_dir="regulations",
315 |             db_path="compliance-guardian/database/compliance.db",
316 |             chunk_size=512,  # tokens
317 |             chunk_overlap=50  # tokens
318 |         )
319 |         
320 |         success = initializer.run()
321 |         sys.exit(0 if success else 1)
322 |     
323 |     except KeyboardInterrupt:
324 |         logger.info("\n\nProcess interrupted by user")
325 |         sys.exit(1)
326 |     
327 |     except Exception as e:
328 |         logger.error(f"\n\nFatal error: {str(e)}")
329 |         logger.error(traceback.format_exc())
330 |         sys.exit(1)
331 | 
332 | 
333 | if __name__ == "__main__":
334 |     main()
335 | 
336 | # Made with Bob
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\init_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:05:39.561Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.01

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Now I'll create a comprehensive RAG system test script. Let me create the test script with all the required functionality.

<write_to_file>
<path>compliance-guardian/scripts/test_rag.py</path>
<content>#!/usr/bin/env python3
"""
RAG System Test Script
Comprehensive testing of the RAG system functionality
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import traceback
import sqlite3
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore


# Configure logging
def setup_logging(log_file: str = "data/rag_test.log"):
    """Setup logging configuration"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


class RAGTester:
    """Comprehensive RAG system testing"""
    
    def __init__(self, db_path: str = "compliance-guardian/database/compliance.db"):
        """
        Initialize RAG tester
        
        Args:
            db_path: Path to SQLite database
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        
        # Test results
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'performance_metrics': {}
        }
        
        # Sample queries for testing
        self.test_queries = [
            {
                'query': "What are GDPR requirements for data processing?",
                'expected_topics': ['GDPR', 'data processing', 'personal data', 'consent'],
                'min_similarity': 0.3
            },
            {
                'query': "What security controls does NIST recommend?",
                'expected_topics': ['NIST', 'security', 'controls', 'framework'],
                'min_similarity': 0.3
            },
            {
                'query': "What are OWASP top security vulnerabilities?",
                'expected_topics': ['OWASP', 'security', 'vulnerabilities', 'injection'],
                'min_similarity': 0.3
            },
            {
                'query': "What does EU AI Act say about high-risk AI systems?",
                'expected_topics': ['AI', 'high-risk', 'EU', 'artificial intelligence'],
                'min_similarity': 0.3
            }
        ]
        
        # Edge case queries
        self.edge_case_queries = [
            {
                'query': "What are the requirements for quantum computing in blockchain?",
                'description': "Non-existent topic (should return low similarity)",
                'max_similarity': 0.4
            },
            {
                'query': "GDPR Article 17 right to erasure",
                'description': "Very specific regulation reference",
                'min_similarity': 0.25
            },
            {
                'query': "security authentication encryption",
                'description': "General security terms",
                'min_similarity': 0.25
            }
        ]
        
        # Initialize components
        self.logger.info("Initializing RAG components for testing...")
        try:
            self.embedder = Embedder(model_name='all-MiniLM-L6-v2')
            self.vector_store = VectorStore(db_path=db_path)
            self.logger.info("✓ RAG components initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize RAG components: {str(e)}")
            raise
    
    def test_database_connection(self) -> bool:
        """
        Test 1: Verify database connection and structure
        
        Returns:
            True if test passed
        """
        test_name = "Database Connection Test"
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"TEST 1: {test_name}")
        self.logger.info(f"{'='*60}")
        
        try:
            # Check if database file exists
            if not os.path.exists(self.db_path):
                raise Exception(f"Database file not found: {self.db_path}")
            
            self.logger.info(f"✓ Database file exists: {self.db_path}")
            
            # Check if embeddings table exists
            cursor = self.vector_store.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='embeddings'
            """)
            
            if not cursor.fetchone():
                raise Exception("Embeddings table does not exist")
            
            self.logger.info("✓ Embeddings table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(embeddings)")
            columns = cursor.fetchall()
            expected_columns = ['id', 'document_id', 'chunk_text', 'embedding', 'metadata', 'created_at']
            actual_columns = [col[1] for col in columns]
            
            for col in expected_columns:
                if col not in actual_columns:
                    raise Exception(f"Missing column: {col}")
            
            self.logger.info(f"✓ Table structure verified: {', '.join(actual_columns)}")
            
            # Count embeddings
            cursor.execute("SELECT COUNT(*) as count FROM embeddings")
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise Exception("No embeddings found in database")
            
            self.logger.info(f"✓ Total embeddings in database: {count}")
            
            # Count unique documents
            cursor.execute("SELECT COUNT(DISTINCT document_id) as count FROM embeddings")
            doc_count = cursor.fetchone()[0]
            self.logger.info(f"✓ Unique documents: {doc_count}")
            
            # Get document list
            cursor.execute("SELECT DISTINCT document_id FROM embeddings")
            documents = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"✓ Documents in database:")
            for doc in documents:
                cursor.execute("SELECT COUNT(*) FROM embeddings WHERE document_id = ?", (doc,))
                doc_count = cursor.fetchone()[0]
                self.logger.info(f"  - {doc}: {doc_count} chunks")
            
            self._record_test_result(test_name, True, f"Database verified with {count} embeddings")
            return True
        
        except Exception as e:
            self.logger.error(f"✗ {test_name} FAILED: {str(e)}")
            self._record_test_result(test_name, False, str(e))
            return False
    
    def test_retrieval_functionality(self) -> bool:
        """
        Test 2: Test retrieval with sample queries
        
        Returns:
            True if test passed
        """
        test_name = "Retrieval Functionality Test"
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"TEST 2: {test_name}")
        self.logger.info(f"{'='*60}")
        
        all_passed = True
        query_times = []
        
        for idx, test_query in enumerate(self.test_queries, 1):
            query = test_query['query']
            expected_topics = test_query['expected_topics']
            min_similarity = test_query['min_similarity']
            
            self.logger.info(f"\n[Query {idx}/{len(self.test_queries)}] {query}")
            self.logger.info("-" * 60)
            
            try:
                # Measure query time
                start_time = time.time()
                
                # Create query embedding
                query_embedding = self.embedder.embed_text(query)
                
                # Search for similar chunks
                results = self.vector_store.search_similar(query_embedding, top_k=5)
                
                query_time = time.time() - start_time
                query_times.append(query_time)
                
                self.logger.info(f"Query time: {query_time:.3f} seconds")
                
                if not results:
                    raise Exception("No results returned")
                
                # Display results
                self.logger.info(f"\nTop 5 Results:")
                for i, result in enumerate(results, 1):
                    self.logger.info(f"\n  Result {i}:")
                    self.logger.info(f"    Source: {result['document_id']}")
                    self.logger.info(f"    Similarity: {result['similarity']:.4f}")
                    self.logger.info(f"    Page: {result['metadata'].get('page_number', 'N/A')}")
                    
                    # Show chunk preview (first 200 chars)
                    chunk_preview = result['chunk_text'][:200].replace('\n', ' ')
                    self.logger.info(f"    Text: {chunk_preview}...")
                
                # Verify relevance
                top_result = results[0]
                if top_result['similarity'] < min_similarity:
                    raise Exception(f"Top similarity {top_result['similarity']:.4f} below threshold {min_similarity}")
                
                # Check if expected topics appear in results
                all_text = ' '.join([r['chunk_text'].lower() for r in results[:3]])
                found_topics = [topic for topic in expected_topics if topic.lower() in all_text]
                
                self.logger.info(f"\n✓ Expected topics found: {', '.join(found_topics)}")
                
                if len(found_topics) == 0:
                    self.logger.warning(f"⚠ No expected topics found in results")
                
                self.logger.info(f"✓ Query {idx} PASSED")
            
            except Exception as e:
                self.logger.error(f"✗ Query {idx} FAILED: {str(e)}")
                all_passed = False
        
        # Calculate average query time
        avg_query_time = sum(query_times) / len(query_times) if query_times else 0
        self.test_results['performance_metrics']['avg_query_time'] = avg_query_time
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Average query time: {avg_query_time:.3f} seconds")
        
        if avg_query_time > 1.0:
            self.logger.warning(f"⚠ Average query time exceeds 1 second threshold")
        else:
            self.logger.info(f"✓ Query performance acceptable (<1 second)")
        
        self._record_test_result(
            test_name, 
            all_passed, 
            f"Tested {len(self.test_queries)} queries, avg time: {avg_query_time:.3f}s"
        )
        return all_passed
    
    def test_edge_cases(self) -> bool:
        """
        Test 3: Test edge cases
        
        Returns:
            True if test passed
        """
        test_name = "Edge Cases Test"
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"TEST 3: {test_name}")
        self.logger.info(f"{'='*60}")
        
        all_passed = True
        
        for idx, test_case in enumerate(self.edge_case_queries, 1):
            query = test_case['query']
            description = test_case['description']
            
            self.logger.info(f"\n[Edge Case {idx}/{len(self.edge_case_queries)}] {description}")
            self.logger.info(f"Query: {query}")
            self.logger.info("-" * 60)
            
            try:
                # Create query embedding
                query_embedding = self.embedder.embed_text(query)
                
                # Search for similar chunks
                results = self.vector_store.search_similar(query_embedding, top_k=5)
                
                if not results:
                    raise Exception("No results returned")
                
                # Display top result
                top_result = results[0]
                self.logger.info(f"Top result similarity: {top_result['similarity']:.4f}")
                self.logger.info(f"Source: {top_result['document_id']}")
                
                # Check constraints
                if 'max_similarity' in test_case:
                    if top_result['similarity'] > test_case['max_similarity']:
                        raise Exception(
                            f"Similarity {top_result['similarity']:.4f} exceeds max {test_case['max_similarity']}"
                        )
                    self.logger.info(f"✓ Similarity below max threshold")
                
                if 'min_similarity' in test_case:
                    if top_result['similarity'] < test_case['min_similarity']:
                        raise Exception(
                            f"Similarity {top_result['similarity']:.4f} below min {test_case['min_similarity']}"
                        )
                    self.logger.info(f"✓ Similarity above min threshold")
                
                self.logger.info(f"✓ Edge case {idx} PASSED")
            
            except Exception as e:
                self.logger.error(f"✗ Edge case {idx} FAILED: {str(e)}")
                all_passed = False
        
        self._record_test_result(test_name, all_passed, f"Tested {len(self.edge_case_queries)} edge cases")
        return all_passed
    
    def test_similarity_scores(self) -> bool:
        """
        Test 4: Verify similarity score distribution
        
        Returns:
            True if test passed
        """
        test_name = "Similarity Score Distribution Test"
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"TEST 4: {test_name}")
        self.logger.info(f"{'='*60}")
        
        try:
            all_similarities = []
            
            # Test with multiple queries
            test_queries = [
                "GDPR data protection",
                "NIST cybersecurity framework",
                "OWASP security vulnerabilities"
            ]
            
            for query in test_queries:
                query_embedding = self.embedder.embed_text(query)
                results = self.vector_store.search_similar(query_embedding, top_k=10)
                
                similarities = [r['similarity'] for r in results]
                all_similarities.extend(similarities)
            
            # Calculate statistics
            avg_similarity = np.mean(all_similarities)
            max_similarity = np.max(all_similarities)
            min_similarity = np.min(all_similarities)
            std_similarity = np.std(all_similarities)
            
            self.logger.info(f"Similarity Statistics:")
            self.logger.info(f"  Average: {avg_similarity:.4f}")
            self.logger.info(f"  Maximum: {max_similarity:.4f}")
            self.logger.info(f"  Minimum: {min_similarity:.4f}")
            self.logger.info(f"  Std Dev: {std_similarity:.4f}")
            
            # Store metrics
            self.test_results['performance_metrics']['avg_similarity'] = float(avg_similarity)
            self.test_results['performance_metrics']['max_similarity'] = float(max_similarity)
            self.test_results['performance_metrics']['min_similarity'] = float(min_similarity)
            
            # Verify reasonable distribution
            if avg_similarity < 0.2:
                raise Exception(f"Average similarity too low: {avg_similarity:.4f}")
            
            if max_similarity < 0.3:
                raise Exception(f"Maximum similarity too low: {max_similarity:.4f}")
            
            self.logger.info(f"✓ Similarity scores within acceptable range")
            
            self._record_test_result(test_name, True, f"Avg similarity: {avg_similarity:.4f}")
            return True
        
        except Exception as e:
            self.logger.error(f"✗ {test_name} FAILED: {str(e)}")
            self._record_test_result(test_name, False, str(e))
            return False
    
    def _record_test_result(self, test_name: str, passed: bool, details: str):
        """Record test result"""
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
        else:
            self.test_results['failed_tests'] += 1
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'details': details
        })
    
    def print_summary(self):
        """Print test summary"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info("TEST SUMMARY")
        self.logger.info(f"{'='*60}")
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        
        self.logger.info(f"Total Tests: {total}")
        self.logger.info(f"Passed: {passed} ✓")
        self.logger.info(f"Failed: {failed} ✗")
        
        if total > 0:
            success_rate = (passed / total) * 100
            self.logger.info(f"Success Rate: {success_rate:.1f}%")
        
        self.logger.info(f"\nPerformance Metrics:")
        for metric, value in self.test_results['performance_metrics'].items():
            self.logger.info(f"  {metric}: {value:.4f}")
        
        self.logger.info(f"\nDetailed Results:")
        for result in self.test_results['test_details']:
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            self.logger.info(f"  {status} - {result['test_name']}")
            self.logger.info(f"    {result['details']}")
        
        self.logger.info(f"{'='*60}")
    
    def save_results(self, output_file: str = "data/rag_test_results.txt"):
        """Save detailed results to file"""
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*60 + "\n")
                f.write("RAG SYSTEM TEST RESULTS\n")
                f.write("="*60 + "\n")
                f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Database: {self.db_path}\n\n")
                
                f.write("SUMMARY\n")
                f.write("-"*60 + "\n")
                f.write(f"Total Tests: {self.test_results['total_tests']}\n")
                f.write(f"Passed: {self.test_results['passed_tests']}\n")
                f.write(f"Failed: {self.test_results['failed_tests']}\n")
                
                if self.test_results['total_tests'] > 0:
                    success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
                    f.write(f"Success Rate: {success_rate:.1f}%\n")
                
                f.write("\nPERFORMANCE METRICS\n")
                f.write("-"*60 + "\n")
                for metric, value in self.test_results['performance_metrics'].items():
                    f.write(f"{metric}: {value:.4f}\n")
                
                f.write("\nDETAILED RESULTS\n")
                f.write("-"*60 + "\n")
                for result in self.test_results['test_details']:
                    status = "PASS" if result['passed'] else "FAIL"
                    f.write(f"\n[{status}] {result['test_name']}\n")
                    f.write(f"Details: {result['details']}\n")
                
                f.write("\n" + "="*60 + "\n")
            
            self.logger.info(f"\n✓ Results saved to: {output_file}")
        
        except Exception as e:
            self.logger.error(f"✗ Failed to save results: {str(e)}")
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        start_time = datetime.now()
        
        self.logger.info("="*60)
        self.logger.info("RAG SYSTEM COMPREHENSIVE TEST")
        self.logger.info("="*60)
        self.logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Run tests
        test1_passed = self.test_database_connection()
        test2_passed = self.test_retrieval_functionality()
        test3_passed = self.test_edge_cases()
        test4_passed = self.test_similarity_scores()
        
        # Print summary
        self.print_summary()
        
        # Save results
        self.save_results()
        
        # Calculate duration
        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info(f"\nEnd time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Total duration: {duration}")
        
        # Close database connection
        self.vector_store.close()
        
        # Overall result
        all_passed = (self.test_results['failed_tests'] == 0)
        
        if all_passed:
            self.logger.info("\n✓ ALL TESTS PASSED - RAG system is working correctly!")
            return True
        else:
            self.logger.error(f"\n✗ SOME TESTS FAILED - {self.test_results['failed_tests']} test(s) failed")
            return False


def main():
    """Main entry point"""
    # Setup logging
    logger = setup_logging()
    
    try:
        # Create tester and run tests
        tester = RAGTester(db_path="compliance-guardian/database/compliance.db")
        success = tester.run_all_tests()
        
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("\n\nTests interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n\nFatal error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
</content>
<line_count>625</line_count>
</write_to_file>

---

**User:**

[write_to_file for 'compliance-guardian/scripts/test_rag.py'] Result:
<file_write_result>
<path>compliance-guardian/scripts/test_rag.py</path>
<operation>created</operation>
<problems>

New problems detected after saving the file:
compliance-guardian/scripts/test_rag.py
- [basedpyright Error] 136 |             cursor = self.vector_store.conn.cursor() : "cursor" is not a known attribute of "None"</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:07:03.660Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.06

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Perfect! I've created a comprehensive RAG system test script. The type error is just a static analysis warning and won't affect runtime since the connection is established in the `__init__` method. Now let me test the script to make sure it works correctly.

<execute_command>
<command>cd compliance-guardian && python scripts/test_rag.py</command>
</execute_command>

---

**User:**

[execute_command for 'cd compliance-guardian && python scripts/test_rag.py'] Result:
Command executed in terminal  within working directory 'c:/Users/kanch/Downloads/Bob'. Command execution was not successful, inspect the cause and adjust as needed.
Exit code: 1
Output:
At line:1 char:24
+ cd compliance-guardian && python scripts/test_rag.py
+                        ~~
The token '&&' is not a valid statement separator in this version.
    + CategoryInfo          : ParserError: (:) [], ParentContainsErrorRecordException
    + FullyQualifiedErrorId : InvalidEndOfLine
 

<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:07:39.487Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.11

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I need to use PowerShell syntax. Let me run the test script correctly:

<execute_command>
<command>cd compliance-guardian; python scripts/test_rag.py</command>
</execute_command>

---

**User:**

[execute_command for 'cd compliance-guardian; python scripts/test_rag.py'] Result:
Command is still running in terminal  from 'c:/Users/kanch/Downloads/Bob'.


You will be updated on the terminal status and new output in the future.
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Actively Running Terminals
## Terminal 1 (Active)
### Working Directory: `c:\Users\kanch\Downloads\Bob`
### Original command: `cd compliance-guardian; python scripts/test_rag.py`
### New Output
2026-05-15 17:08:35,141 - ERROR - Error connecting to database: unable to open database file
--- Logging error ---
Traceback (most recent call last):
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 110, in __init__
    self.vector_store = VectorStore(db_path=db_path)
                        ~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\src\rag\vector_store.py", line 27, in __init__
    self._connect()
    ~~~~~~~~~~~~~^^
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\src\rag\vector_store.py", line 33, in _connect
    self.conn = sqlite3.connect(self.db_path)
                ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
sqlite3.OperationalError: unable to open database file

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\kanch\AppData\Local\Programs\Python\Python313\Lib\logging\__init__.py", line 1154, in emit
    stream.write(msg + self.terminator)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kanch\AppData\Local\Programs\Python\Python313\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2717' in position 34: character maps to <undefined>
Call stack:
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 555, in <module>
    main()
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 539, in main
    tester = RAGTester(db_path="compliance-guardian/database/compliance.db")
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 113, in __init__
    self.logger.error(f"\u2717 Failed to initialize RAG components: {str(e)}")
Message: '\u2717 Failed to initialize RAG components: unable to open database file'
Arguments: ()
--- Logging error ---
Traceback (most recent call last):
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 110, in __init__
    self.vector_store = VectorStore(db_path=db_path)
                        ~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\src\rag\vector_store.py", line 27, in __init__
    self._connect()
    ~~~~~~~~~~~~~^^
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\src\rag\vector_store.py", line 33, in _connect
    self.conn = sqlite3.connect(self.db_path)
                ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
sqlite3.OperationalError: unable to open database file

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\kanch\AppData\Local\Programs\Python\Python313\Lib\logging\__init__.py", line 1154, in emit
    stream.write(msg + self.terminator)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\kanch\AppData\Local\Programs\Python\Python313\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2717' in position 34: character maps to <undefined>
Call stack:
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 555, in <module>
    main()
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 539, in main
    tester = RAGTester(db_path="compliance-guardian/database/compliance.db")
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 113, in __init__
    self.logger.error(f"\u2717 Failed to initialize RAG components: {str(e)}")
Message: '\u2717 Failed to initialize RAG components: unable to open database file'
Arguments: ()
2026-05-15 17:08:35,153 - ERROR - 

Fatal error: unable to open database file
2026-05-15 17:08:35,155 - ERROR - Traceback (most recent call last):
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 539, in main
    tester = RAGTester(db_path="compliance-guardian/database/compliance.db")
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\scripts\test_rag.py", line 110, in __init__
    self.vector_store = VectorStore(db_path=db_path)
                        ~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\src\rag\vector_store.py", line 27, in __init__
    self._connect()
    ~~~~~~~~~~~~~^^
  File "C:\Users\kanch\Downloads\Bob\compliance-guardian\src\rag\vector_store.py", line 33, in _connect
    self.conn = sqlite3.connect(self.db_path)
                ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
sqlite3.OperationalError: unable to open database file



# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:08:36.270Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.16

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

I see two issues:
1. The database path is incorrect when running from the compliance-guardian directory
2. Unicode characters causing encoding issues on Windows

Let me fix the script:

<apply_diff>
<path>compliance-guardian/scripts/test_rag.py</path>
<diff>
<<<<<<< SEARCH
:start_line:1
-------
#!/usr/bin/env python3
"""
RAG System Test Script
Comprehensive testing of the RAG system functionality
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import traceback
import sqlite3
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore


# Configure logging
def setup_logging(log_file: str = "data/rag_test.log"):
    """Setup logging configuration"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)
=======
#!/usr/bin/env python3
"""
RAG System Test Script
Comprehensive testing of the RAG system functionality
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import traceback
import sqlite3
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.embedder import Embedder
from src.rag.vector_store import VectorStore


# Configure logging
def setup_logging(log_file: str = "data/rag_test.log"):
    """Setup logging configuration"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'compliance-guardian/scripts/test_rag.py'] Result:
<file_write_result>
<path>compliance-guardian/scripts/test_rag.py</path>
<operation>modified</operation>
<problems>

New problems detected after saving the file:
compliance-guardian/scripts/test_rag.py
- [basedpyright Error] 136 |             cursor = self.vector_store.conn.cursor() : "cursor" is not a known attribute of "None"</problems>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:09:10.135Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.21

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Now let me fix the database path issue and remove Unicode characters:

<apply_diff>
<path>compliance-guardian/scripts/test_rag.py</path>
<diff>
<<<<<<< SEARCH
:start_line:38
-------
class RAGTester:
    """Comprehensive RAG system testing"""
    
    def __init__(self, db_path: str = "compliance-guardian/database/compliance.db"):
        """
        Initialize RAG tester
        
        Args:
            db_path: Path to SQLite database
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
=======
class RAGTester:
    """Comprehensive RAG system testing"""
    
    def __init__(self, db_path: str = "database/compliance.db"):
        """
        Initialize RAG tester
        
        Args:
            db_path: Path to SQLite database
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'compliance-guardian/scripts/test_rag.py'] Result:
<file_write_result>
<path>compliance-guardian/scripts/test_rag.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:09:27.022Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.27

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Now let me fix the Unicode characters and update the main function:

<apply_diff>
<path>compliance-guardian/scripts/test_rag.py</path>
<diff>
<<<<<<< SEARCH
:start_line:108
-------
        # Initialize components
        self.logger.info("Initializing RAG components for testing...")
        try:
            self.embedder = Embedder(model_name='all-MiniLM-L6-v2')
            self.vector_store = VectorStore(db_path=db_path)
            self.logger.info("✓ RAG components initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize RAG components: {str(e)}")
            raise
=======
        # Initialize components
        self.logger.info("Initializing RAG components for testing...")
        try:
            self.embedder = Embedder(model_name='all-MiniLM-L6-v2')
            self.vector_store = VectorStore(db_path=db_path)
            self.logger.info("[PASS] RAG components initialized successfully")
        except Exception as e:
            self.logger.error(f"[FAIL] Failed to initialize RAG components: {str(e)}")
            raise
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'compliance-guardian/scripts/test_rag.py'] Result:
<file_write_result>
<path>compliance-guardian/scripts/test_rag.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:09:44.094Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.33

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Let me replace all Unicode checkmarks and X marks with ASCII equivalents in one go:

<apply_diff>
<path>compliance-guardian/scripts/test_rag.py</path>
<diff>
<<<<<<< SEARCH
:start_line:140
-------
            self.logger.info(f"✓ Database file exists: {self.db_path}")
            
            # Check if embeddings table exists
            cursor = self.vector_store.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='embeddings'
            """)
            
            if not cursor.fetchone():
                raise Exception("Embeddings table does not exist")
            
            self.logger.info("✓ Embeddings table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(embeddings)")
            columns = cursor.fetchall()
            expected_columns = ['id', 'document_id', 'chunk_text', 'embedding', 'metadata', 'created_at']
            actual_columns = [col[1] for col in columns]
            
            for col in expected_columns:
                if col not in actual_columns:
                    raise Exception(f"Missing column: {col}")
            
            self.logger.info(f"✓ Table structure verified: {', '.join(actual_columns)}")
            
            # Count embeddings
            cursor.execute("SELECT COUNT(*) as count FROM embeddings")
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise Exception("No embeddings found in database")
            
            self.logger.info(f"✓ Total embeddings in database: {count}")
            
            # Count unique documents
            cursor.execute("SELECT COUNT(DISTINCT document_id) as count FROM embeddings")
            doc_count = cursor.fetchone()[0]
            self.logger.info(f"✓ Unique documents: {doc_count}")
            
            # Get document list
            cursor.execute("SELECT DISTINCT document_id FROM embeddings")
            documents = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"✓ Documents in database:")
=======
            self.logger.info(f"[PASS] Database file exists: {self.db_path}")
            
            # Check if embeddings table exists
            cursor = self.vector_store.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='embeddings'
            """)
            
            if not cursor.fetchone():
                raise Exception("Embeddings table does not exist")
            
            self.logger.info("[PASS] Embeddings table exists")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(embeddings)")
            columns = cursor.fetchall()
            expected_columns = ['id', 'document_id', 'chunk_text', 'embedding', 'metadata', 'created_at']
            actual_columns = [col[1] for col in columns]
            
            for col in expected_columns:
                if col not in actual_columns:
                    raise Exception(f"Missing column: {col}")
            
            self.logger.info(f"[PASS] Table structure verified: {', '.join(actual_columns)}")
            
            # Count embeddings
            cursor.execute("SELECT COUNT(*) as count FROM embeddings")
            count = cursor.fetchone()[0]
            
            if count == 0:
                raise Exception("No embeddings found in database")
            
            self.logger.info(f"[PASS] Total embeddings in database: {count}")
            
            # Count unique documents
            cursor.execute("SELECT COUNT(DISTINCT document_id) as count FROM embeddings")
            doc_count = cursor.fetchone()[0]
            self.logger.info(f"[PASS] Unique documents: {doc_count}")
            
            # Get document list
            cursor.execute("SELECT DISTINCT document_id FROM embeddings")
            documents = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"[PASS] Documents in database:")
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'compliance-guardian/scripts/test_rag.py'] Result:
<file_write_result>
<path>compliance-guardian/scripts/test_rag.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:10:04.516Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.40

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Let me continue replacing all the Unicode symbols with ASCII equivalents:

<apply_diff>
<path>compliance-guardian/scripts/test_rag.py</path>
<diff>
<<<<<<< SEARCH
:start_line:186
-------
            
            self._record_test_result(test_name, True, f"Database verified with {count} embeddings")
            return True
        
        except Exception as e:
            self.logger.error(f"✗ {test_name} FAILED: {str(e)}")
            self._record_test_result(test_name, False, str(e))
            return False
=======
            
            self._record_test_result(test_name, True, f"Database verified with {count} embeddings")
            return True
        
        except Exception as e:
            self.logger.error(f"[FAIL] {test_name} FAILED: {str(e)}")
            self._record_test_result(test_name, False, str(e))
            return False
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'compliance-guardian/scripts/test_rag.py'] Result:
<file_write_result>
<path>compliance-guardian/scripts/test_rag.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<notice>Making multiple related changes in a single apply_diff is more efficient. If other changes are needed in this file, please include them as additional SEARCH/REPLACE blocks.</notice>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:10:18.629Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.47

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Let me replace all remaining Unicode symbols in the file at once using search_files to find them all:

<search_files>
<path>compliance-guardian/scripts/test_rag.py</path>
<regex>[✓✗⚠]</regex>
</search_files>

---

**User:**

[search_files for '[✓✗⚠]'] Result:
Found 10 results.

# compliance-guardian/scripts/test_rag.py
251 | 
252 |                 self.logger.info(f"\n✓ Expected topics found: {', '.join(found_topics)}")
253 | 
254 |                 if len(found_topics) == 0:
255 |                     self.logger.warning(f"⚠ No expected topics found in results")
256 | 
257 |                 self.logger.info(f"✓ Query {idx} PASSED")
258 | 
259 |             except Exception as e:
260 |                 self.logger.error(f"✗ Query {idx} FAILED: {str(e)}")
261 |                 all_passed = False
----
270 |         if avg_query_time > 1.0:
271 |             self.logger.warning(f"⚠ Average query time exceeds 1 second threshold")
272 |         else:
273 |             self.logger.info(f"✓ Query performance acceptable (<1 second)")
274 | 
----
324 |                         )
325 |                     self.logger.info(f"✓ Similarity below max threshold")
326 | 
----
331 |                         )
332 |                     self.logger.info(f"✓ Similarity above min threshold")
333 | 
334 |                 self.logger.info(f"✓ Edge case {idx} PASSED")
335 | 
336 |             except Exception as e:
337 |                 self.logger.error(f"✗ Edge case {idx} FAILED: {str(e)}")
338 |                 all_passed = False
----
395 | 
396 |             self.logger.info(f"✓ Similarity scores within acceptable range")
397 | 
----
401 |         except Exception as e:
402 |             self.logger.error(f"✗ {test_name} FAILED: {str(e)}")
403 |             self._record_test_result(test_name, False, str(e))
----
430 |         self.logger.info(f"Total Tests: {total}")
431 |         self.logger.info(f"Passed: {passed} ✓")
432 |         self.logger.info(f"Failed: {failed} ✗")
433 | 
----
443 |         for result in self.test_results['test_details']:
444 |             status = "✓ PASS" if result['passed'] else "✗ FAIL"
445 |             self.logger.info(f"  {status} - {result['test_name']}")
----
485 | 
486 |             self.logger.info(f"\n✓ Results saved to: {output_file}")
487 | 
488 |         except Exception as e:
489 |             self.logger.error(f"✗ Failed to save results: {str(e)}")
490 | 
----
524 |         if all_passed:
525 |             self.logger.info("\n✓ ALL TESTS PASSED - RAG system is working correctly!")
526 |             return True
527 |         else:
528 |             self.logger.error(f"\n✗ SOME TESTS FAILED - {self.test_results['failed_tests']} test(s) failed")
529 |             return False
----
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:10:28.002Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.54

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Now let me replace all remaining Unicode symbols in one comprehensive diff:

<apply_diff>
<path>compliance-guardian/scripts/test_rag.py</path>
<diff>
<<<<<<< SEARCH
:start_line:250
-------
                
                self.logger.info(f"\n✓ Expected topics found: {', '.join(found_topics)}")
                
                if len(found_topics) == 0:
                    self.logger.warning(f"⚠ No expected topics found in results")
                
                self.logger.info(f"✓ Query {idx} PASSED")
            
            except Exception as e:
                self.logger.error(f"✗ Query {idx} FAILED: {str(e)}")
                all_passed = False
        
        # Calculate average query time
        avg_query_time = sum(query_times) / len(query_times) if query_times else 0
        self.test_results['performance_metrics']['avg_query_time'] = avg_query_time
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Average query time: {avg_query_time:.3f} seconds")
        
        if avg_query_time > 1.0:
            self.logger.warning(f"⚠ Average query time exceeds 1 second threshold")
        else:
            self.logger.info(f"✓ Query performance acceptable (<1 second)")
=======
                
                self.logger.info(f"\n[PASS] Expected topics found: {', '.join(found_topics)}")
                
                if len(found_topics) == 0:
                    self.logger.warning(f"[WARN] No expected topics found in results")
                
                self.logger.info(f"[PASS] Query {idx} PASSED")
            
            except Exception as e:
                self.logger.error(f"[FAIL] Query {idx} FAILED: {str(e)}")
                all_passed = False
        
        # Calculate average query time
        avg_query_time = sum(query_times) / len(query_times) if query_times else 0
        self.test_results['performance_metrics']['avg_query_time'] = avg_query_time
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Average query time: {avg_query_time:.3f} seconds")
        
        if avg_query_time > 1.0:
            self.logger.warning(f"[WARN] Average query time exceeds 1 second threshold")
        else:
            self.logger.info(f"[PASS] Query performance acceptable (<1 second)")
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:323
-------
                        )
                    self.logger.info(f"✓ Similarity below max threshold")
                
                if 'min_similarity' in test_case:
                    if top_result['similarity'] < test_case['min_similarity']:
                        raise Exception(
                            f"Similarity {top_result['similarity']:.4f} below min {test_case['min_similarity']}"
                        )
                    self.logger.info(f"✓ Similarity above min threshold")
                
                self.logger.info(f"✓ Edge case {idx} PASSED")
            
            except Exception as e:
                self.logger.error(f"✗ Edge case {idx} FAILED: {str(e)}")
                all_passed = False
=======
                        )
                    self.logger.info(f"[PASS] Similarity below max threshold")
                
                if 'min_similarity' in test_case:
                    if top_result['similarity'] < test_case['min_similarity']:
                        raise Exception(
                            f"Similarity {top_result['similarity']:.4f} below min {test_case['min_similarity']}"
                        )
                    self.logger.info(f"[PASS] Similarity above min threshold")
                
                self.logger.info(f"[PASS] Edge case {idx} PASSED")
            
            except Exception as e:
                self.logger.error(f"[FAIL] Edge case {idx} FAILED: {str(e)}")
                all_passed = False
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:394
-------
            
            self.logger.info(f"✓ Similarity scores within acceptable range")
            
            self._record_test_result(test_name, True, f"Avg similarity: {avg_similarity:.4f}")
            return True
        
        except Exception as e:
            self.logger.error(f"✗ {test_name} FAILED: {str(e)}")
            self._record_test_result(test_name, False, str(e))
            return False
=======
            
            self.logger.info(f"[PASS] Similarity scores within acceptable range")
            
            self._record_test_result(test_name, True, f"Avg similarity: {avg_similarity:.4f}")
            return True
        
        except Exception as e:
            self.logger.error(f"[FAIL] {test_name} FAILED: {str(e)}")
            self._record_test_result(test_name, False, str(e))
            return False
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:429
-------
        self.logger.info(f"Total Tests: {total}")
        self.logger.info(f"Passed: {passed} ✓")
        self.logger.info(f"Failed: {failed} ✗")
        
        if total > 0:
            success_rate = (passed / total) * 100
            self.logger.info(f"Success Rate: {success_rate:.1f}%")
        
        self.logger.info(f"\nPerformance Metrics:")
        for metric, value in self.test_results['performance_metrics'].items():
            self.logger.info(f"  {metric}: {value:.4f}")
        
        self.logger.info(f"\nDetailed Results:")
        for result in self.test_results['test_details']:
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            self.logger.info(f"  {status} - {result['test_name']}")
            self.logger.info(f"    {result['details']}")
=======
        self.logger.info(f"Total Tests: {total}")
        self.logger.info(f"Passed: {passed} [PASS]")
        self.logger.info(f"Failed: {failed} [FAIL]")
        
        if total > 0:
            success_rate = (passed / total) * 100
            self.logger.info(f"Success Rate: {success_rate:.1f}%")
        
        self.logger.info(f"\nPerformance Metrics:")
        for metric, value in self.test_results['performance_metrics'].items():
            self.logger.info(f"  {metric}: {value:.4f}")
        
        self.logger.info(f"\nDetailed Results:")
        for result in self.test_results['test_details']:
            status = "[PASS]" if result['passed'] else "[FAIL]"
            self.logger.info(f"  {status} - {result['test_name']}")
            self.logger.info(f"    {result['details']}")
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:484
-------
            
            self.logger.info(f"\n✓ Results saved to: {output_file}")
        
        except Exception as e:
            self.logger.error(f"✗ Failed to save results: {str(e)}")
=======
            
            self.logger.info(f"\n[PASS] Results saved to: {output_file}")
        
        except Exception as e:
            self.logger.error(f"[FAIL] Failed to save results: {str(e)}")
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:523
-------
        
        if all_passed:
            self.logger.info("\n✓ ALL TESTS PASSED - RAG system is working correctly!")
            return True
        else:
            self.logger.error(f"\n✗ SOME TESTS FAILED - {self.test_results['failed_tests']} test(s) failed")
            return False
=======
        
        if all_passed:
            self.logger.info("\n[PASS] ALL TESTS PASSED - RAG system is working correctly!")
            return True
        else:
            self.logger.error(f"\n[FAIL] SOME TESTS FAILED - {self.test_results['failed_tests']} test(s) failed")
            return False
>>>>>>> REPLACE
<<<<<<< SEARCH
:start_line:537
-------
        # Create tester and run tests
        tester = RAGTester(db_path="compliance-guardian/database/compliance.db")
        success = tester.run_all_tests()
=======
        # Create tester and run tests
        tester = RAGTester(db_path="database/compliance.db")
        success = tester.run_all_tests()
>>>>>>> REPLACE
</diff>
</apply_diff>

---

**User:**

[apply_diff for 'compliance-guardian/scripts/test_rag.py'] Result:
<file_write_result>
<path>compliance-guardian/scripts/test_rag.py</path>
<operation>modified</operation>
<notice>
<i>You do not need to re-read the file, as you have seen all changes</i>
<i>Proceed with the task using these changes as the new baseline.</i>
</notice>
</file_write_result>

<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:11:03.601Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.62

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Perfect! Now let me test the script again:

<execute_command>
<command>cd compliance-guardian; python scripts/test_rag.py</command>
</execute_command>

---

**User:**

[execute_command for 'cd compliance-guardian; python scripts/test_rag.py'] Result:
Command executed in terminal  within working directory 'c:/Users/kanch/Downloads/Bob'. Command execution was not successful, inspect the cause and adjust as needed.
Exit code: 1
Output:
2026-05-15 17:11:21,989 - INFO - Initializing RAG components for testing...
2026-05-15 17:11:21,989 - INFO - Loading embedding model: all-MiniLM-L6-v2
2026-05-15 17:11:21,997 - INFO - Use pytorch device_name: cpu
2026-05-15 17:11:21,997 - INFO - Load pretrained SentenceTransformer: all-MiniLM-L6-v2
2026-05-15 17:11:24,150 - INFO - Model loaded. Embedding dimension: 384
2026-05-15 17:11:24,177 - INFO - Connected to database: database/compliance.db
2026-05-15 17:11:24,204 - INFO - Database tables created/verified
2026-05-15 17:11:24,205 - INFO - [PASS] RAG components initialized successfully
2026-05-15 17:11:24,205 - INFO - ============================================================
2026-05-15 17:11:24,205 - INFO - RAG SYSTEM COMPREHENSIVE TEST
2026-05-15 17:11:24,205 - INFO - ============================================================
2026-05-15 17:11:24,205 - INFO - Start time: 2026-05-15 17:11:24

2026-05-15 17:11:24,206 - INFO - 
============================================================
2026-05-15 17:11:24,206 - INFO - TEST 1: Database Connection Test
2026-05-15 17:11:24,206 - INFO - ============================================================
2026-05-15 17:11:24,206 - INFO - [PASS] Database file exists: database/compliance.db
2026-05-15 17:11:24,207 - INFO - [PASS] Embeddings table exists
2026-05-15 17:11:24,208 - INFO - [PASS] Table structure verified: id, document_id, chunk_text, embedding, metadata, created_at
2026-05-15 17:11:24,208 - ERROR - [FAIL] Database Connection Test FAILED: No embeddings found in database
2026-05-15 17:11:24,209 - INFO - 
============================================================
2026-05-15 17:11:24,209 - INFO - TEST 2: Retrieval Functionality Test
2026-05-15 17:11:24,209 - INFO - ============================================================
2026-05-15 17:11:24,209 - INFO - 
[Query 1/4] What are GDPR requirements for data processing?
2026-05-15 17:11:24,209 - INFO - ------------------------------------------------------------
Batches: 100%|##########| 1/1 [00:00<00:00,  3.62it/s]
2026-05-15 17:11:24,499 - INFO - Query time: 0.289 seconds
2026-05-15 17:11:24,499 - ERROR - [FAIL] Query 1 FAILED: No results returned
2026-05-15 17:11:24,500 - INFO - 
[Query 2/4] What security controls does NIST recommend?
2026-05-15 17:11:24,500 - INFO - ------------------------------------------------------------
Batches: 100%|##########| 1/1 [00:00<00:00, 43.12it/s]
2026-05-15 17:11:24,529 - INFO - Query time: 0.029 seconds
2026-05-15 17:11:24,529 - ERROR - [FAIL] Query 2 FAILED: No results returned
2026-05-15 17:11:24,530 - INFO - 
[Query 3/4] What are OWASP top security vulnerabilities?
2026-05-15 17:11:24,530 - INFO - ------------------------------------------------------------
Batches: 100%|##########| 1/1 [00:00<00:00, 37.98it/s]
2026-05-15 17:11:24,562 - INFO - Query time: 0.032 seconds
2026-05-15 17:11:24,563 - ERROR - [FAIL] Query 3 FAILED: No results returned
2026-05-15 17:11:24,563 - INFO - 
[Query 4/4] What does EU AI Act say about high-risk AI systems?
2026-05-15 17:11:24,563 - INFO - ------------------------------------------------------------
Batches: 100%|##########| 1/1 [00:00<00:00, 43.11it/s]
2026-05-15 17:11:24,592 - INFO - Query time: 0.029 seconds
2026-05-15 17:11:24,592 - ERROR - [FAIL] Query 4 FAILED: No results returned
2026-05-15 17:11:24,593 - INFO - 
============================================================
2026-05-15 17:11:24,593 - INFO - Average query time: 0.095 seconds
2026-05-15 17:11:24,593 - INFO - [PASS] Query performance acceptable (<1 second)
2026-05-15 17:11:24,594 - INFO - 
============================================================
2026-05-15 17:11:24,594 - INFO - TEST 3: Edge Cases Test
2026-05-15 17:11:24,594 - INFO - ============================================================
2026-05-15 17:11:24,594 - INFO - 
[Edge Case 1/3] Non-existent topic (should return low similarity)
2026-05-15 17:11:24,594 - INFO - Query: What are the requirements for quantum computing in blockchain?
2026-05-15 17:11:24,595 - INFO - ------------------------------------------------------------
Batches: 100%|##########| 1/1 [00:00<00:00, 47.09it/s]
2026-05-15 17:11:24,622 - ERROR - [FAIL] Edge case 1 FAILED: No results returned
2026-05-15 17:11:24,622 - INFO - 
[Edge Case 2/3] Very specific regulation reference
2026-05-15 17:11:24,622 - INFO - Query: GDPR Article 17 right to erasure
2026-05-15 17:11:24,623 - INFO - ------------------------------------------------------------
Batches: 100%|##########| 1/1 [00:00<00:00, 46.94it/s]
2026-05-15 17:11:24,650 - ERROR - [FAIL] Edge case 2 FAILED: No results returned
2026-05-15 17:11:24,650 - INFO - 
[Edge Case 3/3] General security terms
2026-05-15 17:11:24,650 - INFO - Query: security authentication encryption
2026-05-15 17:11:24,651 - INFO - ------------------------------------------------------------
Batches: 100%|##########| 1/1 [00:00<00:00, 50.15it/s]
2026-05-15 17:11:24,676 - ERROR - [FAIL] Edge case 3 FAILED: No results returned
2026-05-15 17:11:24,676 - INFO - 
============================================================
2026-05-15 17:11:24,677 - INFO - TEST 4: Similarity Score Distribution Test
2026-05-15 17:11:24,677 - INFO - ============================================================
Batches: 100%|##########| 1/1 [00:00<00:00, 55.95it/s]
Batches: 100%|##########| 1/1 [00:00<00:00, 46.71it/s]
Batches: 100%|##########| 1/1 [00:00<00:00, 54.35it/s]
C:\Users\kanch\AppData\Local\Programs\Python\Python313\Lib\site-packages\numpy\_core\fromnumeric.py:3860: RuntimeWarning: Mean of empty slice.
  return _methods._mean(a, axis=axis, dtype=dtype,
C:\Users\kanch\AppData\Local\Programs\Python\Python313\Lib\site-packages\numpy\_core\_methods.py:145: RuntimeWarning: invalid value encountered in scalar divide
  ret = ret.dtype.type(ret / rcount)
2026-05-15 17:11:24,757 - ERROR - [FAIL] Similarity Score Distribution Test FAILED: zero-size array to reduction operation maximum which has no identity
2026-05-15 17:11:24,758 - INFO - 
============================================================
2026-05-15 17:11:24,758 - INFO - TEST SUMMARY
2026-05-15 17:11:24,758 - INFO - ============================================================
2026-05-15 17:11:24,758 - INFO - Total Tests: 4
2026-05-15 17:11:24,758 - INFO - Passed: 0 [PASS]
2026-05-15 17:11:24,758 - INFO - Failed: 4 [FAIL]
2026-05-15 17:11:24,759 - INFO - Success Rate: 0.0%
2026-05-15 17:11:24,759 - INFO - 
Performance Metrics:
2026-05-15 17:11:24,759 - INFO -   avg_query_time: 0.0948
2026-05-15 17:11:24,759 - INFO - 
Detailed Results:
2026-05-15 17:11:24,759 - INFO -   [FAIL] - Database Connection Test
2026-05-15 17:11:24,759 - INFO -     No embeddings found in database
2026-05-15 17:11:24,760 - INFO -   [FAIL] - Retrieval Functionality Test
2026-05-15 17:11:24,760 - INFO -     Tested 4 queries, avg time: 0.095s
2026-05-15 17:11:24,760 - INFO -   [FAIL] - Edge Cases Test
2026-05-15 17:11:24,760 - INFO -     Tested 3 edge cases
2026-05-15 17:11:24,760 - INFO -   [FAIL] - Similarity Score Distribution Test
2026-05-15 17:11:24,761 - INFO -     zero-size array to reduction operation maximum which has no identity
2026-05-15 17:11:24,761 - INFO - ============================================================
2026-05-15 17:11:24,763 - INFO - 
[PASS] Results saved to: data/rag_test_results.txt
2026-05-15 17:11:24,764 - INFO - 
End time: 2026-05-15 17:11:24
2026-05-15 17:11:24,764 - INFO - Total duration: 0:00:00.558760
2026-05-15 17:11:24,764 - INFO - Database connection closed
2026-05-15 17:11:24,765 - ERROR - 
[FAIL] SOME TESTS FAILED - 4 test(s) failed

<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:11:26.601Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.69

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Perfect! The test script is working correctly. The tests are failing because the database is empty - we need to run the initialization script first to populate the database with embeddings. Let me check if the test results file was created and then present the completion:

<list_files>
<path>compliance-guardian/data</path>
<recursive>false</recursive>
</list_files>

---

**User:**

[list_files for 'compliance-guardian/data'] Result:
.gitkeep
rag_test_results.txt
rag_test.log
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:11:36.356Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.78

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Excellent! Let me check the test results file to confirm everything is working:

<read_file>
<args>
<file>
<path>compliance-guardian/data/rag_test_results.txt</path>
</file>
</args>
</read_file>

---

**User:**

[read_file for 'compliance-guardian/data/rag_test_results.txt'. Reading multiple files at once is more efficient for the LLM. If other files are relevant to your current task, please read them simultaneously.] Result:
<files>
<file><path>compliance-guardian/data/rag_test_results.txt</path>
<content lines="1-33">
 1 | ============================================================
 2 | RAG SYSTEM TEST RESULTS
 3 | ============================================================
 4 | Test Date: 2026-05-15 17:11:24
 5 | Database: database/compliance.db
 6 | 
 7 | SUMMARY
 8 | ------------------------------------------------------------
 9 | Total Tests: 4
10 | Passed: 0
11 | Failed: 4
12 | Success Rate: 0.0%
13 | 
14 | PERFORMANCE METRICS
15 | ------------------------------------------------------------
16 | avg_query_time: 0.0948
17 | 
18 | DETAILED RESULTS
19 | ------------------------------------------------------------
20 | 
21 | [FAIL] Database Connection Test
22 | Details: No embeddings found in database
23 | 
24 | [FAIL] Retrieval Functionality Test
25 | Details: Tested 4 queries, avg time: 0.095s
26 | 
27 | [FAIL] Edge Cases Test
28 | Details: Tested 3 edge cases
29 | 
30 | [FAIL] Similarity Score Distribution Test
31 | Details: zero-size array to reduction operation maximum which has no identity
32 | 
33 | ============================================================
</content>
</file>
</files>
<environment_details>
# VSCode Visible Files
compliance-guardian\scripts\test_rag.py

# VSCode Open Tabs
TECHNICAL_SPEC.md,compliance-guardian/src/__init__.py,compliance-guardian/src/rag/__init__.py,compliance-guardian/src/rag/pdf_processor.py,compliance-guardian/src/rag/embedder.py,compliance-guardian/src/rag/vector_store.py,compliance-guardian/src/analyzer/__init__.py,compliance-guardian/src/analyzer/repo_cloner.py,compliance-guardian/src/analyzer/file_parser.py,compliance-guardian/src/checker/__init__.py,compliance-guardian/src/checker/quick_scanner.py,compliance-guardian/src/checker/deep_analyzer.py,compliance-guardian/src/checker/rules_engine.py,compliance-guardian/src/orchestrator/__init__.py,compliance-guardian/src/orchestrator/workflow.py,compliance-guardian/src/reports/__init__.py,compliance-guardian/src/reports/summary_generator.py,compliance-guardian/src/reports/detailed_report.py,compliance-guardian/src/api/__init__.py,compliance-guardian/src/api/app.py

# Current Time
Current time in ISO 8601 UTC format: 2026-05-15T16:11:43.005Z
User time zone: Europe/London, UTC+1:00

# Current Cost
$0.87

# Review Exclusions
The following file patterns are excluded from code reviews:
- .vscode/**

# Current Mode
<slug>code</slug>
<name>💻 Code</name>
You have not created a todo list yet. Create one with `update_todo_list` if your task is complicated or involves multiple steps.
</environment_details>

---

**Assistant:**

Perfect! The test script is working correctly. Now let me present the completion:

<attempt_completion>
<result>
Successfully created a comprehensive RAG system test script at `compliance-guardian/scripts/test_rag.py`!

## What the Script Does

The test script verifies all aspects of the RAG system with 4 comprehensive test suites:

### 1. **Database Connection Test**
- Verifies database file exists
- Checks embeddings table structure
- Counts total embeddings and unique documents
- Lists all documents with their chunk counts

### 2. **Retrieval Functionality Test**
Tests 4 sample compliance queries:
- "What are GDPR requirements for data processing?"
- "What security controls does NIST recommend?"
- "What are OWASP top security vulnerabilities?"
- "What does EU AI Act say about high-risk AI systems?"

For each query, it:
- Retrieves top 5 most relevant chunks
- Displays source document, similarity score, page number, and text preview
- Verifies results meet minimum similarity threshold
- Checks if expected topics appear in results
- Measures query response time

### 3. **Edge Cases Test**
Tests 3 edge cases:
- Non-existent topic (quantum computing in blockchain) - should return low similarity
- Very specific regulation reference (GDPR Article 17)
- General security terms

### 4. **Similarity Score Distribution Test**
- Analyzes similarity score statistics across multiple queries
- Calculates average, max, min, and standard deviation
- Verifies scores are within acceptable ranges

## Performance Metrics
- Measures and reports average query time
- Verifies queries complete in <1 second
- Tracks similarity score distributions

## Output
The script provides:
- **Console output**: Real-time test progress with [PASS]/[FAIL] indicators
- **Log file**: `data/rag_test.log` with detailed execution logs
- **Results file**: `data/rag_test_results.txt` with comprehensive test summary

## Test Results
The script ran successfully and correctly identified that the database is empty (no embeddings). This is expected behavior - you need to run `scripts/init_rag.py` first to populate the database with regulatory document embeddings.

## Usage
```bash
cd compliance-guardian
python scripts/test_rag.py
```

The script will exit with code 0 if all tests pass, or code 1 if any tests fail, making it suitable for CI/CD pipelines.

**Next Step**: Run `python scripts/init_rag.py` to populate the database, then run the test script again to verify the RAG system is working correctly with real data.
</result>
</attempt_completion>

