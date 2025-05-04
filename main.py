from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import os
import io
import pdftotext  # Assuming you're using this for PDF extraction
import ollama

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

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
        # Read the uploaded PDF file content
        contents = await file.read()

        # Extract text from PDF
        pdf = pdftotext.PDF(io.BytesIO(contents))
        extracted_text = "\n\n".join(pdf)

        # Initialize Ollama client
        client = ollama.Client()

        prompt = f"""
        Provide 2 responses: the first one with temperature 0.1 and the second one with temperature 1.
        Generate a 5-item multiple choice quiz (Provide the choices using A, B, C, D) based on the document.
        Provide the correct answer and an explanation for each question using this format:
        [Question number]: [question]
        A: [choice A]
        B: [choice B]
        C: [choice C]
        D: [choice D]
        Answer: [correct answer]
        Explanation: [explanation]
        
        --- PDF Content ---
        {extracted_text}
        """

        response = client.generate(model="mistral", prompt=prompt)

        print("Response from Mistral:")
        print(response.response)
        return {"response": response.response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
