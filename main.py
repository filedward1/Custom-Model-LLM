from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
import re
from pdftotext import extract_text_from_pdf
import ollama
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def welcome():
    return {"message": "Welcome to the Quiz Generator API using Ollama's Mistral model!"}

def parse_quiz_response(response_text: str) -> List[Dict[str, any]]:
    """Parse the raw quiz response into structured format."""
    quiz_data = []
    current_question = None
    
    for line in response_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Question detection (supports multiple formats)
        if re.match(r'^(?:\[?Question\s?\d+\]?:|Q\d+[:.]?|\d+[.:])\s*', line, re.IGNORECASE):
            if current_question:
                quiz_data.append(current_question)
            
            # Extract question number and text
            question_parts = re.split(r'[:.]', line, 1)
            question_text = question_parts[1].strip() if len(question_parts) > 1 else line
            question_num = len(quiz_data) + 1
            
            current_question = {
                'question_number': question_num,
                'question': question_text,
                'choices': {},
                'correct_answer': None,
                'explanation': None
            }
        
        # Choice detection (A, B, C, D with various separators)
        elif match := re.match(r'^([A-D])[):.]?\s+(.*)', line, re.IGNORECASE):
            choice_key = match.group(1).upper()
            choice_text = match.group(2).strip()
            if current_question:
                current_question['choices'][choice_key] = choice_text
        
        # Answer detection
        elif line.lower().startswith(('answer:', 'correct answer:', 'correct:')):
            if current_question:
                answer = line.split(':', 1)[1].strip()
                current_question['correct_answer'] = answer[0].upper() if answer else None
        
        # Explanation detection
        elif line.lower().startswith('explanation:'):
            if current_question:
                current_question['explanation'] = line.split(':', 1)[1].strip()
        
        # Continuation lines
        elif current_question:
            if not current_question['choices']:
                current_question['question'] += ' ' + line
            else:
                last_choice = max(current_question['choices'].keys(), default=None)
                if last_choice:
                    current_question['choices'][last_choice] += ' ' + line
    
    if current_question:
        quiz_data.append(current_question)
    
    return quiz_data

def validate_quiz_data(quiz_data: List[Dict[str, any]]) -> List[str]:
    """Validate the parsed quiz structure and return warnings."""
    warnings = []
    
    if len(quiz_data) != 5:
        warnings.append(f"Expected 5 questions, got {len(quiz_data)}")
    
    for i, question in enumerate(quiz_data):
        if not question.get('question'):
            warnings.append(f"Question {i+1} missing question text")
        if len(question.get('choices', {})) < 4:
            warnings.append(f"Question {i+1} has only {len(question['choices'])} choices")
        if not question.get('correct_answer'):
            warnings.append(f"Question {i+1} missing correct answer")
        if not question.get('explanation'):
            warnings.append(f"Question {i+1} missing explanation")
    
    return warnings

@app.post("/get-response")
async def get_response(file: UploadFile = File(...)):
    try:
        # Read and validate PDF
        contents = await file.read()
        try:
            extracted_text = extract_text_from_pdf(file_bytes=contents)
            if not extracted_text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded PDF contains no extractable text"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to process PDF: {str(e)}"
            )

        # Generate quiz prompt
        prompt = f"""Generate a 5-item multiple choice quiz from this document. For each question:
1. Start with "Question [number]: [question text]"
2. Provide choices as:
A: [choice A]
B: [choice B]
C: [choice C]
D: [choice D]
3. Specify "Answer: [letter]"
4. Include "Explanation: [text]"

Document content:
{extracted_text}"""

        # Get response from Ollama
        try:
            response = ollama.generate(
                model="mistral",
                prompt=prompt,
                options={"temperature": 0.7}
            )
            
            # Parse and validate response
            quiz_data = parse_quiz_response(response["response"])
            warnings = validate_quiz_data(quiz_data)
            
            return {
                "data": {
                    "quiz": quiz_data,
                }
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate quiz: {str(e)}. Response sample: {response.get('response', '')[:200]}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)