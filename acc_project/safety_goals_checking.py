"""
Safety goal related checking
"""
import re

from acc_project.scripts.asil import Asil


def get_safety_goals(in_md_file='project/3-7.5.2 Safety goals.md'):
    SGS = {}
    SG = {}
    SG_name_regex = re.compile(r'###\s+(.+):\s+(.+)')
    SG_asil_regex = re.compile(r'ASIL:\s+(.+)')
    for line in open(in_md_file):
        m = SG_name_regex.match(line)
        if m is not None:
            if 'id' in SG:
                # Found new one
                SG = {}
            SG['id'] = m.group(1)
            SG['name'] = m.group(2)
            SGS[SG['id']] = SG
        m = SG_asil_regex.match(line)
        if m is not None:
            SG['asil'] = Asil(m.group(1))
    return SGS


if __name__ == '__main__':
    sgs = get_safety_goals()
    print(sgs)
