from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_message_reply_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='pair_key',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]

