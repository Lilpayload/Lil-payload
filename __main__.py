import os
import sys
import logging

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
logging.basicConfig(level=logging.DEBUG)
from modern_dashboard import main

if __name__ == '__main__':
    main()