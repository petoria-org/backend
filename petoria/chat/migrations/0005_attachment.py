from django.db import migrations, models
import chat.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('chat', '0004_populate_pair_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=chat.models.attachment_upload_to)),
                ('content_type', models.CharField(max_length=100)),
                ('size', models.PositiveIntegerField()),
                ('type', models.CharField(choices=[('image', 'Image'), ('video', 'Video'), ('other', 'Other')], default='other', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, related_name='attachments', to='chat.message')),
                ('uploaded_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='uploaded_attachments', to='users.user')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

