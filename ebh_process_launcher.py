#! /usr/bin/env python



def ebh_process_launcher(argv: list) -> None:
    """Launches the appropiate functions to calculate the ebh_lines from the sbf_ifn file
    from which it retrievers the correct timings, 
    decides whether the RTK or PPK solution has a sufficient quality, 
    and finally outputs correct ASSUR formatted files for each ebh line.
    
    Args: 
    argv (list): CLI arguments (check argument_parser.py for more info)
    
    """
    
    