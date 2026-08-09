"""Golden map fixtures generated with the reference parser (vacuum-map-parser-xiaomi)."""

from __future__ import annotations

import base64

MODEL = "xiaomi.vacuum.d109gl"
DEVICE_ID = "412345678"

GOLDEN_BLOB = base64.b64decode(
    "bQdIjqhKVYm0eeQlrzKI90OL2dABy83lTjKZCfYHztbVbuIhRpgV5B5K7pwxJOCZB73hirKN84sR"
    "scW9+O9CDW9lejIZjWhg3hZcw6GpiO4IWOAa2RhA0uCFyklVS4IThRxMaXgwAzzz+GdPxzFDFdk/"
    "H/LlPbCs5X7+B6WAz8YuSLwiPdQNrPRR2sRfYBpGFHtmONw0q6XogFZ/CRaA81fvnqafxKaZlyge"
    "K5R3jrYG1C+B8st8QBxMGxiokDDasGOQceuEiM475jNK4Q9MKcIYD8WEZFvVNUAMXDvHjFQ+e+3r"
    "MNsBUtrESIDCAhQVIOwaPXlDipzzz8V0t64oTocrqVv7v8R3nNyxXkWzFUC/ZvqKTDGeDsmkJISV"
    "t5RtGRYZn6Hz9brpiscwvAhfLnlQis2W6ho+0OxVkcno9vOGaKRNtwfzedn4Wyl+mWYV"
)

GOLDEN_BLOB_WITH_ENVELOPE = base64.b64decode(
    "eyJkYXRhIjogImJRZElqcWhLVlltMGVlUWxyektJOTBPTDJkQUJ5ODNsVGpLWkNmWUh6dGJWYnVJ"
    "aFJwZ1Y1QjVLN3B3eEpPQ1pCNzNoaXJLTjg0c1JcbnNjVzkrTzlDRFc5bGVqSVpqV2hnM2haY3c2"
    "R3BpTzRJV09BYTJSaEEwdUNGeWtsVlM0SVRoUnhNYVhnd0F6enorR2RQeHpGREZkay9cbkgvTGxQ"
    "YkNzNVg3K0I2V0F6OFl1U0x3aVBkUU5yUFJSMnNSZllCcEdGSHRtT053MHE2WG9nRlovQ1JhQTgx"
    "ZnZucWFmeEthWmx5Z2Vcbks1UjNqcllHMUMrQjhzdDhRQnhNR3hpb2tERGFzR09RY2V1RWlNNDc1"
    "ak5LNFE5TUtjSVlEOFdFWkZ2Vk5VQU1YRHZIakZRK2UrM3Jcbk1Oc0JVdHJFU0lEQ0FoUVZJT3dh"
    "UFhsRGlwenp6OFYwdDY0b1RvY3JxVnY3djhSM25OeXhYa1d6RlVDL1p2cUtUREdlRHNta0pJU1Zc"
    "bnQ1UnRHUllabjZIejlicnBpc2N3dkFoZkxubFFpczJXNmhvKzBPeFZrY25vOXZPR2FLUk50d2Z6"
    "ZWRuNFd5bCttV1lWXG4ifQ=="
)

GOLDEN_PAYLOAD = {
    "map_id": 7,
    "width": 8,
    "height": 8,
    "resolution": 50,
    "origin_x": -200,
    "origin_y": -200,
    "map_data": "eJxjYIACBzAA0szMLCzINCMThIbKowEAqh4EqA==",
    "have_pile": 1,
    "pile_x": -100,
    "pile_y": -100,
    "pile_yaw": 9000,
    "position": {"x": 0, "y": 0, "yaw": 4500},
    "paths": {"points": [{"x": -100, "y": -100}, {"x": 0, "y": -50}, {"x": 50, "y": 0}]},
    "fb_regions": [
        {
            "points": [
                {"x": -150, "y": -150},
                {"x": -120, "y": -150},
                {"x": -120, "y": -120},
                {"x": -150, "y": -120},
            ],
            "type": "no_go",
        },
        {"id": 1, "fb_attr": 1, "fb_point": [60, 60, 90, 60, 90, 90, 60, 90]},
    ],
    "fb_walls": [{"id": 2, "wall_points": [-150, 100, 150, 100]}],
    "current_cleaning_config": {"zones": [{"x1": 0, "y1": 0, "x2": 80, "y2": 80}]},
}
