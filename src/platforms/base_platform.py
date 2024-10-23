from abc import ABC, abstractmethod

class BasePlatform(ABC):
    @abstractmethod
    def login(self):
        pass

    @abstractmethod
    def send_post(self, content):
        pass

    @abstractmethod
    def get_post(self, post_id):
        pass
