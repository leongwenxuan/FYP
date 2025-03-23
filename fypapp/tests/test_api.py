from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from fypapp.models import AccessibilityIssue, IssueComment
from fypapp.model_factories import AccessibilityIssueFactory, UserFactory, IssueCommentFactory

class IssueAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.issue = AccessibilityIssueFactory()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.issue_url = reverse('accessibilityissue-detail', kwargs={'pk': self.issue.pk})
        self.issuelist_url = reverse('accessibilityissue-list')
        self.upvote_url = reverse('accessibilityissue-upvote', kwargs={'pk': self.issue.pk})
        self.nearby_url = reverse('accessibilityissue-nearby')
        
    def test_issue_list(self):
        response = self.client.get(self.issuelist_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 1)
    
    def test_issue_detail(self):
        response = self.client.get(self.issue_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.issue.pk)
    
    def test_upvote_issue(self):
        # Initial upvote
        response = self.client.post(self.upvote_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['upvote_count'], 1)
        self.assertTrue(response.json()['has_upvoted'])
        
        # Upvote toggle (remove)
        response = self.client.post(self.upvote_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['upvote_count'], 0)
        self.assertFalse(response.json()['has_upvoted'])
    
    def test_nearby_issues(self):
        # Create an issue near Singapore
        nearby = AccessibilityIssueFactory(
            latitude=1.3522,  # Very close to the query point
            longitude=103.8199
        )
        
        # Create an issue far away
        far_away = AccessibilityIssueFactory(
            latitude=40.7128,  # New York
            longitude=-74.0060
        )
        
        response = self.client.get(
            f"{self.nearby_url}?latitude=1.3521&longitude=103.8198&radius=1"
        )
        self.assertEqual(response.status_code, 200)
        
        # IDs of issues in the response
        issue_ids = [item['id'] for item in response.json()]
        
        # The nearby issue should be in results
        self.assertIn(nearby.pk, issue_ids)
        # The far away issue should not be in results
        self.assertNotIn(far_away.pk, issue_ids)