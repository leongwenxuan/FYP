from fypapp.views import transcribe_audio

urlpatterns = [
    # ... existing urls ...
    path('api/transcribe-audio/', transcribe_audio, name='transcribe-audio'),
    # ... existing urls ...
] 