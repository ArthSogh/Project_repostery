import math

def inverseKinematics(x, y, z):
    # global j1Speed, j2Speed, baseSpeed
    # j1Speed = 600
    # j2Speed = 800
    # baseSpeed = 800

    pi = 3.141593
    j1 = 104  # Longueur J1 en mm
    # j2 = 70.5  # Longueur J2 en mm
    j2 = 250  # Longueur J2 en mm

    # Mouvement Z
    delta = math.atan(z / x)  # Angle de déplacement de la base
    delta *= (180 / pi)  # Radians en degrés

    x2 = math.sqrt(pow(z, 2) + pow(x, 2)) - x  # Différence ajoutée à x pour rester aligné avec la coordonnée x lorsque la base se déplace

    if z != 0:
        x += x2

    theta2 = -math.acos((pow(x, 2) + pow(y, 2) - pow(j1, 2) - pow(j2, 2)) / (2 * j1 * j2))  # Calcul de theta2 (en radians)

    theta1 = math.atan(y / x) + math.atan((j2 * math.sin(theta2)) / (j1 + j2 * math.cos(theta2)))  # Calcul de theta1 (en radians)

    # Radians en degrés
    theta2 *= (180 / pi)
    theta1 *= (180 / pi)

    # Ajustement des angles
    if theta2 < 0 and theta1 > 0:
        if theta1 < 90:
            theta1 += (180 - (theta1 * 2))  # Miroir par rapport à y
            theta2 *= -1
        elif theta1 > 90:
            theta1 = theta1 - (2 * (theta1 - 90))  # Miroir par rapport à y
            theta2 *= -1
    elif theta1 < 0 and theta2 < 0:
        theta1 *= -1
        theta2 *= -1

    # Orientation de la pince
    # Psi est l'orientation désirée par rapport à l'axe y. (180 est tout droit vers le bas)
    psi = 180  # Remplacer psi par la valeur désirée
    theta3 = psi - theta2 - (90 - theta1)  # (90 - theta1) pour le rendre relatif à l'axe y
    theta3 = 180 - theta3  # 180 car c'est l'angle pour que la pince soit droite, et signe moins car vers le bas est négatif selon la façon dont la pince est montée

    # Impression des résultats
    print("(X, Y, Z): (", x, ", ", y, ", ", z, ")    ",
          "Theta 1: ", 90 - theta1, "    ",
          "Theta 2: ", theta2, "    ",
          "Theta 3: ", theta3, "    ",
          "Delta: ", delta, "    ",
          "X2: ", x2)
    L = [90 - theta1,theta2, theta3, delta]
    
    return L

# Exemple d'utilisation de la fonction
# inverseKinematics(170, 0, 230)  # Remplacer les valeurs par les coordonnées désirées
