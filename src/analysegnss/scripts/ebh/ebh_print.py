from rich import print as rprint
from logging import Logger


def print_ebh_ok(logger: Logger, pnt_analysis: dict, source: str) -> tuple[str, str]:
    """Print message for when all EBH lines meet quality criteria.

    Args:
        logger (Logger): Logger instance
        pvt_qanalysis (dict): Dictionary of PVT quality analysis
        source (str): Source of the solution (RTK or PPK)
    """
    msg_ebh_decision = f"[SUCCESS] {source} solution for all measured EBH lines meets the quality criteria. ASSUR EBH files -> OK.\n"
    logger.info(msg_ebh_decision)
    rprint(f"[bold green]{msg_ebh_decision}[/bold green]")

    # Format PNT quality analysis output
    formatted_pnt_analysis = []
    for line, quality_data in pnt_analysis.items():
        formatted_pnt_analysis.append(f"pnt quality line {line}:")
        formatted_pnt_analysis.append(f"{quality_data}\n")

    msg_pnt_analysis = "\n".join(formatted_pnt_analysis)
    logger.info(msg_pnt_analysis)
    # rprint(f"{msg_pnt_qanalysis}")

    return msg_ebh_decision, msg_pnt_analysis


def print_ebh_nok(
    logger: Logger,
    pnt_analysis: dict,
    rejected_lines: list,
    rejection_level: float,
    source: str,
) -> tuple[str, dict]:
    """Print message for when all EBH lines do not meet quality criteria.

    Args:
        logger (Logger): Logger instance
        pvt_qanalysis (dict): Dictionary of PVT quality analysis
        rejected_lines (list): List of rejected EBH lines
        rejection_level (float): The rejection threshold percentage
        source (str): Source of the solution (RTK or PPK)
    """
    # Message about the decision process
    msg_ebh_decision = f"[WARNING] {source} solution for the following {rejected_lines} measured EBH lines does NOT meet the quality criteria of {rejection_level}% fixed PNT points.\n"
    logger.warning(msg_ebh_decision)
    rprint(f"[bold yellow]{msg_ebh_decision}[/bold yellow]")

    # Format PNT quality analysis output
    formatted_pnt_analysis = []
    for line, quality_data in pnt_analysis.items():
        formatted_pnt_analysis.append(f"pnt quality line {line}:")
        formatted_pnt_analysis.append(f"{quality_data}\n")

    msg_pnt_analysis = "\n".join(formatted_pnt_analysis)
    logger.info(msg_pnt_analysis)

    return msg_ebh_decision, msg_pnt_analysis


def print_starting_ppk_process(
    logger: Logger, rejected_lines: list, ebh_timings: dict
) -> None:
    """Print message when starting PPK process.

    Args:
        logger (Logger): Logger instance
        rejected_lines (list): List of rejected EBH lines
        ebh_timings (dict): Dictionary of EBH timings
    """
    rprint(f"[yellow]Starting PPK process for all EBH lines.[/yellow]\n")
    logger.warning(
        f"RTK solution for the following ebh lines {rejected_lines} is not of sufficient quality. "
        f"Recalculating these lines in PPK mode with timings {ebh_timings}"
    )
