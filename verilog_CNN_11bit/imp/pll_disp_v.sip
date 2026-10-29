set_global_assignment -entity "pll_disp_v" -library "lib_pll_disp_v" -name IP_TOOL_NAME "altera_pll"
set_global_assignment -entity "pll_disp_v" -library "lib_pll_disp_v" -name IP_TOOL_VERSION "18.0"
set_global_assignment -entity "pll_disp_v" -library "lib_pll_disp_v" -name IP_TOOL_ENV "mwpim"
set_global_assignment -library "lib_pll_disp_v" -name SPD_FILE [file join $::quartus(sip_path) "pll_disp_v.spd"]

set_global_assignment -library "lib_pll_disp_v" -name MISC_FILE [file join $::quartus(sip_path) "pll_disp_v_sim/pll_disp_v.vo"]
