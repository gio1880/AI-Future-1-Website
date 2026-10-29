ROBOT DATA - every run saved automatically
============================================

FOR STUDENTS
  1. Open the "AI Future 1" folder in VS Code. The run saver starts by itself
     (Terminal panel, tab "Robot data: auto-save runs" says "Robot data saver is ON").
  2. Run your program like always: Pybricks: Compile and Start Program.
  3. A few seconds after the run ends you see "Saved: Run 1 ..." in that terminal.
  4. Open dashboard.html (this folder) in your browser. It refreshes by itself.
     Or in VS Code: Terminal > Run Task... > "Robot data: open dashboard".

  Name your runs: start("Run 1") in your run file. Same name = easy to compare tries.
  To throw away a bad run, delete its CSV file in runs\ (it disappears from the dashboard).

WHAT IS IN THIS FOLDER
  runs\*.csv              one file per run, one row per move (open in Excel / Google Sheets)
  runs\runs.json          list of runs (name, time, battery, how it ended)
  dashboard.html          the dashboard - rebuilt after every new run, do not edit
  dashboard_template.html the dashboard's design and tuning tips (edit this one)
  collect_runs.py         the saver
  inbox\                  paste output from code.pybricks.com into a .txt file here; it gets saved too

COLUMNS - see "LOG NOTES" at the bottom of robot_master.py.

FIRST TIME ON A COMPUTER
  - Python 3 must be installed and the "python" command must work in a terminal.
  - VS Code asks once whether this folder may run automatic tasks: choose Allow
    (or Command Palette > "Tasks: Manage Automatic Tasks" > Allow).
  - Nothing to install: collect_runs.py uses only standard Python.

HOW IT WORKS (coaches)
  VS Code keeps a copy of the "Pybricks" output panel in its log folder
  (%APPDATA%\Code\logs\...\*-Pybricks.log). collect_runs.py reads those copies, finds the
  LOG_NAME / LOG,step,... header / LOG,... rows / LOG_END lines that robot_master.py prints,
  and writes one CSV per run. It never connects to the robot, so it cannot get in the way of
  the Pybricks extension. Runs that end without LOG_END (stopped with the button, an error,
  or a run file that never calls finish()) are saved too, with that status.
  VS Code deletes old log folders after a while, so runs are saved as soon as they happen -
  keep the saver running while testing.
