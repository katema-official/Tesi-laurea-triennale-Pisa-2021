import math
from random import *
from qiskit import *
from qiskit.tools.visualization import plot_histogram
import random

#Molte cose saranno simili al codice classico, cambia solo la rappresentazione della
#funzione di transizione, ovvero come l'agente sceglie la prossima stanza in cui andare

#variabili aggiuntive che uso per tenere traccia della situazione
qc_list = []
counts_list = []

#dizionario di coppie <contenuto di una stanza - relativo valore in bit>
room_types_dict = {"Enemies":"00", "Treasure":"01", "Shop":"10", "Boss":"11"}

#dichiaro i qubit di cui avro' bisogno nel mio circuito

#dato che la scelta e' tra tre stanze, ho bisongo di due qubit per salvarmi
#il movimento scelto dall'agente. In particolare:
#00 = vado a sinistra
#01 = vado al centro
#10 = vado a destra
phi = QuantumRegister(2, "phi")

#due qubit per la salute, dove 00 = 1, 01 = 2, 10 = 3 e 11 = 4
health = QuantumRegister(2, "health")

#due qubit anche per l'attacco, stesso discorso di prima
attack = QuantumRegister(2, "attack")

#un qubit per sapere se ho gia' visto la treasure, uno per sapere se ho gia'
#visto il negozio e un ulteriore qubit per sapere se il qubit che mi dice
#se ho gia' visto il negozio e' a 1 (e' un qubit di lavoro)
treasure_seen = QuantumRegister(1, "if treasure seen")
shop_seen = QuantumRegister(1, "if shop seen")
shop_seen_true = QuantumRegister(1, "if shop seen = 1")

#due qubit che descrivono il contenuto della stanza a sinistra
left_content = QuantumRegister(2, "left content")

#due qubit che descrivono il contenuto della stanza al centro
center_content = QuantumRegister(2, "center content")

#due qubit che descrivono il contenuto della stanza a destra
right_content = QuantumRegister(2, "right content")

#tre qubit, ciascuno dei quali mi dice se ho visto di gia' la stanza a sinistra, 
#al centro e a destra
left_seen = QuantumRegister(1, "left seen")
center_seen = QuantumRegister(1, "center seen")
right_seen = QuantumRegister(1, "right seen")

#tre qubit, ciascuno per sapere se ho adiacente il tesoro, il negozio o il boss
is_treasure_adjacent = QuantumRegister(1, "treasure adjacent")
is_shop_adjacent = QuantumRegister(1, "shop adjacent")
is_boss_adjacent = QuantumRegister(1, "boss adjacent")

#due qubit di lavoro aggiuntivi che mi serviranno per scegliere tra negozio e boss quando 
#ce li ho entrambi adiacenti
shop_max_quality = QuantumRegister(1, "shop max quality")
boss_max_quality = QuantumRegister(1, "boss max quality")

#nella implementazione classica associo un valore ad ogni stanza adiacente. In particolare sia
#il negozio che il boss possono assumere, a seconda delle stanze adiacenti e quelle viste
#in precedenza, uno tra quattro valori distinti. Bene, qui facciamo lo stesso: usiamo due qubit
#per mantenerci il valore del negozio e altri due per il valore del boss.
#Occhio alle associazioni (da confrontare col codice classico):
#NEGOZIO
#00 = -1
#01 = 0
#10 = 6
#11 = 8
#BOSS
#00 = 0
#01 = 1
#10 = 3
#11 = 7
shop_quality = QuantumRegister(2, "shop quality")
boss_quality = QuantumRegister(2, "boss quality")

#non dimentichiamoci il qubit dell'oracolo che deve effettuare il kickback di fase
oracle_qubit = QuantumRegister(1, "oracle qubit")

#cosi' come di due bit classici per leggere quale sara' la prossima stanza che il nostro agente
#vorra' esplorare
measure_bits = ClassicalRegister(2, "next_room")

#ci sara' un'altra cosa che vorremo misurare: se abbiamo visto il negozio o meno. Questo
#non e' necessario nel caso del tesoro, in quanto l'agente se vede la stanza del tesoro
#ci entra di sicuro. Per il negozio invece abbiamo visto nel codice classico che la situazione
#e' un po' diversa: se l'agente ha visto il tesoro e ha di fianco il negozio, si segna
#che comunque l'ha visto, in quanto, se non ci entra adesso, non ci entra piu' (dato che,
#una volta ottenuto il tesoro, la vita puo' solo scendere)
shop_bit = ClassicalRegister(1, "shop_seen_bit")


#costruiamo l'inizio del circuito
qc_1 = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, shop_seen_true, 
                      left_content, center_content, right_content, left_seen, center_seen, 
                      right_seen, is_treasure_adjacent, is_shop_adjacent, is_boss_adjacent, 
                      shop_max_quality, boss_max_quality, shop_quality, boss_quality, 
                      oracle_qubit, measure_bits, shop_bit)

qc_1.draw('mpl')



#ora ci serve una funzione che costruisca il circuito vero e proprio. O meglio, ci servono
#tre funzioni principali:
#-una che inizializzi i qubit del circuito
#-l'oracolo, ovvero la funzione di transizione
#-il diffuser
#a sua volta, la funzione dell'oracolo e' divisa in piu' parti per semplificare la lettura:
#-una funzione relativa alla scelta del tesoro
#-una funzione relativa alla scelta del negozio
#-una funzione relativa alla scelta del boss
#-una funzione che decide, quando necessario, se sia meglio andare al negozio o dal boss

def initialize_dungeon_circuit(qc, agent, adjacent_rooms):
    
    initialize_dungeon_circuit_debug = False
    
    #come prima cosa porto nello stato di ugual sovrapposizione i qubit phi
    qc.h(phi)
    
    #poi inizializzo i qubit che descrivono la salute e l'attacco del personaggio
    if(agent.health_points == 2):
        qc.x(health[0])
    elif(agent.health_points == 3):
        qc.x(health[1])
    elif(agent.health_points == 4):
        qc.x(health[0])
        qc.x(health[1])
    
    if(agent.attack_points == 2):
        qc.x(attack[0])
    elif(agent.attack_points == 3):
        qc.x(attack[1])
    elif(agent.attack_points == 4):
        qc.x(attack[0])
        qc.x(attack[1])
    
    #poi i qubit che descrivono se ho visto o meno il tesoro e il negozio
    if(agent.treasure_seen == True):
        qc.x(treasure_seen[0])
    if(agent.shop_seen == True):
        qc.x(shop_seen[0])
    qc.cx(shop_seen[0], shop_seen_true[0])
    
    
    
    #ora i qubit che descrivono il contenuto delle stanze adiacenti
    sx_cx_dx_content = [left_content, center_content, right_content]
    i = 0
    for room in adjacent_rooms:
        value = room_types_dict[room.content]
        if value == "01":
            qc.x(sx_cx_dx_content[i][0])
            if initialize_dungeon_circuit_debug:
                print("room number " + str(i) + ": applied content qubits 01")
        elif value == "10":
            qc.x(sx_cx_dx_content[i][1])
            if initialize_dungeon_circuit_debug:
                print("room number " + str(i) + ": applied content qubits 10")
        elif value == "11":
            qc.x(sx_cx_dx_content[i][0])
            qc.x(sx_cx_dx_content[i][1])
            if initialize_dungeon_circuit_debug:
                print("room number " + str(i) + ": applied content qubits 11")
        i += 1
            
    #e anche i qubit che mi dicono se ho gia' visto una delle stanze adiacenti
    dx_cx_sx_seen = [left_seen, center_seen, right_seen]
    i = 0
    for room in adjacent_rooms:
        if room.visited == True:
            qc.x(dx_cx_sx_seen[i])
        i += 1
    
    #inizializzo infine il qubit dell'oracolo
    qc.x(oracle_qubit)
    qc.h(oracle_qubit)
        

        
        
def treasure_logic():
    qc = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, shop_seen_true, 
                      left_content, center_content, right_content, left_seen, center_seen,
                      right_seen, is_treasure_adjacent, is_shop_adjacent, is_boss_adjacent,
                      shop_max_quality, boss_max_quality, shop_quality, boss_quality,
                      oracle_qubit)
        
    #TREASURE: se ho la stanza del tesoro vicina, ci vado, e mi segno che mi e' adiacente
    
    #tesoro a sinistra
    qc.x(phi)
    qc.x(left_content[1])
    qc.x(treasure_seen[0])
    qc.mcx([phi[0], phi[1], left_content[0], left_content[1], treasure_seen[0]], oracle_qubit)
    qc.mcx([left_content[0], left_content[1], treasure_seen[0]], is_treasure_adjacent[0])
    qc.x(treasure_seen[0])
    qc.x(left_content[1])
    qc.x(phi)
    
    
    
    #tesoro al centro
    qc.x(phi[1])
    qc.x(center_content[1])
    qc.x(treasure_seen[0])
    qc.mcx([phi[0], phi[1], center_content[0], center_content[1], treasure_seen[0]], 
        oracle_qubit)
    qc.mcx([center_content[0], center_content[1], treasure_seen[0]], is_treasure_adjacent[0])
    qc.x(treasure_seen[0])
    qc.x(center_content[1])
    qc.x(phi[1])
    
    
    
    #tesoro a destra
    qc.x(phi[0])
    qc.x(right_content[1])
    qc.x(treasure_seen[0])
    qc.mcx([phi[0], phi[1], right_content[0], right_content[1], treasure_seen[0]], oracle_qubit)
    qc.mcx([right_content[0], right_content[1], treasure_seen[0]], is_treasure_adjacent[0])
    qc.x(treasure_seen[0])
    qc.x(right_content[1])
    qc.x(phi[0])
    
    
    gate = qc.to_gate()
    gate.name = "Treasure logic"
    return gate



def shop_logic():
    qc = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, shop_seen_true, 
                      left_content, center_content, right_content, left_seen, center_seen, 
                      right_seen, is_treasure_adjacent, is_shop_adjacent, is_boss_adjacent, 
                      shop_max_quality, boss_max_quality, shop_quality, boss_quality,
                      oracle_qubit)
    
    #SHOP: devo capire il valore del negozio
    
    #...ma mi segno anche se effettivamente ce l'ho il negozio adiacente
    qc.x(left_content[0])
    qc.mcx([left_content[0], left_content[1]], is_shop_adjacent[0])
    qc.x(left_content[0])
    
    qc.x(center_content[0])
    qc.mcx([center_content[0], center_content[1]], is_shop_adjacent[0])
    qc.x(center_content[0])
    
    qc.x(right_content[0])
    qc.mcx([right_content[0], right_content[1]], is_shop_adjacent[0])
    qc.x(right_content[0])
    
    
    
    
    #dicevamo: VALORE DEL NEGOZIO
    #di default, se non ce l'ho adiacente, varra' -1. Questo semplifica il circuito 
    #quando arriviamo alla parte delle stanze contenenti nemici
    #-1 anche se ho 1 di salute (default, non devo applicare porte)
    
    #0 se, andando nel negozio, peggiorerei la mia chance di vittoria. Succede solo 
    #quando ho 2 salute e 3 attacco
    qc.x(health[1])
    qc.x(attack[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[0])
    qc.x(attack[0])
    qc.x(health[1])
    
    
    
    #6 se, andando nel negozio, le mie probabilita' di vittoria non cambiano. Succede quando:
    #health = 2 attack = 2
    #health = 3 attack = 3
    qc.x(health[1])
    qc.x(attack[1])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack[1])
    qc.x(health[1])
    
    
    
    qc.x(health[0])
    qc.x(attack[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack[0])
    qc.x(health[0])
    
    
    
    #8 se, andando nel negozio, le mie probabilita' di vittoria aumentano strettamente.
    #Succede quando:
    #health = 2 and attack = 1
    #health = 3 and (attack=1 or attack=2)
    #health = 4 and (attack=1 or attack=2 or attack=3)
    qc.x(health[1])
    qc.x(attack)
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack)
    qc.x(health[1])
    
    
    
    qc.x(health[0])
    qc.x(attack)
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack)
    qc.x(health[0])
    
    
    
    qc.x(health[0])
    qc.x(attack[1])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack[1])
    qc.x(health[0])
    
    
    
    qc.x(attack)
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack)
    
    
    
    qc.x(attack[1])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack[1])
    
    
    
    qc.x(attack[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[0])
    qc.mcx([health[0], health[1], attack[0], attack[1], is_shop_adjacent[0]], shop_quality[1])
    qc.x(attack[0])
    
    
    
    
    #prima di passare al boss, devo vedere se ho il negozio adiacente e ho gia' visto il tesoro.
    #Questo serve per decidere poi se andare dal boss, in quanto, se ho visto il tesoro e ho
    #il negozio adiacente, o ci vado ora o non ci vado mai piu'
    #quindi: se ho visto il tesoro, non ho ancora segnato shop_seen = 1 e il negozio ce l'ho
    #di fianco, mi segno di averlo visto
    
    qc.x(left_content[0])
    qc.x(shop_seen_true[0])
    qc.mcx([treasure_seen[0], shop_seen_true[0], left_content[0], left_content[1]],
        shop_seen[0])
    qc.x(shop_seen_true[0])
    qc.x(left_content[0])
    
    
    
    qc.x(center_content[0])
    qc.x(shop_seen_true[0])
    qc.mcx([treasure_seen[0], shop_seen_true[0], center_content[0], center_content[1]], 
        shop_seen[0])
    qc.x(shop_seen_true[0])
    qc.x(center_content[0])
    
    
    
    qc.x(right_content[0])
    qc.x(shop_seen_true[0])
    qc.mcx([treasure_seen[0], shop_seen_true[0], right_content[0], right_content[1]],
        shop_seen[0])
    qc.x(shop_seen_true[0])
    qc.x(right_content[0])
    
    
    #aggiungo questa riga per rimettere a zero il qubit shop_seen_true, cosi' da poterlo 
    #"riciclare" piu' tardi. L'uso che ne faccio e' spiagato meglio in fondo a questo circuito, 
    #nella parte dedicata ai nemici
    qc.cx(shop_seen[0], shop_seen_true[0])
    
    gate = qc.to_gate()
    gate.name = "Shop logic"
    return gate
        
    
    
def boss_logic():
    
    qc = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, shop_seen_true, 
                      left_content, center_content, right_content, left_seen, center_seen, 
                      right_seen, is_treasure_adjacent, is_shop_adjacent, is_boss_adjacent,
                      shop_max_quality, boss_max_quality, shop_quality, boss_quality,
                      oracle_qubit)
    
    #BOSS: devo capire il valore del boss
    #vale lo stesso discorso di prima: se non ho il boss adiacente, il suo valore 
    #e' il minimo possibile (0)
    
    #controlliamo quindi se ce l'abbiamo adiacente
    qc.mcx([left_content[0], left_content[1]], is_boss_adjacent[0])
    
    qc.mcx([center_content[0], center_content[1]], is_boss_adjacent[0])
    
    qc.mcx([right_content[0], right_content[1]], is_boss_adjacent[0])
    
    
    
    
    #dunque: VALORE DEL BOSS
    #0 se non ho visto il tesoro (default)
    
    #7 se ho visto il tesoro E il negozio
    qc.mcx([treasure_seen[0], shop_seen[0], is_boss_adjacent[0]], boss_quality[0])
    qc.mcx([treasure_seen[0], shop_seen[0], is_boss_adjacent[0]], boss_quality[1])
    
    
    
    #3 se ho visto il tesoro, non il negozio e non ho interesse ad andare nel negozio 
    #(perche' non mi aumenterebbe le chance di vittoria)
    qc.x(health)
    qc.x(shop_seen)
    qc.mcx([treasure_seen[0], shop_seen[0], health[0], health[1], is_boss_adjacent[0]], 
           boss_quality[1])
    qc.x(shop_seen)
    qc.x(health)
    
    
    
    #1 se ho visto il tesoro, ma prima di andare dal boss, mi conviene passare per il 
    #negozio, dato che aumenterebbe strettamente le mie chance di vittoria. 
    #Succede quando (come prima):
    #health = 2 and attack = 1
    #health = 3 and (attack=1 or attack=2)
    #health = 4 and (attack=1 or attack=2 or attack=3)
    
    qc.x(health[1])
    qc.x(attack)
    qc.x(shop_seen)
    qc.mcx([treasure_seen[0], shop_seen[0], health[0], health[1], attack[0], attack[1],
            is_boss_adjacent[0]], boss_quality[0])
    qc.x(shop_seen)
    qc.x(attack)
    qc.x(health[1])
    
    
    
    qc.x(health[0])
    qc.x(attack)
    qc.x(shop_seen)
    qc.mcx([treasure_seen[0], shop_seen[0], health[0], health[1], attack[0], attack[1], 
            is_boss_adjacent[0]], boss_quality[0])
    qc.x(shop_seen)
    qc.x(attack)
    qc.x(health[0])
    
    
    
    qc.x(health[0])
    qc.x(attack[1])
    qc.x(shop_seen)
    qc.mcx([treasure_seen[0], shop_seen[0], health[0], health[1], attack[0], attack[1],
            is_boss_adjacent[0]], boss_quality[0])
    qc.x(shop_seen)
    qc.x(attack[1])
    qc.x(health[0])
    
    
    
    qc.x(attack)
    qc.x(shop_seen)
    qc.mcx([treasure_seen[0], shop_seen[0], health[0], health[1], attack[0], attack[1],
            is_boss_adjacent[0]], boss_quality[0])
    qc.x(shop_seen)
    qc.x(attack)
    
    
    
    qc.x(attack[1])
    qc.x(shop_seen)
    qc.mcx([treasure_seen[0], shop_seen[0], health[0], health[1], attack[0], attack[1],
            is_boss_adjacent[0]], boss_quality[0])
    qc.x(shop_seen)
    qc.x(attack[1])
    
    
    
    qc.x(attack[0])
    qc.x(shop_seen)
    qc.mcx([treasure_seen[0], shop_seen[0], health[0], health[1], attack[0], attack[1],
            is_boss_adjacent[0]], boss_quality[0])
    qc.x(shop_seen)
    qc.x(attack[0])
    
    
    gate = qc.to_gate()
    gate.name = "Boss logic"
    return gate



def shop_vs_boss_logic():
    
    qc = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, shop_seen_true, 
                      left_content, center_content, right_content, left_seen, center_seen, 
                      right_seen, is_treasure_adjacent, is_shop_adjacent, is_boss_adjacent,
                      shop_max_quality, boss_max_quality, shop_quality, boss_quality,
                      oracle_qubit)
    
    #la scelta di andare nel negozio o dal boss dipende dal valore che ho assegnato a queste
    #stanze e dal fatto che potrei averne di fianco una, l'altra o entrambe (ma in ogni caso 
    #NON avro' di fianco il tesoro, altrimenti andrei la'). Allora distinguo tre casi:
    #-ho adiacente solo il negozio
    #-ho adiacente solo il boss
    #-ho adiacenti entrambi
    #a seconda di quale caso si verifica e della qualita' che ho assegnato a queste due stanze,
    #decidero' dove andare
    
    #caso 1) ho adiacente solo il negozio
    
    #se non ho il tesoro adiacente...
    qc.x(is_treasure_adjacent[0])
    #...e nemmeno il boss...
    qc.x(is_boss_adjacent[0])
    #...e ho il negozio a sinistra...
    qc.x(left_content[0])
    #...e il negozio vale piu' dei nemici (ovvero vale 6 o 8, che si traduce 
    #in shop_quality[1] = 1)...
    #...allora ci vado
    qc.x(phi)
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], left_content[0], 
            left_content[1], shop_quality[1]], oracle_qubit)
    qc.x(phi)
    qc.x(left_content[0])
    qc.x(is_boss_adjacent[0])
    qc.x(is_treasure_adjacent[0])
    
    
    
    #ripetere per il centro e per la destra
    qc.x(is_treasure_adjacent[0])
    qc.x(is_boss_adjacent[0])
    qc.x(center_content[0])
    qc.x(phi[1])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], center_content[0],
            center_content[1], shop_quality[1]], oracle_qubit)
    qc.x(phi[1])
    qc.x(center_content[0])
    qc.x(is_boss_adjacent[0])
    qc.x(is_treasure_adjacent[0])
    
    
    
    qc.x(is_treasure_adjacent[0])
    qc.x(is_boss_adjacent[0])
    qc.x(right_content[0])
    qc.x(phi[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], right_content[0], 
            right_content[1], shop_quality[1]], oracle_qubit)
    qc.x(phi[0])
    qc.x(right_content[0])
    qc.x(is_boss_adjacent[0])
    qc.x(is_treasure_adjacent[0])
    
    
    
    #caso 2) ho adiacente solo il boss
    
    #se non ho adiacente la stanza del tesoro...
    qc.x(is_treasure_adjacent[0])
    #...e nemmeno il negozio...
    qc.x(is_shop_adjacent[0])
    #...e ho il boss a sinistra (left_content = 11)...
    #...e il boss vale piu' dei nemici (vero quando vale 3 o 7, ovvero boss_quality[1] = 1)...
    #...allora ci vado
    qc.x(phi)
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], left_content[0],
            left_content[1], boss_quality[1]], oracle_qubit)
    qc.x(phi)
    qc.x(is_shop_adjacent[0])
    qc.x(is_treasure_adjacent[0])
    
    
    
    #ripetere per il centro e per la destra
    qc.x(is_treasure_adjacent[0])
    qc.x(is_shop_adjacent[0])
    qc.x(phi[1])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], center_content[0],
            center_content[1], boss_quality[1]], oracle_qubit)
    qc.x(phi[1])
    qc.x(is_shop_adjacent[0])
    qc.x(is_treasure_adjacent[0])
    
    
    
    qc.x(is_treasure_adjacent[0])
    qc.x(is_shop_adjacent[0])
    qc.x(phi[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], right_content[0], 
            right_content[1], boss_quality[1]], oracle_qubit)
    qc.x(phi[0])
    qc.x(is_shop_adjacent[0])
    qc.x(is_treasure_adjacent[0])
    
    
    
    #caso 3) ho adiacenti entrambi
    
    #se non ho adiacente il tesoro...
    qc.x(is_treasure_adjacent[0]) 
    #(Questa volta, per cambiare, metto l'altra riga che flippa il valore del qubit 
    #is_treasure_adjacent[0] dopo aver compiuto TUTTE le operazioni, tanto deve essere 
    #sempre vero che il tesoro non e' adiacente.)
    #...ma ho adiacenti sia il boss che il negozio (is_shop_adjacent = is_boss_adjacent = 1)...
    #...allora devo capire chi ha piu' importanza tra loro due e la stanza del nemico
    #Per farlo, devo analizzare il valore massimo che c'e' tra negozio e boss. Ricordiamo che:
    #1) il negozio puo' avere come valori di qualita' 8, 6, 0 e -1
    #2) il boss puo' avere come valori di qualita' 7, 3, 1 e 0
    
    #Quindi: se il negozio vale 8 e ce l'ho a sinistra, al centro o a destra, ci vado.
    qc.x(left_content[0])
    qc.x(phi)
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], left_content[0], 
            left_content[1], shop_quality[0], shop_quality[1]], oracle_qubit)
    qc.x(phi)
    qc.x(left_content[0])
    
    
    
    qc.x(center_content[0])
    qc.x(phi[1])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], center_content[0], 
            center_content[1], shop_quality[0], shop_quality[1]], oracle_qubit)
    qc.x(phi[1])
    qc.x(center_content[0])
    
    
    
    qc.x(right_content[0])
    qc.x(phi[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], right_content[0], 
            right_content[1], shop_quality[0], shop_quality[1]], oracle_qubit)
    qc.x(phi[0])
    qc.x(right_content[0])
    
    
    
    #Mi segno anche che shop_max_quality = 1, se effettivamente il negozio ha la qualita' 
    #piu' alta possibile
    qc.mcx([shop_quality[0], shop_quality[1]], shop_max_quality[0])
    
    
    
    
    #Se il boss vale 7 e il negozio NON vale 8 (ovvero vale meno del boss), vado dal boss
    qc.x(phi)
    qc.x(shop_max_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], left_content[0], 
            left_content[1], boss_quality[0], boss_quality[1], shop_max_quality[0]],
            oracle_qubit)
    qc.x(shop_max_quality[0])
    qc.x(phi)
    
    
    
    qc.x(phi[1])
    qc.x(shop_max_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], center_content[0], 
            center_content[1], boss_quality[0], boss_quality[1], shop_max_quality[0]],
            oracle_qubit)
    qc.x(shop_max_quality[0])
    qc.x(phi[1])
    
    
    
    qc.x(phi[0])
    qc.x(shop_max_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], right_content[0], 
            right_content[1], boss_quality[0], boss_quality[1], shop_max_quality[0]],
            oracle_qubit)
    qc.x(shop_max_quality[0])
    qc.x(phi[0])

    
    
    #Anche qui mi segno se boss_max_quality = 1
    qc.mcx([boss_quality[0], boss_quality[1]], boss_max_quality[0])
    
    
    
    
    
    #Ora si applica lo stesso discorso per quando lo shop vale 6 e il boss NON vale 7 
    #(ovvero, vale comunque meno del negozio).
    #In questo caso vado nel negozio
    qc.x(phi)
    qc.x(left_content[0])
    qc.x(shop_quality[0])
    qc.x(boss_max_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], left_content[0], 
            left_content[1], shop_quality[0], shop_quality[1], boss_max_quality[0]],
            oracle_qubit)
    qc.x(boss_max_quality[0])
    qc.x(shop_quality[0])
    qc.x(left_content[0])
    qc.x(phi)
    
    
    
    qc.x(phi[1])
    qc.x(center_content[0])
    qc.x(shop_quality[0])
    qc.x(boss_max_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], center_content[0],
            center_content[1], shop_quality[0], shop_quality[1], boss_max_quality[0]],
            oracle_qubit)
    qc.x(boss_max_quality[0])
    qc.x(shop_quality[0])
    qc.x(center_content[0])
    qc.x(phi[1])
    
    
    
    qc.x(phi[0])
    qc.x(right_content[0])
    qc.x(shop_quality[0])
    qc.x(boss_max_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_boss_adjacent[0], right_content[0], 
            right_content[1], shop_quality[0], shop_quality[1], boss_max_quality[0]],
            oracle_qubit)
    qc.x(boss_max_quality[0])
    qc.x(shop_quality[0])
    qc.x(right_content[0])
    qc.x(phi[0])
    
    
    
    
    
    #Infine, se lo shop non vale ne' 8 ne' 6, e il boss non vale 7 ma 3, allora va bene il boss
    qc.x(phi)
    qc.x(shop_quality[1])
    qc.x(boss_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], left_content[0],
            left_content[1], shop_quality[1], boss_quality[0], boss_quality[1]], oracle_qubit)
    qc.x(boss_quality[0])
    qc.x(shop_quality[1])
    qc.x(phi)
    
    
    
    qc.x(phi[1])
    qc.x(shop_quality[1])
    qc.x(boss_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], center_content[0],
            center_content[1], shop_quality[1], boss_quality[0], boss_quality[1]], oracle_qubit)
    qc.x(boss_quality[0])
    qc.x(shop_quality[1])
    qc.x(phi[1])
    
    
    
    qc.x(phi[0])
    qc.x(shop_quality[1])
    qc.x(boss_quality[0])
    qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], is_shop_adjacent[0], right_content[0],
            right_content[1], shop_quality[1], boss_quality[0], boss_quality[1]], oracle_qubit)
    qc.x(boss_quality[0])
    qc.x(shop_quality[1])
    qc.x(phi[0])
    
    qc.x(is_treasure_adjacent[0])
    
    gate = qc.to_gate()
    gate.name = "Shop vs boss logic"
    return gate
    

def enemies_logic():
    
    qc = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, shop_seen_true, 
                      left_content, center_content, right_content, left_seen, center_seen,
                      right_seen, is_treasure_adjacent, is_shop_adjacent, is_boss_adjacent,
                      shop_max_quality, boss_max_quality, shop_quality, boss_quality, 
                      oracle_qubit)
    
    #NEMICI: quando non ci sono alternative migliori
    
    #Potrebbe accadere che ho adiacenti tre stanze dei nemici non ancora esplorate (per esempio
    #all'inizio dell'esplorazione). In un caso del genere seleziono un ordine casuale
    #per valutare le stanze, perche' se altrimenti ogni stanza potesse fornire un kickback 
    #di fase a phi, otterrei come risultato 11. Quindi solo una di queste deve generare il 
    #kickback di fase. Per sapere quindi quando una stanza con nemici e' stata scelta, mettero' 
    #in pratica una procedura un po' strana ma che permette di risparmiare qubit:
    #-per andare in una stanza, anche shop_seen_true[0] deve essere a 0
    #-se ho scelto di andare in una certa stanza, setto shop_seen_true[0] a 1
    #-se quest'ultimo qubit e' a uno, flippo il valore di shop_quality[1], cosi' che 
    #le prossime stanze contenenti nemici non vengano considerate
    #-rimetto a 0 shop_seen_true[0]
    
    directions = ["left", "center", "right"]
    random.shuffle(directions)
    for d in directions:
        if d == "left":
            #La spiego per quando devo andare a sinistra, le altre sono analoghe.
            #Se non ho il tesoro adiacente...
            qc.x(is_treasure_adjacent[0])
            #...e il negozio e il boss valgono meno di me (cioe' il negozio vale -1 o 0 
            #e il boss vale 0 o 1)...
            qc.x(shop_quality[1])
            qc.x(boss_quality[1])
            #...e non ho mai esplorato la stanza a sinistra...
            qc.x(left_seen[0])
            #...e a sinistra ci sono nemici...
            qc.x(left_content)
            #...allora puo' interessarmi andare a sinistra.
            qc.x(phi)
            #aggiungo come controllo anche not(shop_seen_true[0]). Potevo aggiungere 
            #un nuovo qubit del tipo enemies_chosen[0], ma non l'ho fatto perche' cosi' 
            #sono in grado di riciclare un vecchio qubit.
            #Fondamentalmente, a questo punto del circuito, uso shop_seen_true[0] come segue:
            #-se e' a 0, vuol dire che non ho ancora scelto una stanza con nemici dove andare
            #-se e' a 1, vuol dire che invece l'ho scelta
            #tanto la scelta di entrare in una stanza con nemici verra' considerata solo quando 
            #non e' possibile procedere in una stanza migliore, e mi sono assicurato di
            #far si' che, a questo punto del circuito, shop_seen_true[0] sia a 1. Questo
            #ragionamento vale per tutti e tre i casi
            qc.x(shop_seen_true[0])
            qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], shop_quality[1], boss_quality[1],
                    left_seen[0], left_content[0], left_content[1], shop_seen_true[0]],
                    oracle_qubit)
            qc.x(shop_seen_true[0])
            #se effettivamente ho deciso di andare a sinistra, mi segno questo fatto 
            #mettendo a uno il qubit shop_seen_true[0]
            qc.mcx([is_treasure_adjacent[0], shop_quality[1], boss_quality[1], left_seen[0],
                    left_content[0], left_content[1]], shop_seen_true[0])
            #e cambio il valore di shop_quality[1] cosi' che le prossime stanze contenenti 
            #nemici vengano ignorate
            qc.cx(shop_seen_true[0], shop_quality[1])
            #ora rimetto a posto shop_seen_true[0]
            qc.x(shop_quality[1])
            qc.mcx([is_treasure_adjacent[0], shop_quality[1], boss_quality[1], left_seen[0],
                    left_content[0], left_content[1]], shop_seen_true[0])
            qc.x(shop_quality[1])
            qc.x(phi)
            qc.x(left_content)
            qc.x(left_seen[0])
            qc.x(boss_quality[1])
            qc.x(shop_quality[1])
            qc.x(is_treasure_adjacent[0])
            
            
        if d == "center":
            #vado al centro
            qc.x(is_treasure_adjacent[0])
            qc.x(shop_quality[1])
            qc.x(boss_quality[1])
            qc.x(center_seen[0])
            qc.x(center_content)
            qc.x(phi[1])
            qc.x(shop_seen_true[0])
            qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], shop_quality[1], boss_quality[1], 
                    center_seen[0], center_content[0], center_content[1], shop_seen_true[0]], 
                    oracle_qubit)
            qc.x(shop_seen_true[0])
            qc.mcx([is_treasure_adjacent[0], shop_quality[1], boss_quality[1], center_seen[0], 
                    center_content[0], center_content[1]], shop_seen_true[0])
            qc.cx(shop_seen_true[0], shop_quality[1])
            qc.x(shop_quality[1])
            qc.mcx([is_treasure_adjacent[0], shop_quality[1], boss_quality[1], center_seen[0], 
                    center_content[0], center_content[1]], shop_seen_true[0])
            qc.x(shop_quality[1])
            qc.x(phi[1])
            qc.x(center_content)
            qc.x(center_seen[0])
            qc.x(boss_quality[1])
            qc.x(shop_quality[1])
            qc.x(is_treasure_adjacent[0])
            
            
        if d == "right":
            #vado a destra
            qc.x(is_treasure_adjacent[0])
            qc.x(shop_quality[1])
            qc.x(boss_quality[1])
            qc.x(right_seen[0])
            qc.x(right_content)
            qc.x(phi[0])
            qc.x(shop_seen_true[0])
            qc.mcx([phi[0], phi[1], is_treasure_adjacent[0], shop_quality[1], boss_quality[1], 
                    right_seen[0], right_content[0], right_content[1], shop_seen_true[0]], 
                    oracle_qubit)
            qc.x(shop_seen_true[0])
            qc.mcx([is_treasure_adjacent[0], shop_quality[1], boss_quality[1], right_seen[0], 
                    right_content[0], right_content[1]], shop_seen_true[0])
            qc.cx(shop_seen_true[0], shop_quality[1])
            qc.x(shop_quality[1])
            qc.mcx([is_treasure_adjacent[0], shop_quality[1], boss_quality[1], right_seen[0], 
                    right_content[0], right_content[1]], shop_seen_true[0])
            qc.x(shop_quality[1])
            qc.x(phi[0])
            qc.x(right_content)
            qc.x(right_seen[0])
            qc.x(boss_quality[1])
            qc.x(shop_quality[1])
            qc.x(is_treasure_adjacent[0])
            
            
    
    
    gate = qc.to_gate()
    gate.name = "Enemies logic"
    return gate

        

#definiamo adesso l'oracolo, cioe' la funzione di transizione che deve indicare all'agente 
#in quale stanza muoversi
def oracle_function(qc):
    
    qc.append(treasure_logic(), [phi[0], phi[1], health[0], health[1], attack[0], attack[1], 
                treasure_seen, shop_seen, shop_seen_true, left_content[0], left_content[1],
                center_content[0], center_content[1], right_content[0], right_content[1],
                left_seen, center_seen, right_seen, is_treasure_adjacent, is_shop_adjacent,
                is_boss_adjacent, shop_max_quality, boss_max_quality, shop_quality[0],
                shop_quality[1], boss_quality[0], boss_quality[1], oracle_qubit])
    

    
    qc.append(shop_logic(), [phi[0], phi[1], health[0], health[1], attack[0], attack[1], 
                treasure_seen, shop_seen, shop_seen_true, left_content[0], left_content[1],
                center_content[0], center_content[1], right_content[0], right_content[1],
                left_seen, center_seen, right_seen, is_treasure_adjacent, is_shop_adjacent,
                is_boss_adjacent, shop_max_quality, boss_max_quality, shop_quality[0],
                shop_quality[1], boss_quality[0], boss_quality[1], oracle_qubit])
    

    
    qc.append(boss_logic(), [phi[0], phi[1], health[0], health[1], attack[0], attack[1],
                treasure_seen, shop_seen, shop_seen_true, left_content[0], left_content[1], 
                center_content[0], center_content[1], right_content[0], right_content[1],
                left_seen, center_seen, right_seen, is_treasure_adjacent, is_shop_adjacent,
                is_boss_adjacent, shop_max_quality, boss_max_quality, shop_quality[0],
                shop_quality[1], boss_quality[0], boss_quality[1], oracle_qubit])
    

    
    qc.append(shop_vs_boss_logic(), [phi[0], phi[1], health[0], health[1], attack[0], attack[1],
                treasure_seen, shop_seen, shop_seen_true, left_content[0], left_content[1],
                center_content[0], center_content[1], right_content[0], right_content[1],
                left_seen, center_seen, right_seen, is_treasure_adjacent, is_shop_adjacent,
                is_boss_adjacent, shop_max_quality, boss_max_quality, shop_quality[0],
                shop_quality[1], boss_quality[0], boss_quality[1], oracle_qubit])
    

    
    qc.append(enemies_logic(), [phi[0], phi[1], health[0], health[1], attack[0], attack[1],
                treasure_seen, shop_seen, shop_seen_true, left_content[0], left_content[1],
                center_content[0], center_content[1], right_content[0], right_content[1],
                left_seen, center_seen, right_seen, is_treasure_adjacent, is_shop_adjacent,
                is_boss_adjacent, shop_max_quality, boss_max_quality, shop_quality[0],
                shop_quality[1], boss_quality[0], boss_quality[1], oracle_qubit])
    

    
    
    
#e ora definisco la funzione diffuser
def diffuser():
    
    qc = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, shop_seen_true, 
                      left_content, center_content, right_content, left_seen, center_seen,
                      right_seen, is_treasure_adjacent, is_shop_adjacent, is_boss_adjacent,
                      shop_max_quality, boss_max_quality, shop_quality, boss_quality,
                      oracle_qubit)
    
    qc.h(phi)
    qc.x(phi)
    qc.mcx(phi, oracle_qubit)
    qc.x(phi)
    qc.h(phi)
    
    gate = qc.to_gate()
    gate.name = "Diffuser"
    return gate

    
    
    

#----------VARIABILI PER CONSERVARE L'ESECUZIONE DI UNA ESPLORAZIONE----------
all_explorations_path = []

class Exploration:
    def __init__(self):
        self.rooms_explored = []
        self.health = -1
        self.attack = -1
        self.outcome = None
        
    def print_exploration(self):
        print("In this exploration, the rooms explored were: \n" + str(self.rooms_explored) +
              "\n and the stats are: \n " + "health = " + str(self.health) + "\n attack = "
              + str(self.attack) + "\n and the outcome was: " + str(self.outcome))

class ExplorationOutcome():
    BOSSDEFEATED = "Boss defeated!"
    BOSSKILLEDYOU = "The Boss killed you!"
    YOUDIED = "You died while exploring the dungeon!"


#----------LOGICA DEL DUNGEON----------
class RoomContent():
    ENEMIES = "Enemies"
    TREASURE = "Treasure"
    SHOP = "Shop"
    BOSS = "Boss"

class Room:

    #ogni stanza avra' un indice (tre bit rappresentati come stringa) e un contenuto 
    #(rappresentato anch'esso da una stringa). Altre cose che mi interessa sapere di una stanza
    #sono se l'ho gia' visitata e qual e' la sua percentuale qualitativa (quest'ultimo attributo
    #sara' l'avventuriero a settarlo)
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
    
    #la qualita' della stanza puo' essere intesa sia come la probabilita' di non prendere danno 
    #quando si parla di stanze coi nemici, sia come la probabilita' di vincere contro il boss 
    #se si tratta della stanza del boss, e sara' sempre 100% quando si tratta del tesoro e puo' 
    #variare per il negozio. Sia il negozio che il boss usano la stessa formula per indicare
    #la loro qualita', che ha come parametri i punti vita e i punti attacco
    def __init__(self, current_room, dungeon):
        self.current_room = current_room
        self.dungeon = dungeon
        self.treasure_seen = False
        self.shop_seen = False
        self.health_points = 4
        self.attack_points = 1

        
    #definisco una funzione che iteri nel dizionario e mi restituisca la chiave di valore
    #piu' alto (serve per capire dove dovrei andare secondo l'algoritmo di Grover).
    #Questa funzione serve anche ad aggiornare il valore shop_seen
    def choice_quantum_movement(self, counts, dungeon, current_room_index):
        choice = ""
        max = -1
        for k in counts.keys():
            if counts[k] > max:
                max = counts[k]
                choice = k
                
        shop_seen_string = choice[0]
        if shop_seen_string == "1":
            if Agent.DEBUG:
                print("From the measure, I can tell i saw the shop!")
            self.shop_seen = True
                
        next_room_string = choice[2] + choice[3]
        
        #next_room_string mi dice semplicemente in che stanza ho scelto di andare:
        #00 = sinistra (devo cambiare il primo bit indice)
        #01 = centro (devo cambiare il secondo bit indice)
        #10 = destra (devo cambiare il terzo bit indice)
        
        next_room_index = ""
        if next_room_string == "00":
            opposite_bit = opposite(current_room_index[0])
            next_room_index = opposite_bit + current_room_index[1] + current_room_index[2]
        elif next_room_string == "01":
            opposite_bit = opposite(current_room_index[1])
            next_room_index = current_room_index[0] + opposite_bit + current_room_index[2]
        elif next_room_string == "10":
            opposite_bit = opposite(current_room_index[2])
            next_room_index = current_room_index[0] + current_room_index[1] + opposite_bit
        else:
            if Agent.DEBUG:
                print("TOO MUCH NOISE IN SELECTING NEXT ROOM! Retry this room")
            next_room_index = current_room_index
        
        next_room = dungeon[next_room_index]
            
        return next_room


    

    #funzione che implementa l'intera esplorazione del mio agente
    def explore(self):

        #eo sara' l'oggetto che maniene il riepilogo di questa esplorazione
        eo = Exploration()

        #finche' non ho trovato il boss
        while not self.current_room.content == RoomContent.BOSS:

            eo.rooms_explored.append(self.current_room.index)

            if(Agent.DEBUG):
                print("++++++++++++++++++++++++++++++++++++++++++++\n")
                print("Stanza = " + str(self.current_room.index))
                print("Contenuto = " + str(self.current_room.content))
                print("Vista = " + str(self.current_room.visited))
            
            #-----PARTE IN CUI APPLICO GLI EFFETTI DELLA STANZA IN CUI SONO APPENA ENTRATO-----

            #se sono entrato in una stanza con nemici, lancio una monetina e forse prendo danno
            if (self.current_room.content == RoomContent.ENEMIES and not 
                (self.current_room.index == "000" and self.current_room.visited == False)):
                #switch del danno e poi scegli
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

            #se sono entrato nella stanza del tesoro o nel negozio, me lo segno, e aggiorno 
            #il contenuto di queste stanze con dei nemici
            if self.current_room.content == RoomContent.TREASURE:
                self.treasure_seen = True

                #ottengo il potenziamento casuale
                values = [1, 2]
                power_up_types = ["health", "attack"]
                v = random.choice(values)
                p = random.choice(power_up_types)
                if Agent.DEBUG:
                    print("Power up found = " + str(v) + " " + p)
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

            #--------------------STANZA ESPLORATA, ORA DECIDO SE SONO MORTO O MENO. SE NON 
            #SONO MORTO, MI SEGNO CHE HO ESPLORATO QUESTA STANZA--------------------

            #se un nemico mi ha ucciso, esco dal ciclo
            if self.health_points == 0:
                break

            #segno che mi sono visto la stanza corrente
            self.current_room.visited = True

            #--------------------ADESSO C'e' LA FUNZIONE DI TRANSIZIONE, OVVERO LA LOGICA 
            #CHE PORTA A SCEGLIERE LA PROSSIMA STANZA--------------------

            #considero le stanze adiacenti
            adj_r_index = self.current_room.adjacent_rooms
            adjacent_rooms = []
            for i in adj_r_index:
                adjacent_rooms.append(dungeon[i])

            
            
            
            #A causa del rumore il personaggio potrebbe non riuscire a prendere una decisione
            #circa la prossima stanza da esplorare (ovvero la misura sarebbe 11, che non
            #corrisponde a nessuna stanza adiacente). Finche' questo e' vero, ri-eseguiamo 
            #il circuito
            
            new_room_chosen = False
            while not new_room_chosen:
                #Parte la parte (gioco di parole) quantistica.
                #costruisco il circuito che mi serve per fare i calcoli
                qc_curr = QuantumCircuit(phi, health, attack, treasure_seen, shop_seen, 
                          shop_seen_true, left_content, center_content, right_content, left_seen,
                          center_seen, right_seen, is_treasure_adjacent, is_shop_adjacent,
                          is_boss_adjacent, shop_max_quality, boss_max_quality, shop_quality,
                          boss_quality, oracle_qubit, measure_bits, shop_bit)

                #lo inizializzo
                initialize_dungeon_circuit(qc_curr, self, adjacent_rooms)

                #applico l'oracolo di grover
                oracle_function(qc_curr)

                #applico il diffuser
                qc_curr.append(diffuser(), [phi[0], phi[1], health[0], health[1], attack[0], 
                      attack[1], treasure_seen, shop_seen, shop_seen_true, left_content[0], 
                      left_content[1], center_content[0], center_content[1], right_content[0],
                      right_content[1], left_seen, center_seen, right_seen, is_treasure_adjacent,
                      is_shop_adjacent, is_boss_adjacent, shop_max_quality, boss_max_quality,
                      shop_quality[0], shop_quality[1], boss_quality[0], boss_quality[1],
                      oracle_qubit])

                #metto le misure
                qc_curr.measure(phi, measure_bits)
                qc_curr.measure(shop_seen, shop_bit)

                #aggiungo il circuito all'array di circuiti
                qc_list.append(qc_curr)

                #eseguo il circuito
                simulator = Aer.get_backend('qasm_simulator')
                result = execute(qc_curr, backend = simulator).result()
                counts = result.get_counts(qc_curr)

                #aggiungo i counts di questa esecuzione all'array di counts
                counts_list.append(counts)

                #scelgo dove andare
                next_room = self.choice_quantum_movement(counts, self.dungeon, 
                    self.current_room.index)
            
                if not next_room.index == self.current_room.index:
                    new_room_chosen = True
                    if Agent.DEBUG:
                        print("I chose a new room! I'm in room " + str(self.current_room.index) +
                              ", but I'm going to room " + str(next_room.index))
                else:
                    if Agent.DEBUG:
                        print("I didn't choose a new room! I'm gonna retry...")
            
                
            self.current_room = next_room
        
        

        outcome = None
        if self.health_points == 0:
            outcome = ExplorationOutcome.YOUDIED
            if Agent.DEBUG:
                print("Sei morto!")
        else:
            probability_of_victory = 5 * (1 + self.health_points) * self.attack_points
            if Agent.DEBUG:
                print("La tua probabilita' di vittoria, con " + str(self.health_points) +
                      " punti vita e " + str(self.attack_points) + " punti attacco, e' del " +
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

        
        eo.health = self.health_points
        eo.attack = self.attack_points
        eo.outcome = outcome

        all_explorations_path.append(eo)


    

    

#solita funzione per invertire un bit
def opposite(bit):
    res = "-1"
    if bit == "0": res = "1"
    if bit == "1": res = "0"
    return res
    
    
#definisco un metodo che, dato l'indice di una stanza, restituisce tutte le stanze adiacenti
def getAdjacentRooms(index):

    res = []

    for i in range(len(index)):

        #prendo l'indice originale e swappo ogni suo qubit, ottenendo tre nuove stringhe
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
        


#funzione che, dato un numero naturale e un numero di bits, codifica tale numero in una stringa
#di bit lunga number_of_bits
def intToBinary(num, number_of_bits):
    
    if num > pow(2, number_of_bits) - 1:
        raise Exception("Error: number " + str(num) + " cannot be reperesented with only " +
            str(number_of_bits) + " bits")

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
def full_exploration():
    rooms = []
    for i in range(8):
        rooms.append(Room(intToBinary(i, 3)))

    #la prima stanza contiene sempre nemici
    rooms[0].content = RoomContent.ENEMIES
    rooms[0].visited = False


    #questo e' il dungeon di prova usato nella Tesi
    rooms[1].content = RoomContent.ENEMIES
    rooms[1].visited = False
    rooms[2].content = RoomContent.ENEMIES
    rooms[2].visited = False
    rooms[3].content = RoomContent.BOSS
    rooms[3].visited = False
    rooms[4].content = RoomContent.ENEMIES
    rooms[4].visited = False
    rooms[5].content = RoomContent.SHOP
    rooms[5].visited = False
    rooms[6].content = RoomContent.TREASURE
    rooms[6].visited = False
    rooms[7].content = RoomContent.ENEMIES
    rooms[7].visited = False

    if Agent.DEBUG:
        for i in rooms:
            print("contenuto della stanza " + str(i.index) + " = " + str(i.content) +
                  ", le sue stanze adiacenti sono " + str(i.adjacent_rooms))

    #metto adesso le stanze in un dizionario cosi' che per il mio agente sia piu' semplice
    #vederne il contenuto
    
    for i in rooms:
        dungeon[i.index] = i

    if Agent.DEBUG:
        for i in rooms:
            i.room_to_string()


    a = Agent(dungeon["000"], dungeon)
    a.explore()
    
    
        
#per la tesi ho fatto anche qui 100 esplorazioni, ma ho dovuto lasciare il computer
#acceso tutta la notte. Ora lo metto a uno cosi' che se uno volesse copia-incollare
#questo codice per eseguirlo non dovrebbe aspettare 10 ore prima che termini, ma
#qualche minuto.
for k in range(1):
    full_exploration()   
    


#giusto per vedere qualcosa
qc_list[0].draw('mpl')    
plot_histogram(counts_list[0])



#settando a true questa variabile e' possibile visualizzare il contenuto di una delle liste
#di percorsi con cui abbiamo lavorato finora.
visualize_a_list = True
if visualize_a_list:
    #e' possibile modificare la lista da assegnare a f_list per vedere 
    #un diverso tipo di output. 
    #Le liste possibili includono:
    #all_explorations_path
    #explorations_path_boss_reached
    #explorations_path_high_stats
    #explorations_path_shortest

    f_list = all_explorations_path
    f = open("dungeon_summary.txt", "w")
    for i in range(len(f_list)):
        if i < 10:
            f.write("00")
        elif i>=10 and i<100:
            f.write("0")
        f.write(str(i) + "° exploration = " + str(f_list[i].rooms_explored))
        
        #assumo che un agente non possa esplorare piu' di 20 stanze
        blank_spaces = 20 - len(f_list[i].rooms_explored)
        for j in range(blank_spaces):
            f.write("       ")
        
        f.write(", h = " + str(f_list[i].health) + ", a = " + str(f_list[i].attack) + 
            ", outcome = " + str(f_list[i].outcome) + "\n")
    f.close()


    f = open("dungeon_summary.txt", "r")
    print(f.read())

