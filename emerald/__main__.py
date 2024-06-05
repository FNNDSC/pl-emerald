#!/usr/bin/env python
import sys
from pathlib import Path
from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter
from typing import Optional, List, Tuple

from chris_plugin import chris_plugin, PathMapper, curry_name_mapper

from emerald import DISPLAY_TITLE
from emerald.emerald import emerald
from emerald.model import Unet
from skimage.morphology import square, disk, cube

import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__AVAILABLE_FUNCTIONS = [square, disk, cube]
"""Functions which (might) get called by eval."""


parser = ArgumentParser(description='Fetal brain masking',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-p', '--pattern', type=str, default='**/*.nii',
                    help='Input files pattern')
parser.add_argument('-m', '--mask-suffix', type=str, default='_mask.nii',
                    help='Mask output file suffix. Provide "" to not save mask.')
parser.add_argument('-o', '--outputs', type=str, default='',
                    help='Background intensity multiplier and output suffix.')
parser.add_argument('-w', '--weights', type=str, default='nancy', choices=['nancy', 'emerald'],
                    help='Which weights to use. ("nancy" is newer and better)')
parser.add_argument('--no-post-processing', dest='post_processing', action='store_false',
                    help='Predicted mask should not be post processed (morphological closing and defragmentation)')
parser.add_argument('--dilation-footprint', default='disk(2)', type=str,
                    help='Dilation footprint: either a Python expression or None.')


@chris_plugin(
    parser=parser,
    title='Fetal brain masking',
    category='MRI',
    min_memory_limit='2Gi',      # supported units: Mi, Gi
    min_cpu_limit='1000m',       # millicores, e.g. "1000m" = 1 CPU core
    min_gpu_limit=1,
    max_gpu_limit=1
)
def main(options: Namespace, inputdir: Path, outputdir: Path):
    print(DISPLAY_TITLE, flush=True)
    logger.info(f'using the "{options.weights}" weights')
    model = Unet(options.weights)
    footprint = eval(options.dilation_footprint)
    outputs = parse_outputs(options.outputs)

    mapper = PathMapper.file_mapper(inputdir, outputdir, glob=options.pattern)
    for input_file, output_file in mapper:
        mask_path = change_suffix(output_file, options.mask_suffix)
        brain_path = [(n, change_suffix(output_file, s)) for n, s in outputs]
        start = time.monotonic()
        emerald(model, input_file, mask_path, brain_path, options.post_processing, footprint)
        end = time.monotonic()
        elapsed = end - start
        logger.info(f'{input_file} -> {mask_path}, {[str(p) for _, p in brain_path]} (took {elapsed:.1f}s)')


def change_suffix(path: Path, suffix: Optional[str]) -> Optional[Path]:
    if not suffix:
        return None
    if '.' not in path.name:
        return path.with_name(path.name + suffix)
    name_part, _old_suffix = path.name.rsplit('.', maxsplit=1)
    return path.with_name(name_part + suffix)


def parse_outputs(val: str) -> List[Tuple[float, str]]:
    val = val.strip()
    if not val:
        return []
    try:
        return [parse_pair(p) for p in val.split(',')]
    except ValueError as e:
        print(e)
        sys.exit(1)


def parse_pair(val: str) -> Tuple[float, str]:
    num, suffix = val.split(':', maxsplit=1)
    return float(num), suffix


if __name__ == '__main__':
    main()
