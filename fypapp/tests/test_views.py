from django.test import TestCase, Client
from django.urls import reverse
from fypapp.model_factories import AccessibilityIssueFactory, UserFactory, AgencyFactory
from fypapp.models import AccessibilityIssue

class IssueViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.issue = AccessibilityIssueFactory()
        self.user = UserFactory()
        self.client.force_login(self.user)
        
    def test_issue_list_view(self):
        response = self.client.get(reverse('issue_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'issue_list.html')
    
    def test_issue_detail_view(self):
        response = self.client.get(reverse('issue_detail', kwargs={'pk': self.issue.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'issue_detail.html')
        self.assertContains(response, self.issue.title)
    
    def test_report_issue_view_auth(self):
        # Log out first
        self.client.logout()
        
        # Should redirect to login when not authenticated
        response = self.client.get(reverse('report_issue'))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Login and try again
        self.client.force_login(self.user)
        response = self.client.get(reverse('report_issue'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'report_issue.html')