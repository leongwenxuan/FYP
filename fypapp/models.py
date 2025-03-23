from django.db import models
from django.contrib.auth.models import User

class Agency(models.Model):
    AGENCY_CHOICES = [
        ('Government', 'Government'),
    ]
    
    name = models.CharField(max_length=100, choices=AGENCY_CHOICES)
    description = models.TextField()
    logo = models.ImageField(upload_to='agency_logos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    jurisdiction = models.CharField(max_length=100)  # Area or type of issues they handle
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name

class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Agency Admin')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='staff')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    employee_id = models.CharField(max_length=50, unique=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()} at {self.agency.name})"
    
    
class AccessibilityIssue(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical')
    ]
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned to Agency'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ]
    

    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=1)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='open')
    current_agency = models.ForeignKey(Agency, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_issues') 
    upvotes = models.ManyToManyField(User, related_name='upvoted_issues', blank=True)
    image = models.ImageField(upload_to='issue_images/', null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def upvote_count(self):
        return self.upvotes.count()
    
class IssueAssignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ]
    
    issue = models.ForeignKey(AccessibilityIssue, on_delete=models.CASCADE, related_name='assignments')
    agency = models.ForeignKey(Agency, on_delete=models.CASCADE, related_name='assigned_issues')
    assigned_to = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    estimated_completion = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"Issue #{self.issue.id} assigned to {self.agency.name}"

class StatusUpdate(models.Model):
    assignment = models.ForeignKey(IssueAssignment, on_delete=models.CASCADE, related_name='updates')
    status = models.CharField(max_length=20, choices=IssueAssignment.STATUS_CHOICES)
    note = models.TextField()
    created_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    photo_evidence = models.ImageField(upload_to='status_updates/', null=True, blank=True)
    
    def __str__(self):
        return f"Update on {self.assignment.issue.title} - {self.status}"

class IssueComment(models.Model):
    issue = models.ForeignKey(AccessibilityIssue, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.issue.title}'