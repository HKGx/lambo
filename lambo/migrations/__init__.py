from lambo.databasy.migrate import main as _main
from functools import partial

main = partial(_main, __file__)

if __name__ == "__main__":
    main()
