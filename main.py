from fastapi import FastAPI, HTTPException
from typing import List, Tuple
from pydantic import BaseModel
import uvicorn
import os
import math
import re

import ollama
from pdftotext import text

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    carbohydrates: int  # User daily intake of carbohydrates
    protein: int    # User daily intake of protein
    sodium: int     # User daily intake of sodium
    carbAvg: int    # Recommended daily intake of carbohydrates
    proteinAvg: int # Recommended daily intake of protein
    sodiumAvg: int  # Recommended daily intake of sodium


@app.get("/")
async def welcome():
    return {"message": "Welcome to the Ollama API using mistral model!"}

@app.post("/get-response")
async def get_response(request: QueryRequest):
    try:
        # Initialize the Ollama client
        client = ollama.Client()

        # Define the model and the input prompt
        model = "mistral"  # Replace with your model name
        prompt = """
        Provide 2 response with the first one having 0.1 temperature and the other one having 1.
        Generate a 5 item multiple choice quiz (Provide the choices using A, B, C, D) based on the document.
        Provide the correct answer and an explanation for each question on why that is the answer using this format:
        [Question number]: [question]
        A: [choice A]
        B: [choice B]
        C: [choice C]
        D: [choice D]
        Answer: [correct answer]
        Explanation: [explanation]
        \n\n""" + text

        # Send the query to the model
        response = client.generate(model=model, prompt=prompt)

        # Print the response from the model
        print("Response from Mistral:")
        print(response.response)
        return { "response": response.response }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)