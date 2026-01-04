"""
SLA Advisor Agent - Main entry point.

Console chat interface for support ticket analysis.
"""

import re
import sys
from agent import SLAAdvisorAgent


def print_header():
    """Print the program header."""
    print()
    print("=" * 50)
    print("        SLA ADVISOR AGENT")
    print("   Support Ticket Elemzo Rendszer")
    print("=" * 50)
    print()
    print("Ird be a support ticket szoveget.")
    print("Opcionálisan add meg az ugyfél IP cimet is.")
    print("Format: <ticket szoveg> IP: <ip_cim>")
    print()
    print("Pelda: A szamlamon dupla terheles van! IP: 8.8.8.8")
    print()
    print("Kilepes: 'kilepes' vagy 'exit'")
    print("-" * 50)
    print()


def parse_input(user_input: str) -> tuple[str, str | None]:
    """
    Parse user input and separate ticket text from IP address.

    Returns:
        (ticket_text, ip_address) tuple
    """
    # Search for IP address in the text
    ip_pattern = r'IP:\s*(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    match = re.search(ip_pattern, user_input, re.IGNORECASE)

    if match:
        ip_address = match.group(1)
        # Remove IP part from ticket text
        ticket_text = re.sub(ip_pattern, '', user_input, flags=re.IGNORECASE).strip()
        return ticket_text, ip_address
    else:
        return user_input.strip(), None


def print_separator():
    """Print section separator."""
    print()
    print("-" * 50)
    print()


def main():
    """Main program - chat loop."""
    print_header()

    # Agent initialization
    try:
        agent = SLAAdvisorAgent()
        print("[OK] Agent sikeresen inicializálva.")
        print()
    except Exception as e:
        print(f"[HIBA] Nem sikerült inicializálni az agentet: {e}")
        print("Ellenőrizd az OPENAI_API_KEY környezeti változót!")
        sys.exit(1)

    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input("Te: ").strip()

            # Empty input
            if not user_input:
                continue

            # Exit
            if user_input.lower() in ['exit', 'quit', 'kilepes', 'kilépés', 'q']:
                print()
                print("Viszlát! A program leállt.")
                print()
                break

            # Help
            if user_input.lower() in ['help', 'segitseg', 'segítség', '?']:
                print()
                print("Használat:")
                print("  - Írd be a support ticket szövegét")
                print("  - Opcionálisan add hozzá: IP: <ip_cim>")
                print("  - Példa: Nem tudok belépni IP: 84.0.64.1")
                print()
                continue

            # Process input
            ticket_text, ip_address = parse_input(user_input)

            if not ticket_text:
                print("Kérlek adj meg egy ticket szöveget!")
                continue

            # Analysis
            print()
            print("Elemzes folyamatban...")
            print()

            result = agent.analyze(ticket_text, ip_address)

            # Display result
            print_separator()
            print(result)
            print_separator()

        except KeyboardInterrupt:
            print()
            print()
            print("Program megszakítva.")
            break
        except Exception as e:
            print(f"[HIBA] {e}")
            print()


if __name__ == "__main__":
    main()
