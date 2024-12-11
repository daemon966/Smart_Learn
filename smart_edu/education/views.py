from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import JsonResponse
from .utils import fetch_youtube_videos, extract_keywords
from .models import QuizQuestion, QuizResult
from django.contrib.auth.decorators import login_required
from collections import Counter
import re
import requests
# education/views.py
from .forms import CustomUserCreationForm



from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render
from .models import QuizQuestion  # Assuming this is where your quiz questions are stored
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests


import json
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables (GROQ API key)
load_dotenv()
groq_api_key = ""

# Chatbot View
@csrf_exempt
def chatbot(request):
    """
    Handles user interaction with the Groq chatbot.
    """
    if request.method == "POST":
        try:
            # Get user input from the request
            data = json.loads(request.body)
            user_message = data.get("message", "")
            conversational_memory_length = data.get("memory_length", 5)

            if not user_message:
                return JsonResponse({"response": "Please enter a message."}, status=400)

            # Initialize memory
            memory = ConversationBufferWindowMemory(k=conversational_memory_length)

            # Initialize Groq Langchain chat object and conversation
            groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name="mixtral-8x7b-32768")
            conversation = ConversationChain(llm=groq_chat, memory=memory)

            # Get response from the chatbot
            response = conversation(user_message)
            bot_message = response['response']

            # Save conversation history in session state
            if 'chat_history' not in request.session:
                request.session['chat_history'] = []
            request.session['chat_history'].append({'human': user_message, 'AI': bot_message})

            return JsonResponse({"response": bot_message})

        except Exception as e:
            print(f"Error occurred: {e}")
            return JsonResponse({"response": "Sorry, there was an error processing your request."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

def get_video_transcript(video_id):
    """
    Fetches the transcript for a YouTube video.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # Combine the transcript into a single string
        full_transcript = " ".join([item['text'] for item in transcript])
        return full_transcript
    except TranscriptsDisabled:
        return "Transcript is disabled for this video."
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return "Error fetching transcript."










from langchain_groq import ChatGroq
from dotenv import load_dotenv

from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq
from django.http import JsonResponse

import json

@login_required

def video_quiz(request, video_id):
    """
    Generates quiz questions based on the transcript of a YouTube video.
    """
    if request.method == "GET":
        try:
            # Fetch the transcript for the given video
            transcript = get_video_transcript(video_id)  # Ensure this function is implemented

            if not transcript or "Error" in transcript:
                return JsonResponse({"error": "Failed to retrieve transcript."}, status=400)

            # Initialize Groq Langchain chat object
            groq_chat = ChatGroq(groq_api_key=groq_api_key, model_name="mixtral-8x7b-32768")
            memory = ConversationBufferWindowMemory(k=5)  # Set memory length
            conversation = ConversationChain(llm=groq_chat, memory=memory)

            # Define the prompt for generating quiz questions
            prompt = f"""
            You are a quiz generator. Based on the following text, create a valid JSON array of 10 multiple-choice questions.
            Each question should have the following format:
            {{
                "question": "Question text",
                "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                "answer": "Correct Option"
            }}
            Ensure the JSON is properly formatted.
            Text: {transcript}
            """

            # Generate quiz questions
            response = conversation(prompt)
            print("Raw Groq API Response:", response)  # Print the entire response

            # Extract the actual quiz JSON from the response text
            raw_quiz_data = response.get('response', '')
            start_index = raw_quiz_data.find('[')  # Find the start of JSON array
            end_index = raw_quiz_data.rfind(']') + 1  # Find the end of JSON array

            if start_index == -1 or end_index == -1:
                return JsonResponse({"error": "Failed to extract valid JSON from the response."}, status=500)

            # Clean the response to include only the valid JSON part
            cleaned_json_data = raw_quiz_data[start_index:end_index].strip()
            print("Cleaned Quiz Data:", cleaned_json_data)  # Debugging line

            # Try to parse the cleaned JSON data
            try:
                quiz_data = json.loads(cleaned_json_data)  # Deserialize JSON string
                if not isinstance(quiz_data, list):
                    raise ValueError("Quiz data is not a list.")
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error: {e}")
                return JsonResponse({"error": "Quiz data format invalid or not JSON."}, status=500)
            except ValueError as e:
                print(f"Value Error: {e}")
                return JsonResponse({"error": "Quiz data is not a valid list."}, status=500)

            # Save quiz data to the database
            QuizQuestion.objects.bulk_create([
                QuizQuestion(
                    video_id=video_id,
                    question_text=question['question'],
                    options=question['options'],
                    correct_option=question['answer']
                ) for question in quiz_data
            ])

            context = {
                'video_id': video_id,
                'questions': quiz_data,
            }

            return render(request, 'quiz.html', context)

        except Exception as e:
            print(f"Error occurred: {e}")
            return JsonResponse({"error": f"Quiz generation failed: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


   


# Landing Page view
def landing_page(request):
    """
    Landing page view which will be displayed first.
    """
    return render(request, 'education/landing.html')

# Login page view
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to the home page or dashboard
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'education/login.html')

# Register page view
from django.shortcuts import render, redirect
from django.contrib import messages


from .forms import CustomUserCreationForm


def register_page(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to login after successful registration
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'education/register.html', {'form': form})


# Home page view after login
@login_required
def home(request):
    """
    Home page view which is visible after the user logs in.
    """
    if request.method == "POST":
        text = request.POST.get('content', '')
        keywords = extract_keywords(text)
        videos = fetch_youtube_videos(' '.join(keywords), api_key='AIzaSyBJLB6CtjTZX46dOjRgDcNWmcKaPTPa-8A')
        return render(request, 'education/home.html', {'videos': videos})
    return render(request, 'education/home.html')

# Logout view
def user_logout(request):
    """
    View for logging out the user.
    """
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('landing')  # Redirect to landing page after logout

# @login_required
# def quiz(request, video_id):
#     """
#     Handle quiz submission and save results.
#     """
#     if request.method == "POST":
#         answers = request.POST
#         questions = json.loads(answers.get('questions'))  # Pass questions via a hidden input
#         user_score = 0

#         for question in questions:
#             q_id = question['id']
#             user_answer = answers.get(str(q_id))
#             correct_answer = question['correct_answer']
#             if user_answer == correct_answer:
#                 user_score += 1

#         QuizResult.objects.create(user=request.user, video_id=video_id, score=user_score)
#         return JsonResponse({"score": user_score})
#     else:
#         return JsonResponse({"error": "Invalid request method."}, status=405)

# @login_required
# def leaderboard(request):
#     """
#     Display a leaderboard with top scores across all users.
#     """
#     results = QuizResult.objects.order_by('-score', '-timestamp')[:10]
#     return render(request, 'education/leaderboard.html', {'results': results})

# # Results view
# def results(request):
#     """
#     Results view to display user scores.
#     """
#     return render(request, 'education/results.html')  # Adjust the template path if necessary


def extract_keywords(text):
    """
    Extract keywords from the given text using regex and Counter.
    """
    # Convert text to lowercase and remove punctuation
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)  # Extract words using regex
    
    # Define a basic stopwords list (can be expanded as needed)
    stopwords = {
        "the", "is", "in", "and", "to", "of", "a", "an", "on", "for", "with", 
        "as", "by", "at", "this", "that", "from", "or", "it", "was", "be", "are"
    }
    filtered_words = [word for word in words if word not in stopwords]
    
    # Count word frequencies
    word_frequencies = Counter(filtered_words)
    
    # Get the top 5 keywords
    keywords = [word for word, _ in word_frequencies.most_common(5)]
    return keywords


def fetch_youtube_videos(query, api_key):
    """
    Fetch YouTube videos based on a query and filter videos longer than 5 minutes.
    """
    youtube_search_url = "https://www.googleapis.com/youtube/v3/search"
    youtube_video_url = "https://www.googleapis.com/youtube/v3/videos"
    search_params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': 10,
        'key': api_key,
    }
    try:
        # Fetch search results
        search_response = requests.get(youtube_search_url, params=search_params)
        search_response.raise_for_status()
        search_results = search_response.json().get('items', [])
        
        # Extract video IDs
        video_ids = [item['id']['videoId'] for item in search_results]
        
        # Fetch video details
        video_params = {
            'part': 'snippet,contentDetails',
            'id': ','.join(video_ids),
            'key': api_key,
        }
        video_response = requests.get(youtube_video_url, params=video_params)
        video_response.raise_for_status()
        video_details = video_response.json().get('items', [])
        
        # Filter videos longer than 5 minutes
        videos = []
        for video in video_details:
            duration = video['contentDetails']['duration']
            match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration)
            hours = int(match.group(1)[:-1]) if match.group(1) else 0
            minutes = int(match.group(2)[:-1]) if match.group(2) else 0
            seconds = int(match.group(3)[:-1]) if match.group(3) else 0
            total_minutes = hours * 60 + minutes + seconds / 60
            
            if total_minutes >= 7:
                videos.append({
                    'video_id': video['id'],
                    'title': video['snippet']['title'],
                    'description': video['snippet']['description'],  # Added description
                    'thumbnail': video['snippet']['thumbnails']['high']['url'],
                    'duration': f"{hours}h {minutes}m {seconds}s" if hours else f"{minutes}m {seconds}s",
                })
        return videos
    except requests.exceptions.RequestException as e:
        print(f"Error fetching YouTube videos: {e}")
        return []


@login_required
def home(request):
    """
    Home view to handle the main page functionality.
    """
    if request.method == "POST":
        text = request.POST.get('content', '')
        keywords = extract_keywords(text)
        videos = fetch_youtube_videos(' '.join(keywords), api_key='AIzaSyBJLB6CtjTZX46dOjRgDcNWmcKaPTPa-8A')
        return render(request, 'education/home.html', {'videos': videos})
    return render(request, 'education/home.html')


# @login_required
# def quiz(request):
#     """
#     Quiz view to display questions and calculate the score.
#     """
#     questions = QuizQuestion.objects.all()
#     if request.method == "POST":
#         answers = request.POST
#         score = 0
#         for question in questions:
#             if answers.get(str(question.id)) == question.correct_option:
#                 score += 1
#         QuizResult.objects.create(user=request.user, score=score)
#         return render(request, 'education/results.html', {'score': score})
#     return render(request, 'education/quiz.html', {'questions': questions})


# @login_required
# def leaderboard(request):
#     """
#     Leaderboard view to display top quiz scores.
#     """
#     results = QuizResult.objects.order_by('-score', '-timestamp')[:10]
#     return render(request, 'education/leaderboard.html', {'results': results})


# def results(request):
#     """
#     Results view to display user scores.
#     """
#     return render(request, 'education/results.html')  # Adjust the template path if necessary


# landing page
# In your views.py
from django.shortcuts import render

def register(request):
    return render(request, 'register.html')

def login_view(request):
    return render(request, 'login.html')

def signin(request):
    return render(request, 'login.html')

def get_started(request):
    return render(request, 'register.html')



# Resources page

import wikipediaapi
from django.shortcuts import render

def input_topic(request):
    if request.method == "POST":
        topic = request.POST.get("topic", "").strip()
        if not topic:
            return render(request, 'education/input_topic.html', {"error": "Please enter a valid topic."})

        # Set up Wikipedia API with a custom User-Agent
        user_agent = "SmartEducationSystem/1.0 (Contact: your_email@example.com)"
        wiki_wiki = wikipediaapi.Wikipedia(language='en', user_agent=user_agent)

        # Fetch the page
        page = wiki_wiki.page(topic)

        if not page.exists():
            return render(request, 'education/input_topic.html', {
                "error": f"Sorry, no information found for '{topic}'. Please try a different topic."
            })

        # Render results
        return render(request, 'education/display_resources.html', {
            "topic": topic.title(),
            "summary": page.summary,
            "details": page.text[:5000],
            "url": page.fullurl,
        })

    return render(request, 'education/input_topic.html')
















# education/views.py
# from django.shortcuts import render, redirect
# from .forms import UserRegistrationForm
# from django.contrib.auth.models import User
# from django.contrib import messages



# from django.shortcuts import render, redirect
# from .forms import UserRegistrationForm

# def register(request):
#     if request.method == 'POST':
#         form = UserRegistrationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('login')  # Redirect to login after successful registration
#     else:
#         form = UserRegistrationForm()

#     return render(request, 'register.html', {'form': form})



import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import QuizResult, Category

# Get quiz questions from Open Trivia Database based on a category or custom topic
def get_quiz_questions(category, difficulty, num_questions=5):
    url = f"https://opentdb.com/api.php?amount={num_questions}&category={category}&difficulty={difficulty}&type=multiple"
    response = requests.get(url)
    data = response.json()
    return data['results']

# Quiz View
@login_required
def quiz(request):
    if request.method == 'POST':
        # Handle quiz submission (calculate score)
        score = 0
        total_questions = len(request.POST.getlist('question_ids'))

        for i in range(total_questions):
            selected_answer = request.POST.get(f"answer_{i}")
            correct_answer = request.POST.get(f"correct_answer_{i}")

            if selected_answer == correct_answer:
                score += 1
        
        # Save the result in the database
        QuizResult.objects.create(user=request.user, score=score)
        return redirect('quiz_result')

    # Handle the form to choose a topic or enter custom one
    categories = Category.objects.all()  # Get predefined categories from database
    custom_topic = request.POST.get('custom_topic', '')  # Get custom topic input

    if custom_topic:
        # You can use a custom search or similar logic to get questions based on the entered topic
        # For simplicity, let's assume you can fetch a category ID by topic name (but the API doesn’t directly support custom topics)
        category = 9  # Replace with the correct category ID for a custom topic
        difficulty = request.POST.get('difficulty', 'easy')
        quiz_questions = get_quiz_questions(category, difficulty)
        return render(request, 'quiz/quiz_page.html', {'quiz_questions': quiz_questions, 'topic': custom_topic})

    return render(request, 'quiz/select_quiz.html', {'categories': categories})

# Quiz Result View
@login_required
def quiz_result(request):
    # Fetch user's score from the database
    results = QuizResult.objects.filter(user=request.user).order_by('-score')
    return render(request, 'quiz/quiz_result.html', {'results': results})

# Leaderboard View
@login_required
def leaderboard(request):
    leaderboard_results = QuizResult.objects.all().order_by('-score')
    return render(request, 'quiz/leaderboard.html', {'leaderboard_results': leaderboard_results})


# education/views.py

from django.shortcuts import render
from .models import QuizResult

# Add the results view
def results(request):
    # Fetch all quiz results from the database, ordered by score (descending)
    quiz_results = QuizResult.objects.all().order_by('-score')

    context = {
        'quiz_results': quiz_results
    }

    return render(request, 'education/results.html', context)

