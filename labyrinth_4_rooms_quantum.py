import math
from random import *
from qiskit import *
from qiskit.tools.visualization import plot_histogram
import random

#Cominciamo col creare un dizionario, che mappa valori binari delle stanze 
#ai loro contenuti.
#OCCHIO: questo dizionario e' quello che cambiera' ad ogni partita.
#In generale dovrei creare una funzione che genera una lista che
#contiene esattamente un boss, una treasure e due enemies, randomizzarla 
#e associare ogni elemento ad ogni coppia di bit. Ma per ora faccio
#un caso semplice. Se dovessi disegnare la mappa su un foglio di carta
#sarebbe una cosa tipo:
#alto a sinistra: 00
#alto a destra: 01
#basso a sinistra: 10
#basso a destra: 11
labyrinth_map = {"00":"enemies", "01":"boss", "10":"treasure", "11":"enemies"}

#ora definisco un altro dizionario che mappa tipo di stanza a valore
#numerico a due bit. Mi serve per
#poi sapere nel circuito cosa c'e' a destra e cosa c'e' a sinistra
room_types_dict = {"treasure":"00", "enemies":"01", "boss":"11"}

#voglio pero' anche sapere dove mi trovo
current_room = "00";
#ho bisogno di un bit per sapere se ho visto il tesoro o no
treasure_seen_bit = "0";

#preparo i registri di cui ho bisogno per il circuito (in particolare per l'oracolo).
#ho bisogno del bit che andra' nello stato di ugual sovrapposizione,
#tanto per cominciare.
#IMPORTANTE: dopo la misura, 0 = cambio il primo qubit, 1 = cambio il secondo qubit
phi = QuantumRegister(1, "phi")

#poi ho bisogno di due qubit che mi dicano qual e' il contenuto della stanza a sinistra
left_room = QuantumRegister(2, "left room")

#stessa cosa per la stanza a destra
right_room = QuantumRegister(2, "right room")

#ora ho bisogno di un qubit che mi dica se ho gia' visto la stanza del tesoro o no
treasure_seen = QuantumRegister(1, "if treasure seen")

#poi ho chiaramente bisogno del qubit dell'oracolo, quello che deve applicare
#un kickback di fase pari a -1 quando passa la soluzione
oracle_q = QuantumRegister(1, "oracle qubit")

#Infine mi serve un bit classico per fare la misura
bit = ClassicalRegister(1, "measure")

#costruisco un circuito quantistico partendo da questi qubit
starting_qc = QuantumCircuit(phi, left_room, right_room, treasure_seen, oracle_q, bit)

starting_qc.draw('mpl')

#funzione per inizializzare il qubit dell'oracolo nello stato |->
def initialize_oracle_q(qc):
    qc.x(oracle_q)
    qc.h(oracle_q)

#definisco una funzione che dato il bit (qubit) 0 mi restituisce 1 e viceversa
def opposite(bit):
    res = "-1"
    if bit == "0": res = "1"
    if bit == "1": res = "0"
    return res

#definisco una funzione che, data la stanza corrente del giocatore
#e la mappa del labirinto, inizializza i qubit che descrivono
#cosa c'e' a sinistra e cosa a destra
def initialize_left_right(qc, current_room, labyrinth_map, room_types_dict):
    
    print("Current room = " + current_room)
    
    #prima prendo gli indici delle stanze adiacenti a quella in cui
    #il giocatore si trova
    left_room_index = opposite(current_room[0]) + current_room[1]
    print("Left room index = " + left_room_index)
    right_room_index = current_room[0] + opposite(current_room[1])
    print("Right room index = " + right_room_index)
    
    #poi devo vedere cosa contengono queste stanze
    left_room_content = labyrinth_map.get(left_room_index)
    right_room_content = labyrinth_map.get(right_room_index)
    print("Left room content = " + left_room_content)
    print("Right room content = " + right_room_content)
    
    #ora posso decodificare il contenuto delle stanze in forma di due bit (qubit)
    left_room_content_bits = room_types_dict.get(left_room_content)
    right_room_content_bits = room_types_dict.get(right_room_content)
    print("Left room content (bits) = " + left_room_content_bits)
    print("Right room content (bits) = " + right_room_content_bits)
    
    #ora posso usare i valori di questi bit per inizializzare i qubit
    #della stanza a sinistra e quella a destra
    if left_room_content_bits[0] == "1":
        qc.x(left_room[0])
    if left_room_content_bits[1] == "1":
        qc.x(left_room[1])
    if right_room_content_bits[0] == "1":
        qc.x(right_room[0])
    if right_room_content_bits[1] == "1":
        qc.x(right_room[1])
        
#funzione per inizializzare il qubit treasure_seen
def initialize_treasure_seen():
    if treasure_seen_bit == "1":
        qc.x(treasure_seen)
        
#definisco il diffuser (quello che serve a effettuare
#una riflessione rispetto a |phi>)

def diffuser(qc):
    qc.h(phi)
    qc.x(phi)
    qc.cx(phi, oracle_q)
    qc.x(phi)
    qc.h(phi)

#definisco una funzione che iteri nel dizionario e mi restituisca la chiave di valore
#piu' alto (serve per capire dove dovrei andare secondo l'algoritmo di Grover)
def choice_quantum_movement():
    choice = ""
    max = -1
    for k in counts.keys():
        if counts[k] > max:
            max = counts[k]
            choice = k
    return choice

#funzione che modifica il valore della stanza corrente data la stanza corrente
#e il movimento. Inoltre, se mi sono appena mosso nella stanza del tesoro
#e non la avevo ancora esplorata, faccio due cose:
#1) mi segno che l'ho esplorata
#2) la sovrascrivo con una stanza con nemici
def update_current_room(direction):
    global current_room
    global treasure_seen_bit
    global labyrinth_map
    if direction == "0":
        current_room = opposite(current_room[0]) + current_room[1]
    if direction == "1":
        current_room = current_room[0] + opposite(current_room[1])
        
    if treasure_seen_bit == "0" and labyrinth_map[current_room] == "treasure":
        treasure_seen_bit = "1"
        labyrinth_map[current_room] = "enemies"

        
              
#variabili aggiuntive che uso per tenere traccia della situazione
qc_list = []
counts_list = []
        


#Da qui comincia la ciccia

#come prima cosa ho bisogno di sapere in che stanza si trova il boss.
#Infatti, se la conosco, so anche quando fermarmi, ovvero
#quando il personaggio e' entrato nella stanza del boss.
boss_index = ""
for key_elem in labyrinth_map.keys():
    if labyrinth_map[key_elem] == "boss":
        boss_index = key_elem
    
#qui inizia il gioco: fintanto che il personaggio non e' giunto
#nella stanza del boss, continua a esplorare
while (current_room != boss_index):
    
    #bisogna innanzitutto costruire il circuito
    qc = QuantumCircuit(phi, left_room, right_room, treasure_seen, oracle_q, bit)
    
    #adesso dobbiamo inizializzare il circuito con le informazioni
    #che abbiamo a disposizione
    
    #come prima cosa, metto nello stato di ugual sovrapposizione phi
    qc.h(phi)

    #poi devo inizializzare il qubit dell'oracolo, oracle_q, nello stato |->
    initialize_oracle_q(qc)

    #poi devo inizializzare i qubit che descrivono il contenuto
    #della stanza sinistra e della stanza destra. I concetti di "sinistra" e "destra"
    #sono difficili da formalizzare, pertanto assumiamo cio' che segue:
    #se il giocatore si trova nella stanza xx, la stanza a sinistra corrispondera'
    #alla stanza yx, dove y e' l'opposto di x. Se il giocatore si trova
    #nella stanza xx, la stanza a destra corrispondera' alla stanza xy,
    #dove y e' l'opposto di x. La nozione di opposto e' da intendersi come
    #opposto(0)=1 e opposto(1)=0 (cvd).
    #Ergo, per sapere cosa c'e' a destra e a sinistra del giocatore
    #mi servono solo due cose:
    #1) la stanza in cui si trova il giocatore adesso
    #2) la mappa del labirinto
    #occhio che la mappa del gioco e' conosciuta dal GIOCO, non dal GIOCATORE.
    #Questo sa solo le stanze che gli stanno adiacenti

    initialize_left_right(qc, current_room, labyrinth_map, room_types_dict)

    #dobbiamo ora inizializzare il qubit che dice se il giocatore ha esplorato
    #la treasure room. Il bit relativo a questa informazione, che e' poi cio'
    #su cui ci basiamo per l'inizializzazione di questo qubit, viene aggiornato
    #dopo che il giocatore si e' spostato sulla mappa. Di fatto questo metodo applica 
    #semplicemente una porta x a questo qubit se la stanza del tesoro e' gia'
    #stata vista
    initialize_treasure_seen()

    qc.barrier()



    #perfetto, adesso la logica vera e propria del labirinto. Lo scopo del
    #nostro giocatore e' passare prima per la treasure room e poi andare
    #subito dal boss.

    #se non ho visto il tesoro e ce l'ho di fianco, ci vado
    qc.x(phi)
    qc.x(left_room)
    qc.x(treasure_seen)
    qc.mcx([phi[0], left_room[0], left_room[1], treasure_seen[0]], oracle_q[0])
    qc.x(treasure_seen)
    qc.x(left_room)
    qc.x(phi)

    qc.barrier()

    qc.x(right_room)
    qc.x(treasure_seen)
    qc.mcx([phi[0], right_room[0], right_room[1], treasure_seen[0]], oracle_q)
    qc.x(treasure_seen)
    qc.x(right_room)

    qc.barrier()
    qc.barrier()

    #se non ho visto il tesoro e non ce l'ho di fianco, sconfiggo i nemici

    qc.x(phi)
    qc.x(left_room[0])
    qc.x(treasure_seen)
    qc.mcx([phi[0], left_room[0], left_room[1], right_room[0], right_room[1],
            treasure_seen[0]], oracle_q)
    qc.x(treasure_seen)
    qc.x(left_room[0])
    qc.x(phi)

    qc.barrier()

    qc.x(right_room[0])
    qc.x(treasure_seen)
    qc.mcx([phi[0], left_room[0], left_room[1], right_room[0], right_room[1],
            treasure_seen[0]], oracle_q)
    qc.x(treasure_seen)
    qc.x(right_room[0])

    qc.barrier()
    qc.barrier()

    #se ho visto il tesoro e ho il boss di fianco, vado dal boss
    qc.x(phi)
    qc.mcx([phi[0], left_room[0], left_room[1], treasure_seen[0]], oracle_q)
    qc.x(phi)

    qc.barrier()

    qc.mcx([phi[0], right_room[0], right_room[1], treasure_seen[0]], oracle_q)

    qc.barrier()
    qc.barrier()

    #come ultima cosa effettuo la rotazione rispetto a |phi>
    diffuser(qc)

    #poi associo il primo qubit al bit classico per la misurazione
    qc.measure(phi, bit)

    
    #aggiungo il circuito all'array di circuiti
    qc_list.append(qc)



    #ora che ho costruito il circuito, posso misurare. Dovrei ripete questa operazione
    #per un tot di volte, ma quante esattamente? sqrt(2), che quindi mi porta
    #a una sola esecuzione. Dunque passo alla simulazione su computer classico

    simulator = Aer.get_backend('qasm_simulator')
    result = execute(qc, backend = simulator).result()
    counts = result.get_counts(qc)


    #aggiungo i counts di questa esecuzione all'array di counts
    counts_list.append(counts)


    #prendo il movimento che il personaggio ha deciso di eseguire
    movement_chosen = choice_quantum_movement()

    #in base a dove ha deciso di muoversi (0 = cambio il primo qubit,
    #1 = cambio il secondo qubit), modifico il valore della stanza corrente

    print("REMEMBER: Current room = " + current_room)
    update_current_room(movement_chosen)
    print("Direction chosen = " + movement_chosen)
    print("New current room = " + current_room)
    print("New map configuration = " + str(labyrinth_map))

print("Boss reached")


qc_list[0].draw('mpl')

plot_histogram(counts_list[0])

qc_list[1].draw('mpl')

plot_histogram(counts_list[1])

qc_list[2].draw('mpl')

plot_histogram(counts_list[2])