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

from config import settings


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
        Use LangChain agent to generate quiz questions
        
        Args:
            context: Document context
            topic: Quiz topic
            num_questions: Number of questions
            difficulty: easy/medium/hard
        
        Returns:
            List of quiz questions
        """
        # Define difficulty guidelines
        difficulty_guidelines = {
            "easy": "straightforward questions directly from text",
            "medium": "questions requiring understanding and application",
            "hard": "fully conceptual and analytical questions"
        }
        
        diff_guide = difficulty_guidelines.get(difficulty.lower(), difficulty_guidelines["medium"])
        
        # Create structured output prompt
        prompt = ChatPromptTemplate.from_template("""
You are an expert quiz creator. Generate {num_questions} multiple-choice questions at {difficulty} difficulty level.

Guidelines: {diff_guide}

Content to create quiz from:
{context}

Topic: {topic}

Generate questions in this EXACT JSON format:
[
  {{
    "id": 1,
    "question": "Question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Brief explanation",
    "concept": "Specific concept tested",
    "difficulty": "{difficulty}"
  }}
]

Return ONLY valid JSON array, no additional text.
""")
        
        # Create chain
        chain = prompt | self.llm
        
        # Invoke
        response = await chain.ainvoke({
            "num_questions": num_questions,
            "difficulty": difficulty,
            "diff_guide": diff_guide,
            "context": context[:3000],
            "topic": topic
        })
        
        # Parse response
        content = response.content
        try:
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            questions = json.loads(content.strip())
            return questions if isinstance(questions, list) else []
        except:
            print(f"Failed to parse quiz JSON: {content[:200]}")
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
