from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from fypapp.model_factories import UserFactory, AgencyFactory
from fypapp.models import AccessibilityIssue

class CreateIssueTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.agency = AgencyFactory()
        self.create_url = reverse('accessibilityissue-list')
        
    def test_create_issue(self):
        issue_data = {
            'title': 'New Test Issue',
            'description': 'This is a test issue',
            'location': 'Singapore Downtown',
            'latitude': '1.3521',
            'longitude': '103.8198',
            'priority': 3,
        }
        
        response = self.client.post(self.create_url, issue_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(AccessibilityIssue.objects.count(), 1)
        self.assertEqual(AccessibilityIssue.objects.first().title, 'New Test Issue')
        self.assertEqual(AccessibilityIssue.objects.first().reported_by, self.user)
        
    def test_create_issue_with_agency(self):
        issue_data = {
            'title': 'Agency Test Issue',
            'description': 'This issue should be assigned to an agency',
            'location': 'Singapore Downtown',
            'latitude': '1.3521',
            'longitude': '103.8198',
            'priority': 3,
            'agency': self.agency.id
        }
        
        response = self.client.post(self.create_url, issue_data, format='json')
        self.assertEqual(response.status_code, 201)
        
        # Get the created issue
        issue = AccessibilityIssue.objects.first()
        
        # Check it was assigned to the agency
        self.assertEqual(issue.status, 'assigned')
        self.assertEqual(issue.current_agency, self.agency)
        
        # Check that an assignment was created
        self.assertEqual(issue.assignments.count(), 1)
        self.assertEqual(issue.assignments.first().agency, self.agency)