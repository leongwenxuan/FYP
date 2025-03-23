from django.contrib import admin
from .models import AccessibilityIssue, IssueComment, Agency, StaffProfile, IssueAssignment, StatusUpdate

@admin.register(AccessibilityIssue)
class AccessibilityIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'priority', 'reported_by', 'created_at', 'upvote_count')
    list_filter = ('priority', 'created_at')
    search_fields = ('title', 'description', 'location')

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'jurisdiction', 'contact_email', 'created_at')
    search_fields = ('name', 'description', 'jurisdiction')

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'agency', 'role', 'employee_id', 'is_verified')
    list_filter = ('agency', 'role', 'is_verified')
    search_fields = ('user__username', 'employee_id')

@admin.register(IssueAssignment)
class IssueAssignmentAdmin(admin.ModelAdmin):
    list_display = ('issue', 'agency', 'assigned_to', 'status', 'assigned_at')
    list_filter = ('status', 'agency')
    search_fields = ('issue__title', 'agency__name')
    
@admin.register(IssueComment)
class IssueCommentAdmin(admin.ModelAdmin):
    list_display = ('issue', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment', 'user__username')

@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('note', 'created_by__user__username')