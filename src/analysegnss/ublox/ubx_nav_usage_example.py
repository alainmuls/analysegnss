# Assuming the UBX_NAV_PVT class is in analysegnss.ublox.ubx_nav_pvt
# from analysegnss.ublox.ubx_nav_pvt import UBX_NAV_PVT
from pyubx2 import UBXReader
from pyubx2.ubxreader import (  # Import specific error types and constants
    UBXParseError,
    UBXStreamError,
    ERR_LOG,
    ERR_RAISE,
    ERR_IGNORE,
)
import logging

# # --- This is a placeholder for the actual class location ---
# # Make sure the UBX_NAV_PVT class definition from above is accessible
# # For example, if it's in ubx_nav_pvt.py in the same directory:
from analysegnss.ublox.ubx_nav_pvt import (
    UBX_NAV_PVT,
)  # Assuming the file is named ubx_nav_pvt.py and in the same directory for this example

# # --- End placeholder ---


if __name__ == "__main__":
    # Basic logging setup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    # Path to your UBX file
    ubx_file_path = "./data/ublox/20250426_132532.ubx"  # IMPORTANT: Replace with your actual file path or a test file

    # Initialize the NAV-PVT handler
    # This will create/overwrite the CSV file
    nav_pvt_handler = UBX_NAV_PVT(fn_nav_pvt="./nav_pvt_data.csv")

    try:
        print(f"Opening UBX file: {ubx_file_path}")
        with open(ubx_file_path, "rb") as stream:
            # Configure UBXReader error handling:
            # Option 1: ERR_LOG (default) - pyubx2 logs errors and tries to continue.
            #           Your `except` block won't catch these recoverable errors.
            # error_mode = ERR_LOG

            # Option 2: ERR_IGNORE - pyubx2 ignores errors silently and tries to continue.
            #           Your `except` block won't catch these.
            # error_mode = ERR_IGNORE

            # Option 3: ERR_RAISE - pyubx2 raises an exception on error.
            #           Your `except` block WILL catch these. The loop will likely stop.
            error_mode = ERR_RAISE  # Let's use this to demonstrate your try-except

            print(f"Using UBXReader with error_mode: {error_mode}")
            ubr = UBXReader(stream, quitonerror=error_mode)

            for raw_data, parsed_message in ubr:
                # This check is important, especially if error_mode is ERR_LOG or ERR_IGNORE,
                # as parsed_message could be None after a skipped error.
                if parsed_message and parsed_message.identity == "NAV-PVT":
                    # print(f"Found NAV-PVT: {parsed_message.iTOW}") # For quick check
                    nav_pvt_handler.decode_pvt(parsed_message)
                elif parsed_message:
                    # Optionally, log other message types if interested
                    # print(f"Other message: {parsed_message.identity}")
                    pass

        print(
            f"Finished processing. NAV-PVT data saved to {nav_pvt_handler.fn_nav_pvt}"
        )
    except FileNotFoundError:
        print(f"Error: UBX file not found at {ubx_file_path}")
    except (UBXParseError, UBXStreamError) as e:
        print(f"A UBX parsing/stream error occurred: {e}")
        print("This error was caught because UBXReader was set to ERR_RAISE.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # Explicitly close the handler (which closes the CSV file)
        nav_pvt_handler.close()
