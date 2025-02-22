# Subtitle Generator

This project provides a simple web application that transcribes audio files into text, effectively generating subtitles. It uses the Whisper speech recognition model from OpenAI for transcription and FastAPI for the web API.

## Features

*   **Web Interface:**  A clean, user-friendly HTML interface for uploading audio files.
*   **Multiple Audio Formats:** Supports `.wav`, `.mp3`, `.m4a`, and `.flac` audio files.
*   **Fast Transcription:** Leverages the Whisper 'base' model for efficient transcription.
*   **Easy Deployment:**  Uses FastAPI and Uvicorn for simple deployment.
*   **Clear API:**  A single endpoint `/upload-audio/` handles file uploads and transcription.

## Requirements

Before you begin, ensure you have the following installed:

1.  **Python:** (3.7 or higher recommended).  You can check your Python version with `python --version` or `python3 --version`.

2.  **FFmpeg:**  This is a crucial dependency for audio file conversion.
    *   **Ubuntu/Debian:**
        ```bash
        sudo apt update
        sudo apt install ffmpeg
        ```
    *   **macOS (using Homebrew):**
        ```bash
        brew install ffmpeg
        ```
    *   **Windows:**  Download a pre-built binary from a trusted source (e.g., [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)) and add the `bin` directory to your system's PATH environment variable.  *Crucially*, make sure the `ffmpeg` and `ffprobe` executables are accessible from your command line.  Test this by opening a new command prompt/terminal and typing `ffmpeg -version`.
    *   **Verification (all platforms):** After installation, verify FFmpeg is correctly installed by running:
          ```bash
          ffmpeg -version
          ```
          You should see version information outputted to the console.

3.  **Python Packages:** Install the necessary Python libraries using pip:
    ```bash
    pip install -r requirements.txt
    ```
    The `requirements.txt` file should contain (create it if it doesn't exist):
    ```
    uvicorn
    fastapi
    python-multipart
    Flask
    SpeechRecognition
    pydub
    openai-whisper
    ```

## Setup and Running the Application

1.  **Clone the Repository (if applicable):**  If you have the code in a Git repository, clone it:
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    Replace `<repository_url>` and `<repository_directory>` with the appropriate values. If you just have the files directly, make sure they are in the same directory.

2.  **Create `index.html`:**  Ensure the provided `index.html` file is in the same directory as your Python script (`main.py` or whatever you've named it).

3.  **Run the Application:** Start the FastAPI server using Uvicorn:
    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8080
    ```
    *   `main:app`:  This assumes your Python file is named `main.py` and the FastAPI app instance is named `app`. Adjust if necessary.
    *   `--reload`:  Enables automatic reloading of the server when you make code changes (very useful during development).
    *   `--host 0.0.0.0`:  Makes the server accessible from other devices on your network (not just your local machine).  If you only want it accessible locally, you can remove this, and it will default to `127.0.0.1`.
    *   `--port 8080`:  Specifies the port the server will listen on. You can change this if needed.

4.  **Access the Application:** Open your web browser and go to:
    *   `http://localhost:8080` (if you're accessing it from the same machine)
    *   `http://<your_server_ip>:8080` (if accessing from another device on your network, replace `<your_server_ip>` with the server's IP address)

    You should see the "Subtitle Generator" web page.

## API Documentation

The API has a single endpoint:

*   **`/upload-audio/` (POST)**
    *   **Description:**  Uploads an audio file and returns its transcription.
    *   **Request:**
        *   `Content-Type`: `multipart/form-data`
        *   Body:  A single file field named `audio_file` containing the audio file.
    *   **Response:**
        *   `Content-Type`: `application/json`
        *   Success (Status Code: 200):
            ```json
            {
                "filename": "name_of_the_uploaded_file.mp3",
                "transcription": "The transcribed text of the audio file."
            }
            ```
        *   Error (Status Code: 400 or 500):
            ```json
            {
                "error": "A description of the error."
            }
            ```
            *   Example Error (Unsupported File Format):
              ```json
              {
                  "detail": "File format not supported"
              }
              ```
            *  Example Error (Processing Error)
            ```json
              {
                  "error": "Processing error: ..."
              }
            ```
## Contributing

Contributions are welcome! If you'd like to contribute:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix: `git checkout -b feature/my-new-feature` or `git checkout -b bugfix/fix-issue-123`.
3.  Make your changes and commit them with clear, concise commit messages.
4.  Push your branch to your forked repository.
5.  Submit a pull request to the main repository.

## Limitations

*   **Model Accuracy:** This project uses the "base" Whisper model. While fast, it may not be as accurate as larger models, especially with noisy audio or complex language.  Consider experimenting with other Whisper models (e.g., "small", "medium", "large") by changing `model = whisper.load_model("base")` in your Python code.  Larger models require more memory and processing power.
*   **No Speaker Recognition:** The current implementation *does not* perform speaker recognition. The README initially stated it did, which was incorrect.  Adding speaker recognition would require integrating a separate speaker diarization library (like `pyannote.audio`).
*   **Real-time Transcription:**  This is *not* a real-time transcription service.  It processes entire audio files after they are uploaded.  Real-time transcription would require a significantly different architecture (e.g., using WebSockets).
*   **Error Handling:**  While basic error handling is included, more robust error handling and logging could be implemented.
* **File Size:** There is no file size validation. This should be implemented.

## Further Improvements (TODOs)

*   **Add File Size Limits:** Prevent excessively large file uploads.
*   **Implement Progress Bar:** Show upload and processing progress to the user.
*   **Improve Error Handling:** Provide more informative error messages to the user.
*   **Add Support for Subtitle Formats (SRT, VTT):** Allow users to download the transcription in common subtitle formats.
*   **Explore Speaker Diarization:** Integrate a library like `pyannote.audio` to add speaker labels to the transcription.
*   **Dockerization:** Create a Dockerfile to simplify deployment.