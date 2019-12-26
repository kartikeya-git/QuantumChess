import unreal_engine as ue

from qiskit import execute, QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info.operators import Operator
from qiskit.quantum_info import process_fidelity
from qiskit.providers.aer import QasmSimulator
from qiskit.providers.aer.noise import NoiseModel, errors

from qiskit.tools.visualization import plot_histogram

from qiskit import Aer, execute
import numpy as np
from qiskit.visualization import plot_histogram

from qiskit.extensions.simulator import Snapshot
from qiskit.extensions.simulator.snapshot import snapshot

simulator = Aer.get_backend('qasm_simulator')
# Define the simulation method
backend_opts_mps = {'method': 'matrix_product_state'}  


sqrt2i = 1/(np.sqrt(2))

iswap_op = Operator([[1, 0, 0, 0],
                     [0, 0, 1j, 0],
                     [0, 1j, 0, 0],
                     [0, 0, 0, 1]])

sqrt_iswap_op = Operator([[1, 0, 0, 0],
                     [0, sqrt2i, sqrt2i*1j, 0],
                     [0, sqrt2i*1j, sqrt2i, 0],
                     [0, 0, 0, 1]])

sqrt_iswap_adj_op = Operator([[1, 0, 0, 0],
                     [0, sqrt2i, -sqrt2i*1j, 0],
                     [0, -sqrt2i*1j, sqrt2i, 0],
                     [0, 0, 0, 1]])

U_slide = Operator([[1, 0, 0, 0, 0, 0, 0, 0], 
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1]])


def full_measure(num_of_shots = 10000):
    
    circ.measure(qr, cr)

    result = execute(circ, simulator, backend_options=backend_opts_mps, shots = num_of_shots).result()
    counts = result.get_counts(circ)
    return counts


def get_prob(n_shots=90):
    counts = full_measure(num_of_shots=n_shots)
    L = []
    for bit, shots in counts.items():
        x = [bit, shots]
        L.append(x)

    P = []
    for qubit in range(65):
        s = 0
        for i in L:
            bit, shots = i[0], i[1]
            bit_num = int(bit[-(qubit + 1)])
            if (bit_num == 1):
                s += shots
        P.append(str(s / n_shots))
    return P


def measurement(qubit):
    circ.measure(qr[qubit], cr[qubit])
    
    result = execute(circ, simulator, backend_options=backend_opts_mps, shots = 1).result()
    es_counts = result.get_counts(circ)   
    
    state = list(es_counts.keys())[0]
    bit_num = int(state[-(qubit+1)])

    circ.reset(qr[qubit])
    if bit_num == 1:
        circ.x(qr[qubit])

    sup = superposition_dict[str(qubit)]
    for i in sup:
        bn = int(state[-(int(i) + 1)])
        circ.reset(qr[int(i)])
        if bn:
            circ.x(qr[int(i)])
    superposition_dict[str(qubit)].clear()
    
    ent = entanglement_dict[str(qubit)]
    for i in ent:
        bit_num = int(state[-(i+1)])
        circ.reset(qr[i])
        if bit_num == 1:
            circ.x(qr[i])
            
        supe = superposition_dict[str(i)]
        for j in supe:
            bn_ = int(state[-(int(j) + 1)])
            circ.reset(qr[int(j)])
            if bn_:
                circ.x(qr[int(j)])
        superposition_dict[str(i)].clear()
    entanglement_dict[str(qubit)].clear()
    
    
    
    return bit_num, state

def standard_move(s,t):
    
    #circ.swap(s, t)
    circ.unitary(iswap_op, [s, t], label='iswap')



def quantum_move(s,t):
    
    circ.unitary(sqrt_iswap_op, [s, t], label='sqrt_iswap') 
    
    source = superposition_dict[str(s)]
    if t not in source:
        superposition_dict[str(s)].append(t)
    target = superposition_dict[str(t)]
    if s not in target:
        superposition_dict[str(t)].append(s)
    merged = list(set(superposition_dict[str(s)]) | set(superposition_dict[str(t)]))

    superposition_dict[str(s)] = merged
    superposition_dict[str(t)] = merged
     
    return superposition_dict

def toff(a,b,c):
    
    circ.h(c)
    circ.cx(b,c)
    circ.tdg(c)
    circ.cx(a,c)
    circ.t(c)
    circ.cx(b,c)
    circ.tdg(c)
    circ.cx(a,c)
    circ.t(b)
    circ.t(c)
    circ.h(c)
    circ.cx(a,b)
    circ.t(a)
    circ.tdg(b)
    circ.cx(a,b)

def slide(s,t,P, ancilla = 64):
    circ.reset(ancilla)
    circ.x(ancilla)
    for i in P:
        circ.cx(i, ancilla)
    
    circ.cx(t, s)
    #circ.ccx(ancilla, s, t)
    toff(ancilla, s, t)
    circ.cx(t, s)

    circ.reset(ancilla)
    circ.x(ancilla)
    
    if len(P)!= 0:
        source = superposition_dict[str(s)]
        if t not in source:
            superposition_dict[str(s)].append(t)
        target = superposition_dict[str(t)]
        if s not in target:
            superposition_dict[str(t)].append(s)
        merged = list(set(superposition_dict[str(s)]) | set(superposition_dict[str(t)]))

        superposition_dict[str(s)] = merged
        superposition_dict[str(t)] = merged
    

        for i in P:
            source = entanglement_dict[str(s)]
            if i not in source:
                entanglement_dict[str(s)].append(i)
            target = entanglement_dict[str(t)]
            if i not in target:
                entanglement_dict[str(t)].append(i)
            mergedq = list(set(entanglement_dict[str(s)]) | set(entanglement_dict[str(t)]))

            entanglement_dict[str(s)] = mergedq
            entanglement_dict[str(t)] = mergedq  


num_qubits = 65
qr = QuantumRegister(num_qubits)
cr = ClassicalRegister(num_qubits)
circ = QuantumCircuit(qr, cr)


list_with_keys = [str(i) for i in range(num_qubits)]
list_with_values = [[] for i in range(num_qubits)]
superposition_dict = dict(zip(list_with_keys, list_with_values))

list_with_qubits = [str(i) for i in range(num_qubits)]
list_with_qvalues = [[] for i in range(num_qubits)]
entanglement_dict = dict(zip(list_with_qubits, list_with_qvalues))


for i in range(16):
    circ.x(qr[i])
for i in range(48, 65):
    circ.x(qr[i])


class QBoard:

    def begin_play(self):
        self.actor = self.uobject.get_owner()
        self.obstacles = []


    def normal_move(self):

        standard_move(int(self.actor.Source), int(self.actor.Target))

    def slide_move(self):

        #ue.print_string(self.actor.P)

        self.obstacles = []
        for i in (self.actor.P):
            self.obstacles.append(int(i))

        slide(int(self.actor.Source), int(self.actor.Target), self.obstacles)

    def quantumm_move(self):

        quantum_move(self.actor.Source, self.actor.Target)

    def get_probability(self):
        
        #ue.print_string(get_prob())

        return get_prob()#n_shots=self.actor.Shots)

    def measure(self):
        return measurement(self.actor.Measure)

    def reset_qubit(self):
        qubit = self.actor.ResetQubit
        circ.reset(qr[qubit])
        '''ent = entanglement_dict[str(qubit)]
        for j in ent:
            bn = int(state[-(int(j) + 1)])
            circ.reset(qr[int(j)])
            if bn:
                circ.x(qr[int(j)])'''

    def reset_qubit1(self):
        circ.reset(qr[self.actor.ResetQubit])
        circ.x(qr[self.actor.ResetQubit])

    def arrange(self):
        for i in range(num_qubits):
            circ.reset(i)
        list_with_keys = [str(i) for i in range(num_qubits)]
        list_with_values = [[] for i in range(num_qubits)]
        entanglement_dict = dict(zip(list_with_keys, list_with_values))
        for i in range(16):
            circ.x(qr[i])
        for i in range(48, 65):
            circ.x(qr[i])


        