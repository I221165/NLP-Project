"""
Groq API client - Comprehensive answer method
"""
from groq import Groq
from config import settings

async def answer_question_comprehensive(client: Groq, model: str, question: str, context_chunks: list[str]) -> dict:
    """
    Answer using ALL chunks with forced comprehensive synthesis
    """
    if not context_chunks:
        return {"answer": "No relevant context found."}
    
    # Number each chunk
    numbered_chunks = "\n\n".join([f"[CHUNK {i+1}]:\n{chunk}" for i, chunk in enumerate(context_chunks)])
    
    system_prompt = """You are an expert AI tutor providing COMPREHENSIVE, DETAILED explanations.

CRITICAL INSTRUCTIONS:
1. You MUST synthesize information from ALL provided chunks
2. Reference specific chunks using [Chunk X] citations  
3. Provide step-by-step, detailed explanations
4. Use examples, analogies, and breakdowns
5. Create a complete answer covering all relevant aspects
6. If multiple chunks have related info, COMBINE them
7. Be DETAILED and COMPREHENSIVE - don't summarize, EXPLAIN FULLY

Format:
- Start with overview
- Break into clear sections
- Use bullet points
- End with summary
- Include [Chunk X] citations throughout"""
    
    user_prompt = f"""You have {len(context_chunks)} chunks from the document.

USE ALL RELEVANT CHUNKS for a COMPREHENSIVE answer to:

QUESTION: {question}

DOCUMENT CONTEXT ({len(context_chunks)} CHUNKS):
{numbered_chunks}

REQUIREMENTS:
✓ Synthesize ALL relevant information
✓ Cite chunks using [Chunk X]
✓ Detailed explanations, not summaries
✓ Break down complex concepts
✓ Use examples
✓ Create thorough, complete answer

Your detailed answer:"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=2000
        )
        
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": f"Error: {str(e)}"}
