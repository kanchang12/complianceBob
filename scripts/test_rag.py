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
            self.logger.info("[PASS] RAG components initialized successfully")
        except Exception as e:
            self.logger.error(f"[FAIL] Failed to initialize RAG components: {str(e)}")
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
            for doc in documents:
                cursor.execute("SELECT COUNT(*) FROM embeddings WHERE document_id = ?", (doc,))
                doc_count = cursor.fetchone()[0]
                self.logger.info(f"  - {doc}: {doc_count} chunks")
            
            self._record_test_result(test_name, True, f"Database verified with {count} embeddings")
            return True
        
        except Exception as e:
            self.logger.error(f"[FAIL] {test_name} FAILED: {str(e)}")
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
            
            self.logger.info(f"[PASS] Similarity scores within acceptable range")
            
            self._record_test_result(test_name, True, f"Avg similarity: {avg_similarity:.4f}")
            return True
        
        except Exception as e:
            self.logger.error(f"[FAIL] {test_name} FAILED: {str(e)}")
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
            
            self.logger.info(f"\n[PASS] Results saved to: {output_file}")
        
        except Exception as e:
            self.logger.error(f"[FAIL] Failed to save results: {str(e)}")
    
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
            self.logger.info("\n[PASS] ALL TESTS PASSED - RAG system is working correctly!")
            return True
        else:
            self.logger.error(f"\n[FAIL] SOME TESTS FAILED - {self.test_results['failed_tests']} test(s) failed")
            return False


def main():
    """Main entry point"""
    # Setup logging
    logger = setup_logging()
    
    try:
        # Create tester and run tests
        tester = RAGTester(db_path="database/compliance.db")
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