> Fictional document created for ProposalBench.

# Final Report: Oakhaven Provost's Seed Grant (2025–2026)

**Project Title:** Spectral Bounds for Bounded-Delay Consensus
**Principal Investigator:** Dr. Elias V. Thorne
**Funding Agency:** Oakhaven University Provost's Office
**Award Amount:** $45,000
**Performance Period:** 1 January 2025 to 31 August 2026
**Date of Report:** 5 September 2026

## 1. Executive Summary

This seed project investigated the mathematical foundations of consensus algorithms in distributed systems subject to communication delays. The primary objective was to establish rigorous convergence guarantees using spectral graph theory. Over the 20-month performance period, the project successfully proved convergence for bounded-delay consensus on fixed connected graphs under explicitly stated spectral assumptions. We also explored extensions to adversarial environments and sensor-fault inference, laying the theoretical groundwork for future large-scale federal grant applications.

## 2. Mathematical Framework and Main Results

### 2.1. Convergence on Fixed Connected Graphs

The core achievement of this grant is a published theorem demonstrating that continuous-time consensus algorithms converge even when communication between nodes is subject to a bounded delay, provided the underlying network topology possesses specific spectral properties.

Let $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ be a fixed, undirected, connected graph with $N$ nodes and unit edge weights $a_{ij} \in \{0, 1\}$. Let $L$ be the standard symmetric Laplacian matrix of $\mathcal{G}$, with eigenvalues $0 = \lambda_1 < \lambda_2 \le \dots \le \lambda_N = \lambda_{max}$. We analyzed the delayed consensus protocol with coupling rate $\kappa > 0$:

$\dot{x}_i(t) = \kappa \sum_{j \in \mathcal{N}_i} a_{ij} (x_j(t - \tau) - x_i(t - \tau))$

where $\tau$ is the uniform communication delay, and initial histories are continuous functions on $[-\tau, 0]$.

**Theorem 1 (Thorne, 2025):** The system achieves asymptotic consensus for any admissible initial history if the coupling rate, delay, and maximum eigenvalue satisfy $\kappa \tau \lambda_{max} < \pi/2$.

The proof, detailed in our 2025 *Journal of Theoretical Distributed Systems* paper, utilizes frequency-domain analysis and the Nyquist criterion for the corresponding symmetric delayed Laplacian system. For a typical network with $\lambda_{max} \le 10$ and $\kappa = 0.1$ s$^{-1}$, this guarantees convergence for delays up to $\tau \le 1.5$ seconds.

### 2.2. The Adversarial-Node Extension (Conjecture)

A secondary objective was to extend Theorem 1 to networks containing Byzantine (adversarial) nodes that intentionally broadcast incorrect state values to disrupt consensus. We assume an adversary that can compromise up to $F$ nodes, which can send arbitrary, conflicting messages to their neighbors, but cannot spoof identities or delay messages beyond $\tau$.

**Conjecture 3.1 (Internal Working Paper, 12 August 2026):** Let $\mathcal{G}$ be a $(2F+1)$-robust graph. Under the resilient update rule where each normal node $i$ sorts the received delayed values $x_j(t-\tau)$ from its neighbors, discards the highest $F$ and lowest $F$ values, and applies the standard consensus protocol to the remaining values, the normal nodes achieve approximate agreement (their states converge to a common value within the convex hull of the initial normal states) provided $\kappa \tau \lambda_{max}(\mathcal{G}_{reduced}) < \pi/2$, where $\mathcal{G}_{reduced}$ is any graph formed by removing $F$ incoming edges per node.

Because the non-linear nature of the resilient update rules (discarding extreme values) breaks the symmetry of the Laplacian matrix, this adversarial-node extension remains a conjecture. It is not a published theorem. The standard Lyapunov-Krasovskii approach failed to yield a negative semi-definite derivative along the system trajectories when local filtering was applied. Resolving this conjecture requires entirely new proof techniques, likely involving non-smooth analysis and differential inclusions.

## 3. Preliminary Work: Sensor-Fault Inference

In the final six months of the seed grant, we pivoted to investigate how spectral methods might apply to inference under faulty or sparse sensing in distributed autonomous systems. This represents a mathematical stretch from our core consensus work.

We modeled the sensor network as a discrete-time linear dynamical system $x(k+1) = Ax(k)$ with measurements $y(k) = Cx(k) + f(k)$ under zero process and measurement noise. The adversarial fault vector $f(k)$ is restricted to an unknown but fixed set of at most $s$ compromised sensor channels over an observation horizon of $T$ steps. We analyzed the $T$-step observability operator $\mathcal{O}_T(A, C)$. We established a preliminary bound: if the system satisfies $2s$-sparse observability (meaning $\mathcal{O}_T(A, C_{\setminus K})$ has full column rank for any subset $K$ of $2s$ sensors removed from $C$), then the initial state $x(0)$ and the non-zero injected faults $f(k)$ on the $s$ compromised channels can be uniquely recovered. State estimation is maintained as a corollary of this successful fault isolation.

To validate these mathematical limits, we have planned a comprehensive simulation framework using Python and ROS2 (Robot Operating System). It is important to note that we have no existing robot lab or physical testbed. All validation of the sensor-fault inference theory is restricted to planned simulation. A manuscript detailing these preliminary sensor bounds was submitted in July 2026 and is currently under review.

## 4. Educational Integration and Assessment

As part of the seed grant's educational mandate, I developed and taught a new graduate seminar in Spring 2026: *CSAM 510: Proof-Based Learning in Distributed Systems*. 

The course enrolled 18 students. The pedagogical goal was to integrate formal mathematical proofs directly into the computer science curriculum, moving away from purely empirical algorithm testing. Students were required to construct formal proofs for consensus convergence as their final projects.

**Assessment Limitations:** While we collected qualitative end-of-semester surveys (which were highly positive, with 15 of 18 students reporting increased confidence in mathematical reasoning), no causal learning gain was estimated. We did not employ a control group, pre-test/post-test methodology, or validated concept inventories. Future educational plans must incorporate rigorous, distinct assessment mechanisms to measure actual learning outcomes rather than just student satisfaction.

## 5. Budget Summary

The $45,000 budget was fully expended. Major categories included:
*   Summer salary for the PI (1 month): $11,500
*   Graduate Research Assistant (partial support, 2 semesters): $24,000
*   Travel to conferences (Pacific Symposium): $3,500
*   Publication fees and computational resources: $6,000
