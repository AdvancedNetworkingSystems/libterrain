import sys
from distutils.core import setup

if sys.argv[-1] == 'setup.py':
    print("To install, run 'python setup.py install'\n")


def get_install_requires():
    """
    parse requirements.txt, ignore links, exclude comments
    """
    requirements = []
    for line in open('requirements.txt').readlines():
        # skip to next iteration if comment or empty line
        if line.startswith('#') or line == '' or line.startswith('http') or line.startswith('git'):
            continue
        # add line to requirements
        requirements.append(line.replace('\n', ''))
    return requirements


setup(
    name='libterrain',
    version='0.1dev',
    packages=['libterrain',],
    license='MIT',
    long_description=open('README.txt').read(),
    author='Gabriel Gemmi',
    author_email="gabriele.gemmi@studenti.unitn.it",
    install_requires=get_install_requires()
)
