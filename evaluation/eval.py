import argparse
import itertools
import json
import logging
from logging import config

import numpy as np

import synthetic
from sharetrace import propagation, search, util

logging.config.dictConfig(util.logging_config())


class LogExposuresRiskPropagation(propagation.RiskPropagation):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self) -> np.ndarray:
        results = super().run()
        self.logger.info(json.dumps({'ExposureScores': results.tolist()}))
        return results


def parse():
    parser = argparse.ArgumentParser(
        description='''
            EXPERIMENTS

                Experiments 1 - 5: Evaluate contact search over a range of 
                processors and users.
                
                Experiments 6 - 8: Evaluate risk propagation over a range of 
                processors and users with a different backend implementation.
                
                Experiments 9 – 13: Evaluate risk propagation over a wider 
                range of users with a fixed number of processors. The 
                computed exposure scores are also logged.

                Abbreviations
                    CS:  contact search
                    RP:  risk propagation (implementation)
                    P:   number of processes
                    U:   number of users
                    S:   step size

                1: CS               P = 1 – 4   U = 100 – 2.9K    S = 100
                2: CS               P = 1 – 4   U = 3K – 5.4K     S = 100
                3: CS               P = 1 – 4   U = 5.5K – 7.4K   S = 100
                4: CS               P = 1 – 4   U = 7.5K – 8.9K   S = 100
                5: CS               P = 1 – 4   U = 9K – 10K      S = 100
                6: RP (serial)      P = 1       U = 100 – 1K      S = 100
                7: RP (lewicki)     P = 1 – 4   U = 100 – 1K      S = 100
                8: RP (ray)         P = 1 – 4   U = 100 – 1K      S = 100
                9: RP (ray)         P = 4       U = 100 – 2.9K    S = 100
                10: RP (ray)        P = 4       U = 3K – 5.4K     S = 100
                11: RP (ray)        P = 4       U = 5.5K – 7.4K   S = 100
                12: RP (ray)        P = 4       U = 7.5K – 8.9K   S = 100
                13: RP (ray)        P = 4       U = 9K – 10K      S = 100
            ''',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('experiment', type=int)
    return parser.parse_args()


def exp1():
    contact_search(100, 3000)


def exp2():
    contact_search(3000, 5500)


def exp3():
    contact_search(5500, 7500)


def exp4():
    contact_search(7500, 9000)


def exp5():
    contact_search(9000, 10100)


def contact_search(start: int, stop: int, step: int = 100):
    logger = get_logger('contact-search', start, stop)
    histories = synthetic.load_histories()
    for w, n in itertools.product(range(1, 5), range(start, stop, step)):
        cs = search.KdTreeContactSearch(logger=logger, min_dur=900, workers=w)
        contacts = cs.search(histories[:n])
        synthetic.save_contacts(contacts, n)


def exp6():
    exp678(timeout=0.001, impl='serial', start=1, stop=2)


def exp7():
    exp678(timeout=3, impl='lewicki', start=1, stop=5)


def exp8():
    exp678(timeout=3, impl='ray', start=1, stop=5)


def exp678(timeout: float, impl: str, start: int, stop: int):
    scores = synthetic.load_scores()
    logger = logging.getLogger(f'risk-propagation:{impl}')
    for n, p in itertools.product(range(100, 1100, 100), range(start, stop)):
        contacts = synthetic.load_contacts(n)
        rp = propagation.RiskPropagation(
            timeout=timeout, parts=p, logger=logger)
        rp.setup(scores[:n], contacts)
        rp.run()


def exp9():
    exp9_13(100, 3000)


def exp10():
    exp9_13(3000, 5500)


def exp11():
    exp9_13(5500, 7500)


def exp12():
    exp9_13(7500, 9000)


def exp13():
    exp9_13(9000, 10100)


def exp9_13(start: int, stop: int, step: int = 100):
    scores = synthetic.load_scores()
    logger = get_logger('risk-propagation', start, stop)
    for n, t in itertools.product(range(start, stop, step), range(1, 11)):
        contacts = synthetic.load_contacts(n)
        rp = LogExposuresRiskPropagation(
            tol=round(t / 10, 1), timeout=3, logger=logger)
        rp.setup(scores[:n], contacts)
        rp.run()


def get_logger(algorithm: str, start: int, stop: int):
    return logging.getLogger(f'{algorithm}:{start}-{stop - 100}')


def main():
    eval(f'exp{parse().experiment}()')


if __name__ == '__main__':
    main()
