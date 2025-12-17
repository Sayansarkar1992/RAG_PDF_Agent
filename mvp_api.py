from fastapi import FastAPI, UploadFile, HTTPException
from rag_pdf_agent import chat_with_pdf
import os

app = FastAPI()

UPLOAD_FOLDER = "pdf"


os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
async def health():
    return {"status": "healthy"}


@app.post("/chat")
async def chat(file: UploadFile, query: str):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    response = chat_with_pdf(file_path, query, top_k=1)

    return {
        "query": query,
        "response": response,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
