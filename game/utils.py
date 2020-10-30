from __future__ import annotations
import math


def is_outside_box(x: float, y: float, width: float, height: float) -> bool:
    return x < 0 or x > width or y < 0 or y > height


def circles_collide(center1: Vec, center2: Vec, r1: float, r2: float) -> bool:
    return Vec.distance(center1, center2) < r1 + r2


def point_in_circle(p: Vec, c: Vec, r: float) -> bool:
    return Vec.distance(p, c) < r


class Vec:
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return f'{self.x}, {self.y}'

    def __sub__(self, other: Vec) -> Vec:
        return Vec(self.x - other.x, self.y - other.y)

    def __add__(self, other: Vec) -> Vec:
        return Vec(self.x + other.x, self.y + other.y)

    def __mul__(self, other: float) -> Vec:
        return Vec(self.x * other, self.y * other)

    def __truediv__(self, other: float) -> Vec:
        return Vec(self.x / other, self.y / other)

    def __rmul__(self, other) -> Vec:
        return self.__mul__(other)

    def __abs__(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other: Vec):
        return self.x == other.x and self.y == other.y

    def length(self) -> float:
        return math.sqrt(self.x**2 + self.y**2)

    @staticmethod
    def unit(v: Vec) -> Vec:
        l = v.length()
        if l == 0:
            return Vec(0.0, 0.0)
        else:
            return Vec(v.x/l, v.y/l)

    @staticmethod
    def distance(v1: Vec, v2: Vec) -> float:
        return math.sqrt((v1.x - v2.x)**2 + (v1.y - v2.y)**2)

    @staticmethod
    def rotate(v: Vec, angle: float):
        return Vec(
            v.x * math.cos(angle) - v.y * math.sin(angle),
            v.x * math.sin(angle) + v.y * math.cos(angle)
        )

    def is_zero(self) -> bool:
        return self.x == 0.0 and self.y == 0.0
