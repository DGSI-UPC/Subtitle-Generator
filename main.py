from fastapi import FastAPI, File, Response, UploadFile, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import os
import whisper
from pydub import AudioSegment
from pyannote.audio import Pipeline
import tempfile
from dotenv import load_dotenv
import psutil
import torch

app = FastAPI()

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/upload-audio/":
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > MAX_UPLOAD_SIZE:
                return JSONResponse(content={"detail": "File size exceeds the maximum limit of 50 MB."}, status_code=413)
        return await call_next(request)

app.add_middleware(LimitUploadSizeMiddleware)

# Define Whisper models with memory requirements (in GB)
models = [
    ("large", 10),  # Most accurate, 10 GB
    ("turbo", 6),   # Fast, near-large accuracy, 6 GB
    ("medium", 5),  # 5 GB
    ("small", 2),   # 2 GB
    ("base", 1),    # 1 GB
    ("tiny", 1)     # Least accurate, 1 GB
]

# Get available RAM in GB
available_ram_GB = psutil.virtual_memory().available / (1024 ** 3)

# Select the largest model that fits in available RAM
selected_model = None
selected_requirement = None
for model_name, requirement in models:
    if requirement <= available_ram_GB:
        selected_model = model_name
        selected_requirement = requirement
        break

if selected_model is None:
    raise ValueError("Insufficient RAM to load even the 'tiny' model (requires ~1 GB).")

# Decide the device: use GPU if available and VRAM is sufficient
device = "cpu"
if torch.cuda.is_available():
    total_vram_GB = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    if total_vram_GB >= selected_requirement:
        device = "cuda"

# Load the selected model on the chosen device
model = whisper.load_model(selected_model, device=device)
print(f"Selected model: {selected_model} (requires ~{selected_requirement} GB) on {device}")

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

# Helper function to convert seconds to VTT timestamp format
def seconds_to_vtt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.post("/upload-audio/")
async def upload_audio(audio_file: UploadFile = File(...), file_type: str = Form(...)):
    allowed_extensions = {'.wav', '.mp3', '.m4a', '.flac'}
    file_ext = os.path.splitext(audio_file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File format not supported. Please upload a file with one of the following extensions: .wav, .mp3, .m4a, .flac")

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
        
        # Initialize content and counter
        content = ""
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
                
                # Generate entries for each transcription segment
                for seg in result["segments"]:
                    seg_start = start_time + seg['start']
                    seg_end = start_time + seg['end']
                    text = seg['text'].strip().replace('\n', ' ')
                    
                    if file_type == 'srt':
                        entry = f"{counter}\n"
                        entry += f"{seconds_to_srt_time(seg_start)} --> {seconds_to_srt_time(seg_end)}\n"
                        entry += f"{speaker}: {text}\n\n"
                    elif file_type == 'vtt':
                        entry = f"{counter}\n"
                        entry += f"{seconds_to_vtt_time(seg_start)} --> {seconds_to_vtt_time(seg_end)}\n"
                        entry += f"{speaker}: {text}\n\n"
                    
                    content += entry
                    counter += 1
            
            finally:
                # Clean up temporary segment file
                if os.path.exists(temp_segment_file):
                    os.remove(temp_segment_file)

        # Modified return statement for file download
        base_filename = os.path.splitext(audio_file.filename)[0]
        if file_type == 'srt':
            filename = f"{base_filename}.srt"
            media_type = "application/x-subrip"
        elif file_type == 'vtt':
            filename = f"{base_filename}.vtt"
            media_type = "text/vtt"
        
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        return Response(content=content, media_type=media_type, headers=headers)

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"An unexpected error occurred during processing: {str(e)}"})
    
    finally:
        # Clean up main temporary files
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        if os.path.exists(wav_filename):
            os.remove(wav_filename)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)