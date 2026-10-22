import multiprocessing

from whoop_mcp.cli import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
