# How to Run Tests

This guide explains how to run the generated SAT solver tests.

## Option 1: Run Direct Test

You can run any test case directly by passing the Test ID to the solver script.

Example to run Test 11:

```powershell
python dpll_solver.py 11
```

This will automatically:
1.  Copy `test/initial_state_test_11.txt` -> `initial_state.txt`
2.  Copy `test/bcp_output_11.txt` -> `bcp_output.txt`
3.  Run the solver.

Available tests: `01` to `11`, plus custom tests `90`, `91`, `92`, `93`, `99`.

## Option 2: Manual Execution

If you prefer to copy files manually without any scripts:

1.  **Copy the initial state:**
    ```powershell
    copy "test\initial_state_test_11.txt" "initial_state.txt"
    ```

2.  **Copy the BCP output (mock):**
    ```powershell
    copy "test\bcp_output_11.txt" "bcp_output.txt"
    ```

3.  **Run the Solver:**
    ```powershell
    python dpll_solver.py
    ```
