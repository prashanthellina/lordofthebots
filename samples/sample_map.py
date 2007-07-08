"""
Sample map file
"""

map_name = 'sample_map'

rows = 10
cols = 10

row = [0] * cols
map = [row[:] for i in range(rows)]

for i in range(rows): map[i][0] = 1
for i in range(rows): map[i][cols-1] = 1
for i in range(cols): map[0][i] = 1
for i in range(cols): map[rows-1][i] = 1

bonus = [
    ('health', 2, 3),
    ('health', 4, 5),
    ('ammo', 6, 6)
]
