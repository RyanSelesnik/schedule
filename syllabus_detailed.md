# Detailed Course Syllabus

## ELEC70028 - Predictive Control

### Schedule
- **Monday** 16:00-17:00: Lecture
- **Thursday** 15:00-16:00: Lecture
- **Lab**: One session (choose Mon or Fri 09:00-11:00)

### Topic Breakdown by Week

| Week | Dates | Topics | Assignment Focus |
|------|-------|--------|------------------|
| 1 | 19-25 Jan | ODEs, Numerical Integration | Basic Part 1 |
| 2 | 26 Jan-1 Feb | Quadrature, Linear Systems | Basic Part 1 & 2 |
| 3 | 2-8 Feb | Nonlinear optimization (fmincon) | Basic Part 2, Core 1 |
| 4 | 9-15 Feb | Gantry Crane Model | Core Part 1 |
| 5 | 16-22 Feb | LQ-RHC without constraints | Core Part 1 |
| 6 | 23 Feb-1 Mar | LQ-RHC with constraints | Core Part 1 & 2 |
| 7 | 2-8 Mar | Nonlinear OCP | Core Part 2 |
| 8 | 9-15 Mar | Advanced MPC topics | Core Part 2 |
| 9 | 16-20 Mar | **Oral Examination** | Exam prep |

### Key Concepts to Master
1. **Differential Equations (ODEs)**
   - Solving ODEs numerically
   - Initial value problems

2. **Numerical Methods**
   - Integration/Quadrature techniques
   - Systems of linear equations (Ax = b)
   - MATLAB implementations

3. **Optimization**
   - `fmincon` usage in MATLAB
   - Constraint handling
   - Objective function formulation

4. **Model Predictive Control**
   - Gantry Crane dynamics
   - Receding Horizon Control (RHC)
   - Linear Quadratic (LQ) formulation
   - Constraint satisfaction
   - Nonlinear Optimal Control Problems

### MATLAB Grader Tips
- Submit early for feedback
- Basic: First submission counts (5 attempts)
- Core: Last submission counts (20 attempts)
- Test code locally before submitting

---

## ELEC70082 - Distributed Optimisation and Learning

### Schedule
- **Tuesday** 11:00-12:00: Class (EEE 508)
- **Thursday** 09:00-11:00: Lecture (EEE 508)

### Topic Breakdown by Week

| Week | Dates | Part | Topics | Assessment |
|------|-------|------|--------|------------|
| 1 | 20-26 Jan | I | Inference and learning | PS1 |
| 2 | 27 Jan-2 Feb | I | Deterministic optimization | PS1 due 29 Jan |
| 3 | 3-9 Feb | II | Stochastic optimization, Parallel GD | PS2 |
| 4 | 10-16 Feb | II | Distributed GD, Federated learning | PS2 due 12 Feb |
| 5 | 17-23 Feb | - | **MID-TERM EXAM** (Parts I & II) | Exam 17 Feb |
| 6 | 24 Feb-2 Mar | III | Graph theory | PS3 due 26 Feb |
| 7 | 3-9 Mar | III | Averaging over graphs | PS3 |
| 8 | 10-16 Mar | III | Primal optimization algorithms | PS4 due 12 Mar |
| 9 | 17-23 Mar | III | Primal-dual algorithms | Paper Study |
| 10 | 24-30 Mar | IV | Advanced: RL, Asynchrony, Privacy | Paper due 26 Mar |

### Part I: Foundations
- Statistical inference basics
- Machine learning fundamentals
- Deterministic optimization
- Stochastic optimization
- Gradient descent variants

### Part II: Distributed Learning with Fusion Center
- Parallel gradient descent
- Distributed gradient descent
- Communication efficiency
- Federated learning principles
- Privacy considerations in federated settings

### Part III: Decentralized Learning
- **Graph Theory**
  - Graph representations
  - Adjacency matrices
  - Laplacian matrices
- **Consensus Algorithms**
  - Averaging over graphs
  - Convergence analysis
- **Optimization Algorithms**
  - Primal methods
  - Primal-dual methods
  - Convergence guarantees

### Part IV: Advanced Concepts
- Reinforcement learning basics
- Asynchronous updates
- Privacy-preserving methods
- Multitask learning (if time permits)

### Paper Study Guidelines (20%)
- Choose a recent paper relevant to module topics
- 2-page report format
- Required sections:
  1. Key contribution identification
  2. Limitations analysis
  3. Numerical results reproduction

---

## ELEC70073 - Computer Vision and Pattern Recognition

### Schedule
- **Friday** 14:00-16:00: Main Lecture (406/407)

### Topic Breakdown

| Week | Dates | Section | Topics |
|------|-------|---------|--------|
| 1 | 23-29 Jan | PR | Introduction to Pattern Recognition |
| 2 | 30 Jan-5 Feb | PR | Statistical classifiers |
| 3 | 6-12 Feb | PR | Feature extraction & selection |
| 4 | 9-15 Feb | PR | Neural networks basics |
| 5 | 16-22 Feb | PR | Advanced PR topics | CW due 12 Feb |
| 6 | 23 Feb-1 Mar | CV | Introduction to Computer Vision |
| 7 | 2-8 Mar | CV | Image processing fundamentals |
| 8 | 9-15 Mar | CV | Object detection & recognition |
| 9 | 16-22 Mar | CV | Deep learning for CV | Test 13 Mar |
| 10 | 23-29 Mar | CV | Advanced CV topics | CW due 18 Mar |

### Pattern Recognition (Weeks 1-5)
1. **Statistical Pattern Recognition**
   - Bayesian decision theory
   - Discriminant functions
   - Parameter estimation

2. **Classifiers**
   - Linear classifiers
   - k-Nearest Neighbors
   - Support Vector Machines
   - Decision trees

3. **Feature Engineering**
   - Feature extraction
   - Dimensionality reduction (PCA, LDA)
   - Feature selection methods

4. **Neural Networks**
   - Perceptrons
   - Multi-layer networks
   - Backpropagation
   - Activation functions

### Computer Vision (Weeks 6-10)
1. **Image Fundamentals**
   - Image representation
   - Color spaces
   - Filtering operations

2. **Feature Detection**
   - Edge detection
   - Corner detection
   - SIFT, SURF, ORB

3. **Object Recognition**
   - Template matching
   - Bag of visual words
   - CNN-based approaches

4. **Deep Learning for CV**
   - Convolutional Neural Networks
   - Popular architectures (VGG, ResNet)
   - Transfer learning

### Coursework Notes
- Done in pairs - find partner early!
- PR Coursework: Due 12 Feb 16:00
- CV Coursework: Due 18 Mar 16:00

---

## ELEC70066 - Applied Advanced Optimisation

### Schedule
- **Friday** 11:00-13:00: Lecture (flipped classroom)

### Class Format (Flipped Classroom)
1. **Before class**: Watch video lectures at home
2. **In class**:
   - iRAT: Individual multiple-choice test (5 mins)
   - Group problems: Collaborative work (ungraded)
   - Discussion: Solutions review (~1 hour)
   - tRAT: Team test (30 mins)

### Topic Breakdown by Week

| Week | Dates | Topics | Pre-class Video |
|------|-------|--------|-----------------|
| 1 | 23-29 Jan | Introduction to optimization | Video 1 |
| 2 | 30 Jan-5 Feb | Unconstrained optimization | Video 2 |
| 3 | 6-12 Feb | Gradient methods | Video 3 |
| 4 | 13-19 Feb | Constrained optimization | Video 4 |
| 5 | 20-26 Feb | KKT conditions | Video 5 |
| 6 | 27 Feb-5 Mar | Duality theory | Video 6 |
| 7 | 6-12 Mar | Interior point methods | Video 7 |
| 8 | 13-19 Mar | Applications | Video 8 |

### Key Topics
1. **Unconstrained Optimization**
   - Gradient descent
   - Newton's method
   - Quasi-Newton methods
   - Line search strategies

2. **Constrained Optimization**
   - Equality constraints
   - Inequality constraints
   - Lagrangian formulation

3. **Optimality Conditions**
   - First-order conditions
   - Second-order conditions
   - KKT conditions

4. **Duality**
   - Lagrange duality
   - Weak and strong duality
   - Dual problems

5. **Algorithms**
   - Interior point methods
   - Active set methods
   - Sequential Quadratic Programming

### Assessment Strategy
- **iRAT (5%)**: Easy marks - just watch videos!
- **tRAT (20%)**: Work well with your team
- **Peer Assessment (10%)**: Participate actively in groups
- **Final Exam (65%)**: Focus here for main grade impact

### Tips for Success
- ALWAYS watch videos before Friday class
- Take notes during videos for iRAT
- Participate actively in group discussions
- Practice problems from group work for exam prep
