from random import randint
import time
from copy import deepcopy
from pathlib import Path
import pygame as pg
import csv

pg.init() #Nécessaire, par exemple pour définir la police d'écriture "rétrofont"

###################################CONSTANTES###################################

#Dimensions
HAUTEUR = 20
LARGEUR = 10

#Couleurs
black = (0,0,0)
white = (255,255,255)
yellow = (255,255,0)

#Highscores_Type_A
highscores_Type_A = csv.reader(open("Score Type_A.csv", "r"), delimiter = ",")
highscoredict_Type_A = {player:score for player,score in highscores_Type_A}

#Highscores_Type_B
highscores_Type_B = csv.reader(open("Score Type_B.csv", "r"), delimiter = ",")
highscoredict_Type_B = {player:score for player,score in highscores_Type_B}

sortscore_A = lambda : {player:score for (player,score) in sorted(highscoredict_Type_A.items(), key=lambda item: int(item[1]), reverse=True)}
getlistscore_A = lambda: [value for value in highscoredict_Type_A.values()]

sortscore_B = lambda : {player:score for (player,score) in sorted(highscoredict_Type_B.items(), key=lambda item: int(item[1].split(":")[0])*60+int(item[1].split(":")[1]))}
getlistscore_B = lambda: [value for value in highscoredict_Type_B.values()]

reversedict = lambda dict : {value:key for key,value in dict.items()}


#Police d'écriture
retrofont = pg.font.Font("Retro.ttf",30)

#Relation entre le nombre de lignes et le score
Lignes_Score = {0:0,1:40,2:100,3:300,4:1200}

#On crée la grille :

grille = [['E' for i in range(HAUTEUR)] for i in range(LARGEUR)]
reset = grille #La valeur de la grille par défaut, qu'on utilise pour la réinitialiser.

########################INITIALISATION DE LA CLASSE BLOCS########################

class Blocs:
    """
    Auteurs : Aliocha + Elodie + Valentin
    Description : La classe qui regroupe tous les blocs de Tetris (7), et résume leurs caractéristiques.
    """
    current_orientation = lambda self,add=0: self.orientations[(self.orientation_key+add)%len(self.orientations)] #add sert à obtenir ces informations pour d'autres orientations du bloc

    current_orientation.__doc__ = """
    Auteur : Aliocha
    Description : Renvoie l'orientation souhaitée du bloc.
    Entrée : add permet d'obtenir une orientation différée que celle active au moment de l'appel de la fonction
    Sortie : 4 tuples (x,y) pour x l'abscisse relative de chaque carré qui compose le bloc par rapport à un bloc de référence et de même pour y l'ordonnée relative de chaque carré qui compose le bloc.
    """

    blocs_coords = lambda self, orientationadd=0, xadd=0, yadd=0: [(coord[0] + self.grid_position[0] + xadd, coord[1] + self.grid_position[1] + yadd) for coord in self.current_orientation(orientationadd)] #Idem pour ici, orientationadd peut servir à tester une autre orientation. On peut également utiliser xadd et yadd pour tester un déplacement possible du bloc.

    blocs_coords.__doc__ = """
    Auteur : Aliocha
    Description : Permet d'obtenir les coordonnées des 4 carrés qui composent le bloc.
    Entrée : - orientationadd (optionnel) un entier qui permet de sélectionner une autre orientation que l'actuelle orientation du bloc. Par exemple, +1 désigne le même bloc ayant tourné dans le sens horaire, et -1 anti-horaire
             - xadd (optionnel) considère le bloc de même type que celui qui appelle la fonction, mais en ajoutant à son abscisse la valeur de xadd.
             - yadd (optionnel) considère le bloc de même type que celui qui appelle la fonction, mais en ajoutant à son ordonnée la valeur de yadd.
    Sortie : 4 tuples (x,y) pour x l'abscisse de chaque carré qui compose le bloc et y l'ordonnée de chaque carré qui compose le bloc.
    """
    
    def canSpawn(self) :
        """
        Auteur : Aliocha
        Description : Fonction qui détermine si le bloc qui l'appelle peut apparaitre dans la grille. Elle n'est donc à appeller uniquement si le bloc n'est pas déjà présent dans la grille.
        Par conséquent, si cette fonction renvoie False, c'est un Game Over.
        Entrée : None
        Sortie : Valeur Booléene qui désigne l'information en question.
        """
        for bloc in self.blocs_coords() :
            if grille[bloc[0]][bloc[1]] != 'E' :
                return False
        return True

    def assistBlock(self) :
        """
        Auteur : Aliocha
        Description : fonction qui crée un bloc "d'aide" qui désigne l'endroit où le bloc qui appelle la fonction tomberait après un harddrop. Cette fonction a l'avantage de ne pas faire apparaitre ce bloc dans la matrice "grille".
        Entrée : /
        Sortie : Bloc qui a la même classe que celui en entrée
        """
        assistblock=deepcopy(self) #Le bloc d'aide est une copie du bloc qui l'appelle...
        assistblock.harddrop() #Auquel on a fait un harddrop
        return assistblock

    def Limits(self, orientationadd=0, xadd=0, yadd=0):
        """
        Auteur : Aliocha
        Retourne les bords du bloc concerné, c'est à dire ses abscisses et ordonnées minimales et maximales.
        Entrée : - orientationadd (optionnel) un entier qui permet de sélectionner une autre orientation que l'actuelle orientation du bloc. Par exemple, +1 désigne le même bloc ayant tourné dans le sens horaire, et -1 anti-horaire
                 - xadd (optionnel) considère le bloc de même type que celui qui appelle la fonction, mais en ajoutant à son abscisse la valeur de xadd.
                 - yadd (optionnel) considère le bloc de même type que celui qui appelle la fonction, mais en ajoutant à son ordonnée la valeur de yadd.
        Sortie : liste de 2 tuples : (xmin,xmax) et (ymin,ymax)
        """
        x = [bloc[0] for bloc in self.blocs_coords(orientationadd, xadd, yadd)]
        y = [bloc[1] for bloc in self.blocs_coords(orientationadd, xadd, yadd)]
        return [(min(x),max(x)), (min(y),max(y))]

    def rotate(self, sens):
        """
        Auteur : Aliocha + Valentin 
        Description : Effectue une rotation sur le bloc qui appelle la fonction.
        Entrée : sens, un entier qui désigne le sens de la rotation ; 1 pour une rotation horaire et -1 pour une rotation anti-horaire
        Sortie : None
        """
        if self.isBorderLeft() :
            while self.Limits(1)[0][0] < 0 :
                self.moveRight()
        if self.isBorderRight() :
            while self.Limits(1)[0][1] > 9 :
                self.moveLeft()
        if not self.canRotate(sens) :
            if self.canRotate(sens,1) :
                self.moveRight()
            elif self.canRotate(sens,-1) :
                self.moveLeft()
            elif self.canRotate(sens,-2) and type(self)==Iblock:
                self.moveLeft(2)
            elif self.canRotate(sens,0,-1) :
                self.Fall()
            else :
                while not self.canRotate(sens) :
                    self.Fall(-1)
        self.orientation_key += sens
        self.orientation_key %= len(self.orientations)

    def Fall(self, way=1):
        """
        Auteur : Valentin
        Description : Fait tomber un bloc d'une ligne vers le bas
        Entrée : way (optionnel) un entier qui désigne le sens du mouvement vertical (on peut ainsi faire monter le bloc)
        Sortie : None 
        """
        self.grid_position = (self.grid_position[0], self.grid_position[1] - way)
    
    def moveLeft(self,times=1) :
        """
        Auteur : Valentin
        Description : Fais déplacer un bloc d'une colonne vers la gauche
        Entrée : Times (optionnel) le nombre de fois que le mouvement est répété 
        Sortie : None
        """
        self.grid_position = (self.grid_position[0] - times, self.grid_position[1])
    
    def moveRight(self, times=1) :
        """
        Auteur : Valentin
        Description : Fais déplacer un bloc d'une colonne vers la droite
        Entrée : Times (optionnel) le nombre de fois que le mouvement est répété 
        Sortie : None
        """
        self.grid_position = (self.grid_position[0] + times, self.grid_position[1])
    
    def canMove(self, dir) :
        """
        Auteur : Aliocha
        Description : Teste la possibilité de déplacer un bloc dans la direction "dir". A l'avantage de ne pas nécessiter le déplacement du bloc pour effectuer le test.
        Entrée : Le sens du déplacement (1 pour droite, -1 pour gauche)
        Sortie : True ou False, si c'est possible ou non.
        """
        if isinstance(self,Iblock) :
            if self.orientation_key == 1 :
                if (dir == 1 and self.Limits()[0][0]==0) or (
                    dir == -1 and self.Limits()[0][0]==9) :
                    return True
        if (self.isBorderRight() and dir==1) or (self.isBorderLeft() and dir==-1) :
            return False
        if self.Limits()[0][int((dir+1)/2)] in (0,9) :
            return False
        for bloc in self.blocs_coords(0,dir):
            if grille[bloc[0]][bloc[1]] !='E' :
                return False
        return True

    isBorderLeft = lambda self: self.Limits()[0][0]==0
    isBorderRight = lambda self: self.Limits()[0][1]==9
    isOutOfBounds = lambda self, orientationadd=0, xadd=0, yadd=0: self.Limits(orientationadd,xadd,yadd)[0][0] not in range (0,10) or self.Limits(orientationadd,xadd,yadd)[0][1] not in range (0,10)

    def canRotate(self,sens,xadd=0,yadd=0) :
        """
        Auteur : Aliocha + Elodie
        Description : Teste la possibilité de tourner un bloc dans le sens "sens". A l'avantage de ne pas nécessiter la rotation du bloc pour effectuer le test.
        Entrée : Le sens de la rotation (1 pour horaire, -1 pour anti-horaire)
        Sortie : True ou False, si c'est possible ou non
        """
        if self.isOutOfBounds(sens, xadd, yadd) :
            return False
        for bloc in self.blocs_coords(sens,xadd,yadd):
            if grille[bloc[0]][bloc[1]] !='E' :
                return False
        return True
    
    def canFall(self):
        """
        Auteur : Aliocha + Valentin
        Description : Teste la possibilité de faire tomber un bloc dans la grille. A l'avantage de ne pas nécessiter la rotation du bloc pour effectuer le test.
        Entrée et sortie : None
        """
        if self.Limits()[1][0] == 0 :
            return False
        for bloc in self.blocs_coords(0,0,-1):
            if grille[bloc[0]][bloc[1]] !='E' :
                return False
        return True
    
    def popingrid(self):
        """
        Auteur : Aliocha
        Description : Le bloc qui appelle la fonction "s'inscrit" un bloc dans la grille à la position grid_position
        Entrée et sortie : None
        """
        for i in self.current_orientation():
            grille[self.grid_position[0] + i[0]][self.grid_position[1] + i[1]] = self.colorcoding

    def softdrop(self, newGame):
        """
        Auteure : Elodie
        Description : Fait chuter le bloc d'une unité sur la grille, si il en a la possibilité.
        Entrée et sortie : None
        """
        self.Fall()
        newGame.Score+=1

    def harddrop(self, newGame=None):
        """
        Auteur : Aliocha
        Description : A partir de sa position actuelle, fait chuter le bloc qui appelle la fonction à la position la plus basse possible.
        Entrée et sortie : None
        """
        while self.canFall():
            self.Fall()
            if newGame!=None :
                newGame.Score+=2


##############################SOUS-CLASSES DE BLOCS##############################

#On définit tous les blocs
class Iblock(Blocs):
    """
    Auteure : Elodie
    Description : Propriétés d'un bloc de type I à son initialisation.
    """
    def __init__(self):
        self.orientations = [[(x, 0) for x in range(-1, 3)],
                             [(0, y) for y in range(-2, 2)]]
        self.colorcoding = 'C'
        self.orientation_key = 0
        self.grid_position = (5, 18)  #La position d'un carré de référence dans le bloc
        self.moving = True

class Jblock(Blocs):
    """
    Auteure : Elodie
    Description : Propriétés d'un bloc de type J à son initialisation.
    """
    def __init__(self):
        self.orientations = [[(-1, 0), (0, 0), (1, 0), (1, -1)],
                             [(0, 1), (0, 0), (0, -1), (-1, -1)],
                             [(-1, 1), (-1, 0), (0, 0), (1, 0)],
                             [(1, 1), (0, 1), (0, 0), (0, -1)]]
        self.colorcoding = 'B'
        self.orientation_key = 0
        self.grid_position = (5, 18)
        self.moving = True



class Lblock(Blocs):
    """
    Auteure : Elodie
    Description : Propriétés d'un bloc de type L à son initialisation.
    """
    def __init__(self):
        self.orientations = [[(-1, 0), (0, 0), (1, 0), (1, 1)],
                             [(0, 1), (0, 0), (0, -1), (1, -1)],
                             [(-1, 0), (0, 0), (1, 0), (-1, -1)],
                             [(0, 1), (0, 0), (0, -1), (-1, 1)]]
        self.colorcoding = 'O'
        self.orientation_key = 0
        self.grid_position = (5, 18)
        self.moving = True


class Sblock(Blocs):
    """
    Auteure : Elodie
    Description : Propriétés d'un bloc de type S à son initialisation.
    """
    def __init__(self):
        self.orientations = [[(-1, 0), (0, 0), (0, 1), (1, 1)],
                             [(-1, 1), (-1, 0), (0, 0), (0, -1)]]
        self.colorcoding = 'G'
        self.orientation_key = 0
        self.grid_position = (5, 18)
        self.moving = True

class Zblock(Blocs):
    """
    Auteure : Elodie
    Description : Propriétés d'un bloc de type Z à son initialisation.
    """
    def __init__(self):
        self.orientations = [[(-1, 1), (0, 1), (0, 0), (1, 0)],
                             [(-1, -1), (-1, 0), (0, 0), (0, 1)]]
        self.colorcoding = 'R'
        self.orientation_key = 0
        self.grid_position = (5, 18)
        self.moving = True


class Tblock(Blocs):
    """
    Auteure : Elodie
    Description : Propriétés d'un bloc de type T à son initialisation.
    """
    def __init__(self):
        self.orientations = [[(-1, 0), (0, 0), (0, -1), (1, 0)],
                             [(-1, 0), (0, -1), (0, -0), (0, 1)],
                             [(-1, 0), (0, 0), (0, 1), (1, 0)],
                             [(0, -1), (0, 0), (0, 1), (1, 0)]]
        self.colorcoding = 'P'
        self.orientation_key = 0
        self.grid_position = (5, 18)
        self.moving = True


class Sqblock(Blocs):
    """
    Auteure : Elodie
    Description : Propriétés d'un bloc carré à son initialisation.
    """
    def __init__(self):
        self.orientations = [[(0, 0), (0, 1), (1, 0), (1, 1)]]
        self.colorcoding = 'Y'
        self.orientation_key = 0
        self.grid_position = (5, 18)
        self.moving = True
    
class Stoneblock(Blocs) :
    """
    Auteur : Aliocha
    Description : Propriétés d'un bloc gris à supprimer dans la catégorie mini-jeu si on a le tps de la faire.
    """
    def __init__(self,grid_position):
        self.orientations = [[(0, 0)]]
        self.colorcoding = 'S'
        self.orientation_key = 0
        self.grid_position = grid_position

class Noneblock(Blocs):
    """
    Auteur : Aliocha
    Description : Propriétés d'un bloc vide qui servira lors d'opérations comme l'affichage de la grille lors d'une partie finie, lorsqu'aucun bloc n'est en chute.
    """
    def __init__(self):
        self.orientations = [[]]
        self.colorcoding = 'E'
        self.orientation_key = 0
        self.grid_position = (9, 19)

####Probabilités d'apparition des blocs (sélectionnés avec un randint(0,99))

probabilities = {
    Iblock:range(0, 5), #5% de chance d'apparition
    Sqblock:range(5,10), #5% de chance d'apparition
    Tblock:range(10,20), #10% de chance d'apparition
    Sblock:range(20,35), #15% de chance d'apparition
    Zblock:range(35,60), #15% de chance d'apparition
    Jblock:range(60,80), #20% de chance d'apparition
    Lblock:range(80,100) #20% de chance d'apparition
}

def getRandomBlock(probas=probabilities) :
    """
    Auteur : Aliocha
    Description : Renvoie un bloc d'un type déterminé aléatoirement, en tenant compte des probabilités défini ci-dessus par le dictionnaire "probabilities"
    Entrée : Le dictionnaire de probabilité utilisé (probabilities par défaut)
    Sortie : Le bloc généré aléatoirement
    """
    number = randint(0,99)
    inverted = {value: key for key, value in probas.items()} #Le dict proba inversé
    for rng in probas.values() :
        if number in rng :
            output = inverted[rng]
    return output()

def displayText(text, taille, x, y, couleur) :
    """
    Auteur : Valentin
    """
    largeText = pg.font.Font("Retro.ttf", taille)
    Surf = largeText.render(text,1,couleur)
    ecran.blit(Surf, (x,y))

##################################CLASSE GAME##################################

class Game:

    ligne = lambda HAUTEUR: [grille[x][HAUTEUR] for x in range(LARGEUR)]
    
    lignecomplete = lambda numligne: 'E' not in Game.ligne(numligne)

    checklines = lambda: [ligne for ligne in range(20) if Game.lignecomplete(ligne)]

    grille_vide = reset

    def grille_nettoyage(holerange,nb_full_lines) :
        grille2 = deepcopy(reset)
        for ligne in range(nb_full_lines) :
            for i in range (10) :
                grille2[i][ligne] = 'S'
            nbblockvide = randint(holerange[0],holerange[1])
            blocs = [x for x in range (10)]
            for i in range (nbblockvide) :
                empty = randint(0,len(blocs)-1)
                blocs.remove(blocs[empty])
                grille2[empty][ligne]= 'E'
        return grille2
    
    def acc_blocs (self):
        if self.line_count == 1 :
            self.tps_chute -= 0.01
        if self.line_count == 10 :
            self.tps_chute -= 0.1
        if self.line_count == 20:
            self.tps_chute -= 0.1
        if self.line_count == 30:
            self.tps_chute -=0.2
        if self.line_count == 40:
            self.tps_chute -= 0.2
        if self.line_count == 50:
            self.tps_chute -= 0.2
    """
        Auteur : Aliocha
        Description : Fonction inspirée de "Popgridinshell" qui retranscrit les données contenues dans "grille" dans l'interface graphique
        """
    
    def displayGrid(self,currentblock) :
        
        pg.draw.rect(ecran, yellow,(0,0,ecran.get_width(),ecran.get_height()))
        pg.draw.rect(ecran, black, (528,641,304,-600), 3)

        pg.draw.rect(ecran, black,(880,42,225,120),7)
        displayText("Score :", 30, 900, 62, black)
        displayText(f"{self.Score:06d}", 30, 910, 112, black)
        
        pg.draw.rect(ecran, black,(880,192,225,120),7)
        displayText("Temps :", 30, 900, 212, black)
        displayText(f"{int(self.chrono//60):02d}:{int((self.chrono%60)//1):02d}", 30, 925, 262, black)

        pg.draw.rect(ecran, black,(880,342,225,120),7)
        displayText("Lignes:", 30, 900, 362, black)
        displayText(f"{self.line_count:02d}", 30, 960, 415, black)
        
        pg.draw.rect(ecran, black, (230,41,225,280),7)
        displayText("Next :", 30, 268, 61, black)
        nextblocksurf = pg.image.load(fullblocks[type(self.nextblock)]).convert_alpha()
        ecran.blit(pg.transform.scale(nextblocksurf,(90,180)), (295,109))

        tempgrille = deepcopy(grille)
        if not isinstance(currentblock,Noneblock) :
            for position in currentblock.assistBlock().blocs_coords():
                tempgrille[position[0]][position[1]] = currentblock.colorcoding.lower()
        for position in currentblock.blocs_coords():
            tempgrille[position[0]][position[1]] = currentblock.colorcoding
        for x in range (len(grille_visu)) :
            for y in range (len(grille_visu[0])) :
                ecran.blit(pg.image.load(bloclink[tempgrille[x][y]]).convert_alpha(),grille_visu[x][y])
        pg.display.flip()
    
    def chuteligne(self, numligne):
        """
        Auteur : Valentin
        Description : Déplace d'une ligne vers le bas toutes les lignes situées au-dessus de la ligne entrée dans les paramètres
        """
        for i in range (10) :
            grille[i][numligne] = 'E'
        self.displayGrid(Noneblock())
        pg.display.flip()
        time.sleep(0.25)
        for y in range(numligne, HAUTEUR - 1):
            for x in range(LARGEUR):
                grille[x][y] = grille[x][y + 1]
        for x in range(LARGEUR):
            grille[x][19] = 'E'
        self.displayGrid(Noneblock())
        pg.display.flip()
        time.sleep(0.25)
    
    def mainLoop(self) :
        """
        Auteurs : Aliocha + Elodie + Valentin
        Description : Une version généralisée de la boucle répétée pendant une partie de n'importe quel mode. Elle est prévue pour envisager toutes les éventualités et actions du joueur. Les actions spécifiques à certains mode sont donc décrites sous forme de fonction, en dehors de celle-ci.
        Note : Le module pg.event à le désavantage de ne pouvoir traiter qu'un seul input à la fois. Pour résoudre ce problème, les inputs pour les mouvements sont traités par un module différent (pg.event) que les rotations (pg.key), pour pouvoir effectuer une rotation en même temps qu'un déplacement. En revanche, le fait que l'on traite les déplacements latéraux dans le même module (pg.event) permet d'interdire de se déplacer à droite et à gauche en même temps, ainsi qu'un déplacement en diagonale, en alternant mouvement horizontal et vertical.
        Entrée et Sortie : None
        """
        self.currentblock = self.nextblock # On associe le "prochain bloc" au currentblock 
        self.nextblock = getRandomBlock() #Puis on détermine le prochain pour l'afficher sur la gauche de l'écran.
        
        delay_left = delay_right = delay_down = time.time() #Valeurs de référence mises à jour à chaque mouvement, qui permettent de limiter la répétition d'une action dans le temps.
        delay_chute = time.time()
        temps_ref = time.time() #Sert pour le chrono

        while self.currentblock.moving : #Boucle active tant que le bloc n'a pas touché le sol

            #Traitement du hardrop et des rotations.
            for move in pg.event.get():
                if move.type == pg.KEYUP :
                    if move.key == pg.K_SPACE :
                        self.currentblock.harddrop(self)
                        self.currentblock.moving = False
                    
                    if move.key == pg.K_UP:
                        self.currentblock.rotate(1)
                    
                    elif move.key == pg.K_z :
                        self.currentblock.rotate(-1)
            
            #Traitement du softdrop et des mouvements droite/gauche
            move = pg.key.get_pressed()
            
            if move[pg.K_LEFT]  and self.currentblock.canMove(-1) and self.currentblock.moving and time.time()-delay_left>0.10 :
                self.currentblock.moveLeft()
                delay_left = time.time()
            
            elif move[pg.K_RIGHT] and self.currentblock.canMove(1) and self.currentblock.moving and time.time()-delay_right>0.10 :
                self.currentblock.moveRight()
                delay_right = time.time()
            
            if move[pg.K_DOWN]:
                if self.currentblock.canFall() and self.currentblock.moving :
                    if time.time()-delay_down>0.05 :
                        self.currentblock.softdrop(self)
                        delay_chute = time.time()
                        self.displayGrid(self.currentblock)
                        pg.display.flip()
                        delay_down=time.time()
                else :
                    self.currentblock.moving = False #Si le bloc ne peut plus tomber, on sort de la boucle
            
            #Chute automatique du bloc :
            if time.time()-delay_chute > self.tps_chute :
                if self.currentblock.canFall() :
                    self.currentblock.Fall()
                    delay_chute = time.time()
                else :
                    self.currentblock.moving = False #Si le bloc ne peut plus tomber, on sort de la boucle
            
            self.displayGrid(self.currentblock)
            time.sleep(1/60) #Temps de latence défini, pour que la boucle ne s'exécute qu'une fois par "frame". Ainsi le jeu (peut) tourne(r) approximativement à 60fps (frames par secondes)

            self.chrono+=time.time()-temps_ref #On ajoute le temps écoulé pendant l'exécution de la boucle au chrono qui s'affiche sur la droite de l'écran.
            temps_ref = time.time()
            
            if self.isOver() : #Si la partie atteint un point d'arrêt, on sort de la boucle
                break
        
        if not self.isOver() : #Ainsi, la partie s'arrête instantanément une fois le(s) point(s) d'arrêt atteint, sans effectuer des opérations inutiles.
            self.displayGrid(self.currentblock)
            self.currentblock.popingrid()
            nb_lignes = len(Game.checklines())
            self.delete_lines() #Suppression des lignes :
            self.Score+=Lignes_Score[nb_lignes] #On suit la relation entre ligne et score établit dans la section "CONSTANTES"
            self.displayGrid(Noneblock())
            time.sleep(0.25)

######################SOUS-CLASSES DE GAME (MODES DE JEU)######################

class Type_A (Game) :
    def __init__(self):
        self.over = False
        self.nextblock = getRandomBlock()
        self.tps_chute = 1
        self.currentblock = None
        self.line_count = 0
        self.Score = 0
        self.chrono = 0
        self.defaultgrid = reset
    
    isOver = lambda self: not self.nextblock.canSpawn()
    
    def delete_lines(self) :
        for i in range (len(Game.checklines())):
            self.chuteligne(Game.checklines()[0])
            self.line_count += 1
            self.acc_blocs()

class Type_B (Game):
    """
    Auteure : Elodie
    Description : Aussi appelé mode "Sprint", le but du Type_B est de faire un nombre de lignes demandé le plus rapidement possible. Un meilleur temps signifie donc un meilleur score. 
    Entrée : nblignes le nombre de ligne à réaliser (variable en fonction de la difficulté)
    """
    def __init__(self, nblignes):
        self.over = False
        self.nextblock = getRandomBlock()
        self.tps_chute = 1
        self.currentblock = None
        self.line_count = 0
        self.Score = 0
        self.rest_lignes = nblignes
        self.defaultgrid = reset
        self.chrono = 0
    
    isOver = lambda self : self.rest_lignes<=0 or not self.nextblock.canSpawn()
    victoire = lambda self : self.rest_lignes<=0
    
    def delete_lines(self) :
        for i in range (len(Game.checklines())):
            self.chuteligne(Game.checklines()[0])
            self.line_count += 1
            self.rest_lignes -=1
            self.acc_blocs()

class workout (Game) :
    """
    Auteure : Elodie
    Description : le but du workout est de faire le plus de lignes possibles en un temps limité.
    Entrée : le temps délimité du jeu (variable)
    """
    def __init__(self, temps_limite):
        self.over = False
        self.nextblock = getRandomBlock()
        self.tps_chute = 1
        self.currentblock = None
        self.line_count = 0
        self.Score = 0
        self.defaultgrid = reset
        self.temps_limite = temps_limite
        self.chrono = 0
        
    isOver = lambda self : self.chrono>self.temps_limite or not self.nextblock.canSpawn()
    
    def delete_lines(self) :
        for i in range (len(Game.checklines())):
            self.chuteligne(Game.checklines()[0])
            self.line_count += 1
            self.acc_blocs()


class grand_nettoyage (Game) :
    """
    Auteur : Aliocha
    Description : Le principe est simple : La grille est envahie de blocs de pierre (gris). Dans un temps limité, le but est de supprimer tous les blocs de pierre en faisant des lignes.
    Entrée : La difficulté choisie, parmi 5 difficultés : Débutant, Facile, Intermédiare, Difficile et Extrème (impossible, vraiment)
    """
    difficultés = {"Débutant" : {"nb_hole_range":(1,2),
                                 "nb_full_lines":2,
                                 "temps_imparti":30},
                   "Facile" : {"nb_hole_range":(1,2),
                               "nb_full_lines":3,
                               "temps_imparti":60},
                   "Intermédiaire": {"nb_hole_range":(2,3),
                                     "nb_full_lines":3,
                                     "temps_imparti":90},
                   "Difficile": {"nb_hole_range":(2,4),
                                 "nb_full_lines":4,
                                 "temps_imparti":160},
                   "Extreme": {"nb_hole_range":(3,4),
                               "nb_full_lines":6,
                               "temps_imparti":300}}

    def __init__(self,difficulté):
        self.over = False
        self.nextblock = getRandomBlock()
        self.tps_chute = 1
        self.currentblock = None
        self.line_count = 0
        self.Score = 0
        self.chrono = 0
        self.nb_hole_range = grand_nettoyage.difficultés[difficulté]["nb_hole_range"]
        self.nb_full_lines = grand_nettoyage.difficultés[difficulté]["nb_full_lines"]
        self.temps_imparti = grand_nettoyage.difficultés[difficulté]["temps_imparti"]
        self.defaultgrid = Game.grille_nettoyage(self.nb_hole_range, self.nb_full_lines)
    
    numbstone = lambda self : len([y for x in grille for y in x if y=='S'])
    isOver = lambda self : self.numbstone()==0 or not self.nextblock.canSpawn() or self.chrono>=self.temps_imparti
    victoire = lambda self: self.numbstone()==0
    
    def delete_lines(self) :
        for i in range (len(Game.checklines())):
            self.chuteligne(Game.checklines()[0])
            self.line_count += 1
            self.acc_blocs()

##############################INTERFACE GRAPHIQUE##############################

ecran = pg.display.set_mode((1280,690))
pg.key.set_repeat(1,10)

def animate(what, way, base, other_sprite) :
    a = base
    for i in range(5) :
        pg.draw.rect(ecran,(255,255,0),(0,0,1280,720))
        displayText("esc to menu", 20, 5, 5, black)
        what(a)
        other_sprite()
        pg.display.flip()
        a+=way
        time.sleep(0.01)

def textinput() :
    input_box = pg.Rect(ecran.get_width()/2-150, ecran.get_height()/2-18, 300, 36)
    color_inactive = pg.Color('lightskyblue3')
    color_active = pg.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False
    clock = pg.time.Clock()
    pg.key.set_repeat(0,10)
    while not done:
        for event in pg.event.get():
            if event.type == pg.MOUSEBUTTONDOWN:
                # Quand on clique sur la boite de texte
                if input_box.collidepoint(event.pos):
                    # On active les inputs
                    active = not active
                else:
                    active = False
                # Et on change
                if active :
                    color = color_active 
                else :
                    color = color_inactive
            if event.type == pg.KEYDOWN:
                if active:
                    if event.key == pg.K_RETURN:
                        done = True
                    elif event.key == pg.K_BACKSPACE:
                        text = text[:-1]
                    elif len(text)<10 :
                        text += event.unicode

        pg.draw.rect(ecran, yellow,(0,0,ecran.get_width(),ecran.get_height()))
        displayText("Highscore !", 30, ecran.get_width()/2-150, 100, black)
        displayText("Tapez un pseudo :", 30, ecran.get_width()/2-220, 200, black)
        displayText(text, 30, input_box.x+5, input_box.y+5, black)
        # L'input box
        pg.draw.rect(ecran, color, input_box, 2)
        pg.display.flip()
        clock.tick(30)
    pg.key.set_repeat(1,10)
    return text
    

icon = pg.image.load("Tetris.png").convert_alpha()
pg.display.set_icon(icon)

blocdir = Path("blocks/")
assistblocdir = Path("assistblocks/")
fullblocdir = Path("fullblocks/")

bloclink = {file.name[0]:file for file in blocdir.iterdir()}
assistbloclink = {file.name[0]:file for file in assistblocdir.iterdir()}
bloclink.update(assistbloclink)

fullblocks = {Iblock : fullblocdir/"Iblock.png",
              Jblock : fullblocdir/"Jblock.png",
              Lblock : fullblocdir/"Lblock.png",
              Sblock : fullblocdir/"Sblock.png",
              Sqblock : fullblocdir/"Sqblock.png",
              Tblock : fullblocdir/"Tblock.png",
              Zblock : fullblocdir/"Zblock.png"}

isActive = True
grille_visu = [[(x,y) for y in range (610,30,-30)] for x in range (530,810,30)]

pg.display.set_caption("Menu Tetris")
logo = pg.image.load('images/logo.png')
arcade_button = pg.image.load('images/arcade.png')
minijeux_button = pg.image.load('images/minijeux.png')
highscore_button = pg.image.load('images/highscore.png')
quit_button = pg.image.load('images/bouton.quit.png')
background = pg.image.load('images/bg.jpg')

running = True
mainmenu = True

while running :
       
    #le fond prend la taille de la fenêtre
    background = pg.transform.scale(background, ecran.get_size())
    
    #affichage du fond
    ecran.blit(background,(0,0))
    
    for event in pg.event.get():

        if mainmenu :
            #affichage du logo dans le mainmenu
            logo = pg.transform.scale(logo, (int(ecran.get_width() // 3.5), (int(ecran.get_height() // 3))))
            logo_rect = logo.get_rect()
            logo_rect.x = ecran.get_width() / 2 - logo.get_width() / 2
            logo_rect.y = ecran.get_height() / 8
            ecran.blit(logo, logo_rect)
            
            #affichage du bouton play dans le mainmenu 
            arcade_button = pg.transform.scale(arcade_button, (int(ecran.get_size()[0] //6),int(ecran.get_size()[1] // 14)))
            arcade_button_rect = arcade_button.get_rect()
            arcade_button_rect.x = ecran.get_width() / 2 - arcade_button.get_width() / 2
            arcade_button_rect.y = ecran.get_height() / 1.8
            ecran.blit(arcade_button, arcade_button_rect)
            
            #affichage du bouton minigames dans le mainmenu
            minijeux_button = pg.transform.scale(minijeux_button, (int(ecran.get_size()[0] //6),int(ecran.get_size()[1] // 14)))
            minijeux_button_rect = minijeux_button.get_rect()
            minijeux_button_rect.x = ecran.get_width() / 2 - minijeux_button.get_width() / 2
            minijeux_button_rect.y = ecran.get_height() / 1.51
            ecran.blit(minijeux_button, minijeux_button_rect)
            
            #affichage du bouton highscore dans le mainmenu
            highscore_button = pg. transform.scale(highscore_button, (int(ecran.get_size()[0] //6),int(ecran.get_size()[1] // 14)))
            highscore_button_rect = highscore_button.get_rect()
            highscore_button_rect.x = ecran.get_width() / 2 - highscore_button.get_width() / 2
            highscore_button_rect.y = ecran.get_height() / 1.3
            ecran.blit(highscore_button, highscore_button_rect)
            
            #affichage du bouton options dans le mainmenu
            quit_button = pg.transform.scale(quit_button, (int(ecran.get_size()[0] //6),int(ecran.get_size()[1] // 14)))
            quit_button_rect = quit_button.get_rect()
            quit_button_rect.x = ecran.get_width() / 2 - quit_button.get_width() / 2
            quit_button_rect.y = ecran.get_height() / 1.14
            ecran.blit(quit_button, quit_button_rect)
            
            pg.display.flip()
              

        if event.type == pg.MOUSEBUTTONDOWN:
            #vérification si le click sur le bouton play lance le jeu
            if arcade_button_rect.collidepoint(event.pos) and mainmenu == True : 
                Type_A_dir = Path("Menu/Type_A/") #sélection de l'icone à animer
                Type_A_anims = {int(file.name[-5]):file for file in Type_A_dir.iterdir()}
                Type_B_dir = Path("Menu/Type_B/") #sélection de l'icone à animer
                Type_B_anims = {int(file.name[-5]):file for file in Type_B_dir.iterdir()}
                pg.draw.rect(ecran,(255,255,0),(0,0,1280,690))
                Type_A_button = pg.image.load(Type_A_anims[0]).convert_alpha()
                def A (current_animation=0):
                    Type_A_button = pg.image.load(Type_A_anims[current_animation]).convert_alpha()
                    ecran.blit(Type_A_button,(50,100))
                Type_B_button = pg.image.load(Type_B_anims[0]).convert_alpha()
                def B (current_animation=0):
                    Type_B_button = pg.image.load(Type_B_anims[current_animation]).convert_alpha()
                    ecran.blit(Type_B_button,(600,100))
                A()
                B()
                displayText("esc to menu", 20, 5, 5, black)
                pg.display.flip()

                mouse_on_Type_A = lambda : pg.mouse.get_pos()[0] in range (150,580) and pg.mouse.get_pos()[1] in range (100, 620)

                mouse_on_Type_B = lambda : pg.mouse.get_pos()[0] in range (700, 1130) and pg.mouse.get_pos()[1] in range (100, 620) 
                
                arcademenu = True
                A_isSelected = 0
                B_isSelected = 0
                while arcademenu :
                    for event in pg.event.get() :
                        if event.type == pg.MOUSEMOTION :
                            if mouse_on_Type_A() :
                                if A_isSelected == 0 :
                                    animate(A,1,0,B)
                                    A_isSelected=1
                                
                            elif A_isSelected == 1 :
                                animate(A,-1,4,B)
                                A_isSelected=0
                            if mouse_on_Type_B() : 
                                if B_isSelected == 0:
                                    animate(B,1,0,A)
                                    B_isSelected=1
                                    
                            elif B_isSelected == 1:
                                animate(B,-1,4,A)
                                B_isSelected=0
                        
                        if event.type == pg.MOUSEBUTTONDOWN :
                            if mouse_on_Type_A() :
                                newGame = Type_A()
                                grille = deepcopy(newGame.defaultgrid)
                                while not newGame.isOver() :
                                    newGame.mainLoop()
                                if len(getlistscore_A())<10 or newGame.Score>int(getlistscore_A()[9]) :
                                    name = textinput()
                                    highscoredict_Type_A[name] = f" {newGame.Score}"
                                    highscoredict_Type_A = sortscore_A()
                                else :
                                    pg.draw.rect(ecran, yellow, pg.Rect(10,20, 1260, 660))
                                    displayText("Perdu !", 60, ecran.get_width()/2-150, ecran.get_height()/2, black)
                                    pg.display.flip()
                                    time.sleep(2)
                                arcademenu = False
                                menu = True
                                
                            if mouse_on_Type_B() :
                                newGame = Type_B(25)
                                grille = deepcopy(newGame.defaultgrid)
                                while not newGame.isOver() :
                                    newGame.mainLoop()
                                if newGame.victoire() :
                                    displayText("Gagne !", 60, ecran.get_width()/2-150, ecran.get_height()/2, black)
                                    pg.display.flip()
                                    minutes = int(getlistscore_B()[9].split(":")[0])
                                    secondes =  int(getlistscore_B()[9].split(":")[1])
                                    if minutes>int(newGame.chrono)//60 or (minutes==int(newGame.chrono)//60 and secondes>int(newGame.chrono)%60) :
                                        name = textinput()
                                        highscoredict_Type_B[name] = f"{int(newGame.chrono)//60}:{int(newGame.chrono)%60}"
                                        highscoredict_Type_B = sortscore_B()
                                else :
                                    pg.draw.rect(ecran, yellow, pg.Rect(10,20, 1260, 660))
                                    displayText("Perdu !", 60, ecran.get_width()/2-150, ecran.get_height()/2, black)
                                    pg.display.flip()
                                    time.sleep(2)
                                arcademenu = False
                                menu = True

                        if event.type == pg.KEYDOWN :
                            if event.key == pg.K_ESCAPE :
                                arcademenu = False
                                menu = True

            elif minijeux_button_rect.collidepoint(event.pos) and mainmenu == True :
                grand_nettoyage_dir = Path("Menu/Grand Nettoyage/") #sélection de l'icone à animer
                grand_nettoyage_anims = {int(file.name[-5]):file for file in grand_nettoyage_dir.iterdir()}
                Workout_dir = Path("Menu/Workout/") #sélection de l'icone à animer
                Workout_anims = {int(file.name[-5]):file for file in Workout_dir.iterdir()}
                pg.draw.rect(ecran,(255,255,0),(0,0,1280,690))
                grand_nettoyage_button = pg.image.load(grand_nettoyage_anims[0]).convert_alpha()
                def Nettoyage (current_animation=0):
                    grand_nettoyage_button = pg.image.load(grand_nettoyage_anims[current_animation]).convert_alpha()
                    ecran.blit(grand_nettoyage_button,(50,100))
                Workout_button = pg.image.load(Workout_anims[0]).convert_alpha()
                def Work (current_animation=0):
                    Workout_button = pg.image.load(Workout_anims[current_animation]).convert_alpha()
                    ecran.blit(Workout_button,(600,100))
                Nettoyage()
                Work()
                displayText("esc to menu", 20, 5, 5, black)
                pg.display.flip()
                
                mouse_on_grand_nettoyage = lambda: pg.mouse.get_pos()[0] in range (150,580) and pg.mouse.get_pos()[1] in range (100, 620)

                mouse_on_Workout = lambda: pg.mouse.get_pos()[0] in range (700, 1130) and pg.mouse.get_pos()[1] in range (100, 620) 

                minigamemenu = True
                grand_nettoyage_isSelected = 0
                Workout_isSelected = 0
                while minigamemenu :
                    for event in pg.event.get() :
                        if event.type == pg.MOUSEMOTION :
                            if mouse_on_grand_nettoyage() :
                                if grand_nettoyage_isSelected == 0 :
                                    animate(Nettoyage,1,0,Work)
                                    grand_nettoyage_isSelected=1
                                    
                            elif grand_nettoyage_isSelected == 1 :
                                animate(Nettoyage,-1,4,Work)
                                grand_nettoyage_isSelected=0
                            if mouse_on_Workout() : 
                                if Workout_isSelected == 0:
                                    animate(Work,1,0,Nettoyage)
                                    Workout_isSelected=1
                                    
                            elif Workout_isSelected == 1:
                                animate(Work,-1,4,Nettoyage)
                                Workout_isSelected=0
                        if event.type == pg.MOUSEBUTTONDOWN :
                            if mouse_on_grand_nettoyage() :
                                newGame = grand_nettoyage(["Débutant",
                                                           "Facile",
                                                           "Intermédiaire",
                                                           "Difficile",
                                                           "Extreme"][randint(0,4)])
                                grille = deepcopy(newGame.defaultgrid)
                                while not newGame.isOver() :
                                    newGame.mainLoop()
                                if newGame.victoire() :
                                    pg.draw.rect(ecran, yellow, pg.Rect(10,20, 1260, 660))
                                    displayText("Gagne !", 60, ecran.get_width()/2-150, ecran.get_height()/2, black)
                                    pg.display.flip()
                                    time.sleep(1)
                                else :
                                    pg.draw.rect(ecran, yellow, pg.Rect(10,20, 1260, 660))
                                    displayText("Perdu !", 60, ecran.get_width()/2-150, ecran.get_height()/2, black)
                                    pg.display.flip()
                                    time.sleep(1)
                                minigamemenu = False
                                menu = True
                            if mouse_on_Workout() :
                                newGame = workout(60)
                                grille = deepcopy(newGame.defaultgrid)
                                while not newGame.isOver() :
                                    newGame.mainLoop()
                                if newGame.isOver :
                                    pg.draw.rect(ecran, yellow, pg.Rect(10,20, 1260, 660))
                                    displayText("Time out !", 60, ecran.get_width()/2-250, ecran.get_height()/2, black)
                                    pg.display.flip()
                                    time.sleep(2)
                                minigamemenu = False
                                menu = True
                                
                        if event.type == pg.KEYDOWN :
                            if event.key == pg.K_ESCAPE :
                                minigamemenu = False
                                menu = True

            elif highscore_button_rect.collidepoint(event.pos) and mainmenu == True :
                mainmenu == False
                pg.draw.rect(ecran, yellow, pg.Rect(10,20, 1260, 660))
                pg.draw.rect(ecran, black, pg.Rect(10,20, 630, 660), 7)
                pg.draw.rect(ecran, black, pg.Rect(640,20, 630, 660), 7)
                displayText("esc to menu", 12, 15, 25, black)
                displayText("TYPE A", 40, 200, 70,black)
                displayText("TYPE B", 40, 840, 70,black)
                pg.display.flip()
                time.sleep(0.5)
                i = 1
                for elemA, elemB in zip(sortscore_A().items(), sortscore_B().items()) :
                    if i <= 10 :
                        displayText("#" + str(i), 28, 25, 150+i*49,black)
                        displayText(elemA[0], 28, 140, 150+i*49,black)
                        displayText(elemA[1], 28, 470, 150+i*49,black)
                        displayText("#" + str(i), 28, 655, 150+i*49,black)
                        displayText(elemB[0], 28, 770, 150+i*49,black)
                        displayText(elemB[1], 28, 1100, 150+i*49,black)
                        pg.display.flip()
                        time.sleep(0.2)
                        i+=1
                looking = True
                while looking :
                    for event in pg.event.get(): #dès action avec clavier/souris fin highscore
                        if event.type == pg.KEYDOWN :
                            if event.key == pg.K_ESCAPE :
                                looking = False
                                mainmenu = True
                    
            elif quit_button_rect.collidepoint(event.pos) and mainmenu == True :
                running = False

                with open('Score Type_A.csv','w') as fichier :
                    for i in range(len(sorted(getlistscore_A())[:9])):
                        player = reversedict(highscoredict_Type_A)[getlistscore_A()[i]]
                        score = getlistscore_A()[i]
                        fichier.write(f"{player},{score}\n")
                
                with open('Score Type_B.csv','w') as fichier :
                    for i in range(len(sorted(getlistscore_B())[:9])):
                        player = reversedict(highscoredict_Type_B)[getlistscore_B()[i]]
                        score = getlistscore_B()[i]
                        fichier.write(f"{player},{score}\n")

pg.quit()

