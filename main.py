from fastapi import FastAPI, File, Response, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
import os
import whisper
from pydub import AudioSegment
from pyannote.audio import Pipeline
import tempfile
from dotenv import load_dotenv

app = FastAPI()

model = whisper.load_model("base")
if model is None:
    raise ValueError("Failed to load Whisper model")

load_dotenv()

auth_token = os.getenv("HF_AUTH_TOKEN")

if not auth_token:
    raise ValueError("HF_AUTH_TOKEN not found in environment variables")

print(f"HF_AUTH_TOKEN: {auth_token}")

try:
    diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization", use_auth_token=auth_token)
    if diarization_pipeline is None:
        raise ValueError("Failed to load diarization pipeline")
    print(f"diarization_pipeline: {diarization_pipeline}")
except Exception as e:
    raise ValueError(f"Failed to load diarization pipeline: {str(e)}. Ensure your token has the necessary permissions and you have accepted the user conditions at https://hf.co/pyannote/speaker-diarization.")

# Helper function to convert seconds to SRT timestamp format
def seconds_to_srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

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
        # Save the uploaded file
        content = await audio_file.read()
        with open(temp_filename, "wb") as temp_file:
            temp_file.write(content)

        # Convert to WAV if necessary
        if file_ext != '.wav':
            audio = AudioSegment.from_file(temp_filename)
            audio.export(wav_filename, format="wav")
            processing_file = wav_filename
        else:
            processing_file = temp_filename

        # Perform speaker diarization
        if diarization_pipeline is None:
            raise ValueError("Diarization pipeline is not initialized")
        diarization = diarization_pipeline(processing_file)
        
        # Load audio for segment extraction
        audio = AudioSegment.from_file(processing_file)
        
        # Initialize SRT content and counter
        srt_content = ""
        counter = 1

        # Process each speaker turn
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            start_time = turn.start
            end_time = turn.end
            
            # Extract audio segment for this speaker
            segment = audio[start_time * 1000 : end_time * 1000]  # pydub uses milliseconds
            
            # Create temporary file for the segment
            temp_segment_file = tempfile.mktemp(suffix='.wav')
            try:
                segment.export(temp_segment_file, format="wav")
                
                # Transcribe the segment
                if model is None:
                    raise ValueError("Whisper model is not initialized")
                result = model.transcribe(temp_segment_file)
                
                # Generate SRT entries for each transcription segment
                for seg in result["segments"]:
                    seg_start = start_time + seg['start']
                    seg_end = start_time + seg['end']
                    text = seg['text'].strip().replace('\n', ' ')
                    
                    srt_entry = f"{counter}\n"
                    srt_entry += f"{seconds_to_srt_time(seg_start)} --> {seconds_to_srt_time(seg_end)}\n"
                    srt_entry += f"{speaker}: {text}\n\n"
                    srt_content += srt_entry
                    counter += 1
            
            finally:
                # Clean up temporary segment file
                if os.path.exists(temp_segment_file):
                    os.remove(temp_segment_file)

        # Modified return statement for file download
        base_filename = os.path.splitext(audio_file.filename)[0]
        srt_filename = f"{base_filename}.srt"
        headers = {
            "Content-Disposition": f'attachment; filename="{srt_filename}"'
        }
        return Response(content=srt_content, media_type="application/x-subrip", headers=headers)

    except Exception as e:
        return {"error": f"Processing error: {str(e)}"}
    
    finally:
        # Clean up main temporary files
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        if os.path.exists(wav_filename):
            os.remove(wav_filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)