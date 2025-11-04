"""
Simplified Agentic RAG Workflow without LangGraph dependencies.

This module implements a human-like reasoning process using basic Python classes
instead of LangGraph, making it more reliable and easier to debug.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Types of user query intents."""
    FACTUAL = "factual"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    PROCEDURAL = "procedural"
    CONVERSATIONAL = "conversational"
    MULTI_STEP = "multi_step"


class WorkflowStage(Enum):
    """Stages in the workflow."""
    INTENT_CLASSIFICATION = "intent_classification"
    QUERY_PLANNING = "query_planning"
    INFORMATION_RETRIEVAL = "information_retrieval"
    CONTEXT_ANALYSIS = "context_analysis"
    ANSWER_GENERATION = "answer_generation"
    FACT_CHECKING = "fact_checking"
    RESPONSE_REFINEMENT = "response_refinement"
    CITATION_FORMATTING = "citation_formatting"
    QUALITY_ASSESSMENT = "quality_assessment"
    COMPLETED = "completed"


@dataclass
class WorkflowStep:
    """Individual step in the workflow."""
    stage: WorkflowStage
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time: float
    success: bool
    reasoning: str


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    original_query: str
    query_intent: str
    complexity_score: float
    sub_queries: List[str]
    chunks_retrieved: int
    confidence_score: float
    initial_answer: str
    refined_answer: str
    final_response: str
    citations: List[Dict[str, Any]]
    workflow_steps: List[WorkflowStep]
    total_execution_time: float
    success: bool
    error_messages: List[str]


class SimpleAgenticWorkflow:
    """
    Simplified agentic workflow that implements human-like reasoning
    without complex LangGraph dependencies.
    """
    
    def __init__(self, 
                 llm_manager=None,
                 vector_store=None,
                 max_retrieval_chunks: int = 6,
                 confidence_threshold: float = 0.6):
        """Initialize the workflow."""
        self.llm_manager = llm_manager
        self.vector_store = vector_store
        self.max_retrieval_chunks = max_retrieval_chunks
        self.confidence_threshold = confidence_threshold
        
        # Metrics
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "average_execution_time": 0.0,
            "stage_performance": {}
        }
    
    async def process_query(self, query: str, user_context: Optional[Dict] = None) -> WorkflowResult:
        """Process a query through the complete agentic workflow."""
        start_time = time.time()
        workflow_steps = []
        error_messages = []
        
        try:
            # Step 1: Classify Intent
            intent_result = await self._classify_intent(query)
            workflow_steps.append(intent_result["step"])
            
            query_intent = intent_result["intent"]
            complexity_score = intent_result["complexity"]
            sub_queries = intent_result["sub_queries"]
            
            # Step 2: Plan Query Approach
            planning_result = await self._plan_query_approach(query_intent, complexity_score, sub_queries)
            workflow_steps.append(planning_result["step"])
            
            retrieval_strategy = planning_result["strategy"]
            max_chunks = planning_result["max_chunks"]
            
            # Step 3: Retrieve Information
            retrieval_result = await self._retrieve_information(sub_queries, max_chunks)
            workflow_steps.append(retrieval_result["step"])
            
            retrieved_chunks = retrieval_result["chunks"]
            chunks_retrieved = len(retrieved_chunks)
            
            # Step 4: Analyze Context
            context_result = await self._analyze_context(retrieved_chunks)
            workflow_steps.append(context_result["step"])
            
            context_summary = context_result["summary"]
            confidence_score = context_result["confidence"]
            
            # Step 5: Generate Answer
            answer_result = await self._generate_answer(query, context_summary, query_intent)
            workflow_steps.append(answer_result["step"])
            
            initial_answer = answer_result["answer"]
            
            # Step 6: Check Facts
            fact_check_result = await self._check_facts(initial_answer, context_summary)
            workflow_steps.append(fact_check_result["step"])
            
            # Step 7: Refine Response
            refinement_result = await self._refine_response(initial_answer, confidence_score)
            workflow_steps.append(refinement_result["step"])
            
            refined_answer = refinement_result["answer"]
            
            # Step 8: Format Citations
            citation_result = await self._format_citations(retrieved_chunks)
            workflow_steps.append(citation_result["step"])
            
            citations = citation_result["citations"]
            
            # Step 9: Assess Quality
            quality_result = await self._assess_quality(refined_answer, citations, confidence_score)
            workflow_steps.append(quality_result["step"])
            
            final_response = quality_result["final_response"]
            
            total_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(total_time, True)
            
            return WorkflowResult(
                original_query=query,
                query_intent=query_intent,
                complexity_score=complexity_score,
                sub_queries=sub_queries,
                chunks_retrieved=chunks_retrieved,
                confidence_score=confidence_score,
                initial_answer=initial_answer,
                refined_answer=refined_answer,
                final_response=final_response,
                citations=citations,
                workflow_steps=workflow_steps,
                total_execution_time=total_time,
                success=True,
                error_messages=error_messages
            )
            
        except Exception as e:
            total_time = time.time() - start_time
            error_messages.append(str(e))
            self._update_metrics(total_time, False)
            
            logger.error(f"Workflow failed: {e}")
            
            return WorkflowResult(
                original_query=query,
                query_intent="unknown",
                complexity_score=0.0,
                sub_queries=[],
                chunks_retrieved=0,
                confidence_score=0.0,
                initial_answer="",
                refined_answer="",
                final_response="I apologize, but I encountered an error processing your request.",
                citations=[],
                workflow_steps=workflow_steps,
                total_execution_time=total_time,
                success=False,
                error_messages=error_messages
            )
    
    async def _classify_intent(self, query: str) -> Dict[str, Any]:
        """Step 1: Classify query intent."""
        start_time = time.time()
        
        # Simple rule-based classification
        query_lower = query.lower()
        
        # Intent classification logic
        if any(word in query_lower for word in ["what is", "who is", "when", "where", "define"]):
            intent = QueryIntent.FACTUAL.value
            complexity = 3.0
        elif any(word in query_lower for word in ["compare", "analyze", "explain why", "differences"]):
            intent = QueryIntent.ANALYTICAL.value
            complexity = 7.0
        elif any(word in query_lower for word in ["how to", "steps", "process", "method"]):
            intent = QueryIntent.PROCEDURAL.value
            complexity = 5.0
        elif any(word in query_lower for word in ["write", "create", "generate", "design"]):
            intent = QueryIntent.CREATIVE.value
            complexity = 6.0
        elif " and " in query_lower or len(query.split()) > 15:
            intent = QueryIntent.MULTI_STEP.value
            complexity = 8.0
        else:
            intent = QueryIntent.FACTUAL.value
            complexity = 4.0
        
        # Generate sub-queries for complex queries
        if complexity > 6:
            sub_queries = self._decompose_query(query)
        else:
            sub_queries = [query]
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.INTENT_CLASSIFICATION,
            input_data={"query": query},
            output_data={"intent": intent, "complexity": complexity, "sub_queries": sub_queries},
            execution_time=execution_time,
            success=True,
            reasoning=f"Classified as {intent} with complexity {complexity}"
        )
        
        return {
            "step": step,
            "intent": intent,
            "complexity": complexity,
            "sub_queries": sub_queries
        }
    
    def _decompose_query(self, query: str) -> List[str]:
        """Decompose complex queries into sub-queries."""
        sub_queries = [query]
        
        if " and " in query.lower():
            parts = query.split(" and ")
            sub_queries = [part.strip() for part in parts if part.strip()]
        elif "?" in query and query.count("?") > 1:
            parts = query.split("?")
            sub_queries = [part.strip() + "?" for part in parts if part.strip()]
        
        return sub_queries[:3]  # Limit to 3
    
    async def _plan_query_approach(self, intent: str, complexity: float, sub_queries: List[str]) -> Dict[str, Any]:
        """Step 2: Plan the retrieval approach."""
        start_time = time.time()
        
        # Determine strategy based on intent and complexity
        if intent == QueryIntent.FACTUAL.value and complexity <= 5:
            strategy = "direct"
            max_chunks = 3
        elif intent == QueryIntent.ANALYTICAL.value or complexity > 7:
            strategy = "comprehensive"
            max_chunks = self.max_retrieval_chunks
        else:
            strategy = "balanced"
            max_chunks = 4
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.QUERY_PLANNING,
            input_data={"intent": intent, "complexity": complexity},
            output_data={"strategy": strategy, "max_chunks": max_chunks},
            execution_time=execution_time,
            success=True,
            reasoning=f"Planned {strategy} approach for {intent} query"
        )
        
        return {
            "step": step,
            "strategy": strategy,
            "max_chunks": max_chunks
        }
    
    async def _retrieve_information(self, sub_queries: List[str], max_chunks: int) -> Dict[str, Any]:
        """Step 3: Retrieve relevant information."""
        start_time = time.time()
        
        all_chunks = []
        
        if self.vector_store and self.llm_manager:
            for query in sub_queries:
                try:
                    # Generate embedding
                    success, embedding = await self.llm_manager.generate_embeddings(query)
                    
                    if success:
                        # Search vector store
                        results = await self.vector_store.search_similar(
                            query_embedding=embedding,
                            limit=max_chunks // len(sub_queries),
                            score_threshold=0.1
                        )
                        
                        # Convert to dict format
                        for chunk in results.chunks:
                            chunk_dict = {
                                "id": chunk.id,
                                "content": chunk.content,
                                "metadata": chunk.metadata,
                                "score": chunk.score
                            }
                            all_chunks.append(chunk_dict)
                
                except Exception as e:
                    logger.warning(f"Retrieval failed for query '{query}': {e}")
        
        # Remove duplicates and sort by score
        unique_chunks = []
        seen_content = set()
        
        for chunk in all_chunks:
            content_hash = hash(chunk["content"])
            if content_hash not in seen_content:
                unique_chunks.append(chunk)
                seen_content.add(content_hash)
        
        # Sort by relevance
        unique_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        final_chunks = unique_chunks[:max_chunks]
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.INFORMATION_RETRIEVAL,
            input_data={"sub_queries": sub_queries, "max_chunks": max_chunks},
            output_data={"chunks_found": len(final_chunks)},
            execution_time=execution_time,
            success=True,
            reasoning=f"Retrieved {len(final_chunks)} relevant chunks"
        )
        
        return {
            "step": step,
            "chunks": final_chunks
        }
    
    async def _analyze_context(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Step 4: Analyze retrieved context."""
        start_time = time.time()
        
        if not chunks:
            summary = "No relevant context found."
            confidence = 0.0
        else:
            # Combine content
            contents = [chunk["content"] for chunk in chunks]
            summary = "\n\n".join(contents)
            
            # Calculate confidence from scores
            scores = [chunk.get("score", 0) for chunk in chunks]
            confidence = sum(scores) / len(scores) if scores else 0.0
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.CONTEXT_ANALYSIS,
            input_data={"chunk_count": len(chunks)},
            output_data={"summary_length": len(summary), "confidence": confidence},
            execution_time=execution_time,
            success=True,
            reasoning=f"Analyzed {len(chunks)} chunks with confidence {confidence:.3f}"
        )
        
        return {
            "step": step,
            "summary": summary,
            "confidence": confidence
        }
    
    async def _generate_answer(self, query: str, context: str, intent: str) -> Dict[str, Any]:
        """Step 5: Generate initial answer."""
        start_time = time.time()
        
        if not context.strip():
            answer = "I don't have enough relevant information to answer your question."
        elif self.llm_manager:
            prompt = f"""Based on the provided context, answer the user's question accurately.

Context:
{context}

Question: {query}

Instructions:
- Use only information from the provided context
- Be accurate and factual
- If the context doesn't contain enough information, say so
- Structure your response clearly for a {intent} query

Answer:"""
            
            success, response = await self.llm_manager.generate_simple_response(
                prompt,
                "You are a helpful AI assistant. Base your answers on the provided context."
            )
            
            answer = response.strip() if success else "I'm unable to generate a response at this time."
        else:
            answer = "I'm unable to process your request at this time."
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.ANSWER_GENERATION,
            input_data={"query": query, "context_length": len(context)},
            output_data={"answer_length": len(answer)},
            execution_time=execution_time,
            success=True,
            reasoning="Generated initial answer from context"
        )
        
        return {
            "step": step,
            "answer": answer
        }
    
    async def _check_facts(self, answer: str, context: str) -> Dict[str, Any]:
        """Step 6: Check facts in the answer."""
        start_time = time.time()
        
        # Simple fact checking
        has_context = bool(context and len(context) > 50)
        answer_grounded = len(answer) > 20 and "don't have" not in answer.lower()
        
        check_results = {
            "has_context": has_context,
            "answer_grounded": answer_grounded,
            "issues": []
        }
        
        if not has_context:
            check_results["issues"].append("Limited context available")
        if not answer_grounded:
            check_results["issues"].append("Answer may not be well grounded")
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.FACT_CHECKING,
            input_data={"answer_length": len(answer)},
            output_data=check_results,
            execution_time=execution_time,
            success=True,
            reasoning=f"Fact check completed, {len(check_results['issues'])} issues found"
        )
        
        return {
            "step": step,
            "results": check_results
        }
    
    async def _refine_response(self, answer: str, confidence: float) -> Dict[str, Any]:
        """Step 7: Refine the response."""
        start_time = time.time()
        
        refined = answer
        
        # Add confidence disclaimer if needed
        if confidence < self.confidence_threshold:
            refined += "\n\nNote: This response is based on limited available information."
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.RESPONSE_REFINEMENT,
            input_data={"original_length": len(answer)},
            output_data={"refined_length": len(refined)},
            execution_time=execution_time,
            success=True,
            reasoning="Refined response for clarity"
        )
        
        return {
            "step": step,
            "answer": refined
        }
    
    async def _format_citations(self, chunks: List[Dict]) -> Dict[str, Any]:
        """Step 8: Format citations."""
        start_time = time.time()
        
        citations = []
        for i, chunk in enumerate(chunks[:5], 1):  # Top 5 sources
            if chunk.get("score", 0) > 0.3:  # Only cite relevant sources
                citation = {
                    "id": i,
                    "source": chunk.get("metadata", {}).get("filename", "Unknown"),
                    "relevance": chunk.get("score", 0),
                    "preview": chunk.get("content", "")[:100] + "..."
                }
                citations.append(citation)
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.CITATION_FORMATTING,
            input_data={"total_chunks": len(chunks)},
            output_data={"citations_created": len(citations)},
            execution_time=execution_time,
            success=True,
            reasoning=f"Created {len(citations)} citations"
        )
        
        return {
            "step": step,
            "citations": citations
        }
    
    async def _assess_quality(self, answer: str, citations: List[Dict], confidence: float) -> Dict[str, Any]:
        """Step 9: Assess final quality."""
        start_time = time.time()
        
        # Quality assessment
        quality_score = 0.0
        
        if len(answer) > 50:
            quality_score += 0.3
        if len(citations) > 0:
            quality_score += 0.3
        if confidence > self.confidence_threshold:
            quality_score += 0.4
        
        # Create final response with citations
        final_response = answer
        
        if citations:
            final_response += "\n\n**Sources:**\n"
            for citation in citations:
                final_response += f"{citation['id']}. {citation['source']} (relevance: {citation['relevance']:.2f})\n"
        
        execution_time = time.time() - start_time
        
        step = WorkflowStep(
            stage=WorkflowStage.QUALITY_ASSESSMENT,
            input_data={"answer_length": len(answer)},
            output_data={"quality_score": quality_score, "final_length": len(final_response)},
            execution_time=execution_time,
            success=True,
            reasoning=f"Quality assessment: {quality_score:.2f}"
        )
        
        return {
            "step": step,
            "final_response": final_response
        }
    
    def _update_metrics(self, execution_time: float, success: bool):
        """Update performance metrics."""
        self.metrics["total_queries"] += 1
        if success:
            self.metrics["successful_queries"] += 1
        
        # Update average time
        total = self.metrics["total_queries"]
        current_avg = self.metrics["average_execution_time"]
        self.metrics["average_execution_time"] = (current_avg * (total - 1) + execution_time) / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get workflow metrics."""
        metrics = self.metrics.copy()
        if metrics["total_queries"] > 0:
            metrics["success_rate"] = metrics["successful_queries"] / metrics["total_queries"]
        else:
            metrics["success_rate"] = 0.0
        return metrics
    
    def visualize_execution(self, result: WorkflowResult) -> str:
        """Create visualization of workflow execution."""
        viz = f"\n🤖 Agentic Workflow Execution\n"
        viz += f"{'='*40}\n"
        viz += f"Query: {result.original_query}\n"
        viz += f"Intent: {result.query_intent} | Complexity: {result.complexity_score}\n"
        viz += f"Execution Time: {result.total_execution_time:.3f}s\n"
        viz += f"Success: {'✅' if result.success else '❌'}\n\n"
        
        for i, step in enumerate(result.workflow_steps, 1):
            stage_name = step.stage.value.replace('_', ' ').title()
            viz += f"{i:2d}. ✅ {stage_name}\n"
            viz += f"     Time: {step.execution_time:.3f}s | {step.reasoning}\n\n"
        
        if result.citations:
            viz += f"📚 {len(result.citations)} sources cited\n"
        
        viz += f"🎯 Confidence: {result.confidence_score:.2f}\n"
        
        return viz


# Example usage
if __name__ == "__main__":
    async def test_simple_workflow():
        workflow = SimpleAgenticWorkflow()
        result = await workflow.process_query("What is machine learning?")
        print(workflow.visualize_execution(result))
    
    asyncio.run(test_simple_workflow())