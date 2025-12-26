from posts.models import LostPost, FoundPost, SurrenderCustodyPet, PostImage
from success_story.models import SuccessStoryImage, SuccessStory
from django.core.management.base import BaseCommand
from random import choice
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


def model_circuit():
    i = 0
    models = [LostPost, FoundPost, SurrenderCustodyPet,]
    while True:
        yield models[i]
        i = (i+1) % len(models)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with open("fixtures/dev_medium.json", 'r') as file:
            model_samples = json.load(file)
        for ms in model_samples:
            sample_model = ms["model"]
            post = ...
            if sample_model in [
                'posts.postimage',
                'posts.surrendercustodypet',
            ]:
                for _ in range(3):
                    post_model = next(model_circuit())
                    try:
                        post = post_model.objects.get(pk=ms['pk'])
                    except post_model.DoesNotExist:
                        continue
                    else:
                        break
                else:
                    continue

                try:
                    pet_type = post.pet_type
                except Exception as err:
                    raise err
                else:
                    PostImage.objects.create(post=post, image_url=PicLinkManager.get_pic_link(
                        pet_type), uploaded_by=post.user)

            elif sample_model == 'success_story.successstoryimage':
                post = SuccessStory.objects.get(pk=ms['pk'])
                SuccessStoryImage.objects.create(
                    uploaded_by=post.user,
                    image_url=PicLinkManager.get_pic_link(
                        choice(['dog', 'cat'])))
            else:
                continue
            print(f'image added to the {sample_model}...')
