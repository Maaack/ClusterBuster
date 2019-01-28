from room.models import Person, Group, Room


class RoomContext:
    @staticmethod
    def load(room: Room) -> dict:
        """
        :param room: Room
        :return: dict
        """
        data = dict()
        data['room'] = room
        return data


class PersonContext:
    @staticmethod
    def load(person: Person) -> dict:
        """
        :param person: Person
        :return: dict
        """
        data = dict()
        data['person'] = person
        data['is_person'] = True
        return data


class GroupContext:
    @staticmethod
    def load(group: Group) -> dict:
        """
        :param group: Group
        :return: dict
        """
        data = dict()
        data['group'] = group
        return data


class Person2RoomContext:
    @staticmethod
    def load(person: Person, room: Room):
        """
        :param person: Person
        :param room: Room
        :return: dict
        """
        data = dict()
        has_person = room.has_person(person)
        data['has_person'] = has_person
        data['can_join'] = room.can_join(person)
        if has_person:
            data['is_leader'] = room.is_leader(person)
        return data


class Person2GroupContext:
    @staticmethod
    def load(person: Person, group: Group):
        """
        :param person: Person
        :param group: Group
        :return: dict
        """
        data = dict()
        has_person = group.has_person(person)
        data['has_person'] = group.has_person(person)
        data['can_join'] = group.can_join(person)
        if has_person:
            data['is_leader'] = group.is_leader(person)
        return data
