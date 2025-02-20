from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Subtitle Generator</title>
    </head>
    <body>
        <h1>Welcome to the Subtitle Generator</h1>
        <form action="/upload-audio/" method="post" enctype="multipart/form-data">
            <input type="file" name="audio_file">
            <input type="submit" value="Upload">
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/upload-audio/")
async def upload_audio(audio_file: UploadFile = File(...)):
    return {"filename": audio_file.filename}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)