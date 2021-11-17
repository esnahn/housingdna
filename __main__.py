import sys
from .cli import main

return_code = 1  # Catchall for general errors
try:
    main()
    return_code = 0
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
sys.exit(return_code)
