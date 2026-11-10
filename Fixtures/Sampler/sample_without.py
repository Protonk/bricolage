"""Public sampleWithout entry point; selection and records belong to the sampler."""
import sys

from sampler import main


if __name__ == '__main__':
    sys.exit(main(without=True))
