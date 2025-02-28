from rich import print as rprint
from logging import Logger

def print_ebh_ok(logger: Logger, source: str) -> None:
    """Print message for when all EBH lines meet quality criteria.
    
    Args:
        logger (Logger): Logger instance
        source (str): Source of the solution (RTK or PPK)
    """
    message = f"Solution for all EBH lines meet the quality criteria.[green] ASSUR EBH files -> OK. ({source} RESULTS).[/green]"
    logger.info(message)
    rprint(f"\n{message}\n")


def print_ebh_nok(logger: Logger, rejected_lines: list, rejection_level: float, source: str) -> None:
    """Print message for when all EBH lines do not meet quality criteria.
    
    Args:
        logger (Logger): Logger instance
        rejected_lines (list): List of rejected EBH lines
        rejection_level (float): The rejection threshold percentage
        source (str): Source of the solution (RTK or PPK)
    """
    if len(rejected_lines) == 1:
        message = f"[bold red]The EBH line {rejected_lines[0]} does NOT meet[/bold red] the EBH rejection value of {rejection_level}% fixed PNT points. ({source} RESULTS)"
        logger.warning(message)
        rprint(f"\n{message}\n")
    else:
        message = f"[bold red]ALL EBH lines do NOT meet[/bold red] the EBH rejection value of {rejection_level}% fixed PNT points. ({source} RESULTS)"
        logger.warning(message)
        rprint(f"\n{message}\n")

def print_starting_ppk_process(logger: Logger, rejected_lines: list, ebh_timings: dict) -> None:
    """Print message when starting PPK process.
    
    Args:
        logger (Logger): Logger instance
        rejected_lines (list): List of rejected EBH lines
        ebh_timings (dict): Dictionary of EBH timings
    """
    if len(rejected_lines) == 1:
        rprint(f"[yellow]Starting PPK process for rejected EBH line {rejected_lines[0]}.[/yellow]")
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