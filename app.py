"""
Copyright (c) 2018-2026 Mat Booth.

This file is part of the Settlers of EMF app for the Tildagon
(see https://github.com/mbooth101/emf-settlers).

License: MIT
"""

import math
import os
import random

import app


# Kinds of resource
SHEEP = {'kind':0, 'col': (0xd4, 0xe1, 0x57)}
WHEAT = {'kind':1, 'col': (0xff, 0xc1, 0x07)}
WOOD = {'kind':2, 'col': (0x99, 0x33, 0x00)}
BRICK = {'kind':3, 'col': (0xff, 0x00, 0x00)}
ORE = {'kind':4, 'col': (0x75, 0x75, 0x75)}
DESERT = {'kind':5, 'col': (0xff, 0xee, 0x55)}  # Not really a resource
RESOURCE_KINDS = [ SHEEP, WHEAT, WOOD, BRICK, ORE ]


class Hex:
    """Hexes are the games tiles. They have a resource kind, correspond to the value
    of a roll of two D6 and may or may not contain the robber."""

    # Screen coords are x,y values that locate pixels on the physical display:
    #
    #       -120
    #         ↓
    # -120 →  0  → 120
    #         ↓
    #        120
    #
    # Hex coords are x,y,z values that locate the relative positions of hexagons:
    #
    #          0,1,-1
    # -1,1,0 ↖  ↑    ↗ 1,0,-1
    #          0,0,0
    # -1,0,1 ↙  ↓    ↘ 1,-1,0
    #          0,-1,1
    #
    # Converting between the two systems can be done by multiplying the x and y
    # coordinates against a matrix. When converting to hex coords, the z value
    # can be computed from the new x and y values because x + y + z must always
    # equal zero.
    #
    # This is the matrix used to convert from hex coords to screen coords
    matrix = [3.0 * 0.5, 0.0, math.sqrt(3.0) * 0.5, math.sqrt(3.0)]

    # Size in pixels of the hex, from the centre point to each corner
    size = 22

    # Hex coord translations for how to get to the neighbouring hexes
    directions = {
        0: [-1, 1, 0],  # South West
        1: [0, 1, -1],  # South
        2: [1, 0, -1],  # South East
        3: [1, -1, 0],  # North East
        4: [0, -1, 1],  # North
        5: [-1, 0, 1],  # North West
        }

    def __init__(self, coords, resource, number, robber):
        """Create a new hex at the given hex coordinates, of the given kind of resource"""
        # Validate coords
        assert len(coords) == 3, 'Invalid number of hexagon coordinates'
        assert coords[0] + coords[1] + coords[2] == 0, 'Invalid hexagon coordinate values'
        self.coords = coords

        # The kind of resource hosted by this hex
        self.resource = resource

        # The dice roll required to win this resource
        self.number = number

        # Whether this hex contains the robber
        self.robber = robber

        # Whether this hex should be highlighted
        self.highlight = False

        # Compute the screen coordinates of the centre of the hex
        x = self.coords[0]
        y = self.coords[1]
        self.centre = [
            (Hex.matrix[0] * x + Hex.matrix[1] * y) * Hex.size,
            (Hex.matrix[2] * x + Hex.matrix[3] * y) * Hex.size,
        ]

        # Generate the list of screen coordinates for each of the corners of the hex
        self.nodes = []
        for i in range(0, 6):
            angle = 2.0 * math.pi * (0 - i) / 6
            offset = [Hex.size * math.cos(angle), Hex.size * math.sin(angle)]
            self.nodes.append([int(self.centre[0] + offset[0]), int(self.centre[1] + offset[1])])

        # Generate the list of pairs of screen coordinates for each of the sides of the hex
        self.edges = []
        for i in range(0, 6):
            node1 = self.nodes[i]
            if i < 5:
                node2 = self.nodes[i + 1]
            else:
                node2 = self.nodes[0]
            if node1[0] <= node2[0]:
                self.edges.append([node1, node2])
            else:
                self.edges.append([node2, node1])

    def set_highlight(self, highlight):
        if self.highlight != highlight:
            self.highlight = highlight

    @staticmethod
    def get_neighbouring_hex_coords(coords, direction):
        return [a + b for a, b in zip(coords, Hex.directions[direction])]

    def draw(self, ctx):
        # Draw hexagon
        ctx.rgb(*self.resource['col'])
        ctx.begin_path()
        ctx.move_to(*self.nodes[0])
        for node in self.nodes[1:]:
            ctx.line_to(*node)
        ctx.close_path()
        ctx.fill()

        # Draw label
        if self.highlight:
            ctx.rgb(255, 255, 255)
        else:
            ctx.rgb(0, 0, 0)
        ctx.text_align = ctx.CENTER
        if self.robber:
            ctx.font_size = 20
            ctx.move_to(self.centre[0], self.centre[1] + 7).text("Rob")
        else:
            ctx.font_size = 30
            if self.resource != DESERT:
                ctx.move_to(self.centre[0], self.centre[1] + 10).text("{}".format(self.number['roll']))

class Settlers(app.App):

    def __init__(self):
        self.hex = Hex([0, 0, 0], SHEEP, {'roll':3, 'prob':2}, True)

    def update(self, delta):
        pass

    def draw(self, ctx):
        self.hex.draw(ctx)

__app_export__ = Settlers
