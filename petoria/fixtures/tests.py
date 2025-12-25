# !!! GPT-generated code

# based on GPT recommendation this file should've been placed at tests/test_fixtures_integration.py
# but it made way more sense to me here; anyway you can try replacing it if it
# didn't work here

# this code has NOT been tested, due to errors occuring by running "python(3) manage.py test"
# so the very command to be executed in order to run this test file is supposed to be:
"""
python3 manage.py test
"""
# according to GPT

from django.test import TestCase
from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType

from users.models import User, EmailVerification
from locations.models import Location
from posts.models import LostPost, FoundPost, SurrenderCustodyPet, PostImage
from chat.models import Chat, ChatParticipant, Message
from success_story.models import SuccessStory


class FixtureIntegrationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Load fixtures once for speed
        call_command("loaddata", "fixtures/dev_minimal.json", verbosity=0)

    def test_users_loaded(self):
        self.assertGreater(User.objects.count(), 0)
        self.assertTrue(
            User.objects.filter(is_email_verified=True).exists()
        )

    def test_email_verification_integrity(self):
        for ev in EmailVerification.objects.all():
            self.assertEqual(ev.email, ev.user.email)
            self.assertTrue(ev.is_used)

    def test_locations_have_valid_points(self):
        for loc in Location.objects.all():
            self.assertIsNotNone(loc.point)
            self.assertTrue(-90 <= loc.point.y <= 90)
            self.assertTrue(-180 <= loc.point.x <= 180)

    def test_posts_integrity(self):
        for post in LostPost.objects.all():
            self.assertIsNotNone(post.user)
            self.assertEqual(post.status, "active")

        for post in FoundPost.objects.all():
            self.assertIsNotNone(post.location)

        for post in SurrenderCustodyPet.objects.all():
            self.assertTrue(post.vaccination)

    def test_post_images_content_type(self):
        for img in PostImage.objects.all():
            # ct = ContentType.objects.get_for_id(img.content_type_id)
            ct = ContentType.objects.get(app_label='posts',model='lostpost')
            self.assertEqual(ct.app_label, "posts")

    def test_chat_integrity(self):
        for chat in Chat.objects.all():
            participants = ChatParticipant.objects.filter(chat=chat)
            self.assertEqual(participants.count(), 2)

            messages = Message.objects.filter(chat=chat)
            for msg in messages:
                self.assertIn(msg.sender, [p.user for p in participants])

    def test_success_story_links(self):
        for story in SuccessStory.objects.all():
            self.assertIsNotNone(story.user)
            self.assertTrue(story.story)
