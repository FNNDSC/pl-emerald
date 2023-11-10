#!/usr/bin/env python

from pathlib import Path
from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter

from chris_plugin import chris_plugin, PathMapper, curry_name_mapper

from emerald import DISPLAY_TITLE
from emerald.emerald import emerald
from emerald.model import Unet
from skimage.morphology import square, disk, cube


__AVAILABLE_FUNCTIONS = [square, disk, cube]
"""Functions which (might) get called by eval."""


parser = ArgumentParser(description='Fetal brain masking',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-p', '--pattern', type=str, default='**/*.nii',
                    help='Input files pattern')
parser.add_argument('-s', '--output-suffix', type=str, default='_mask.nii',
                    help='Output file suffix')
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
    min_gpu_limit=0              # set min_gpu_limit=1 to enable GPU
)
def main(options: Namespace, inputdir: Path, outputdir: Path):
    print(DISPLAY_TITLE, flush=True)

    model = Unet()
    footprint = eval(options.dilation_footprint)

    mapper = PathMapper.file_mapper(inputdir, outputdir,
                                    glob=options.pattern, name_mapper=curry_name_mapper('{}_mask.nii'))
    for input_file, output_file in mapper:
        emerald(model, input_file, output_file, options.post_processing, footprint)


if __name__ == '__main__':
    main()
