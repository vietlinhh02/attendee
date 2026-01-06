# Generated manually on 2026-01-06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0069_remove_botevent_valid_event_type_event_sub_type_combinations_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participantevent',
            name='event_type',
            field=models.IntegerField(choices=[
                (1, 'Join'), 
                (2, 'Leave'), 
                (3, 'Speaking Start'), 
                (4, 'Speaking Stop'), 
                (5, 'Update'),
                (6, 'Microphone On'),
                (7, 'Microphone Off'),
                (8, 'Camera On'),
                (9, 'Camera Off'),
            ]),
        ),
        migrations.AlterField(
            model_name='webhookdeliveryattempt',
            name='webhook_trigger_type',
            field=models.IntegerField(choices=[
                (1, 'Bot State Change'), 
                (2, 'Transcript Update'), 
                (3, 'Chat Messages Update'), 
                (4, 'Participant Join/Leave'), 
                (5, 'Calendar Events Update'), 
                (6, 'Calendar State Change'), 
                (7, 'Async Transcription State Change'), 
                (8, 'Zoom OAuth Connection State Change'), 
                (9, 'Bot Logs Update'),
                (10, 'All Participant Events'),
            ]),
        ),
    ]
