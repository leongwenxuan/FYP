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
from .models import AccessibilityIssue, IssueComment, Agency, IssueAssignment, StatusUpdate
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
from .models import StaffProfile
from rest_framework.parsers import MultiPartParser
import openai
import os
import uuid
from .forms import StaffProfileForm

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        # Check if the user is an agency staff
        is_agency_staff = request.POST.get('is_agency_staff') == 'on'
        
        if form.is_valid():
            user = form.save()
            
            # If registering as agency staff, create a staff profile
            if is_agency_staff:
                agency_id = request.POST.get('agency')
                role = request.POST.get('role')
                employee_id = request.POST.get('employee_id')
                
                if agency_id and role and employee_id:
                    # Create staff profile
                    try:
                        agency = Agency.objects.get(id=agency_id)
                        StaffProfile.objects.create(
                            user=user,
                            agency=agency,
                            role=role,
                            employee_id=employee_id,
                            is_verified=True
                        )
                        messages.success(
                            request, 
                            f'Account created for {user.username}! Please wait for verification by your agency admin.'
                        )
                    except Exception as e:
                        # If there's an error creating the staff profile, delete the user and show error
                        user.delete()
                        messages.error(request, f'Error creating staff profile: {str(e)}')
                        return redirect('register')
                else:
                    # If agency staff fields are missing, delete the user and show error
                    user.delete()
                    messages.error(request, 'Please fill in all agency staff fields')
                    return redirect('register')
            else:
                messages.success(request, f'Account created for {user.username}! You can now log in.')
            
            return redirect('login')
    else:
        form = UserCreationForm()
        
    agencies = Agency.objects.all()

    return render(request, 'registration/register.html', {'form': form, 'agencies': agencies})

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
        'agencies': Agency.objects.all()
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
        # Get the agency ID from the request data
        agency_id = self.request.data.get('agency')
        
        # Save the issue with the current user as reporter
        issue = serializer.save(reported_by=self.request.user)
        
        # Assign to the selected agency if provided
        if agency_id:
            try:
                agency = Agency.objects.get(id=agency_id)
                
                # Create an assignment
                IssueAssignment.objects.create(
                    issue=issue,
                    agency=agency,
                    status='assigned'
                )
                
                # Update the issue status and current_agency
                issue.status = 'assigned'
                issue.current_agency = agency
                issue.save()
            except Agency.DoesNotExist:
                # Handle case where agency doesn't exist (optional)
                pass
        
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
        
@login_required
def agency_dashboard(request):
    # Check if user is agency staff
    try:
        staff_profile = request.user.staff_profile
    except:
        return redirect('home')
        
    # Get agency's assigned issues
    assigned_issues = IssueAssignment.objects.filter(agency=staff_profile.agency)
    
    # Dashboard statistics
    open_count = assigned_issues.filter(status='assigned').count()
    in_progress_count = assigned_issues.filter(status='in_progress').count()
    completed_count = assigned_issues.filter(status='completed').count()
    
    context = {
        'staff_profile': staff_profile,
        'assigned_issues': assigned_issues.order_by('-assigned_at')[:10],
        'open_count': open_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
    }
    
    return render(request, 'agency/dashboard.html', context)

@login_required
def agency_issue_list(request):
    try:
        staff_profile = request.user.staff_profile
    except:
        return redirect('home')
        
    # Get agency's assigned issues
    status_filter = request.GET.get('status', '')
    my_issues_only = request.GET.get('my_issues', '') == 'true'
    
    assigned_issues = IssueAssignment.objects.filter(agency=staff_profile.agency)
    
    # Filter by status if specified
    if status_filter:
        assigned_issues = assigned_issues.filter(status=status_filter)
        
    # Filter by assigned to current user if requested
    if my_issues_only:
        assigned_issues = assigned_issues.filter(assigned_to=staff_profile)
        
    context = {
        'staff_profile': staff_profile,
        'assigned_issues': assigned_issues.order_by('-assigned_at'),
        'status_filter': status_filter,
        'my_issues_only': my_issues_only,
    }
    
    return render(request, 'agency/issue_list.html', context)

@login_required
def update_issue_status(request, assignment_id):
    if request.method != 'POST':
        return redirect('agency_issue_list')
        
    try:
        staff_profile = request.user.staff_profile
        assignment = IssueAssignment.objects.get(id=assignment_id, agency=staff_profile.agency)
    except:
        return redirect('agency_issue_list')
        
    new_status = request.POST.get('status')
    note = request.POST.get('note', '')
    
    if new_status in dict(IssueAssignment.STATUS_CHOICES):
        # Update assignment status
        assignment.status = new_status
        assignment.save()
        
        # Create status update
        status_update = StatusUpdate(
            assignment=assignment,
            status=new_status,
            note=note,
            created_by=staff_profile
        )
        
        # Handle photo evidence if submitted
        if 'photo_evidence' in request.FILES:
            status_update.photo_evidence = request.FILES['photo_evidence']
            
        status_update.save()
        
        # Update the issue's status if needed
        issue = assignment.issue
        if new_status == 'completed':
            issue.status = 'resolved'
        elif new_status == 'in_progress':
            issue.status = 'in_progress'
        issue.save()
        
        messages.success(request, 'Issue status updated successfully!')
    
    return redirect('agency_issue_detail', assignment_id=assignment_id) 

def register_agency_staff(request):
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
        profile_form = StaffProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            messages.success(request, 'Account created! Please wait for verification by your agency admin.')
            return redirect('login')
    else:
        user_form = UserCreationForm()
        profile_form = StaffProfileForm()
        
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'agencies': Agency.objects.all()
    }
    
    return render(request, 'registration/register_staff.html', context) 

@login_required
def agency_issue_detail(request, assignment_id):
    try:
        staff_profile = request.user.staff_profile
        assignment = get_object_or_404(IssueAssignment, id=assignment_id, agency=staff_profile.agency)
    except:
        return redirect('agency_issue_list')
        
    # Get status updates for this assignment
    status_updates = StatusUpdate.objects.filter(assignment=assignment).order_by('-created_at')
    
    # Get all staff members for assignment dropdown (for admins)
    agency_staff = []
    if staff_profile.role == 'admin':
        agency_staff = StaffProfile.objects.filter(agency=staff_profile.agency)
    
    context = {
        'staff_profile': staff_profile,
        'assignment': assignment,
        'issue': assignment.issue,
        'status_updates': status_updates,
        'agency_staff': agency_staff,
        'mapbox_access_token': settings.MAPBOX_ACCESS_TOKEN,
    }
    
    return render(request, 'agency/issue_detail.html', context)


@login_required
def assign_issue(request, assignment_id):
    try:
        staff_profile = request.user.staff_profile
        # Verify the user is an admin
        if staff_profile.role != 'admin':
            messages.error(request, 'Only agency admins can assign issues.')
            return redirect('agency_issue_detail', assignment_id=assignment_id)
            
        assignment = get_object_or_404(IssueAssignment, id=assignment_id, agency=staff_profile.agency)
    except:
        return redirect('agency_issue_list')
        
    if request.method == 'POST':
        staff_id = request.POST.get('staff_id')
        if staff_id:
            try:
                assigned_staff = StaffProfile.objects.get(id=staff_id, agency=staff_profile.agency)
                assignment.assigned_to = assigned_staff
                assignment.save()
                
                # Create status update
                StatusUpdate.objects.create(
                    assignment=assignment,
                    status=assignment.status,
                    note=f"Issue assigned to {assigned_staff.user.username}",
                    created_by=staff_profile
                )
                
                messages.success(request, f'Issue assigned to {assigned_staff.user.username}')
            except StaffProfile.DoesNotExist:
                messages.error(request, 'Invalid staff member selected')
                
    return redirect('agency_issue_detail', assignment_id=assignment_id)