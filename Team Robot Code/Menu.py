from pybricks.tools import hub_menu
from pybricks.parameters import Button, Color
from robot_base import hub   # shared hub — only ONE PrimeHub ever created

# Official Pybricks docs pattern: menu does not create its own PrimeHub.
# hub is imported from robot_base so there is never a double-init conflict.

selected = hub_menu("1","2","3","4","5","6","D")
hub.system.set_stop_button(Button.CENTER)

hub.light.on(Color.RED)

if selected == "1":
    import Run_A_updated
elif selected == "2":
    import Run_B
elif selected == "3":
    import Run_E
elif selected == "4":
    import Run_C
elif selected == "5":
    import Run_D
elif selected == "6":
    import Run_G
elif selected == "7":
    import Run_F
# elif selected == "8":
#     import Run_Bb
elif selected == "D":
    import diagnostics
