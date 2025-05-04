from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
from pdftotext import extract_text_from_pdf
import ollama
from fastapi.middleware.cors import CORSMiddleware

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
    return {"message": "Welcome to the Ollama API using mistral model!"}

@app.post("/get-response")
async def get_response(file: UploadFile = File(...)):
    try:
        # Read the uploaded file content
        contents = await file.read()
        
        # Extract text from PDF using our module
        try:
            extracted_text = extract_text_from_pdf(file_bytes=contents)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to process PDF: {str(e)}"
            )

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF contains no extractable text"
            )

        # Prepare the prompt
        prompt = f"""
        Analyze the following document and generate a 5-item multiple choice quiz based on its content.
        For each question, provide 4 choices (A-D), indicate the correct answer, and include a brief explanation.

        Required format for each question:
        [Question number]: [question text]
        A: [choice A]
        B: [choice B]
        C: [choice C]
        D: [choice D]
        Answer: [correct answer letter]
        Explanation: [brief explanation why this is correct]

        --- DOCUMENT CONTENT ---
        {extracted_text[:10000]}  # Limiting to first 10k chars to avoid overly long prompts
        """

        # Get response from Ollama
        try:
            response = ollama.generate(
                model="mistral",
                prompt=prompt,
                options={"temperature": 0.7}
            )
            return {"quiz": response["response"]}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate quiz: {str(e)}"
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