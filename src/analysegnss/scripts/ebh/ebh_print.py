from rich import print as rprint
from logging import Logger


def print_ebh_ok(logger: Logger, pvt_qanalysis: dict, source: str) -> tuple[str, str]:
    """Print message for when all EBH lines meet quality criteria.
    
    Args:
        logger (Logger): Logger instance
        pvt_qanalysis (dict): Dictionary of PVT quality analysis
        source (str): Source of the solution (RTK or PPK)
    """
    msg_ebh_decision = f"[SUCCESS] Solution for all measured EBH lines meets the quality criteria. ASSUR EBH files -> OK. ({source} RESULTS).\n"
    logger.info(msg_ebh_decision)
    rprint(f"[green]{msg_ebh_decision}[/green]")
    
    msg_pvt_qanalysis = f"PVT quality analysis: {pvt_qanalysis}\n"
    logger.info(msg_pvt_qanalysis)
    #rprint(f"{msg_pvt_qanalysis}")
    
    return msg_ebh_decision, msg_pvt_qanalysis

def print_ebh_nok(logger: Logger, pvt_qanalysis: dict, rejected_lines: list, rejection_level: float, source: str) -> tuple[str, str]:
    """Print message for when all EBH lines do not meet quality criteria.
    
    Args:
        logger (Logger): Logger instance
        pvt_qanalysis (dict): Dictionary of PVT quality analysis
        rejected_lines (list): List of rejected EBH lines
        rejection_level (float): The rejection threshold percentage
        source (str): Source of the solution (RTK or PPK)
    """
    if len(rejected_lines) == 1:
        msg_ebh_decision = f"[WARNING] The measured EBH line {rejected_lines[0]} does NOT meet the quality criteria of {rejection_level}% fixed PNT points. ({source} RESULTS)\n"
        logger.warning(msg_ebh_decision)
        rprint(f"[bold yellow]{msg_ebh_decision}[/bold yellow]")
        
        msg_pvt_qanalysis = f"PVT quality analysis: {pvt_qanalysis}\n"
        logger.info(msg_pvt_qanalysis)
        #rprint(f"{msg_pvt_qanalysis}")
    else:
        msg_ebh_decision = f"[WARNING] All measured EBH lines do NOT meet the quality criteria of {rejection_level}% fixed PNT points. ({source} RESULTS)\n"
        logger.warning(msg_ebh_decision)
        rprint(f"[bold yellow]{msg_ebh_decision}[/bold yellow]")

        msg_pvt_qanalysis = f"PVT quality analysis: {pvt_qanalysis}\n"
        logger.info(msg_pvt_qanalysis)
        #rprint(f"{msg_pvt_qanalysis}")

    return msg_ebh_decision, msg_pvt_qanalysis

def print_starting_ppk_process(logger: Logger, rejected_lines: list, ebh_timings: dict) -> None:
    """Print message when starting PPK process.
    
    Args:
        logger (Logger): Logger instance
        rejected_lines (list): List of rejected EBH lines
        ebh_timings (dict): Dictionary of EBH timings
    """
    if len(rejected_lines) == 1:
        rprint(f"[yellow]Starting PPK process for rejected EBH line {rejected_lines[0]}.[/yellow]\n")
        logger.warning(
            f"Solution for the ebh line {rejected_lines[0]} is not of sufficient quality. "
            f"Calculating this single line in PPK mode with timings {ebh_timings[rejected_lines[0]]}"
        )
    else:
        rprint(f"[yellow]Starting PPK process for all EBH lines.[/yellow]\n")
        logger.warning(
            f"PNT solution for all ebh lines {rejected_lines} are not of sufficient quality. "
            f"Recalculating these lines in PPK mode with timings {ebh_timings}"
        ) 
        