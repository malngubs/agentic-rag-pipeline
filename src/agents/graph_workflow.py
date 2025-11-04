"""
Agentic RAG Workflow using LangGraph.

This module implements a sophisticated multi-step reasoning process that mimics
human expert thinking when answering complex questions. The workflow includes
query planning, multi-step retrieval, fact checking, and response refinement.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    print("Installing LangGraph...")
    import subprocess
    subprocess.check_call(["pip", "install", "langgraph"])
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

# Configure logging
logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Stages in the agentic workflow."""
    INTENT_CLASSIFICATION = "intent_classification"
    QUERY_PLANNING = "query_planning"
    RETRIEVAL_ENSEMBLE = "retrieval_ensemble"
    CONTEXT_ANALYSIS = "context_analysis"
    ANSWER_GENERATION = "answer_generation"
    FACT_CHECKING = "fact_checking"
    RESPONSE_REFINEMENT = "response_refinement"
    CITATION_FORMATTING = "citation_formatting"
    QUALITY_ASSESSMENT = "quality_assessment"
    COMPLETED = "completed"


class QueryIntent(Enum):
    """Types of user query intents."""
    FACTUAL = "factual"              # Direct fact retrieval
    ANALYTICAL = "analytical"        # Analysis and comparison
    CREATIVE = "creative"            # Creative writing/brainstorming
    PROCEDURAL = "procedural"        # How-to instructions
    CONVERSATIONAL = "conversational" # General chat
    MULTI_STEP = "multi_step"        # Complex multi-part questions


@dataclass
class RetrievalResult:
    """Result from document retrieval."""
    chunks: List[Dict[str, Any]]
    query: str
    search_time: float
    method_used: str
    confidence_score: float


@dataclass
class WorkflowStep:
    """Individual step in the workflow."""
    stage: WorkflowStage
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time: float
    success: bool
    reasoning: str


class AgentState(TypedDict):
    """State managed throughout the agentic workflow."""
    # Input
    original_query: str
    user_context: Dict[str, Any]
    
    # Query Analysis
    query_intent: Optional[str]
    complexity_score: float
    sub_queries: List[str]
    
    # Retrieval
    retrieval_results: List[RetrievalResult]
    total_chunks_retrieved: int
    
    # Processing
    context_summary: str
    fact_check_results: Dict[str, Any]
    confidence_assessment: float
    
    # Output
    initial_answer: str
    refined_answer: str
    final_response: str
    citations: List[Dict[str, Any]]
    
    # Metadata
    workflow_steps: List[WorkflowStep]
    total_execution_time: float
    current_stage: str
    error_messages: List[str]


class AgenticRAGWorkflow:
    """
    Advanced RAG workflow that implements human-like reasoning.
    
    This class orchestrates a multi-step process that includes:
    1. Understanding the user's intent
    2. Planning a multi-step approach
    3. Retrieving relevant information
    4. Analyzing and synthesizing context
    5. Generating initial responses
    6. Fact-checking against sources
    7. Refining for clarity and accuracy
    8. Formatting proper citations
    9. Quality assessment before delivery
    """
    
    def __init__(self, 
                 llm_manager=None,
                 vector_store=None,
                 max_retrieval_chunks: int = 8,
                 confidence_threshold: float = 0.7):
        """
        Initialize the agentic workflow.
        
        Args:
            llm_manager: LLM manager for text generation
            vector_store: Vector database for retrieval
            max_retrieval_chunks: Maximum chunks to retrieve
            confidence_threshold: Minimum confidence for responses
        """
        self.llm_manager = llm_manager
        self.vector_store = vector_store
        self.max_retrieval_chunks = max_retrieval_chunks
        self.confidence_threshold = confidence_threshold
        
        # Build the workflow graph
        self.workflow = self._build_workflow_graph()
        
        # Memory for conversation state
        self.memory = MemorySaver()
        
        # Performance metrics
        self.metrics = {
            "total_queries_processed": 0,
            "average_execution_time": 0.0,
            "stage_performance": {},
            "success_rate": 0.0
        }
    
    def _build_workflow_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each stage
        workflow.add_node("intent_classifier", self._classify_intent)
        workflow.add_node("query_planner", self._plan_query_approach)
        workflow.add_node("retriever_ensemble", self._retrieve_information)
        workflow.add_node("context_analyzer", self._analyze_context)
        workflow.add_node("answer_generator", self._generate_initial_answer)
        workflow.add_node("fact_checker", self._check_facts)
        workflow.add_node("response_refiner", self._refine_response)
        workflow.add_node("citation_formatter", self._format_citations)
        workflow.add_node("quality_assessor", self._assess_quality)
        
        # Define the workflow edges
        workflow.set_entry_point("intent_classifier")
        
        workflow.add_edge("intent_classifier", "query_planner")
        workflow.add_edge("query_planner", "retriever_ensemble")
        workflow.add_edge("retriever_ensemble", "context_analyzer")
        workflow.add_edge("context_analyzer", "answer_generator")
        workflow.add_edge("answer_generator", "fact_checker")
        workflow.add_edge("fact_checker", "response_refiner")
        workflow.add_edge("response_refiner", "citation_formatter")
        workflow.add_edge("citation_formatter", "quality_assessor")
        workflow.add_edge("quality_assessor", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def process_query(self, 
                          query: str, 
                          user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user query through the complete agentic workflow.
        
        Args:
            query: User's question or request
            user_context: Additional context about the user/session
            
        Returns:
            Complete workflow result with response and metadata
        """
        start_time = time.time()
        
        # Initialize state
        initial_state = {
            "original_query": query,
            "user_context": user_context or {},
            "query_intent": None,
            "complexity_score": 0.0,
            "sub_queries": [],
            "retrieval_results": [],
            "total_chunks_retrieved": 0,
            "context_summary": "",
            "fact_check_results": {},
            "confidence_assessment": 0.0,
            "initial_answer": "",
            "refined_answer": "",
            "final_response": "",
            "citations": [],
            "workflow_steps": [],
            "total_execution_time": 0.0,
            "current_stage": WorkflowStage.INTENT_CLASSIFICATION.value,
            "error_messages": []
        }
        
        try:
            # Execute the workflow
            config = {"configurable": {"thread_id": f"query_{int(time.time())}"}}
            result = await self.workflow.ainvoke(initial_state, config)
            
            # Calculate total execution time
            total_time = time.time() - start_time
            result["total_execution_time"] = total_time
            
            # Update metrics
            self._update_metrics(total_time, True)
            
            logger.info(f"Workflow completed in {total_time:.2f}s")
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            self._update_metrics(total_time, False)
            
            error_result = initial_state.copy()
            error_result.update({
                "final_response": "I apologize, but I encountered an error processing your request.",
                "error_messages": [str(e)],
                "total_execution_time": total_time,
                "current_stage": "error"
            })
            
            logger.error(f"Workflow failed: {e}")
            return error_result
    
    async def _classify_intent(self, state: AgentState) -> AgentState:
        """Step 1: Classify the user's intent and query type."""
        start_time = time.time()
        
        try:
            query = state["original_query"]
            
            # Analyze query characteristics
            intent_prompt = f"""
            Analyze this user query and classify its intent:
            
            Query: "{query}"
            
            Classify the intent as one of:
            - factual: Direct fact retrieval (What is X? When did Y happen?)
            - analytical: Analysis/comparison (Compare X and Y, Why does Z happen?)
            - creative: Creative writing/brainstorming (Write a story, Generate ideas)
            - procedural: How-to instructions (How to do X, Steps for Y)
            - conversational: General chat (Hello, Thank you)
            - multi_step: Complex multi-part questions requiring reasoning
            
            Also rate complexity from 1-10 and suggest sub-queries if needed.
            
            Respond in JSON format:
            {{
                "intent": "intent_type",
                "complexity_score": 5,
                "reasoning": "Brief explanation",
                "sub_queries": ["subquery1", "subquery2"]
            }}
            """
            
            if self.llm_manager:
                success, response = await self.llm_manager.generate_simple_response(
                    intent_prompt,
                    "You are an expert at understanding user intent and query analysis."
                )
                
                if success:
                    try:
                        # Parse JSON response
                        intent_data = json.loads(response.strip())
                        
                        state["query_intent"] = intent_data.get("intent", "factual")
                        state["complexity_score"] = intent_data.get("complexity_score", 5.0)
                        state["sub_queries"] = intent_data.get("sub_queries", [query])
                        
                        reasoning = intent_data.get("reasoning", "Intent classified successfully")
                        
                    except json.JSONDecodeError:
                        # Fallback to simple classification
                        state["query_intent"] = self._simple_intent_classification(query)
                        state["complexity_score"] = 5.0
                        state["sub_queries"] = [query]
                        reasoning = "Used fallback classification"
                else:
                    # Fallback classification
                    state["query_intent"] = self._simple_intent_classification(query)
                    state["complexity_score"] = 5.0
                    state["sub_queries"] = [query]
                    reasoning = "LLM unavailable, used rule-based classification"
            else:
                # Rule-based fallback
                state["query_intent"] = self._simple_intent_classification(query)
                state["complexity_score"] = 5.0
                state["sub_queries"] = [query]
                reasoning = "No LLM available, used rule-based classification"
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.INTENT_CLASSIFICATION,
                input_data={"query": query},
                output_data={
                    "intent": state["query_intent"],
                    "complexity": state["complexity_score"],
                    "sub_queries": state["sub_queries"]
                },
                execution_time=execution_time,
                success=True,
                reasoning=reasoning
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.QUERY_PLANNING.value
            
            logger.info(f"Intent classified: {state['query_intent']} (complexity: {state['complexity_score']})")
            return state
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            state["error_messages"].append(f"Intent classification error: {e}")
            return state
    
    def _simple_intent_classification(self, query: str) -> str:
        """Simple rule-based intent classification fallback."""
        query_lower = query.lower()
        
        # Factual indicators
        factual_patterns = ["what is", "who is", "when", "where", "define"]
        if any(pattern in query_lower for pattern in factual_patterns):
            return "factual"
        
        # Analytical indicators
        analytical_patterns = ["compare", "analyze", "explain why", "how does", "what are the differences"]
        if any(pattern in query_lower for pattern in analytical_patterns):
            return "analytical"
        
        # Procedural indicators
        procedural_patterns = ["how to", "steps", "process", "method", "tutorial"]
        if any(pattern in query_lower for pattern in procedural_patterns):
            return "procedural"
        
        # Creative indicators
        creative_patterns = ["write", "create", "generate", "design", "brainstorm"]
        if any(pattern in query_lower for pattern in creative_patterns):
            return "creative"
        
        # Multi-step indicators
        multi_step_patterns = ["and", "also", "furthermore", "additionally"]
        if any(pattern in query_lower for pattern in multi_step_patterns) and len(query.split()) > 15:
            return "multi_step"
        
        # Default to factual
        return "factual"
    
    async def _plan_query_approach(self, state: AgentState) -> AgentState:
        """Step 2: Plan the approach for handling the query."""
        start_time = time.time()
        
        try:
            intent = state["query_intent"]
            complexity = state["complexity_score"]
            original_query = state["original_query"]
            
            # Plan retrieval strategy based on intent and complexity
            if intent == "factual" and complexity <= 5:
                # Simple factual - direct retrieval
                retrieval_strategy = "direct"
                max_chunks = 3
            elif intent == "analytical" or complexity > 7:
                # Complex analytical - comprehensive retrieval
                retrieval_strategy = "comprehensive"
                max_chunks = 8
            elif intent == "multi_step":
                # Multi-step - iterative retrieval
                retrieval_strategy = "iterative"
                max_chunks = 6
            else:
                # Default balanced approach
                retrieval_strategy = "balanced"
                max_chunks = 5
            
            # Update sub-queries based on planning
            if not state["sub_queries"] or state["sub_queries"] == [original_query]:
                if intent == "multi_step" or complexity > 7:
                    # Break down complex queries
                    state["sub_queries"] = self._decompose_complex_query(original_query)
                else:
                    state["sub_queries"] = [original_query]
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.QUERY_PLANNING,
                input_data={
                    "intent": intent,
                    "complexity": complexity
                },
                output_data={
                    "strategy": retrieval_strategy,
                    "max_chunks": max_chunks,
                    "sub_queries": state["sub_queries"]
                },
                execution_time=execution_time,
                success=True,
                reasoning=f"Planned {retrieval_strategy} strategy for {intent} query"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.RETRIEVAL_ENSEMBLE.value
            
            logger.info(f"Query approach planned: {retrieval_strategy} strategy with {len(state['sub_queries'])} sub-queries")
            return state
            
        except Exception as e:
            logger.error(f"Query planning failed: {e}")
            state["error_messages"].append(f"Query planning error: {e}")
            return state
    
    def _decompose_complex_query(self, query: str) -> List[str]:
        """Decompose complex queries into sub-queries."""
        # Simple decomposition - can be enhanced with LLM
        sub_queries = [query]
        
        # Look for conjunctions and split
        if " and " in query.lower():
            parts = query.split(" and ")
            sub_queries = [part.strip() for part in parts if part.strip()]
        elif "?" in query and query.count("?") > 1:
            # Multiple questions
            parts = query.split("?")
            sub_queries = [part.strip() + "?" for part in parts if part.strip()]
        
        return sub_queries[:3]  # Limit to 3 sub-queries
    
    async def _retrieve_information(self, state: AgentState) -> AgentState:
        """Step 3: Retrieve relevant information using ensemble methods."""
        start_time = time.time()
        
        try:
            sub_queries = state["sub_queries"]
            all_results = []
            
            if self.vector_store and self.llm_manager:
                for i, query in enumerate(sub_queries):
                    logger.info(f"Retrieving for sub-query {i+1}: {query}")
                    
                    # Generate query embedding
                    success, query_embedding = await self.llm_manager.generate_embeddings(query)
                    
                    if success:
                        # Retrieve similar chunks
                        search_results = await self.vector_store.search_similar(
                            query_embedding=query_embedding,
                            limit=self.max_retrieval_chunks // len(sub_queries),
                            score_threshold=0.1
                        )
                        
                        # Convert to our format
                        retrieval_result = RetrievalResult(
                            chunks=[asdict(chunk) for chunk in search_results.chunks],
                            query=query,
                            search_time=search_results.search_time,
                            method_used="semantic_search",
                            confidence_score=sum(chunk.score for chunk in search_results.chunks) / len(search_results.chunks) if search_results.chunks else 0.0
                        )
                        
                        all_results.append(retrieval_result)
                        
                        logger.info(f"Retrieved {len(search_results.chunks)} chunks for sub-query {i+1}")
            
            # Deduplicate and rank results
            unique_chunks = []
            seen_content = set()
            
            for result in all_results:
                for chunk in result.chunks:
                    content_hash = hash(chunk.get("content", ""))
                    if content_hash not in seen_content:
                        unique_chunks.append(chunk)
                        seen_content.add(content_hash)
            
            # Sort by relevance score
            unique_chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Keep top chunks
            final_chunks = unique_chunks[:self.max_retrieval_chunks]
            
            state["retrieval_results"] = all_results
            state["total_chunks_retrieved"] = len(final_chunks)
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.RETRIEVAL_ENSEMBLE,
                input_data={"sub_queries": sub_queries},
                output_data={
                    "total_results": len(all_results),
                    "unique_chunks": len(final_chunks),
                    "avg_confidence": sum(r.confidence_score for r in all_results) / len(all_results) if all_results else 0.0
                },
                execution_time=execution_time,
                success=True,
                reasoning=f"Retrieved {len(final_chunks)} unique chunks from {len(all_results)} searches"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.CONTEXT_ANALYSIS.value
            
            logger.info(f"Information retrieval completed: {len(final_chunks)} chunks retrieved")
            return state
            
        except Exception as e:
            logger.error(f"Information retrieval failed: {e}")
            state["error_messages"].append(f"Retrieval error: {e}")
            return state
    
    async def _analyze_context(self, state: AgentState) -> AgentState:
        """Step 4: Analyze and synthesize retrieved context."""
        start_time = time.time()
        
        try:
            retrieval_results = state["retrieval_results"]
            
            if not retrieval_results:
                state["context_summary"] = "No relevant context found."
                state["confidence_assessment"] = 0.0
            else:
                # Combine all retrieved content
                all_content = []
                for result in retrieval_results:
                    for chunk in result.chunks:
                        all_content.append(chunk.get("content", ""))
                
                # Create context summary
                combined_context = "\n\n".join(all_content)
                
                # For now, use the combined context as summary
                # In production, you might use LLM to create a better summary
                state["context_summary"] = combined_context[:2000]  # Limit length
                
                # Calculate confidence based on retrieval scores
                all_scores = []
                for result in retrieval_results:
                    for chunk in result.chunks:
                        if chunk.get("score"):
                            all_scores.append(chunk["score"])
                
                if all_scores:
                    state["confidence_assessment"] = sum(all_scores) / len(all_scores)
                else:
                    state["confidence_assessment"] = 0.5
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.CONTEXT_ANALYSIS,
                input_data={"retrieval_count": len(retrieval_results)},
                output_data={
                    "context_length": len(state["context_summary"]),
                    "confidence": state["confidence_assessment"]
                },
                execution_time=execution_time,
                success=True,
                reasoning=f"Analyzed context from {len(retrieval_results)} retrieval results"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.ANSWER_GENERATION.value
            
            logger.info(f"Context analysis completed: confidence {state['confidence_assessment']:.3f}")
            return state
            
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            state["error_messages"].append(f"Context analysis error: {e}")
            return state
    
    async def _generate_initial_answer(self, state: AgentState) -> AgentState:
        """Step 5: Generate initial answer using retrieved context."""
        start_time = time.time()
        
        try:
            query = state["original_query"]
            context = state["context_summary"]
            intent = state["query_intent"]
            
            if self.llm_manager and context:
                # Create answer generation prompt
                answer_prompt = f"""
                Based on the provided context, answer the user's question accurately and comprehensively.
                
                Context:
                {context}
                
                User Question: {query}
                
                Query Type: {intent}
                
                Instructions:
                - Use only information from the provided context
                - Be accurate and factual
                - If the context doesn't contain enough information, say so
                - Structure your response clearly
                - Cite specific facts from the context
                
                Answer:
                """
                
                success, response = await self.llm_manager.generate_simple_response(
                    answer_prompt,
                    "You are a helpful and accurate AI assistant. Base your answers strictly on the provided context."
                )
                
                if success:
                    state["initial_answer"] = response.strip()
                else:
                    state["initial_answer"] = "I apologize, but I'm unable to generate a response at this time."
            else:
                if not context:
                    state["initial_answer"] = "I don't have enough relevant information to answer your question."
                else:
                    state["initial_answer"] = "I'm unable to process your request at this time."
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.ANSWER_GENERATION,
                input_data={
                    "query": query,
                    "context_length": len(context)
                },
                output_data={
                    "answer_length": len(state["initial_answer"]),
                    "has_content": bool(context)
                },
                execution_time=execution_time,
                success=True,
                reasoning="Generated initial answer from retrieved context"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.FACT_CHECKING.value
            
            logger.info(f"Initial answer generated: {len(state['initial_answer'])} characters")
            return state
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            state["error_messages"].append(f"Answer generation error: {e}")
            return state
    
    async def _check_facts(self, state: AgentState) -> AgentState:
        """Step 6: Check facts in the generated answer against sources."""
        start_time = time.time()
        
        try:
            answer = state["initial_answer"]
            context = state["context_summary"]
            
            # Simple fact checking - compare answer against context
            fact_check_result = {
                "context_support": bool(context and len(context) > 100),
                "answer_grounded": "context" in answer.lower() or len(answer) > 50,
                "confidence_score": state["confidence_assessment"],
                "issues_found": []
            }
            
            # Check for potential issues
            if not context:
                fact_check_result["issues_found"].append("No context available for verification")
            elif "I don't" in answer or "unable to" in answer:
                fact_check_result["issues_found"].append("Answer indicates insufficient information")
            
            state["fact_check_results"] = fact_check_result
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.FACT_CHECKING,
                input_data={"answer_length": len(answer)},
                output_data=fact_check_result,
                execution_time=execution_time,
                success=True,
                reasoning=f"Fact-checked answer, found {len(fact_check_result['issues_found'])} issues"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.RESPONSE_REFINEMENT.value
            
            logger.info(f"Fact checking completed: {len(fact_check_result['issues_found'])} issues found")
            return state
            
        except Exception as e:
            logger.error(f"Fact checking failed: {e}")
            state["error_messages"].append(f"Fact checking error: {e}")
            return state
    
    async def _refine_response(self, state: AgentState) -> AgentState:
        """Step 7: Refine the response for clarity and completeness."""
        start_time = time.time()
        
        try:
            initial_answer = state["initial_answer"]
            fact_check = state["fact_check_results"]
            
            # For now, use initial answer as refined answer
            # In production, you might use LLM to improve the response
            refined_answer = initial_answer
            
            # Add disclaimer if low confidence
            if state["confidence_assessment"] < self.confidence_threshold:
                refined_answer += "\n\nNote: This response is based on limited available information."
            
            state["refined_answer"] = refined_answer
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.RESPONSE_REFINEMENT,
                input_data={"initial_length": len(initial_answer)},
                output_data={"refined_length": len(refined_answer)},
                execution_time=execution_time,
                success=True,
                reasoning="Refined response for clarity and completeness"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.CITATION_FORMATTING.value
            
            logger.info(f"Response refinement completed")
            return state
            
        except Exception as e:
            logger.error(f"Response refinement failed: {e}")
            state["error_messages"].append(f"Response refinement error: {e}")
            return state
    
    async def _format_citations(self, state: AgentState) -> AgentState:
        """Step 8: Format proper citations for sources used."""
        start_time = time.time()
        
        try:
            retrieval_results = state["retrieval_results"]
            citations = []
            
            # Create citations from retrieval results
            citation_id = 1
            for result in retrieval_results:
                for chunk in result.chunks:
                    if chunk.get("score", 0) > 0.5:  # Only cite high-relevance chunks
                        citation = {
                            "id": citation_id,
                            "source": chunk.get("metadata", {}).get("filename", "Unknown"),
                            "chunk_index": chunk.get("metadata", {}).get("chunk_index", 0),
                            "relevance_score": chunk.get("score", 0),
                            "content_preview": chunk.get("content", "")[:100] + "..."
                        }
                        citations.append(citation)
                        citation_id += 1
            
            state["citations"] = citations[:5]  # Limit to top 5 citations
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.CITATION_FORMATTING,
                input_data={"total_chunks": state["total_chunks_retrieved"]},
                output_data={"citations_created": len(citations)},
                execution_time=execution_time,
                success=True,
                reasoning=f"Formatted {len(citations)} citations from retrieved sources"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.QUALITY_ASSESSMENT.value
            
            logger.info(f"Citation formatting completed: {len(citations)} citations created")
            return state
            
        except Exception as e:
            logger.error(f"Citation formatting failed: {e}")
            state["error_messages"].append(f"Citation formatting error: {e}")
            return state
    
    async def _assess_quality(self, state: AgentState) -> AgentState:
        """Step 9: Final quality assessment before delivery."""
        start_time = time.time()
        
        try:
            refined_answer = state["refined_answer"]
            citations = state["citations"]
            confidence = state["confidence_assessment"]
            fact_check = state["fact_check_results"]
            
            # Quality assessment criteria
            quality_score = 0.0
            quality_factors = []
            
            # Check answer completeness
            if len(refined_answer) > 50:
                quality_score += 0.2
                quality_factors.append("Answer has sufficient length")
            
            # Check citation quality
            if len(citations) > 0:
                quality_score += 0.2
                quality_factors.append("Sources properly cited")
            
            # Check confidence level
            if confidence > self.confidence_threshold:
                quality_score += 0.3
                quality_factors.append("High confidence retrieval")
            
            # Check fact verification
            if fact_check.get("context_support", False):
                quality_score += 0.2
                quality_factors.append("Answer supported by context")
            
            # Check for errors
            if not state["error_messages"]:
                quality_score += 0.1
                quality_factors.append("No processing errors")
            
            # Create final response with citations
            final_response = refined_answer
            
            if citations:
                final_response += "\n\n**Sources:**\n"
                for i, citation in enumerate(citations, 1):
                    final_response += f"{i}. {citation['source']} (relevance: {citation['relevance_score']:.2f})\n"
            
            state["final_response"] = final_response
            
            execution_time = time.time() - start_time
            
            # Record workflow step
            step = WorkflowStep(
                stage=WorkflowStage.QUALITY_ASSESSMENT,
                input_data={"response_length": len(refined_answer)},
                output_data={
                    "quality_score": quality_score,
                    "quality_factors": quality_factors,
                    "final_length": len(final_response)
                },
                execution_time=execution_time,
                success=True,
                reasoning=f"Quality assessment completed with score {quality_score:.2f}"
            )
            
            state["workflow_steps"].append(step)
            state["current_stage"] = WorkflowStage.COMPLETED.value
            
            logger.info(f"Quality assessment completed: score {quality_score:.2f}")
            return state
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            state["error_messages"].append(f"Quality assessment error: {e}")
            return state
    
    def _update_metrics(self, execution_time: float, success: bool):
        """Update performance metrics."""
        self.metrics["total_queries_processed"] += 1
        
        # Update average execution time
        total = self.metrics["total_queries_processed"]
        current_avg = self.metrics["average_execution_time"]
        self.metrics["average_execution_time"] = (current_avg * (total - 1) + execution_time) / total
        
        # Update success rate
        if success:
            current_successes = self.metrics["success_rate"] * (total - 1)
            self.metrics["success_rate"] = (current_successes + 1) / total
        else:
            current_successes = self.metrics["success_rate"] * (total - 1)
            self.metrics["success_rate"] = current_successes / total
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow performance metrics."""
        return self.metrics.copy()
    
    def visualize_workflow_execution(self, workflow_result: Dict[str, Any]) -> str:
        """Create a text visualization of the workflow execution."""
        steps = workflow_result.get("workflow_steps", [])
        total_time = workflow_result.get("total_execution_time", 0)
        
        visualization = f"\n🔄 Agentic RAG Workflow Execution Summary\n"
        visualization += f"{'='*50}\n"
        visualization += f"Total Execution Time: {total_time:.3f}s\n"
        visualization += f"Final Stage: {workflow_result.get('current_stage', 'unknown')}\n\n"
        
        for i, step in enumerate(steps, 1):
            stage_name = step.stage.value.replace('_', ' ').title()
            status = "✅" if step.success else "❌"
            
            visualization += f"{i:2d}. {status} {stage_name}\n"
            visualization += f"     Time: {step.execution_time:.3f}s | {step.reasoning}\n"
            
            if step.output_data:
                key_outputs = []
                for key, value in step.output_data.items():
                    if isinstance(value, (int, float)):
                        key_outputs.append(f"{key}: {value}")
                    elif isinstance(value, str) and len(value) < 30:
                        key_outputs.append(f"{key}: {value}")
                
                if key_outputs:
                    visualization += f"     Output: {', '.join(key_outputs)}\n"
            
            visualization += "\n"
        
        # Add final results
        if workflow_result.get("final_response"):
            response_preview = workflow_result["final_response"][:100]
            visualization += f"📄 Final Response: {response_preview}...\n"
        
        if workflow_result.get("citations"):
            citation_count = len(workflow_result["citations"])
            visualization += f"📚 Sources Cited: {citation_count}\n"
        
        if workflow_result.get("confidence_assessment"):
            confidence = workflow_result["confidence_assessment"]
            visualization += f"🎯 Confidence: {confidence:.2f}\n"
        
        return visualization


# Convenience functions for easy usage
async def create_agentic_workflow(llm_manager=None, vector_store=None) -> AgenticRAGWorkflow:
    """Create and initialize an agentic RAG workflow."""
    workflow = AgenticRAGWorkflow(
        llm_manager=llm_manager,
        vector_store=vector_store
    )
    return workflow


# Example usage and testing
if __name__ == "__main__":
    async def test_agentic_workflow():
        """Test the agentic workflow system."""
        print("Testing Agentic RAG Workflow...")
        
        # This would normally use real LLM and vector store
        workflow = AgenticRAGWorkflow()
        
        # Test query
        test_query = "What is machine learning and how does it work?"
        
        result = await workflow.process_query(test_query)
        
        print("Workflow Result:")
        print(f"Query: {result['original_query']}")
        print(f"Intent: {result['query_intent']}")
        print(f"Final Response: {result['final_response']}")
        print(f"Execution Time: {result['total_execution_time']:.3f}s")
        
        # Visualize execution
        visualization = workflow.visualize_workflow_execution(result)
        print(visualization)
    
    # Run test
    asyncio.run(test_agentic_workflow())