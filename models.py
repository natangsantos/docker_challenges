from CTFd.models import Challenges
from CTFd.plugins.challenges import BaseChallenge
from CTFd.utils.decorators.visibility import check_challenge_visibility
from flask import render_template

class DockerChallenge(Challenges, BaseChallenge):
    __mapper_args__ = {
        'polymorphic_identity': 'docker'
    }

    @staticmethod
    def create(request):
        return BaseChallenge.create(request)

    @staticmethod
    def read(challenge):
        return BaseChallenge.read(challenge)

    @staticmethod
    def update(challenge, request):
        return BaseChallenge.update(challenge, request)

    @staticmethod
    def delete(challenge):
        return BaseChallenge.delete(challenge)

    @staticmethod
    def view(challenge):
        return render_template("challenges/docker.html", challenge=challenge)

    @staticmethod
    def attempt(challenge, request):
        return BaseChallenge.attempt(challenge, request)

    @staticmethod
    def solve(challenge, request):
        return BaseChallenge.solve(challenge, request)
