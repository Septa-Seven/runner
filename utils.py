from __future__ import annotations
import math


def is_outside_box(x, y, width, height):
    return x < 0 or x > width or y < 0 or y > height


def line_and_circle_collide(start: Vec, end: Vec, center: Vec, r: float):
    if start.x == end.x and start.y == end.y:
        return False

    start = start - center
    end = end - center
    l1 = abs(start)
    l2 = abs(end)
    if l1 < r or l2 < r:
        return True

    p1 = start.x * (end.x - start.x) + start.y * (end.y - start.y)
    p2 = end.x * (end.x - start.x) + end.y * (end.y - start.y)

    return (p1 >= 0 >= p2 or p1 <= 0 <= p2) and abs((end.x * start.y - start.x * end.y) / Vec.distance(start, end)) <= r


def circles_collide(center1: Vec, center2: Vec, r1, r2):
    return Vec.distance(center1, center2) < r1 + r2


def point_in_circle(p: Vec, c: Vec, r: float):
    return Vec.distance(p, c) < r


class Vec:
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self):
        return f'{self.x}, {self.y}'

    def __sub__(self, other: Vec):
        return Vec(self.x - other.x, self.y - other.y)

    def __add__(self, other: Vec):
        return Vec(self.x + other.x, self.y + other.y)

    def __mul__(self, other: float):
        return Vec(self.x * other, self.y * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __abs__(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    @staticmethod
    def unit(v):
        m = max(abs(v.x), abs(v.y))
        if m == 0:
            return Vec(0.0, 0.0)
        else:
            return Vec(v.x/m, v.y/m)

    @staticmethod
    def reflect(direction, normal):
        return direction - 2.0 * normal * (Vec.scalar(direction, normal) / Vec.scalar(normal, normal))

    @staticmethod
    def distance(v1, v2):
        return math.sqrt((v1.x - v2.x)**2 + (v1.y - v2.y)**2)

    @staticmethod
    def scalar(v1, v2):
        return v1.x * v2.x + v1.y * v2.y

    def is_zero(self):
        return self.x == 0.0 and self.y == 0.0
