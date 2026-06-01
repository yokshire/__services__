# Quantum Algorithm Catalog

This catalog is demo guidance for Quantum Bridge. It helps the API identify where a project computation session might be migrated to a quantum algorithm family. It is not a claim that current hardware will accelerate the workload.

## Included Algorithm Families

| Algorithm family | Where it can speed up computation | Practical note |
| --- | --- | --- |
| Grover search | Repeated candidate checks for unstructured search can become quadratic in oracle calls. | Requires a reversible oracle and deep enough circuits for useful scale. |
| Quantum amplitude estimation | Monte Carlo-style probability, expectation, risk, and integration workloads can reduce sampling complexity under oracle assumptions. | State preparation and payoff oracles are the hard part. |
| Shor factoring/discrete log | Period-finding gives polynomial-time factoring and discrete logarithm algorithms. | Real cryptographic sizes need fault-tolerant quantum computers. |
| HHL linear systems | Sparse, well-conditioned systems can produce a quantum solution state efficiently under strict assumptions. | Advantage is strongest when only observables of the solution are needed. |
| Hamiltonian simulation | Quantum dynamics and many-body systems map naturally to quantum hardware. | Near-term runs are usually small or hybrid; high precision needs better hardware. |
| Quantum phase estimation | Eigenphase and spectral estimation acts as a core subroutine for other algorithms. | Precision requires controlled unitaries and long coherent circuits. |
| VQE | Hybrid ground-state and Hamiltonian expectation workflows for chemistry/materials demos. | Heuristic; broad production speedup is not guaranteed. |
| QAOA | Combinatorial optimization encoded as cost Hamiltonians. | Heuristic; useful as an exploratory migration candidate. |
| Quantum annealing | QUBO/Ising binary optimization on specialized hardware. | Provider-specific and not a gate-model replacement. |

## How The Demo Advisor Uses This

The advisor receives project computation sessions as JSON. It scores sessions against problem tags and text signals, then returns:

- recommended quantum algorithm candidates
- what part of the computation would be replaced
- which migration tool shape should be used, such as `hybrid-qaoa-loop` or `sampler-estimator-wrapper`
- possible quantum hardware platforms
- which API key or cloud credential the service should ask the user to provide

## References

- Shor, "Algorithms for Quantum Computation: Discrete Logarithms and Factoring": https://math.mit.edu/~shor/papers/algsfqc-dlf.pdf
- Grover, "A Fast Quantum Mechanical Algorithm for Database Search": https://arxiv.org/abs/quant-ph/9605043
- Brassard, Hoyer, Mosca, Tapp, "Quantum Amplitude Amplification and Estimation": https://arxiv.org/abs/quant-ph/0005055
- Harrow, Hassidim, Lloyd, "Quantum Algorithm for Linear Systems of Equations": https://arxiv.org/abs/0811.3171
- Childs, Kothari, Somma, "Quantum linear systems algorithm: a primer": https://arxiv.org/abs/1802.08227
- Lloyd, "Universal Quantum Simulators": https://pubmed.ncbi.nlm.nih.gov/8688088/
- Feynman, "Simulating physics with computers": https://philpapers.org/rec/FEYSPW
- Peruzzo et al., "A variational eigenvalue solver on a photonic quantum processor": https://www.nature.com/articles/ncomms5213
- Farhi, Goldstone, Gutmann, "A Quantum Approximate Optimization Algorithm": https://arxiv.org/abs/1411.4028
