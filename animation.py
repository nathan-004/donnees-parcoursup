# Fichier pour animer lors de l'utilisation d'une fonction
import time

char_styles = {
    "dots": ".",
    "hash": "#",
    "star": "*",
    "equal": "=",
    "arrow": "→",
    "block": "█",
    "wave": "~",
    "line": "-",
    "circle": "●",
    "square": "■"
}

chara = "█"
total_iterations = 0
cur_iteration = 1
cur_pos = -1
max_chars = 10
start_title = ""
end_title = ""
start = 0

def init():
    global cur_iteration
    global cur_pos

    cur_iteration = 1
    cur_pos = -1

def animate(*args, char=None, max_char = 100, title="Animation en cours", title_end="Animation terminée"):
    """
    animate initie l'animation avec les valeurs donnéees, renvoie le range() si les args sont des nombres sinon renvoie la liste des éléments si c'est une liste
    
    Parameters
    ----------
    Args  
    -> nombre d'itérations  
    -> nombre de départ, nombre d'arrivée, incrémentation  
    -> nombre de départ, nombre d'arrivée  
    -> itérable  

    char:str
        Charactère utilisé
    max_chars:int
        Nombre de charactère à afficher à l'écran
    """

    global total_iterations
    global chara
    global max_chars
    global start_title
    global end_title
    global start
    
    init()
    
    size = len(args)
    
    if size == 0:
        raise TypeError("animate expected at least 1 argument, got 0")
    elif size > 3:
        raise TypeError("animate expected at most 3 arguments, got 4")

    res = None
    if char is None:
        char = chara
    
    if char not in char_styles:
        chara = char
    else:
        chara = char_styles[char]
    max_chars = max_char
    start_title = title
    end_title = title_end
    start = time.time()

    if size == 1:
        if type(args[0]) == int:
            res = range(args[0])
        else:
            try:
                total_iterations = len(args[0])
            except TypeError:
                total_iterations = len(list(args[0]))
                return list(args[0])
            return args[0]
    else:
        if all([type(el) == int for el in args]):
            res = range(*args)

    total_iterations = res.__len__()

    return res

def print_anim():
    global cur_iteration
    global cur_pos

    duree = time.time()-start

    if cur_iteration == total_iterations:
        p = cur_iteration / total_iterations
        print(f"\r{chara*int(max_chars*p)+ '-' * (max_chars-int(max_chars*p))} {int(p*100)}%  {end_title} - {int(duree)}s", flush=True)
        return 0
    
    if round(cur_iteration * max_chars / total_iterations) != cur_pos:
        cur_pos += 1
        p = cur_iteration / total_iterations
        print(f"\r{chara*int(max_chars*p)+ '-' * (max_chars-int(max_chars*p))} {int(p*100)}%  {start_title} - {int(duree)}s {' '*10}", end="", flush=True) # Recouvrir si changement de texte 

    cur_iteration += 1

if __name__ == "__main__":
    for i in animate(100000000):
        print_anim()
