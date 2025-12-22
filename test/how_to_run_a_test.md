# How to Run Tests

This guide explains how to run the generated SAT solver tests.

## Running a Specific Test
The solver always reads the problem from `initial_cnf.txt` in the root directory. To run a test from the `test/` folder, you must first copy it to the root.


1. **Copy the test input:**
   ```powershell
   copy "test\input_cnf_test_*.cnf" "initial_cnf.txt"
   ```

2. **Run the Solver:**
   ```powershell
   python dpll_solver.py
   ```

3. **Check Output:**
   The solver will print `SATISFIABLE` or `UNSATISFIABLE`.

## Batch Execution
If you want to run all tests sequentially, you can use a loop in PowerShell:

```powershell
dir test\input_cnf_test_*.cnf | ForEach-Object {
    $name = $_.Name
    Write-Host "Running $name..."
    copy "test\$name" "initial_cnf.txt"
    python dpll_solver.py
    Write-Host "--------------------------------"
}
```