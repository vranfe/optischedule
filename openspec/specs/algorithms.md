# Algorithmic Foundations and Mathematical Formulations: OptiSchedule UMB

## 1. Overview of Algorithmic Architectures

OptiSchedule UMB orchestrates two distinct optimization engines and an independent quality auditor:
1. **Macro Institutional Timetabler (`app/optimization/constraint_solver.py`):** An Integer Programming / Constraint Satisfaction Problem (CSP) solver built on **Google OR-Tools CP-SAT**. It constructs the master university schedule across groups, professors, classrooms, and time slots under strict institutional hard constraints and multi-objective soft preferences.
2. **Institutional Solution Auditor (`app/optimization/evaluator.py`):** An independent multicriteria evaluator that computes an objective quality index (0.0% to 100.0%) across five normalized operational dimensions ($S_{\text{pref}}, S_{\text{gap}}, S_{\text{load}}, S_{\text{room}}, S_{\text{dist}}$).
3. **Micro Student Enrollment Optimizer (`app/optimization/student_optimizer.py`):** A custom combinatorial search engine classified formally as **Backtracking with Temporal Consistency Pruning (Forward Checking) and Value-Ordering Heuristic**. It solves the personalized schedule generation for individual students according to credit limits, shift preferences, gap minimizations, and free day distributions.

---

## 2. Macro Institutional Solver (Google OR-Tools CP-SAT)

### 2.1. Decision Variables

Let:
- $G$ be the set of academic groups, indexed by $g \in G$.
- $T$ be the set of faculty teachers, indexed by $t \in T$.
- $R$ be the set of physical classrooms/laboratories, indexed by $r \in R$.
- $D$ be the set of academic days (Monday through Saturday), indexed by $d \in D$.
- $S$ be the set of 2-hour daily time slots, indexed by $s \in S$.

The model instantiates binary decision variables:
$$x_{g,t,r,d,s} \in \{0, 1\}$$
where $x_{g,t,r,d,s} = 1$ if and only if group $g$ is assigned to teacher $t$ in room $r$ on day $d$ during time slot $s$.

### 2.2. Domain Reduction and Candidate Pre-Pruning

To avoid state-space explosion, the variable domain is pruned *a priori* before model building:
1. **Academic Knowledge Area Filtering:**
   Teacher $t$ is only a candidate for group $g$ if:
   $$\text{Area}(t) = \text{Area}(\text{Subject}(g))$$
   Fallback occurs only if no specialized teachers exist in that knowledge domain.
2. **Room Capacity Filtering:**
   Room $r$ is considered for group $g$ only if:
   $$\text{Capacity}(r) \ge \text{ExpectedStudents}(g)$$
   The top candidate rooms are rotated deterministically based on $g.\text{id} \pmod{|\text{ValidRooms}|}$ to balance infrastructure wear.
3. **Institutional Shift Alignment:**
   - Morning cohort ($G1$, `MAÑANA`): restricted to $s \in S_{\text{morning}}$ (06:00 - 12:00).
   - Afternoon cohort ($G2$, `TARDE`): restricted to $s \in S_{\text{afternoon}}$ (12:00 - 18:00).
   - Night cohort ($G3$, `NOCHE`): restricted to $s \in S_{\text{night}}$ (18:00 - 22:00) on weekdays, and $s \le s_{17:00}$ on Saturdays.
4. **Saturday Operational Boundary:**
   On Saturdays ($d = \text{SATURDAY}$), slots ending after 17:00 (5:00 PM) are excluded:
   $$x_{g,t,r,\text{SATURDAY},s} = 0 \quad \forall s \text{ with } \text{EndTime}(s) > 17:00$$
5. **Teacher Availability Matrix:**
   If teacher $t$ marked unavailability for $(d, s)$ in `TeacherAvailability`:
   $$x_{g,t,r,d,s} = 0$$

### 2.3. Hard Constraints (Feasibility Boundary)

A solution is feasible if and only if all of the following constraints are satisfied simultaneously:

1. **Required Hours per Group:**
   Each group $g$ requires a fixed number of 2-hour slots $K_g = \max(1, \lfloor \text{HoursPerWeek}(g) / 2 \rfloor)$:
   $$\sum_{t \in T} \sum_{r \in R} \sum_{d \in D} \sum_{s \in S} x_{g,t,r,d,s} = K_g \quad \forall g \in G$$

2. **Group Non-Collision:**
   A group cannot occupy more than one room or be taught by more than one teacher at the same time:
   $$\sum_{t \in T} \sum_{r \in R} x_{g,t,r,d,s} \le 1 \quad \forall g \in G, \forall d \in D, \forall s \in S$$

3. **Teacher Non-Collision:**
   A teacher cannot teach multiple groups simultaneously:
   $$\sum_{g \in G} \sum_{r \in R} x_{g,t,r,d,s} \le 1 \quad \forall t \in T, \forall d \in D, \forall s \in S$$

4. **Classroom Non-Collision:**
   A classroom cannot host multiple groups simultaneously:
   $$\sum_{g \in G} \sum_{t \in T} x_{g,t,r,d,s} \le 1 \quad \forall r \in R, \forall d \in D, \forall s \in S$$

5. **Academic Cohort Non-Collision Constraint:**
   Groups belonging to the same academic cohort $c$ within the same semester $sem$ cannot overlap in time, guaranteeing that regular students can enroll in all semester subjects without time conflicts:
   $$\sum_{g \in G_{(sem, c)}} \sum_{t \in T} \sum_{r \in R} x_{g,t,r,d,s} \le 1 \quad \forall (sem, c), \forall d \in D, \forall s \in S$$

6. **Teacher Contract Weekly Workload Capacity:**
   Total weekly teaching slots assigned to teacher $t$ cannot exceed their statutory contract ceiling $L(t)$:
   $$\sum_{g \in G} \sum_{r \in R} \sum_{d \in D} \sum_{s \in S} x_{g,t,r,d,s} \le \left\lfloor \frac{L(t)}{2} \right\rfloor \quad \forall t \in T$$
   where:
   $$L(t) = \begin{cases}
   42 \text{ hours} & \text{if } \text{Type}(t) = \text{FULL\_TIME} \\
   21 \text{ hours} & \text{if } \text{Type}(t) = \text{PART\_TIME} \\
   23 \text{ hours} & \text{if } \text{Type}(t) = \text{CATEDRA}
   \end{cases}$$

### 2.4. Multi-Objective Soft Function

The optimization objective balances teacher pedagogical affinity and salaried faculty workload fulfillment:
$$\max Z = \sum_{g,t,r,d,s} x_{g,t,r,d,s} \cdot \Big[ w_{\text{pref}} \cdot P(t, \text{Subject}(g)) + w_{\text{load}} \cdot \Omega(t) \Big]$$

Where:
- $P(t, \text{sub}) \in \{1, 2, 3, 4, 5\}$ is the teacher's preference score for subject $\text{sub}$.
- $\Omega(t) \in \{1, 2, 3\}$ is the contractual salary priority factor designed to prevent institutional underload (subcarga) for fixed-salary faculty:
  $$\Omega(t) = \begin{cases}
  3 & \text{if } \text{Type}(t) = \text{FULL\_TIME} \\
  2 & \text{if } \text{Type}(t) = \text{PART\_TIME} \\
  1 & \text{if } \text{Type}(t) = \text{CATEDRA}
  \end{cases}$$
- Optimization Profile Weights $(w_{\text{pref}}, w_{\text{load}})$:
  - **`balanced`**: $w_{\text{pref}} = \max(1, \lfloor 10 \cdot W_{\text{pref}}^{\text{cfg}} \rfloor) = 3$, $w_{\text{load}} = \max(1, \lfloor 10 \cdot W_{\text{load}}^{\text{cfg}} \rfloor) = 2$
  - **`preferences`**: $w_{\text{pref}} = 10, w_{\text{load}} = 1$
  - **`load_balance`**: $w_{\text{pref}} = 2, w_{\text{load}} = 12$
  - **`compact`**: $w_{\text{pref}} = 3, w_{\text{load}} = 3$

---

## 3. Institutional Quality Auditor (`Evaluator`)

The `Evaluator` class provides an objective audit of any schedule matrix. If any hard constraint violation occurs ($\text{violations} > 0$), the schedule is marked **`NO FACTIBLE`** and receives $\text{GlobalScore} = 0.0\%$.

When feasible ($\text{violations} = 0$), the global score is computed as the normalized weighted sum:
$$\text{GlobalScore} = \left( \sum_{i=1}^{5} \hat{w}_i \cdot S_i \right) \times 100\%$$
with normalized weights $\hat{w}_i = \frac{w_i}{\sum_{k=1}^5 w_k}$ derived from configuration defaults:
- $\hat{w}_{\text{pref}} = 0.35$ (Teacher Subject Affinity)
- $\hat{w}_{\text{gap}} = 0.25$ (Schedule Compactness)
- $\hat{w}_{\text{load}} = 0.20$ (Faculty Load Fulfillment)
- $\hat{w}_{\text{dist}} = 0.10$ (Harmonic Weekly Distribution)
- $\hat{w}_{\text{room}} = 0.10$ (Classroom Capacity Utilization)

### 3.1. Detailed Metric Formulations

1. **Teacher Affinity Score ($S_{\text{pref}} \in [0.0, 1.0]$):**
   $$S_{\text{pref}} = \min\left(1.0, \frac{\sum_{a \in A} P(t_a, \text{Subject}(g_a))}{5 \cdot |A|}\right)$$
   Measures the average pedagogical satisfaction of assigned faculty against the theoretical maximum (5 points).

2. **Schedule Compactness Score ($S_{\text{gap}} \in [0.2, 1.0]$):**
   For each teacher $t$ and each active day $d$, let $S_{t,d} = \text{sort}(\{s_1, s_2, \dots, s_k\})$. The idle gap count is:
   $$\text{Gaps}(t, d) = \sum_{j=1}^{k-1} \max\left(0, (s_{j+1} - s_j - 1)\right)$$
   $$S_{\text{gap}} = \max\left(0.2, 1.0 - \frac{\sum_{t,d} \text{Gaps}(t,d)}{2.0 \cdot N_{\text{teacher\_days}}}\right)$$

3. **Faculty Workload Saturation ($S_{\text{load}} \in [0.0, 1.0]$):**
   $$S_{\text{load}} = \frac{1}{|T|} \sum_{t \in T} \min\left(1.0, \frac{H_{\text{assigned}}(t)}{L(t)}\right)$$
   Measures institutional contract utilization efficiency, preventing idle salaried teaching capacity.

4. **Classroom Utilization Efficiency ($S_{\text{room}} \in [0.0, 1.0]$):**
   $$S_{\text{room}} = \min\left(1.0, \frac{\sum_{a \in A} \text{ExpectedStudents}(g_a)}{\sum_{a \in A} \text{Capacity}(r_a)}\right)$$
   Quantifies physical infrastructure efficiency, rewarding high occupancy relative to room capacity.

5. **Harmonic Weekly Distribution ($S_{\text{dist}} \in [0.5, 1.0]$):**
   Let $C_d$ be the total class sessions scheduled on day $d \in D$, with mean $\mu = \frac{1}{|D|} \sum_{d \in D} C_d$ and variance $\sigma^2 = \frac{1}{|D|} \sum_{d \in D} (C_d - \mu)^2$:
   $$S_{\text{dist}} = \max\left(0.5, 1.0 - \frac{\sigma^2}{\mu^2 + 10^{-5}}\right)$$
   Penalizes scheduling imbalances where certain days are overloaded while others remain deserted.

---

## 4. Student Enrollment Optimizer (`StudentScheduleOptimizer`)

### 4.1. Formal Algorithmic Classification

The student enrollment optimizer is formally classified as:
> **Backtracking with Temporal Consistency Pruning (CSP Forward Checking) and Value-Ordering Heuristic**

#### Clarification of Search Strategy Terminology:
- **Why it is NOT Branch-and-Bound:**
  Classic Branch-and-Bound maintains a global upper bound $UB$ (or lower bound for minimization) and dynamically bounds each subproblem: if $\text{Bound}(\text{node}) \le \text{BestSoFar}$, the branch is pruned. `StudentScheduleOptimizer` does not compute dynamic partial-schedule bounds; its branch pruning is purely **consistency-driven** (temporal non-overlap checks: $g_{\text{slots}} \cap \text{Occupied} = \emptyset$).
- **Why it is NOT global Best-First Search:**
  Standard Best-First Search maintains a global priority queue (frontier) of open nodes across the entire state tree. `StudentScheduleOptimizer` executes depth-first recursive backtracking. However, within each tree level, candidate groups are pre-sorted by a **greedy value-ordering heuristic** ($A(g)$). This ensures that the search descends first through branches matching the student's preferred shift.

### 4.2. Value-Ordering Heuristic ($A(g)$)

Before recursive expansion, candidate groups for subject $s$ are sorted descending by affinity score $A(g)$:
$$A(g) = \text{Score}_{\text{cohort}}(g) + \sum_{slot \in g} \text{Score}_{\text{slot}}(slot)$$

Where:
- **Cohort Naming Match ($\text{Score}_{\text{cohort}}$):**
  - If preferred shift is `NOCHE` and name contains `NOCHE` or `G3`: $+25$ points.
  - If preferred shift is `MAÑANA` and name contains `MAÑANA` or `G1`: $+25$ points.
  - If preferred shift is `TARDE` and name contains `TARDE` or `G2`: $+25$ points.
- **Slot Shift Match ($\text{Score}_{\text{slot}}$):**
  - $+5$ points for each slot matching the student's preferred shift.
  - **Saturday Night Cohort Accommodation:** Night students frequently take intensive Saturday daytime sessions. To prevent nocturnal students from rejecting Saturday classes, $+5$ points are awarded for Saturday slots in `NOCHE`/`G3` cohorts even if the slot time falls during daylight hours.

### 4.3. Consistency Pruning (Forward Checking)

At each depth level $k$ corresponding to subject $s_k$, candidate group $g$ is tested against already occupied slots $\text{Occupied}_{k-1}$:
$$\text{If } \Big(\text{Slots}(g) \cap \text{Occupied}_{k-1} \neq \emptyset\Big) \implies \textbf{Prune Branch (Skip)}$$

Because slot IDs are indexed as tuples $(\text{day}, \text{time\_slot\_id})$, set intersection executes in $O(1)$ amortized time.
Safety guardrails include a global iteration budget:
$$\text{Counter} > 8000 \lor |\text{FeasibleSolutions}| \ge 150 \implies \textbf{Terminate Search}$$

If zero combinations exist for all selected subjects, the algorithm automatically executes an autonomous recovery pass evaluating combinations for $N - 1$ subjects to guarantee students receive the best partial enrollment alternative.

### 4.4. Multicriteria Combination Scoring

Each feasible combination $C$ is ranked by a multi-objective utility function:
$$\text{Score}(C) = \Big( w_{\text{shift}} \cdot S_{\text{shift}} + w_{\text{gap}} \cdot S_{\text{gap}} + w_{\text{free}} \cdot S_{\text{free}} \Big) \cdot \Phi_{\text{comp}} \times 100\%$$

Subject to user-controlled zero-sum weights ($w_{\text{shift}} + w_{\text{gap}} + w_{\text{free}} = 1.0$):
1. **Shift Compatibility ($S_{\text{shift}}$):**
   $$S_{\text{shift}} = \frac{\text{Slots matching preferred shift}}{\text{Total slots in combination}}$$
2. **Schedule Gap Score ($S_{\text{gap}}$):**
   Let $G_{\text{total}}$ be the total unoccupied slots between the first and last class on each active day. Each 2-hour gap slot deducts 10%:
   $$S_{\text{gap}} = \max\left(0.0, 1.0 - 0.10 \cdot G_{\text{total}}\right)$$
3. **Free Days Score ($S_{\text{free}}$):**
   Free days $F = 6 - |\text{ActiveDays}|$. Evaluated against an institutional piecewise satisfaction curve:
   $$S_{\text{free}} = \begin{cases}
   0.00 & \text{if } F = 0 \text{ (classes all 6 days)} \\
   0.35 & \text{if } F = 1 \text{ (5 class days)} \\
   0.70 & \text{if } F = 2 \text{ (4 class days)} \\
   0.90 & \text{if } F = 3 \text{ (3 class days)} \\
   1.00 & \text{if } F \ge 4
   \end{cases}$$
4. **Completeness Penalty Factor ($\Phi_{\text{comp}}$):**
   $$\Phi_{\text{comp}} = \frac{|C|}{N_{\text{requested}}}$$
   Severely penalizes partial schedules where one or more subjects had to be dropped due to institutional bottlenecks.
