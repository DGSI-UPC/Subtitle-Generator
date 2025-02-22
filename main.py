from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import os
import whisper
from pydub import AudioSegment

app = FastAPI()

model = whisper.load_model("base")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r") as file:
        html_content = file.read()

    return HTMLResponse(content=html_content)

@app.post("/upload-audio/")
async def upload_audio(audio_file: UploadFile = File(...)):

    allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac'}
    file_ext = os.path.splitext(audio_file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File format not supported")

    temp_filename = f"temp_{audio_file.filename}"
    wav_filename = f"temp_converted_{audio_file.filename}.wav"
    
    try:
        content = await audio_file.read()
        with open(temp_filename, "wb") as temp_file:
            temp_file.write(content)

        if file_ext != '.wav':
            audio = AudioSegment.from_file(temp_filename)
            audio.export(wav_filename, format="wav")
            processing_file = wav_filename
        else:
            processing_file = temp_filename

        result = model.transcribe(processing_file)
        transcription = result["text"]

        return {
            "filename": audio_file.filename,
            "transcription": transcription
        }

    except Exception as e:
        return {"error": f"Processing error: {str(e)}"}
    
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        if os.path.exists(wav_filename):
            os.remove(wav_filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)