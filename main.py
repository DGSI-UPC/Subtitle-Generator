from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Subtitle Generator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f7fa;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background-color: #ffffff;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                text-align: center;
                width: 80%;
                max-width: 600px;
            }
            h1 {
                color: #4CAF50;
                margin-bottom: 20px;
                font-size: 2em;
            }
            form {
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            input[type="file"] {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #ddd;
                width: 100%;
                max-width: 400px;
            }
            input[type="submit"] {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
                margin-top: 20px;
            }
            input[type="submit"]:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to the Subtitle Generator</h1>
            <form action="/upload-audio/" method="post" enctype="multipart/form-data">
                <input type="file" name="audio_file" required>
                <input type="submit" value="Upload">
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/upload-audio/")
async def upload_audio(audio_file: UploadFile = File(...)):
    return {"filename": audio_file.filename}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)