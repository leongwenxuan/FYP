from django.contrib import admin
from .models import AccessibilityIssue, IssueComment

@admin.register(AccessibilityIssue)
class AccessibilityIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'priority', 'reported_by', 'created_at', 'upvote_count')
    list_filter = ('priority', 'created_at')
    search_fields = ('title', 'description', 'location')

@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ('issue', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username') 