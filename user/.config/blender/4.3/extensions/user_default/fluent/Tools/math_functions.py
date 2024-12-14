import math
import mathutils
from mathutils import Matrix, Vector

def plan_equation(n = 0, v = 0, do = 'CALCUL', eq = [0, 0, 0, 0]):
    # n est le vecteur normal au plan, v un point du plan
    if do == 'CALCUL':
        equation_coef = [0, 0, 0, 0]
        equation_coef[0] = n.x
        equation_coef[1] = n.y
        equation_coef[2] = n.z
        equation_coef[3] = (-1) * n.x * v.x - n.y * v.y - n.z * v.z
        return equation_coef
    elif do == 'CHECK':
        if round(eq[0] * v.x + eq[1] * v.y + eq[2] * v.z + eq[3], 3) == 0:
            return True
        else:
            return False

def distance(x=0, y=0, z=0, xx=0, yy=0, zz=0):
    return math.sqrt( math.pow(x-xx, 2) + math.pow(y-yy, 2) + math.pow(z-zz, 2) )

def align_test(a, b, c):
    u = Vector((b.x-a.x, b.y-a.y, b.z-a.z))
    v = Vector((c.x-a.x, c.y-a.y, c.z-a.z))
    if round(u.angle(v),3) == round(math.radians(180),3):
        return True
    else:
        return False

def angle_between_3_points(a, b, c):
    u = Vector((b.x-a.x, b.y-a.y, b.z-a.z))
    v = Vector((c.x-a.x, c.y-a.y, c.z-a.z))
    return math.degrees(round(u.angle(v),3))

def produit_scalaire(v, u):
    return v.x*u.x + v.y*u.y + v.z*u.z

def vector_3d_length(vec):
    return math.sqrt(vec.x*vec.x + vec.y*vec.y + vec.z*vec.z)