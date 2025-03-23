from django.core.management.base import BaseCommand
from fypapp.models import Agency

class Command(BaseCommand):
    help = 'Adds predefined agencies to the database'

    def handle(self, *args, **kwargs):
        # Define the agencies to add
        agencies = [
            {
                'name': 'Government',
                'description': 'Singapore government agency responsible for accessibility infrastructure',
                'jurisdiction': 'Singapore',
                'contact_email': 'contact@gov.sg',
                'contact_phone': '+65 1234 5678'
            },
            # You can add more agencies here if you expand your AGENCY_CHOICES in the future
        ]

        # Counter for added and existing agencies
        added_count = 0
        existing_count = 0

        # Add each agency
        for agency_data in agencies:
            # Check if the agency already exists
            if not Agency.objects.filter(name=agency_data['name']).exists():
                Agency.objects.create(**agency_data)
                self.stdout.write(self.style.SUCCESS(f'Successfully added {agency_data["name"]} agency'))
                added_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'{agency_data["name"]} agency already exists'))
                existing_count += 1

        # Summary
        self.stdout.write(self.style.SUCCESS(f'Added {added_count} new agencies'))
        if existing_count > 0:
            self.stdout.write(self.style.WARNING(f'{existing_count} agencies already existed'))