# Attack Vectors — 攻击线索库

This catalog is injected into the Red Team sub-agent's prompt based on the detected
language/framework. It primes the attacker with known vulnerability patterns that a
generic code reviewer might miss.

---

## Universal (All Languages)

### Null / Undefined / Empty Handling
- Accessing properties on potentially null/undefined values without guard
- Array/collection methods called on empty collections
- String operations on potentially empty strings
- Default parameter values that mask missing arguments
- Optional chaining missing where it could crash

### Error Handling & Propagation
- Swallowed exceptions (empty catch blocks, `catch(e) {}`)
- Error messages leaking sensitive information (stack traces, internal paths)
- Missing error boundaries in UI components
- Async errors not propagated to error handling middleware
- `try-catch` around `await` without handling rejection reason

### Race Conditions & Concurrency
- Read-modify-write cycles without locking
- Shared mutable state accessed from multiple async contexts
- Timer/setTimeout cleanup missing in teardown lifecycle
- Event listener registration without deregistration
- Promise.all with no error handling on individual promises

### Boundary Conditions
- Off-by-one in loops, array indices, slice ranges
- Integer overflow/underflow in arithmetic
- Division by zero (check denominator before division)
- Date/time boundary bugs (leap years, DST transitions, epoch edges)
- Maximum input length not enforced (DoS via giant payloads)

### State Management
- State updates that don't account for stale closures
- Derived state not recalculated when dependencies change
- Mutating state directly instead of using setter/dispatch
- Inconsistent state after partial update failure
- Default state that doesn't match all possible initial conditions

### Input Validation
- Trusting user input without sanitization
- Missing type checks on external data (API responses, URL params)
- Regex without timeout protection (ReDoS)
- File upload without size/type validation
- Form validation only on client side, not server

---

## JavaScript / TypeScript Specific

### React (JSX/TSX)
- `useEffect` missing dependencies in dependency array
- `useEffect` without cleanup function for subscriptions/timers
- `useCallback`/`useMemo` missing dependencies → stale closures
- `key` prop using array index → incorrect reconciliation
- Conditional hook calls (hooks must be called unconditionally)
- `setState` called on unmounted component
- `dangerouslySetInnerHTML` with unsanitized input
- Component re-rendering on every frame due to inline object/function props
- Missing `key` on list items
- Context value object recreated on every render

### Async / Promise
- `async` function without `.catch()` on the returned promise
- `Promise.all` with mixed sync/async resolution → waterfall instead of parallel
- `await` inside loop → serial execution when parallel was possible
- Fire-and-forget promises with no error handling
- `Promise.race` used for timeout without cleanup of the losing promise
- `setTimeout(fn, 0)` used as a hack instead of proper async handling

### TypeScript
- `any` type used to bypass type checking
- Type assertions (`as`) that narrow incorrectly
- `!` non-null assertion without runtime guarantee
- Discriminated union exhaustive check missing a variant
- Generic type parameter unbounded → accepts unexpected types
- `Record<string, T>` where keys should be constrained

### Security
- `eval()`, `new Function()`, or `setTimeout(string)` with dynamic input
- `innerHTML` / `outerHTML` / `insertAdjacentHTML` with unsanitized data
- `document.write()` — completely banned
- `JSON.parse()` without try-catch on untrusted input
- Prototype pollution via `Object.assign` or spread on user-controlled objects
- `postMessage` without origin checking
- localStorage/sessionStorage for sensitive data (tokens, passwords)
- Hardcoded API keys, tokens, or secrets in source code
- `target="_blank"` without `rel="noopener noreferrer"`

### Performance
- O(n²) nested loops on large datasets
- Array methods chaining that creates intermediate arrays (`.filter().map()` → `.reduce()`)
- Missing `React.memo` / `useMemo` on expensive computations
- Large bundle due to non-tree-shakeable imports (`import * as lib`)
- Debounce/throttle missing on rapid-fire event handlers (scroll, resize, input)
- Memory leak: event listeners, intervals, subscriptions not cleaned up

---

## Python Specific

- Mutable default arguments (`def fn(lst=[])`)
- Bare `except:` catching too broadly (including KeyboardInterrupt)
- `try-except-pass` swallowing all errors silently
- `os.system()` or `subprocess` with shell=True and untrusted input
- `pickle` deserializing untrusted data (arbitrary code execution)
- `eval()` / `exec()` with user input
- File operations without context manager (`with open()`)
- `is` used for equality comparison (`a is 5` vs `a == 5`)
- Global variable mutation inside functions
- List/dict comprehension with side effects

---

## CSS / Style

- `z-index` wars (arbitrary large values like `z-index: 99999`)
- `!important` used to override specificity instead of fixing selector
- Fixed `width`/`height` breaking responsive layout
- Missing `overflow: hidden` when using `border-radius` with children
- `position: absolute` without a positioned parent
- Animations/transitions on properties that trigger layout (use `transform` + `opacity`)
- Missing `will-change` or `contain` for performance-critical animations
- Hardcoded pixel values where relative units should be used

---

## General Architecture Smells

- Circular dependencies between modules
- God object / component (too many responsibilities)
- Prop drilling through more than 3 levels
- Business logic inside UI components
- Duplicated logic across files (DRY violation)
- Magic numbers / strings without named constants
- Comments that explain "what" when the code already says it
- Comments that explain "why" but are outdated/don't match the code
