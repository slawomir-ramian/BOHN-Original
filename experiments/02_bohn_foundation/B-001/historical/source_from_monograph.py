import numpy as np
from collections import defaultdict

def z3_permutation(state_index, n_bits=6):
    """
    Cyclic shift of two-bit blocks.
    (b1b2, b3b4, b5b6) -> (b3b4, b5b6, b1b2)
    """
    bits = format(state_index, f'0{n_bits}b')
    # Two-bit blocks
    block1 = bits[0:2]
    block2 = bits[2:4]
    block3 = bits[4:6]
    # Cyclic shift
    new_bits = block2 + block3 + block1
    return int(new_bits, 2)

def compute_z3_orbits(n_states=64, n_bits=6):
    """
    Compute all orbits of the Z3 action on the set of states.
    """
    visited = set()
    orbits = []
    
    for s in range(n_states):
        if s in visited:
            continue
        # Generate orbit of state s
        orbit = set()
        current = s
        for _ in range(3):  # |Z3| = 3
            orbit.add(current)
            current = z3_permutation(current, n_bits)
        orbits.append(sorted(orbit))
        visited.update(orbit)
    
    return orbits

# Oblicz orbity
orbits = compute_z3_orbits()

# Statystyki
n_orbits = len(orbits)
singleton_orbits = [o for o in orbits if len(o) == 1]
triple_orbits = [o for o in orbits if len(o) == 3]

print("="*60)
print("COMPUTING Z3 ORBITS")
print("="*60)
print(f"Number of states:               {64}")
print(f"Symmetry group:                 Z3")
print(f"Total number of orbits:         {n_orbits}")
print(f"Singleton orbits:               {len(singleton_orbits)}")
print(f"Triple orbits:                  {len(triple_orbits)}")
print()

# Verification lematu Burnside'a
fix_e = 64
fix_g = sum(1 for s in range(64) 
            if z3_permutation(s) == s)
fix_g2 = sum(1 for s in range(64) 
             if z3_permutation(z3_permutation(s)) == s)

burnside = (fix_e + fix_g + fix_g2) / 3
print(f"Verification of Burnside's lemma:")
print(f"  |Fix(e)|  = {fix_e}")
print(f"  |Fix(g)|  = {fix_g}")
print(f"  |Fix(g2)| = {fix_g2}")
print(f"  N_orbit = (1/3)({fix_e}+{fix_g}+{fix_g2}) = {burnside:.0f}")
print()

# Print singleton orbits
print("Singleton orbits (fixed states):")
for o in singleton_orbits:
    s = o[0]
    bits = format(s, '06b')
    print(f"  State {s:2d} = {bits} "
          f"= ({bits[0:2]},{bits[2:4]},{bits[4:6]})")
print()

# Print a few triple orbits
print("Example triple orbits:")
for o in triple_orbits[:5]:
    labels = [f"{s}({format(s,'06b')})" for s in o]
    print(f"  {{{', '.join(labels)}}}")
print(f"  ... (total {len(triple_orbits)} triple orbits)")
