import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collegestats24 import make_ipeds_names


def test_2023_names():
    folder, file = make_ipeds_names('2023')
    assert folder == 'IPEDS_2023-24_Provisional'
    assert file == 'IPEDS202324.accdb'


def test_1999_names():
    folder, file = make_ipeds_names('1999')
    assert folder == 'IPEDS_1999-00_Provisional'
    assert file == 'IPEDS199900.accdb'
