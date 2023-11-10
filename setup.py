from setuptools import setup
import re

_version_re = re.compile(r"(?<=^__version__ = (\"|'))(.+)(?=\"|')")


def get_version(rel_path: str) -> str:
    """
    Searches for the ``__version__ = `` line in a source code file.
    https://packaging.python.org/en/latest/guides/single-sourcing-package-version/
    """
    with open(rel_path, 'r') as f:
        matches = map(_version_re.search, f)
        filtered = filter(lambda m: m is not None, matches)
        version = next(filtered, None)
        if version is None:
            raise RuntimeError(f'Could not find __version__ in {rel_path}')
        return version.group(0)


setup(
    name='emerald',
    version=get_version('emerald/__init__.py'),
    description='Fetal brain masking using u-net',
    author='FNNDSC',
    author_email='dev@babyMRI.org',
    url='https://github.com/FNNDSC/pl-emerald',
    packages=['emerald'],
    license='MIT',
    install_requires=['chris_plugin'],
    package_data={
        'emerald': ['json_models/*', 'weights/*']
    },
    entry_points={
        'console_scripts': [
            'emerald = emerald.__main__:main'
        ]
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Medical Science Apps.'
    ]
)
