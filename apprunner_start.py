"""
AWS App Runner startup script for the Currency Converter A2A Agent
"""

import os
import sys

# Ensure we're using the correct Python path
if __name__ == "__main__":
    # Set default port for App Runner
    port = int(os.environ.get("PORT", "8000"))
    os.environ["A2A_PORT"] = str(port)
    os.environ["A2A_HOST"] = "0.0.0.0"
    
    # Import and run the server
    from a2a_server import main
    main()
