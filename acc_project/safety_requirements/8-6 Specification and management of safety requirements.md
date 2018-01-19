# 6. Specification and management of safety requirements

## 6.4.1.1 Specification of SR
The specification for each requirement consists of:
- natural language
- formal notation for requirement specification
  - recommended for ASIL-ABCD
- semi-formal notation
  - recommended for ASIL-AB
  - highly recommended for ASIL-CD
- informal notation
  - highly recommended for ASIL-AB
  - recommended for ASIL-CD

## 6.4.2.1 SR are different form FR
Safety must be easily distinguishable from other requirements.

## 6.4.2.2 ASIL assignment
ASIL assignment is transitive with respect to inheritance of SR (and safety goals)

## 6.4.2.3 SR are allocated to and item or element

## 6.4.2.4 SR properties:
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

### 6.4.3.3 SR must be verified
It must be verified that SR complies with this clause

### 6.4.3.4 SR must be in the configuration management
Configuration management is described in 8-7

## 6.5 Work products:
- Safety plan (refined) of the above text
