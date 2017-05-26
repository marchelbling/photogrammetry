#!/usr/bin/python
#! -*- encoding: utf-8 -*-
#
# Adapted from https://github.com/openMVG/openMVG/issues/619#issuecomment-268356171
# Created by @FlachyJoe
# Edited by @petern3
#
#usage: MvgMvs_Pipeline.py [-h] [-f FIRST_STEP] [-l LAST_STEP] [--0 0 [0 ...]]
#                          [--1 1 [1 ...]] [--2 2 [2 ...]] [--3 3 [3 ...]]
#                          [--4 4 [4 ...]] [--5 5 [5 ...]] [--6 6 [6 ...]]
#                          [--7 7 [7 ...]] [--8 8 [8 ...]] [--9 9 [9 ...]]
#                          [--10 10 [10 ...]]
#                          input_dir output_dir
#
#Photogrammetry reconstruction with these steps :
#    0. Intrinsics analysis             openMVG_main_SfMInit_ImageListing
#    1. Compute features                openMVG_main_ComputeFeatures
#    2. Compute matches                 openMVG_main_ComputeMatches
#    3. Incremental reconstruction      openMVG_main_IncrementalSfM
#   (4). Colorize Structure             openMVG_main_ComputeSfM_DataColor
#   (5). Structure from Known Poses     openMVG_main_ComputeStructureFromKnownPoses
#   (6). Colorized robust triangulation openMVG_main_ComputeSfM_DataColor
#    4. Export to openMVS               openMVG_main_openMVG2openMVS
#    5. Densify point cloud             OpenMVS/DensifyPointCloud
#    6. Reconstruct the mesh            OpenMVS/ReconstructMesh
#    7. Refine the mesh                 OpenMVS/RefineMesh
#    8. Texture the mesh                OpenMVS/TextureMesh
#
#positional arguments:
#  input_dir             the directory which contains the pictures set.
#  output_dir            the directory which will contain the resulting files.
#
#optional arguments:
#  -h, --help            show this help message and exit
#  -f FIRST_STEP, --first_step FIRST_STEP
#                        the first step to process
#  -l LAST_STEP, --last_step LAST_STEP
#                        the last step to process
#
#Passthrough:
#  Option to be pass to command lines (remove - in front of option names)
#  e.g. --1 p ULTRA to use the ULTRA preset in openMVG_main_ComputeFeatures


import os
import subprocess
import sys


# Indicate the openMVG and openMVS binary directories
OPENMVG_BIN = '/usr/local/bin/'
OPENMVS_BIN = '/usr/local/bin/OpenMVS/'
CAMERA_SENSOR_WIDTH_DIRECTORY = '/usr/local/share/openMVG/'
DEBUG = False

## HELPERS for terminal colors
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
NO_EFFECT, BOLD, UNDERLINE, BLINK, INVERSE, HIDDEN = (0,1,4,5,7,8)

#from Python cookbook, #475186
def has_colours(stream):
    if not hasattr(stream, 'isatty'):
        return False
    if not stream.isatty():
        return False # auto color only on TTYs
    try:
        import curses
        curses.setupterm()
        return curses.tigetnum('colors') > 2
    except:
        # guess false in case of error
        return False
has_colours = has_colours(sys.stdout)

def printout(text, colour=WHITE, background=BLACK, effect=NO_EFFECT):
        if has_colours:
                seq = '\x1b[{};{};{}m'.format(effect, 30+colour, 40+background) + text + '\x1b[0m'
                sys.stdout.write(seq+'\r\n')
        else:
                sys.stdout.write(text+'\r\n')


class Config(object):
    def __init__(self, **kwargs):
        '''Create the folder if not presents'''
        self.input_dir = os.path.abspath(kwargs.get('input_dir'))
        self.output_dir = os.path.abspath(kwargs.get('output_dir'))

        if not os.path.exists(self.input_dir):
            sys.exit('{}: path not found'.format(self.input_dir))

        matches_dir = kwargs.get('matches', 'matches')
        reconstruction_dir = kwargs.get('matches', 'matches')
        mvs_dir = kwargs.get('mvs', 'mvs')
        camera_db = kwargs.get('camera_db',
                               os.path.join(CAMERA_SENSOR_WIDTH_DIRECTORY,
                                            'sensor_width_camera_database.txt'))

        self.matches_dir = os.path.join(self.output_dir, matches_dir)
        self.reconstruction_dir = os.path.join(self.output_dir, reconstruction_dir)
        self.mvs_dir = os.path.join(self.output_dir, kwargs.get('mvs', 'mvs'))
        self.camera_file_params = camera_db

        map(Config.mkdir, [self.output_dir,
                           self.matches_dir,
                           self.reconstruction_dir,
                           self.mvs_dir])

    @staticmethod
    def mkdir(folder):
        if not os.path.exists(folder):
            os.makedirs(folder)

class Step:
    def __init__(self, info, cmd, args):
        self.info = info
        self.cmd = cmd
        self.args = args

    def execute(self)
        pass

class Pipeline(object):
    def __init__(self, config):
        self.steps = [
            {
                'info': 'Intrinsics analysis',
                'cmd': os.path.join(OPENMVG_BIN,'openMVG_main_SfMInit_ImageListing'),
                'args': ['-i', config.input_dir,
                         '-o', config.matches_dir,
                         '-d', config.camera_db]
            },
            {
                'info': 'Compute features',
                'cmd': os.path.join(OPENMVG_BIN,'openMVG_main_ComputeFeatures'),
                'args': ['-i', os.path.join(config.matches_dir, 'sfm_data.json'),
                         '-o', config.matches_dir,
                         '-m', 'SIFT']
            },
            {
                'info': 'Compute matches',
                'cmd': os.path.join(OPENMVG_BIN, 'openMVG_main_ComputeMatches'),
                'args': ['-i', os.path.join(config.matches_dir, 'sfm_data.json'),
                         '-o', config.matches_dir]
            },
            {
                'info': 'Incremental reconstruction',
                'cmd': os.path.join(OPENMVG_BIN, 'openMVG_main_IncrementalSfM'),
                'args': ['-i', os.path.join(config.matches_dir, 'sfm_data.json'),
                         '-m', config.matches_dir,
                         '-o', config.reconstruction_dir]
            },
            {
                'info': 'Colorize Structure',
                'cmd': os.path.join(OPENMVG_BIN,'openMVG_main_ComputeSfM_DataColor'),
                'args': ['-i', os.path.join(config.reconstruction_dir, 'sfm_data.bin'),
                         '-o', os.path.join(config.reconstruction_dir, 'colorized.ply')]
            },
            {
                'info': 'Structure from Known Poses',
                'cmd': os.path.join(OPENMVG_BIN,'openMVG_main_ComputeStructureFromKnownPoses'),
                'args': ['-i', os.path.join(config.reconstruction_dir, 'sfm_data.bin'),
                         '-m', config.matches_dir,
                         '-f', os.path.join(config.matches_dir, 'matches.f.bin'),
                         '-o', os.path.join(config.reconstruction_dir, 'robust.bin')]
            },
            {
                'info': 'Colorized robust triangulation',
                'cmd': os.path.join(OPENMVG_BIN,'openMVG_main_ComputeSfM_DataColor'),
                'args': ['-i', os.path.join(config.reconstruction_dir, 'robust.bin'),
                         '-o', os.path.join(config.reconstruction_dir, 'robust_colorized.ply')]
            },
            {
                'info': 'Export to openMVS',
                'cmd': os.path.join(OPENMVG_BIN,'openMVG_main_openMVG2openMVS'),
                'args': ['-i', os.path.join(config.reconstruction_dir, 'sfm_data.bin'),
                         '-o', os.path.join(config.mvs_dir, 'scene.mvs'),
                         '-d', config.mvs_dir]
            },
            {
                'info': Densify point cloud',
                'cmd': os.path.join(OPENMVS_BIN,'DensifyPointCloud'),
                'args': ['--input-file', os.path.join(config.mvs_dir, 'scene.mvs')], #'--resolution-level','0']], #'-w', '%mvs_dir%'
            },
            {
                'info': 'Reconstruct the mesh',
                'cmd': os.path.join(OPENMVS_BIN,'ReconstructMesh'),
                'args': [os.path.join(config.mvs_dir, 'scene_dense.mvs')], #,'-w', '%mvs_dir%']],
            }
            {
                'info': 'Refine the mesh',
                'cmd': os.path.join(OPENMVS_BIN,'RefineMesh'),
                'args': [os.path.join(config.mvs_dir, 'scene_dense_mesh.mvs')], #,'-w', '%mvs_dir%']]
            }
            {
                'info': 'Texture the mesh',
                'cmd': os.path.join(OPENMVS_BIN,'TextureMesh'),
                'args': [os.path.join(config.mvs_dir, 'scene_dense_mesh_refine.mvs')], #,'-w', '%mvs_dir%']]
            }
        ]

    def __getitem__(self, indice):
        return Step(**self.steps[indice])

    def length(self):
        return len(self.steps)


if __name__ == '__main__':
    parse_options()
    main()


def parse_options():
    ## ARGS
    import argparse
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Photogrammetry reconstruction with these steps : \r\n'+
            '\r\n'.join(('\t{}. {}\t {}'.format(t, steps[t].info, steps[t].cmd) for t in range(steps.length())))
        )
    parser.add_argument('input_dir', help='the directory wich contains the pictures set.')
    parser.add_argument('output_dir', help='the directory wich will contain the resulting files.')
    parser.add_argument('-f','--first_step', type=int, default=0, help='the first step to process')
    parser.add_argument('-l','--last_step', type=int, default=10, help='the last step to process' )

    group = parser.add_argument_group('Passthrough',description='Option to be passed to command lines (remove - in front of option names)\r\ne.g. --1 p ULTRA to use the ULTRA preset in openMVG_main_ComputeFeatures')
    for n in range(steps.length()) :
        group.add_argument('--'+str(n), nargs='+')

    parser.parse_args(namespace=conf) #store args in the ConfContainer


def main()
    steps.apply_conf(conf)

    ## WALK
    print('# Using input dir  :  {}'.format(conf.input_dir))
    print('#       output_dir :  {}'.format(conf.output_dir))
    print('# First step  :  {}'.format(conf.first_step))
    print('# Last step :  {}'.format(conf.last_step))
    steps = Pipeline()
    for cstep in range(conf.first_step, conf.last_step+1):
        try:
            printout('#{}. {}'.format(cstep, steps[cstep].info), effect=INVERSE)
        except IndexError:
            # There are not enough steps in stepsStore.step_data to get to last_step
            break

        opt=getattr(conf,str(cstep))
        if opt is not None :
            #add - sign to short options and -- to long ones
            for o in range(0,len(opt),2):
                if len(opt[o])>1:
                    opt[o]='-'+opt[o]
                opt[o]='-'+opt[o]
        else:
            opt=[]

        #Remove steps[cstep].opt options now defined in opt
        for anOpt in steps[cstep].opt :
            if anOpt in opt :
                idx=steps[cstep].opt.index(anOpt)
                if DEBUG :
                    print('#\t'+'Remove '+ str(anOpt) + ' from defaults options at id ' + str(idx))
                del steps[cstep].opt[idx:idx+2]

        cmdline = [steps[cstep].cmd] + steps[cstep].opt + opt

        if not DEBUG :
            pStep = subprocess.Popen(cmdline)
            pStep.wait()
        else:
            print('\t'+' '.join(cmdline))
