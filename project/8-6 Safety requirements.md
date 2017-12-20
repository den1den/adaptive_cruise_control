# 6. Specification and management of safety requirements

### 6.4.1.1
__Safety requirements__

Consists of an appropriate combination of:
a) natural language
b) Any of:
  - Informal notations (++, ++, +, +)
  - Semi-formal notations (+, +, ++, ++)
  - Formal notations (+, +, +, +)

### 6.4.2.1
Safety requirements and requirements must be separately managed

### 6.4.2.2
ASIL is transitive

### 6.4.2.3
Safety requirements are allocated to an item or an element 

### 6.4.2.4 SR properties:
- unambiguous
- comprehensive
- atomic (w.r.t. the granularity)
- internally consistent (w.r.t. itself)
- feasible
- verifiable

> Note: missing attributes are: measurable, testable, time-bound.
> Note: verification comes into play at 6.4.3.2

### 6.4.2.5 SR additional attributes:
- static ID
- status: (proposed, assumed, agrees, reviewed)
- ASIL

## 6.4.3 Management of safety requirements
### 6.4.3.1 Structure
The collection of SR must be:
- hierarchical (concept, technical, SW/HW)
- organizational structure
- complete w.r.t. hierarchy (all children represent their parent)
- external consistency (no requirement can contradict another)
- no duplication of information (at any level)
- maintainable (requirements may not be static)

### 6.4.3.2 SR traceability
SR should be traceable to each:
- upper level
- vise versa: every SR derived form this
- specification on how they are verified:
    - including impact analysis
    - including assessment of functional safety (?)

### 6.4.3.3 SR must comply with Clause 6
### 6.4.3.3 SR must comply with Clause 7

## 6.5 Work products:
- Safety plan (refined) of the above text
