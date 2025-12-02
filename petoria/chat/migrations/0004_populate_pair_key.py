from django.db import migrations


def populate_pair_keys(apps, schema_editor):
    Chat = apps.get_model('chat', 'Chat')
    ChatParticipant = apps.get_model('chat', 'ChatParticipant')

    for chat in Chat.objects.filter(pair_key__isnull=True):
        user_ids = list(
            ChatParticipant.objects.filter(chat_id=chat.id)
            .values_list('user_id', flat=True)
        )

        if len(user_ids) < 2:
            continue

        first, second = sorted([str(user_ids[0]), str(user_ids[1])])
        pair_key = f"{first}:{second}"

        # skip if another chat already has this pair_key
        if Chat.objects.filter(pair_key=pair_key).exists():
            continue

        Chat.objects.filter(id=chat.id).update(pair_key=pair_key)


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_chat_pair_key'),
    ]

    operations = [
        migrations.RunPython(populate_pair_keys, migrations.RunPython.noop),
    ]

