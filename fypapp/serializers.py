from rest_framework import serializers
from .models import AccessibilityIssue, IssueComment
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class IssueCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = IssueComment
        fields = ['id', 'user', 'content', 'created_at']

class AccessibilityIssueSerializer(serializers.ModelSerializer):
    reported_by = UserSerializer(read_only=True)
    upvote_count = serializers.IntegerField(read_only=True)
    comments = IssueCommentSerializer(many=True, read_only=True)
    has_upvoted = serializers.SerializerMethodField()

    class Meta:
        model = AccessibilityIssue
        fields = ['id', 'title', 'description', 'location', 'latitude', 'longitude',
                 'reported_by', 'created_at', 'updated_at', 'priority', 'status',
                 'upvote_count', 'image', 'comments', 'has_upvoted']

    def get_has_upvoted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.upvotes.filter(id=request.user.id).exists()
        return False