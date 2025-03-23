import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory
from .models import AccessibilityIssue, Agency, IssueComment, StaffProfile, IssueAssignment

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password123')

class AgencyFactory(DjangoModelFactory):
    class Meta:
        model = Agency
    
    name = 'Government'
    description = 'Test agency'
    jurisdiction = 'Singapore'
    contact_email = 'test@agency.gov'
    contact_phone = '12345678'

class AccessibilityIssueFactory(DjangoModelFactory):
    class Meta:
        model = AccessibilityIssue
    
    title = factory.Sequence(lambda n: f'Test Issue {n}')
    description = 'Test description'
    location = 'Test Location'
    latitude = 1.3521
    longitude = 103.8198
    reported_by = factory.SubFactory(UserFactory)
    priority = 2
    status = 'open'

class IssueCommentFactory(DjangoModelFactory):
    class Meta:
        model = IssueComment
    
    issue = factory.SubFactory(AccessibilityIssueFactory)
    user = factory.SubFactory(UserFactory)
    content = 'Test comment'