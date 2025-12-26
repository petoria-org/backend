from posts.models import LostPost, FoundPost, PostImage
from django.core.management.base import BaseCommand
import json


class PicLinkManager:
    animals = ['dog', 'cat']
    # load pictures
    links = dict()
    for animal in animals:
        links[animal] = []
        with open(f'fixtures/{animal}_pics_links.txt') as file:
            for line in file.readlines():
                links[animal].append(line[:-1])

    _index_tracker = {animal: 0 for animal in animals}

    @classmethod
    def get_pic_link(cls, animal: str):
        cls._index_tracker[animal] += 1
        return cls.links[animal][cls._index_tracker[animal]]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open("fixtures/dev_medium.json", 'r') as file:
            model_samples = json.load(file)
        for ms in model_samples:
            img_model = ms["model"]
            to_handle = []
            if img_model in ['posts.postimage']:
                for post_model in [LostPost, FoundPost]:
                    try:
                        post = post_model.objects.get(pk=ms['pk'])
                    except post_model.DoesNotExist:
                        pass
                    else:
                        to_handle.append(post)
                for post in to_handle:
                    pet_type = post.pet_type
                    PostImage.objects.create(
                        post=post,
                        image_url=PicLinkManager.get_pic_link(pet_type),
                        uploaded_by=post.user
                    )
