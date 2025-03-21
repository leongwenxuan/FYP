from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, parser_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import AccessibilityIssue, IssueComment
from .serializers import AccessibilityIssueSerializer, IssueCommentSerializer
from django.db.models import F
from math import cos, radians
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import filters
import django_filters.rest_framework
from django.db.models import Q
from django.db import models
from rest_framework.parsers import MultiPartParser
import openai
import os
import uuid

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def home(request):
    allIssues = AccessibilityIssue.objects.all()
    context = {
        'mapbox_access_token': settings.MAPBOX_ACCESS_TOKEN,
        'allIssues': allIssues
    }
    return render(request, 'home.html', context)

@login_required
def report_issue(request):
    context = {
        'mapbox_access_token': settings.MAPBOX_ACCESS_TOKEN,
    }
    return render(request, 'report_issue.html', context)

def issue_list(request):
    context = {
        'mapbox_access_token': settings.MAPBOX_ACCESS_TOKEN
    }
    return render(request, 'issue_list.html', context)

def profile(request):
    reported_issues = AccessibilityIssue.objects.filter(reported_by=request.user)
    upvoted_issues = AccessibilityIssue.objects.filter(upvotes=request.user)    
    return render(request, 'profile.html', {'reported_issues': reported_issues, 'upvoted_issues': upvoted_issues})

@login_required
def routermap(request):
    issues = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }
    
    all_issues = AccessibilityIssue.objects.all()
    for issue in all_issues:
        issue_data = {
            'id': issue.id,
            'coords': [float(issue.longitude), float(issue.latitude)],
            'title': issue.title,
            'description': issue.description
        }
        
        if issue.priority == 4:  # Critical
            issues['critical'].append(issue_data)
        elif issue.priority == 3:  # High
            issues['high'].append(issue_data)
        elif issue.priority == 2:  # Medium
            issues['medium'].append(issue_data)
        elif issue.priority == 1:  # Low
            issues['low'].append(issue_data)
    
    context = {
        'mapbox_access_token': settings.MAPBOX_ACCESS_TOKEN,
        'issues': issues
    }
    
    return render(request, 'routermap.html', context)

def issue_detail(request, pk):
    issue = get_object_or_404(AccessibilityIssue, pk=pk)
    has_upvoted = False
    if request.user.is_authenticated:
        has_upvoted = issue.upvotes.filter(id=request.user.id).exists()
    
    context = {
        'issue': issue,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        'has_upvoted': has_upvoted
    }
    return render(request, 'issue_detail.html', context)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

@api_view(['POST'])
@parser_classes([MultiPartParser])
def transcribe_audio(request):
    if 'audio' not in request.FILES:
        return Response({'success': False, 'error': 'No audio file provided'}, status=400)

    audio_file = request.FILES['audio']

    try:
        # Create a unique filename in the media directory
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}.webm")

        # Save the file
        with open(temp_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)

        # Process with OpenAI API
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # First, transcribe the audio
        with open(temp_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

        # Now, use GPT to extract structured data
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Extract the following information from the user's description of an accessibility issue: title, description, location, and priority (1=Low, 2=Medium, 3=High, 4=Critical). Return as JSON."},
                {"role": "user", "content": transcript.text}
            ]
        )

        # Parse the structured data
        import json
        try:
            structured_data = json.loads(completion.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            structured_data = {
                "description": transcript.text
            }

        # Clean up the temp file
        os.unlink(temp_path)

        return Response({
            'success': True,
            'transcript': transcript.text,
            'result': structured_data
        })

    except Exception as e:
        import traceback
        print(f"Error in transcribe_audio: {str(e)}")
        print(traceback.format_exc())
        return Response({'success': False, 'error': str(e)}, status=500)

class AccessibilityIssueViewSet(viewsets.ModelViewSet):
    queryset = AccessibilityIssue.objects.all()
    serializer_class = AccessibilityIssueSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = AccessibilityIssue.objects.all()
        
        # Filter by priority
        priority_in = self.request.query_params.get('priority__in')
        if priority_in:
            priorities = priority_in.split(',')
            queryset = queryset.filter(priority__in=priorities)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
            
        # Search functionality - using Q correctly
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(location__icontains=search)
            )
            
        # Sorting
        sort = self.request.query_params.get('sort')
        if sort:
            if sort == '-upvote_count':
                # Special handling for upvote count sorting
                queryset = queryset.annotate(votes=Count('upvotes')).order_by('-votes')
            else:
                queryset = queryset.order_by(sort)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)
        
    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def upvote(self, request, pk=None):
        try:
            issue = self.get_object()
            if not issue:
                return Response({'error': 'Issue not found'}, status=status.HTTP_404_NOT_FOUND)

            if issue.upvotes.filter(id=request.user.id).exists():
                issue.upvotes.remove(request.user)
                message = 'upvote removed'
            else:
                issue.upvotes.add(request.user)
                message = 'upvoted'
            
            serializer = self.get_serializer(issue, context={'request': request})
            return Response({
                'status': message,
                'upvote_count': issue.upvote_count,
                'has_upvoted': issue.upvotes.filter(id=request.user.id).exists()
            })
        except Exception as e:
            return Response({
                'error': str(e),
                'type': type(e).__name__
            }, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['GET'])
    def nearby(self, request):
        user_lat = float(request.query_params.get('latitude', 0))
        user_lng = float(request.query_params.get('longitude', 0))
        radius = float(request.query_params.get('radius', 5))  # radius in kilometers

        # Approximate distance calculation using latitude/longitude
        lat_range = radius / 111.0  # 1 degree latitude = ~111km
        lng_range = radius / (111.0 * cos(radians(user_lat)))

        nearby_issues = AccessibilityIssue.objects.filter(
            latitude__range=(user_lat - lat_range, user_lat + lat_range),
            longitude__range=(user_lng - lng_range, user_lng + lng_range)
        )

        serializer = self.get_serializer(nearby_issues, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def top_priority(self, request):
        top_issues = AccessibilityIssue.objects.annotate(
            vote_count=Count('upvotes')
        ).order_by('-priority', '-vote_count')
        serializer = self.get_serializer(top_issues, many=True)
        return Response(serializer.data)
    

class IssueCommentViewSet(viewsets.ModelViewSet):
    queryset = IssueComment.objects.all()
    serializer_class = IssueCommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        issue = get_object_or_404(AccessibilityIssue, pk=self.kwargs['issue_pk'])
        serializer.save(user=self.request.user, issue=issue)