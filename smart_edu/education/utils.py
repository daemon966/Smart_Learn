import time
from googleapiclient.discovery import build

def fetch_youtube_videos(keywords, api_key):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.search().list(
            q=keywords,
            part="snippet",
            maxResults=5
        )
        response = request.execute()
        videos = [
            {
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
            for item in response.get('items', []) if item['id']['kind'] == 'youtube#video'
        ]
        return videos
    except Exception as e:
        return {"error": f"Error fetching videos: {e}"}



import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('stopwords')

def extract_keywords(text, num_keywords=5):
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    keywords = [word for word in word_tokens if word.isalnum() and word.lower() not in stop_words]
    return keywords[:num_keywords]






import requests
from django.conf import settings

API_KEY = settings.ASSEMBLYAI_API_KEY

# Submit audio URL for transcription
def submit_transcription(audio_url):
    headers = {'authorization': API_KEY}
    response = requests.post(
        'https://api.assemblyai.com/v2/transcript',
        json={'audio_url': audio_url},
        headers=headers
    )
    if response.status_code == 200:
        return response.json()['id']
    else:
        raise Exception("Error submitting audio for transcription: " + response.text)

# Poll for transcription results
def poll_transcription(transcription_id, timeout=300):
    headers = {'authorization': API_KEY}
    url = f'https://api.assemblyai.com/v2/transcript/{transcription_id}'
    elapsed_time = 0
    wait_interval = 5

    while elapsed_time < timeout:
        response = requests.get(url, headers=headers)
        result = response.json()
        
        if result['status'] == 'completed':
            return result['text']
        elif result['status'] == 'failed':
            raise Exception("Transcription failed: " + result['error'])
        
        time.sleep(wait_interval)
        elapsed_time += wait_interval

    raise TimeoutError("Transcription polling timed out.")


# Main function to handle transcription
def get_transcript(audio_url):
    try:
        transcription_id = submit_transcription(audio_url)
        transcript = poll_transcription(transcription_id)
        return transcript
    except Exception as e:
        return str(e)


from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, VideoUnavailable

def get_video_transcript(video_id):
    """
    Fetch the transcript of a YouTube video.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry['text'] for entry in transcript])
        return text
    except (NoTranscriptFound, VideoUnavailable) as e:
        print(f"Error fetching transcript: {e}")
        return None
