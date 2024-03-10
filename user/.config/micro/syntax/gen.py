Hex = lambda x: hex(x)[2:]

for r in range(0,16):
    for R in range(0,16):
        for g in range(0,16):
            for G in range(0,16):
                for b in range(0,16):
                    for B in range(0,16):
                        hex_val = '#' + Hex(r) + Hex(R) + Hex(g) + Hex(G) + Hex(b) + Hex(B)
                        print(f'  - "{hex_val}": "{hex_val}"')
