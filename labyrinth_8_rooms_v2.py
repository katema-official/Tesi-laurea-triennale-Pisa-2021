#----------STRUMENTI PER IL DISEGNO----------
import threading
from tkinter import Tk, Canvas, Frame, BOTH
from typing import Annotated

class Example(Frame):

    def __init__(self, dungeon):
        self.dungeon = dungeon
        super().__init__()

        self.initUI()

    def my_create_rectangle(self, canvas, x, y):
        xlen = 40
        ylen = 40
        canvas.create_rectangle(x, y, x+xlen, y+ylen)
    
    def my_create_text(self, canvas, x, y, t):
        xoffset = 20
        yoffset = 7
        canvas.create_text(x+xoffset, y+yoffset, text=t)

    def get_letter(self, index):
        c = self.dungeon[index].content
        if c == RoomContent.ENEMIES:
            return "E"
        if c == RoomContent.TREASURE:
            return "T"
        if c == RoomContent.SHOP:
            return "S"
        if c == RoomContent.BOSS:
            return "B"
    


    def initUI(self):

        self.master.title("Lines")
        self.pack(fill=BOTH, expand=1)

        canvas = Canvas(self)

        line_len = 40
        rectangle_dim = 40

        x000 = 100
        y000 = 100

        x010 = x000 + rectangle_dim + line_len 
        y010 = y000

        x100 = x000
        y100 = y000 + rectangle_dim + line_len

        x110 = x000 + rectangle_dim + line_len
        y110 = y000 + rectangle_dim + line_len

        x001 = x000 + rectangle_dim
        y001 = y000 - rectangle_dim - line_len/2

        x011 = x010 + rectangle_dim + line_len/2
        y011 = y010 + rectangle_dim

        x111 = x100 + rectangle_dim
        y111 = y100 + rectangle_dim + line_len/2

        x101 = x100 - rectangle_dim - line_len/2
        y101 = y100 - rectangle_dim

        self.my_create_rectangle(canvas, x000, y000)
        self.my_create_rectangle(canvas, x010, y010)
        self.my_create_rectangle(canvas, x100, y100)
        self.my_create_rectangle(canvas, x110, y110)
        self.my_create_rectangle(canvas, x001, y001)
        self.my_create_rectangle(canvas, x011, y011)
        self.my_create_rectangle(canvas, x111, y111)
        self.my_create_rectangle(canvas, x101, y101)

        self.my_create_text(canvas, x000, y000, "000")
        self.my_create_text(canvas, x010, y010, "010")
        self.my_create_text(canvas, x100, y100, "100")
        self.my_create_text(canvas, x110, y110, "110")
        self.my_create_text(canvas, x001, y001, "001")
        self.my_create_text(canvas, x011, y011, "011")
        self.my_create_text(canvas, x111, y111, "111")
        self.my_create_text(canvas, x101, y101, "101")

        self.my_create_text(canvas, x000, y000 + 15, self.get_letter("000"))
        self.my_create_text(canvas, x010, y010 + 15, self.get_letter("010"))
        self.my_create_text(canvas, x100, y100 + 15, self.get_letter("100"))
        self.my_create_text(canvas, x110, y110 + 15, self.get_letter("110"))
        self.my_create_text(canvas, x001, y001 + 15, self.get_letter("001"))
        self.my_create_text(canvas, x011, y011 + 15, self.get_letter("011"))
        self.my_create_text(canvas, x111, y111 + 15, self.get_letter("111"))
        self.my_create_text(canvas, x101, y101 + 15, self.get_letter("101"))


        canvas.create_line(x000 + rectangle_dim, y000 + rectangle_dim/2, 
        x000 + rectangle_dim + line_len, y000 + rectangle_dim/2)
        canvas.create_line(x100 + rectangle_dim, y100 + rectangle_dim/2, 
        x100 + rectangle_dim + line_len, y100 + rectangle_dim/2)
        canvas.create_line(x000 + rectangle_dim/2, y000 + rectangle_dim, 
        x000 + rectangle_dim/2, y000 + + rectangle_dim + line_len)
        canvas.create_line(x010 + rectangle_dim/2, y010 + rectangle_dim, 
        x010 + rectangle_dim/2, y010 + + rectangle_dim + line_len)

        canvas.create_line(x101 + rectangle_dim/2, y101,
        x101 + rectangle_dim/2, y001 + rectangle_dim/2,
        x001, y001 + rectangle_dim/2, smooth = 1)

        canvas.create_line(x001 + rectangle_dim, y001 + rectangle_dim/2,
        x011 + rectangle_dim/2, y001 + rectangle_dim/2,
        x011 + rectangle_dim/2, y011, smooth = 1)

        canvas.create_line(x011 + rectangle_dim/2, y011 + rectangle_dim,
        x011 + rectangle_dim/2, y111 + rectangle_dim/2,
        x111 + rectangle_dim, y111 + rectangle_dim/2, smooth = 1)

        canvas.create_line(x111, y111 + rectangle_dim/2,
        x101 + rectangle_dim/2, y111 + rectangle_dim/2,
        x101 + rectangle_dim/2, y101 + rectangle_dim, smooth = 1)

        canvas.create_line(x000 + rectangle_dim/2, y000,
         x001 + rectangle_dim/2, y001 + rectangle_dim)
        canvas.create_line(x010 + rectangle_dim, y010 + rectangle_dim/2,
         x011, y011 + rectangle_dim/2)
        canvas.create_line(x110 + rectangle_dim/2, y110 + rectangle_dim,
         x111 + rectangle_dim/2, y111)
        canvas.create_line(x100, y100 + rectangle_dim/2,
         x101 + rectangle_dim, y101 + rectangle_dim/2)

        canvas.pack(fill=BOTH, expand=1)

def draw_dungeon(dungeon):

    root = Tk()
    ex = Example(dungeon)
    root.geometry("700x500+600+100")
    a = Agent(dungeon["000"], dungeon)
    root.after(0, a.explore())
    root.mainloop()



#--------VARIABILI PER CONSERVARE L'ESECUZIONE DI UNA ESPLORAZIONE--------
all_explorations_path = []

class Exploration:
    def __init__(self):
        self.rooms_explored = []
        self.health = -1
        self.attack = -1
        self.probability_of_victory = ""
        self.outcome = None

class ExplorationOutcome():
    BOSSDEFEATED = "Boss defeated!"
    BOSSKILLEDYOU = "The Boss killed you!"
    YOUDIED = "You died while exploring the dungeon!"


#----------LOGICA DEL DUNGEON----------

import math
import random

class RoomContent():
    ENEMIES = "Enemies"
    TREASURE = "Treasure"
    SHOP = "Shop"
    BOSS = "Boss"



class Room:

    #ogni stanza avra' un indice (tre bit rappresentati come stringa) e un 
    #contenuto (rappresentato anch'esso da una stringa). Altre cose che mi
    #interessa sapere di una stanza sono se l'ho gia' visitata e qual e' la
    #sua percentuale qualitativa (quest'ultimo attributo sara'
    #l'avventuriero a settarlo)
    def __init__(self, index):
        self.index = index
        self.adjacent_rooms = getAdjacentRooms(self.index)
        self.content = None
        self.visited = False
        self.quality = -10
    
    def room_to_string(self):
        print("Stanza = " + self.index + ", content = " + self.content)



class Agent:

    DEBUG = False

    #definisco il mio agente in termini di:
    #-la stanza in cui si trova
    #-se ha visto il tesoro
    #-se ha visto lo shop
    #-i suoi punti salute
    #-i suoi punti attacco
    
    #la qualita' della stanza puo' essere intesa come la probabilita' di 
    #non prendere danno quando si parla di stanze coi nemici, probabilita'
    #di vincere contro il boss se si tratta della stanza del boss, sara'
    #sempre 100% quando si tratta  del tesoro e puo' variare per il negozio.
    #Sia il negozio che il boss usano la stessa formula per indicare la
    #loro qualita', che ha come parametri i punti vita e i punti attacco
    def __init__(self, current_room, dungeon):
        self.current_room = current_room
        self.dungeon = dungeon
        self.treasure_seen = False
        self.shop_seen = False
        self.health_points = 4
        self.attack_points = 1

        


    #funzione per calcolare la probabilita' di battere il boss in base
    #ai punti salute e i punti attacco
    def get_probability_boss_victory(self, health, attack):
        return 5 * (1 + health) * attack

    

    #funzione che implementa l'intera esplorazione del mio agente
    def explore(self):

        #"eo" sara' l'oggetto che maniene il riepilogo di questa esplorazione
        eo = Exploration()

        #finche' non ho trovato il boss
        while not self.current_room.content == RoomContent.BOSS:

            eo.rooms_explored.append(self.current_room.index)

            if(Agent.DEBUG):
                print("++++++++++++++++++++++++++++++++++++++++++++\n")
                print("Stanza = " + str(self.current_room.index))
                print("Contenuto = " + str(self.current_room.content))
                print("Vista = " + str(self.current_room.visited))
            
            #----------PARTE IN CUI APPLICO GLI EFFETTI DELLA STANZA 
            #IN CUI SONO APPENA ENTRATO----------

            #se sono entrato in una stanza con nemici, lancio una monetina
            #e forse prendo danno. Questo non vale all'inizio della partita,
            #perche' e' vero che sono in una stanza popolata da nemici, ma
            #di fatto non ci sono entrato, ci sono "nato".
            if (self.current_room.content == RoomContent.ENEMIES and
                not (self.current_room.index == "000" and 
                    self.current_room.visited == False)):
                #capisco se ho preso danno o no sulla base dell'attacco
                l = []
                r = 1
                if self.attack_points == 1:
                    for i in range(25):
                        l.append(1)
                    for i in range(75):
                        l.append(0)
                    r = random.choice(l)
                if self.attack_points == 2:
                    for i in range(50):
                        l.append(1)
                    for i in range(50):
                        l.append(0)
                    r = random.choice(l)
                if self.attack_points == 3:
                    for i in range(75):
                        l.append(1)
                    for i in range(25):
                        l.append(0)
                    r = random.choice(l)
                if self.attack_points == 4:
                    r = 1
                
                if r == 0:
                    self.health_points -= 1
                    if Agent.DEBUG:
                        print("Damage taken! Argh!")
                elif Agent.DEBUG:
                    print("No damage taken! Phew!")

            #se sono entrato nella stanza del tesoro o nel negozio, me lo
            #segno, e aggiorno il contenuto di queste stanze con dei nemici
            if self.current_room.content == RoomContent.TREASURE:
                self.treasure_seen = True

                #ottengo il potenziamento casuale
                values = [1, 2]
                power_up_types = ["health", "attack"]
                v = random.choice(values)
                p = random.choice(power_up_types)
                if Agent.DEBUG:
                    print("Power up found = " + str(v) + p)
                if v == 1 and p == "health" and self.health_points <= 3:
                    self.health_points += 1
                    if Agent.DEBUG:
                        print("+1 h")
                if v == 2 and p == "health" and self.health_points <= 3:
                    if self.health_points <=2:
                        if Agent.DEBUG:
                            print("+2 h")
                        self.health_points += 2
                    else:
                        if Agent.DEBUG:
                            print("+2 h, but really +1 h")
                        self.health_points += 1
                if v == 1 and p == "attack":
                    if Agent.DEBUG:
                        print("+1 a")
                    self.attack_points += 1
                if v == 2 and p == "attack":
                    if Agent.DEBUG:
                        print("+2 a")
                    self.attack_points += 2

                self.current_room.content = RoomContent.ENEMIES

            if self.current_room.content == RoomContent.SHOP:
                self.shop_seen = True

                #tolgo un punto vita e ne aggiungo uno di danno
                self.health_points -= 1
                self.attack_points += 1

                self.current_room.content = RoomContent.ENEMIES

            if Agent.DEBUG:
                print("Health = " + str(self.health_points))
                print("Attack = " + str(self.attack_points))

            #----STANZA ESPLORATA, ORA DECIDO SE SONO MORTO O MENO.
            #SE NON SONO MORTO MI SEGNO CHE HO ESPLORATO QUESTA STANZA----

            #se un nemico mi ha ucciso, esco dal ciclo
            if self.health_points == 0:
                break

            #segno che mi sono visto la stanza corrente
            self.current_room.visited = True

            #----------ADESSO C'e' LA FUNZIONE DI TRANSIZIONE, OVVERO
            #LA LOGICA CHE PORTA A SCEGLIERE LA PROSSIMA STANZA----------

            #considero le stanze adiacenti
            adj_r_index = self.current_room.adjacent_rooms
            adjacent_rooms = []
            for i in adj_r_index:
                adjacent_rooms.append(dungeon[i])

            adjacent_rooms = self.assign_quality(adjacent_rooms)

            if Agent.DEBUG:
                for room in adjacent_rooms:
                    print("Adjacent room " + str(room.index) + " has " + 
                        str(room.quality) + " quality")

            #ora che ho assegnato una qualita' a tutte le stanze adiacenti,
            #devo scegliere dove andare. Potrebbero tuttavia esserci piu'
            #stanze con la qualita' massima, e io devo segnarmele tutte.
            max_quality = 0
            best_quality_rooms = []
            for room in adjacent_rooms:

                if room.quality == max_quality:
                    best_quality_rooms.append(room)

                elif room.quality >= max_quality:
                    max_quality = room.quality
                    best_quality_rooms.clear()
                    best_quality_rooms.append(room)

            if Agent.DEBUG:
                print("Best rooms = ", end = "")
                for elem in best_quality_rooms:
                    print(str(elem.index) + ", ", end = "")
                print()

            #ora controllo: se c'e' una sola stanza con la qualita' migliore,
            #ho finito. Altrimenti preferiro' quella non ancora esplorata
            next_room = None
            if len(best_quality_rooms) > 1:
                not_visited_rooms = []
                for room in best_quality_rooms:
                    if room.visited == False:
                        not_visited_rooms.append(room)

                if Agent.DEBUG:
                    print("Not visited rooms = ", end = "")
                    for room in not_visited_rooms:
                        print(str(room.index) + ", ", end="")
                    print()

                #se c'e' una sola stanza che non ho ancora esplorato,
                #vado in quella
                if len(not_visited_rooms) == 1:
                    next_room = not_visited_rooms[0]
                #se invece ci sono piu' stanze che non ho ancora esplorato,
                #ne scelgo una a caso
                if len(not_visited_rooms) > 1:
                    next_room = random.choice(not_visited_rooms)
                #se invece le ho esplorate tutte, ne scelgo comunque
                #una a caso
                if len(not_visited_rooms) == 0:
                    next_room = random.choice(best_quality_rooms)

            else:
                next_room = best_quality_rooms[0]

            if Agent.DEBUG:
                print("Next Room = " + next_room.index)

            #----------------------------------------

            self.current_room = next_room

        outcome = None
        if self.health_points == 0:
            outcome = ExplorationOutcome.YOUDIED
            if Agent.DEBUG:
                print("Sei morto!")
        else:
            health = self.health_points
            attack = self.attack_points
            probability_of_victory = 5 * (1 + health) * attack
            if Agent.DEBUG:
                print("La tua probabilita' di vittoria, con " + 
                    str(self.health_points) + " punti vita e " +
                    str(self.attack_points) + " punti attacco, e' del " +
                    str(probability_of_victory) + " %")
            l = []
            for i in range(probability_of_victory):
                l.append(1)
            for i in range(100 - probability_of_victory):
                l.append(0)
            r = random.choice(l)
            if r == 1:
                outcome = ExplorationOutcome.BOSSDEFEATED
                if Agent.DEBUG:
                    print("Vittoria!")
            else:
                outcome = ExplorationOutcome.BOSSKILLEDYOU
                if Agent.DEBUG:
                    print("Il Boss ti ha ucciso!")

            #cosi' che tutte le partite che finiscono dal boss abbiano 
            #come ultima stanza proprio quella del boss
            eo.rooms_explored.append(self.current_room.index)
            eo.probability_of_victory = str(probability_of_victory) + "%"

        
        eo.health = self.health_points
        eo.attack = self.attack_points
        eo.outcome = outcome

        all_explorations_path.append(eo)



    #funzione per assegnare la giusta qualita' alle stanze
    def assign_quality(self, adjacent_rooms):

        #definisco un ordinamento delle stanze. Questo serve per decidere
        #al meglio la prossima stanza da visitare
        tmp = []
        for i in range(len(adjacent_rooms)):
            tmp.append(None)
        
        j = 0
        #fintanto che non ho tolto tutte le stanze da adjacent_rooms
        while len(adjacent_rooms) > 0:
            #controllo il contenuto di ciascuna stanza. I tipi inseriti
            #nell'array room_types sono in ordine decrescente di
            #importanza (nel senso che voglio prima valutare le stanza
            #del tesoro, poi lo shop, poi il boss e poi i nemici. Questo
            #perche', a seconda della situazione, la "probabilita' di
            #vittoria" di una stanza non rispecchia la qualita' effettiva
            #della stanza. Se ad esempio ho health = 2 e attack = 3,
            #e' vero che ho il 75% di probabilita' di vincere contro
            #un nemico e solo il 45% di vincere contro il boss, ma se
            #ho gia' visitato negozio e tesoro, non me ne importa nulla
            #dei nemici, voglio affrontare il boss!)
            room_types = [RoomContent.TREASURE, RoomContent.SHOP,
                RoomContent.BOSS, RoomContent.ENEMIES]
            for c in room_types:
                i = 0
                while i < len(adjacent_rooms):
                    if adjacent_rooms[i].content == c:
                        tmp[j] = adjacent_rooms.pop(i)
                        j += 1
                        break
                    else:
                        i += 1
                    
        #ora vado ad assegnare la qualita' vera e propria alle stanze    
        for room in tmp:
            #ora assegno una qualita' alle stanze. La qualita' di una
            #stanza dipendera' dalle mie statistiche, dal fatto che
            #ho visto o meno il tesoro e il negozio, e da cosa
            #potrebbe succedere se entrassi in una stanza o meno.

            #se la stanza adiacente contiene il tesoro (e non l'ho
            #ancora visto, ma in teoria non ci sara' mai uno scenario
            #in cui ho gia' visto la stanza del tesoro ma sara' presente
            #tale stanza), ci vado. Il tesoro ha sempre una
            #priorita' elevata
            if (self.treasure_seen == False and
                room.content == RoomContent.TREASURE):
                    room.quality = 10
            
            #negozio
            h = self.health_points
            a = self.attack_points
            if room.content == RoomContent.SHOP:
                #se ho uno di vita per me non ha la minima importanza,
                #dato che morirei se ci entrassi.
                if h == 1:
                    room.quality = -1
                else:
                    #se entrando nel negozio le mie probabilita'
                    #di vittoria aumentano nettamente, ci vorro' andare,
                    #dando pero' sempre priorita' al tesoro
                    if (self.get_probability_boss_victory(h -1, a +1)
                        - self.get_probability_boss_victory(h, a) > 0):
                            room.quality = 8
                    #se invece le mie probailita' rimanessero le stesse
                    #negozio o meno, a volta puo' interessarmi altre no,
                    #dipende se ho il boss vicino
                    elif (self.get_probability_boss_victory(h -1, a +1)
                        - self.get_probability_boss_victory(h, a) == 0):
                            room.quality = 6
                    else:
                        room.quality = 0

                    #devo trattare il negozio in modo diverso a seconda
                    #del fatto che ho gia' visto o meno il tesoro. Se sono
                    #gia' passato per la stanza del tesoro, devo decidere
                    #ADESSO se il negozio mi interessa (dato che la mia
                    #vita puo' solo diminuire a questo punto), altrimenti,
                    #se non ho ancora visto il tesoro, magari adesso non
                    #mi interessa, ma potrebbe in futuro. In questo esempio
                    #con soltanto 8 stanze in realta' questo controllo non
                    #servirebbe, ma sarebbe necessario in uno scenario
                    #piu' complicato
                    if self.treasure_seen == True:
                        #se ho gia' visto il tesoro, a prescindere dal fatto
                        #che poi entrero' nel negozio o meno, mi segno che
                        #l'ho gia' visto, cosi' che, se anche non dovessi
                        #entrarci adesso, in futuro non lo terro' nemmeno
                        #in considerazione
                        self.shop_seen = True

            #boss
            if room.content == RoomContent.BOSS:
                #se non ho visto il tesoro il boss non mi interessa
                if self.treasure_seen == False:
                    room.quality = 0
                #se ho visto sia il negozio che il tesoro dipende:
                #in generale vorro' andare dal boss. Se pero' il negozio
                #e' adiacente, ci sono volte in cui vorrei poterci andare,
                #altre in cui invece non voglio
                elif self.shop_seen == True:
                    room.quality = 7
                #se ho visto il tesoro ma non il negozio, mi interessera'
                #andare prima al negozio solo se andarci mi porta
                #effettivamente un vantaggio stretto (ovvero > e non >=)
                else:
                    #se ho uno di vita e' chiaro che il negozio non
                    #mi interessa. Ma non mi interessa nemmeno se non
                    #ci guadagnerei nulla nell'andare nel negozio
                    #(in realta' e' possibile dimostrare, nell'esempio
                    #del labirinto a 8 stanze cosi' definito, che la seconda
                    #condizione della guardia non puo' MAI essere vera)
                    if (h == 1 or 
                        (self.get_probability_boss_victory(h -1, a +1)
                        - self.get_probability_boss_victory(h, a) <= 0)):
                            room.quality = 3
                    #altrimenti valuto il guadagno che avrei andando
                    #nel negozio. Se mi conviene andare nel negozio, vuol
                    #dire che il boss ha meno importanza anche dei nemici,
                    #dato che il negozio potrebbe essere non immediatamente
                    #disponibile
                    else:
                        if (self.get_probability_boss_victory(h -1, a +1 )
                            - self.get_probability_boss_victory(h, a) > 0):
                            #in realta' questo if non servirebbe dato che,
                            #se siamo arrivati a questo punto, la condizione
                            #nell'if e' sicuramente vera (e' possibile
                            #dimostrarlo, sarebbe il duale di quanto
                            #detto sopra)
                            room.quality = 1
                        
            
            #in fondo alla catena alimentare ci sono i nemici, che mi
            #interessano solo quando tutte le altre alternative
            #sono peggiori
            if room.content == RoomContent.ENEMIES:
                room.quality = 2

        return tmp


#definisco un metodo che, dato l'indice di una stanza, restituisce tutte 
#le stanze adiacenti
def getAdjacentRooms(index):

    res = []

    for i in range(len(index)):

        #prendo l'indice originale e swappo ogni suo qubit, ottenendo
        #tre nuove stringhe
        current_bit = index[i]
        if current_bit == "1":
            current_bit = "0"
        else:
            current_bit = "1"

        list_index = list(index)
        list_index[i] = current_bit
        

        new_index = ""
        for i in list_index:
            new_index += i

        res.append(new_index)

    return res
        


#funzione che, dato un numero naturale e un numero di bits,
#codifica tale numero in una stringa di bit lunga number_of_bits
def intToBinary(num, number_of_bits):
    
    if num > pow(2, number_of_bits) - 1:
        raise Exception("Error: number " + str(num) +
            " cannot be reperesented with only " + str(number_of_bits) +
            " bits")

    list_bits = []

    for i in reversed(range(number_of_bits)):
        current_pow_of_two = pow(2, i)
        if current_pow_of_two <= num:
            list_bits.append(1)
            num -= current_pow_of_two
        else:
            list_bits.append(0)
        
    res = ""
    for i in list_bits:
        res += str(i)
    
    return res





dungeon = {}
def full_exploration(draw):
    rooms = []
    for i in range(8):
        rooms.append(Room(intToBinary(i, 3)))

    #la prima stanza contiene sempre nemici
    rooms[0].content = RoomContent.ENEMIES
    rooms[0].visited = False

    #il contenuto di tutte le altre lo scelgo io. Per personalizzare
    #il dungeon basta cambiare il valore di ogni room[i].content.
    #basta tradurre il valore di i (i = 1...7) in binario per ottenere
    #l'indice a tre bit corrispondente.
    rooms[1].content = RoomContent.ENEMIES
    rooms[2].content = RoomContent.ENEMIES
    rooms[3].content = RoomContent.BOSS
    rooms[4].content = RoomContent.ENEMIES
    rooms[5].content = RoomContent.SHOP
    rooms[6].content = RoomContent.TREASURE
    rooms[7].content = RoomContent.ENEMIES
    rooms[1].visited = False
    rooms[2].visited = False
    rooms[3].visited = False
    rooms[4].visited = False
    rooms[5].visited = False
    rooms[6].visited = False
    rooms[7].visited = False



    if Agent.DEBUG:
        for i in rooms:
            print("contenuto della stanza " + str(i.index) + " = " +
                str(i.content) + ", le sue stanze adiacenti sono " +
                str(i.adjacent_rooms))

    #metto adesso le stanze in un dizionario cosi' che per il mio agente
    #sia piu' semplice vederne il contenuto
    
    for i in rooms:
        dungeon[i.index] = i

    if Agent.DEBUG:
        for i in rooms:
            i.room_to_string()

    if not draw:
        a = Agent(dungeon["000"], dungeon)
        a.explore()
    else:
        #per visualizzare il dungeon a schermo, chiamare un'ultima
        #volta full_exploration(True). Questo tipo di chiamata
        #a questo metodo non effettua una visita del dungeon,
        #ma stampa semplicemente a schermo la struttura del dungeon 
        #in modo comprensibile
        draw_dungeon(dungeon)


#qui 100 e' un numero scelto arbitrariamente. Tanto piu' e' elevato,
#tante piu' saranno le esplorazioni che il mio agente fara', dandomi
#una soluzione piu' affidabile.
for k in range(100):
    full_exploration(False)
    

    


#adesso, in all_explorations_path, ho tutti i percorsi che il mio
#agente ha compiuto. Cominciamo a scremarli.
#prima di tutto, rimuoviamo tutte le esecuzioni che hanno portato
#a una sconfitta, poi possiamo pensare di rimuovere anche
#le esecuzioni dove il boss ci ha sconfitti.
explorations_path_boss_reached = []
for elem in all_explorations_path:
    if not (elem.outcome == ExplorationOutcome.YOUDIED or 
        elem.outcome == ExplorationOutcome.BOSSKILLEDYOU):
            explorations_path_boss_reached.append(elem)

#ora ho solo i casi in cui ho vinto. Da questi, mi piacerebbe 
#tenermi le esecuzioni in cui ho massimizzato le possibilita' 
#di vittoria.
explorations_path_high_stats = []
current_highest_probability = 100
while len(explorations_path_high_stats) == 0:

    for elem in explorations_path_boss_reached:
        if ((5 * (1 + elem.health) * elem.attack) == 
            current_highest_probability):
                explorations_path_high_stats.append(elem)
    
    current_highest_probability -= 5



#ora dobbiamo rimuovere, tra i percorsi vincenti, quelli piu' lunghi.
#e' infatti piu' probabile prendere danno affrontando tante stanze 
#che non affrontandone poche.
explorations_path_shortest = []
shortest_path_dim = 10000
for elem in explorations_path_high_stats:
    if len(elem.rooms_explored) < shortest_path_dim:
        explorations_path_shortest.clear()
        explorations_path_shortest.append(elem)
        shortest_path_dim = len(elem.rooms_explored)
    elif len(elem.rooms_explored) == shortest_path_dim:
        explorations_path_shortest.append(elem)


#e ora, tra tutti i percorsi di ugual minima lunghezza ottenuti, 
#possiamo tenerci quello che ha un'occorrenza maggiore.
dict_explorations_path_shortest = {}
for i in range(len(explorations_path_shortest)):
    curr = str(explorations_path_shortest[i].rooms_explored)
    if curr in dict_explorations_path_shortest:
        dict_explorations_path_shortest[curr] += 1
    else:
        dict_explorations_path_shortest[curr] = 1

max_occurrence = 0
solutions = []
for key in dict_explorations_path_shortest:
    if dict_explorations_path_shortest[key] > max_occurrence:
        solutions.clear()
        solutions.append(key)
        max_occurrence = dict_explorations_path_shortest[key]
    elif dict_explorations_path_shortest[key] == max_occurrence:
        solutions.append(key)

#per visualizzare i migliori percorsi disponibili 
#(l'output del programma)
for elem in solutions:
    print("Possible solution = " + elem)





#settando a true questa variabile e' possibile visualizzare 
#il contenuto di una delle liste di percorsi con cui 
#abbiamo lavorato finora.
visualize_a_list = True
if visualize_a_list:
    #e' possibile modificare la lista da assegnare a f_list 
    #per vedere un diverso tipo di output. Le liste possibili includono:
    #-all_explorations_path
    #-explorations_path_boss_reached
    #-explorations_path_high_stats
    #-explorations_path_shortest

    f_list = all_explorations_path
    f = open("dungeon_summary.txt", "w")
    for i in range(len(f_list)):
        if i < 10:
            f.write("00")
        elif i>=10 and i<100:
            f.write("0")
        f.write(str(i) + "° exploration = " + 
            str(f_list[i].rooms_explored))
        
        #assumo che un agente non possa esplorare piu' di 20 stanze
        blank_spaces = 20 - len(f_list[i].rooms_explored)
        for j in range(blank_spaces):
            f.write("       ")
        
        f.write(", h = " + str(f_list[i].health) + ", a = " + 
            str(f_list[i].attack) + ", outcome = " + 
            str(f_list[i].outcome) + "\n")
    f.close()


    f = open("dungeon_summary.txt", "r")
    print(f.read())

#per disegnare il dungeon
full_exploration(True)