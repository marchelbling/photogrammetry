#!/usr/bin/python
#! -*- encoding: utf-8 -*-

import argparse
import uuid
import os
import shutil
import subprocess
import sys
import time

DATA_DIR = os.path.abspath('data')
pipeline = [
    {
        'label': 'analysis',
        'tool': 'openmvg',
        'command': ['openMVG_main_SfMInit_ImageListing',
                    '-i', '{input_dir}',
                    '-o', '{matches_dir}',
                    '-d', '{camera_database}']
    },
    {
        'label':'features',
        'tool': 'openmvg',
        'command': ['openMVG_main_ComputeFeatures',
                    '-i', '{matches_dir}/sfm_data.json',
                    '-o', '{matches_dir}',
                    '-m', 'SIFT']
    },
    {
        'label':'matches',
        'tool': 'openmvg',
        'command': ['openMVG_main_ComputeMatches',
                    '-i', '{matches_dir}/sfm_data.json',
                    '-o', '{matches_dir}']
    },
    {
        'label':'incremental_reconstruction',
        'tool': 'openmvg',
        'command': ['openMVG_main_IncrementalSfM',
                    '-i', '{matches_dir}/sfm_data.json',
                    '-m', '{matches_dir}',
                    '-o', '{reconstruction_dir}']
    },
    {
        'label':'export_to_mvs',
        'tool': 'openmvg',
        'command': ['openMVG_main_openMVG2openMVS',
                    '-i', '{reconstruction_dir}/sfm_data.bin',
                    '-o', '{mvs_dir}/scene.mvs',
                    '-d', '{mvs_dir}']
    },
    {
        'label':'densify_point cloud',
        'tool': 'openmvs',
        'command': ['DensifyPointCloud',
                    '--input-file', '{mvs_dir}/scene.mvs'],
    },
    {
        'label':'reconstruct_mesh',
        'tool': 'openmvs',
        'command': ['ReconstructMesh',
                    '{mvs_dir}/scene_dense.mvs'],
    },
    {
        'label':'refine_mesh',
        'tool': 'openmvs',
        'command': ['RefineMesh',
                    '{mvs_dir}/scene_dense_mesh.mvs'],
    },
    {
        'label':'texture_mesh',
        'tool': 'openmvs',
        'command': ['TextureMesh',
                    '{mvs_dir}/scene_dense_mesh_refine.mvs'],
    }
]


def list_all_files(path, discard=None, extension=None):
    filenames = []
    path = os.path.abspath(path)
    for root, _, files in os.walk(path, topdown=True):
        filenames.extend(map(lambda x: os.path.join(root, x), files))

    if discard is not None:
        discard = set(discard)
        filenames = filter(lambda x: x not in discard, filenames)

    if extension:
        extensions = extension if isinstance(extension, list) else [extension]
        filenames = filter(lambda x: any(x.endswith(ext) for ext in extensions), filenames)

    return sorted(filenames)


def execute(command=None, output=False, stdout=sys.stdout):
    stdout = open(stdout or os.devnull, 'a') if stdout is not sys.stdout else sys.stdout

    if output:
        caller, caller_args = subprocess.check_output, {}
        stderr = output
    else:
        caller, caller_args = subprocess.check_call, {'stdout': stdout}
        stderr = subprocess.STDOUT

    try:
        return caller(command or [], stderr=stderr, **caller_args)
    finally:
        if stdout != sys.stdout:
            stdout.close()


def get_docker_container(session, volumes=None):
    volumes = volumes or {}
    for local in volumes.keys():
        if not os.path.exists(local):
            os.makedirs(local)
    volumes = ' '.join('-v {}:{}'.format(local, remote) for local, remote in volumes.items())

    return execute(['docker', 'run', '--detach', '--tty', '--privileged', '--rm'] + volumes.split() +
                   ['photogrammetry:latest', 'bash'],
                   output=True).split()[0]

class Context(object):
    def __init__(self, uid=None):
        self.uid = uid or uuid.uuid4().hex
        self.folder = os.path.join(DATA_DIR, self.uid)
        print('Building in {}'.format(self.folder))

        self.log = os.path.join(self.folder, 'processed.log')
        self.input_dir = os.path.join(self.folder, 'source')
        self.output_dir = os.path.join(self.folder, 'build')
        self.matches_dir = os.path.join(self.folder, 'tmp', 'matches')
        self.reconstruction_dir = os.path.join(self.folder, 'tmp', 'reconstruction')
        self.mvs_dir = os.path.join(self.folder, 'tmp', 'mvs')
        self.camera_database = '/usr/local/share/openMVG/sensor_width_camera_database.txt'

        self.steps = []
        self.create_session()


    def create_session(self):
        for path in (self.input_dir,
                     self.output_dir,
                     self.matches_dir,
                     self.reconstruction_dir,
                     self.mvs_dir):
            folder = os.path.join('data', path)
            if not os.path.exists(folder):
                os.makedirs(folder)

    def process(self, source_dir, pipeline):
        self.copy_source(source_dir)
        self.container_id = get_docker_container(self.uid, volumes={self.folder:self.folder})
        try:
            for step in pipeline:
                print('>>> step: {}'.format(step['label']))
                self.run(step)
                print('<<< done in {}s'.format(self.steps[-1]['timing']))
        finally:
            execute(['docker', 'rm', '-f', self.container_id])
            self.container_id = None

    def copy_source(self, source_dir):
        images = list_all_files(source_dir, extension=['.jpg', '.jpeg', '.JPG', '.JPEG'])
        for image in images:
            shutil.copy(image, os.path.join(DATA_DIR, self.input_dir))

    def run(self, step):
        start = time.time()
        execute(self.format(step['command']), stdout=self.log)
        self.steps.append({
            'step': step,
            'timing': time.time() - start
        })

    def format(self, template):
        # inject docker wrapper + format all path
        return ['docker', 'exec', '-it', self.container_id] + \
            list(map(lambda token: token.format(**self.__dict__), template))


def reconstruct(options):
    def get_pipeline_index(value):
        if isinstance(value, basestring):
            indices = [i for i, step in enumerate(pipeline) if step['label'] == value]
            return indices[0] if indices else None
        else:
            return value

    context = Context(uid=options.uid)
    first = get_pipeline_index(options.first)
    last = get_pipeline_index(options.last)
    context.process(options.source, pipeline[first:last])


def parse_options():
    parser = argparse.ArgumentParser(description='Photogrammetry options')
    parser.add_argument('source', type=str, default='', help='Path to folder containing images to use for reconstruction')
    parser.add_argument('--uid', type=str, default='', help='Build uid')
    parser.add_argument('--from', dest='first', default=None, help='First pipeline step to execute')
    parser.add_argument('--to', dest='last', default=None, help='Last pipeline step to execute')
    return parser.parse_args()

def main():
    options = parse_options()
    reconstruct(options)


if __name__ == '__main__':
    main()
