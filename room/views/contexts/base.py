from room.models import Person, Room


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


class Person2RoomContext:
    @staticmethod
    def load(person: Person, room: Room):
        """
        :param person: Person
        :param room: Room
        :return: dict
        """
        data = dict()
        data['person'] = person
        data['is_person'] = True
        has_person = room.has_person(person)
        data['room_has_person'] = has_person
        data['room_can_join'] = room.can_join(person)
        if has_person:
            data['is_leader'] = room.is_leader(person)

