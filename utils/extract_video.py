# import cv2
# import base64
# import os
# import uuid
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI()

# def whisper_transcribe(video_path):
#     with open(video_path, "rb") as video_file:
#         transcript = client.audio.transcriptions.create(
#             model="gpt-4o-transcribe",  # ✅ correct model for speech-to-text
#             file=video_file
#         )
#     return transcript.text

# def extract_from_video(file_path):
#     # ✅ Direct speech-to-text from video
#     transcript = whisper_transcribe(file_path)

#     # ✅ Extract Keyframes (3 frames)
#     cap = cv2.VideoCapture(file_path)
#     frames = []
#     total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#     sample_rate = max(1, total_frames // 3)

#     for i in range(0, total_frames, sample_rate):
#         cap.set(cv2.CAP_PROP_POS_FRAMES, i)
#         ret, frame = cap.read()
#         if not ret:
#             continue
#         _, buffer = cv2.imencode(".jpg", frame)
#         frames.append(base64.b64encode(buffer).decode())

#     cap.release()
#     return transcript, frames
# utils/extract_video.py

# import cv2
# import base64
# import os
# from dotenv import load_dotenv
# import google.generativeai as genai

# load_dotenv()
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# # ---------------- Speech-to-Text using Gemini ---------------- #
# def gemini_transcribe(video_path):
#     # ✅ Use correct model name without "models/" prefix
#     model = genai.GenerativeModel("gemini-1.5-flash")
    
#     with open(video_path, "rb") as f:
#         video_bytes = f.read()
    
#     # Upload the video file
#     video_file = genai.upload_file(path=video_path)
    
#     # Wait for processing
#     import time
#     while video_file.state.name == "PROCESSING":
#         time.sleep(2)
#         video_file = genai.get_file(video_file.name)
    
#     if video_file.state.name == "FAILED":
#         raise ValueError("Video processing failed")
    
#     # Generate transcription
#     response = model.generate_content(
#         [
#             video_file,
#             "Transcribe all the spoken audio from this video clearly and accurately."
#         ],
#         generation_config=genai.GenerationConfig(
#             temperature=0.1,
#         )
#     )
    
#     # Clean up uploaded file
#     genai.delete_file(video_file.name)
    
#     return response.text

# # ---------------- Key-Frame Extraction ---------------- #
# def extract_from_video(video_path):
#     try:
#         # Get transcript from video
#         transcript = gemini_transcribe(video_path)
        
#         # Extract keyframes
#         cap = cv2.VideoCapture(video_path)
#         frames = []
#         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         sample_rate = max(1, total_frames // 3)
        
#         for i in range(0, total_frames, sample_rate):
#             cap.set(cv2.CAP_PROP_POS_FRAMES, i)
#             ret, frame = cap.read()
#             if not ret:
#                 continue
#             _, buffer = cv2.imencode(".jpg", frame)
#             frames.append(base64.b64encode(buffer).decode())
#             if len(frames) == 3:  # Only 3 frames
#                 break
        
#         cap.release()
        
#         return transcript, frames
    
#     except Exception as e:
#         print(f"Error processing video: {e}")
#         return f"Error: {str(e)}", []
    



import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ---------------- Video Summarization (For <20MB videos) ---------------- #
def extract_from_video(video_path):
    # Read video bytes
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    # Initialize model
    model = genai.GenerativeModel("gemini-2.0-flash")

    # Generate summary directly using video bytes
    response = model.generate_content(
        [
            {"mime_type": "video/mp4", "data": video_bytes},
            "Please summarize this video in 3 concise sentences."
        ],
        generation_config=genai.GenerationConfig(
            temperature=0.2
        ),
    )

    return response.text