"""
LangChain Service - Modern Agentic Framework Integration

This service provides LangChain-based agents and chains for:
- RAG (Retrieval Augmented Generation) with ChromaDB
- Chat with conversation memory
- Quiz generation with tool-calling agents
- Structured output parsing
"""
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from typing import List, Dict, Any
import json
from logging_config import get_logger

from config import settings

logger = get_logger(__name__)


class LangChainService:
    """LangChain-based AI service with agents and chains"""
    
    def __init__(self):
        """Initialize LangChain components"""
        # LLM
        self.llm = ChatGroq(
            groq_api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            temperature=0.7
        )
        
        # Embeddings (for RAG)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )
    
    def create_rag_chain(self, collection_name: str) -> RetrievalQA:
        """
        Create a RetrievalQA chain for RAG-based question answering
        
        Args:
            collection_name: ChromaDB collection name (user_id + file_id)
        
        Returns:
            RetrievalQA chain
        """
        # Use PersistentClient to avoid conflicts with existing ChromaDB instance
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Load vector store with existing client
        vectorstore = Chroma(
            client=chroma_client,
            collection_name=collection_name,
            embedding_function=self.embeddings
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Custom prompt for RAG
        prompt_template = """You are a helpful AI tutor. Use the following context from the student's document to answer their question.

Context from document:
{context}

Student's Question: {question}

Provide a clear, educational answer based on the context. If the context doesn't contain the answer, say so clearly.

Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create RetrievalQA chain
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        return chain
    
    async def generate_quiz_with_agent(
        self,
        context: str,
        topic: str,
        num_questions: int,
        difficulty: str
    ) -> List[Dict]:
        """
        Use LangChain agent to generate HIGH-QUALITY quiz questions
        """
        # Define difficulty guidelines (enhanced)
        difficulty_guidelines = {
            "easy": """
EASY Questions (Basic Recall):
- Directly stated facts and definitions from the text
- Simple true/false or identification questions  
- Test basic understanding and memorization
- Answer should be explicitly in the document
- No complex reasoning required
Examples: "What is X?", "Define Y", "Which of these is mentioned?"
""",
            "medium": """
MEDIUM Questions (Understanding & Application):
- Require comprehension beyond simple recall
- Combine 2-3 related concepts
- Test ability to apply knowledge
- May require inference from context
- Compare/contrast related ideas
Examples: "How does X relate to Y?", "What would happen if...?", "Why is X important?"
""",
            "hard": """
HARD Questions (Analysis & Synthesis):
- Deeply conceptual and analytical
- Require critical thinking and synthesis
- Apply concepts to new scenarios
- Evaluate trade-offs or implications
- Multi-step reasoning required
Examples: "Analyze the relationship between...", "Evaluate the impact of...", "Synthesize..."
"""
        }
        
        diff_guide = difficulty_guidelines.get(difficulty.lower(), difficulty_guidelines["medium"])
        
        # Enhanced prompt for quality
        prompt = ChatPromptTemplate.from_template("""
You are an EXPERT QUIZ CREATOR specializing in {difficulty} difficulty questions.

YOUR MISSION: Create {num_questions} HIGH-QUALITY multiple-choice questions that truly test student understanding.

DIFFICULTY LEVEL: {difficulty}
{diff_guide}

CRITICAL QUALITY REQUIREMENTS:
✓ Questions MUST be based on FACTUAL information from the provided content
✓ Create 4 PLAUSIBLE options - make wrong answers tempting but clearly wrong
✓ Ensure ONLY ONE unambiguously correct answer
✓ Avoid "all of the above" or "none of the above" options
✓ Questions should be clear, specific, and well-written
✓ Test different aspects of the topic (don't repeat similar questions)
✓ Provide detailed explanations for WHY the answer is correct
✓ Tag each question with the specific concept/topic it tests

CONTENT TO CREATE QUIZ FROM:
Topic: {topic}

Document Content (use ALL relevant information):
{context}

OUTPUT FORMAT (STRICT JSON):
[
  {{
    "id": 1,
    "question": "Clear, specific question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "The exact text of the correct option",
    "explanation": "Detailed explanation of why this is correct and why others are wrong",
    "concept": "Specific concept this question tests",
    "difficulty": "{difficulty}"
  }},
  ...
]

IMPORTANT: Return ONLY the JSON array. No markdown, no extra text, just valid JSON.
""")
        
        # Create chain
        chain = prompt | self.llm
        
        # Invoke
        try:
            response = await chain.ainvoke({
                "num_questions": num_questions,
                "difficulty": difficulty,
                "diff_guide": diff_guide,
                "context": context[:6000],  # Increased for 20-question quizzes
                "topic": topic
            })
            
            # Parse response
            content = response.content
            
            # Clean JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            questions = json.loads(content.strip())
            
            # Validate questions
            if isinstance(questions, list) and len(questions) > 0:
                logger.info(f"Generated {len(questions)} quality questions")
                return questions
            else:
                logger.warning("No valid questions generated")
                return []
                
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}", exc_info=True)
            print(f"Failed to parse quiz JSON: {str(e)}")
            return []
    
    async def chat_with_memory(
        self,
        collection_name: str,
        question: str,
        chat_history: List[tuple] = None
    ) -> Dict[str, Any]:
        """
        Chat with conversation memory using ConversationalRetrievalChain
        
        Args:
            collection_name: ChromaDB collection
            question: User question
            chat_history: Previous conversation [(q, a), ...]
        
        Returns:
            Answer with source documents
        """
        # Load vector store
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIR
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        
        # Create conversational chain
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True
        )
        
        # Add previous history
        if chat_history:
            for q, a in chat_history:
                memory.chat_memory.add_user_message(q)
                memory.chat_memory.add_ai_message(a)
        
        # Query
        result = await chain.ainvoke({"question": question})
        
        return {
            "answer": result["answer"],
            "source_documents": [doc.page_content for doc in result["source_documents"]]
        }
    
    async def summarize_document(self, context: str) -> Dict:
        """
        Summarize document using LangChain
        
        Args:
            context: Document content
        
        Returns:
            Summary dict
        """
        prompt = ChatPromptTemplate.from_template("""
You are an expert document summarizer. Analyze the provided PDF content and create a comprehensive summary.

Document content:
{context}

Provide the summary in JSON format:
{{
  "overview": "Brief overview of the document",
  "main_topics": ["topic1", "topic2", ...],
  "key_concepts": ["concept1", "concept2", ...],
  "important_points": ["point1", "point2", ...]
}}
""")
        
        chain = prompt | self.llm
        
        response = await chain.ainvoke({"context": context[:4000]})
        
        try:
            return json.loads(response.content)
        except:
            return {"overview": response.content}


# Singleton instance
langchain_service = LangChainService()
