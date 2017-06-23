#!/usr/bin/python
#! -*- encoding: utf-8 -*-

import argparse
import json
import uuid
import os
import shutil
import subprocess
import sys
import time

DATA_DIR = os.path.abspath('data')


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
    def __init__(self, uid=None, pipeline=None):
        self.uid = uid or uuid.uuid4().hex
        self.folder = os.path.join(DATA_DIR, self.uid)
        self.container_id = None
        print('Building in {}'.format(self.folder))

        self.steps = []
        self.log = os.path.join(self.folder, 'processed.log')
        self.input_dir = os.path.join(self.folder, 'source')
        self.output_dir = os.path.join(self.folder, 'build')

        with open(pipeline + '.json') as runner:
            self.pipeline = json.load(runner)
        getattr(self, pipeline + '_configuration')()

    def openmvg_openmvs_configuration(self):
        self.matches_dir = os.path.join(self.folder, 'tmp', 'matches')
        self.reconstruction_dir = os.path.join(self.folder, 'tmp', 'reconstruction')
        self.mvs_dir = os.path.join(self.folder, 'tmp', 'mvs')
        self.camera_database = '/usr/local/share/openMVG/sensor_width_camera_database.txt'


    def create_session(self):
        # make sure all `*_dir` folders for current pipeline exist
        for path in [value for key, value in self.__dict__.items() if key.endswith('_dir')]:
            folder = os.path.join('data', path)
            if not os.path.exists(folder):
                os.makedirs(folder)
        # make sure a container is ready
        if not self.container_id:
            self.container_id = get_docker_container(self.uid, volumes={self.folder:self.folder})

    def end_session(self):
        if self.container_id:
            execute(['docker', 'rm', '-f', self.container_id])
            self.container_id = None

    def process(self, source_dir, entrypoint=None):
        self.create_session()
        self.copy_source(source_dir)
        next = entrypoint or self.pipeline['entrypoint']
        while next:
            try:
                step = self.pipeline['steps'][next]
                print('>>> step: {}'.format(next))
                self.run(step)
                print('<<< done in {}s'.format(self.steps[-1]['timing']))
                next = step.get('on_success')
            except Exception as e:
                self.end_session()
                next = None

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


def parse_options():
    parser = argparse.ArgumentParser(description='Photogrammetry options')
    parser.add_argument('source', type=str, default='', help='Path to folder containing images to use for reconstruction')
    parser.add_argument('--uid', type=str, default='', help='Build uid')
    parser.add_argument('--pipeline', type=lambda x: str(x).replace('.json', ''), default='openmvg_openmvs', help='Pipeline (json) to execute')
    parser.add_argument('--entrypoint', default=None, help='First pipeline step to execute')
    return parser.parse_args()


def reconstruct(options):
    context = Context(uid=options.uid, pipeline=options.pipeline)
    context.process(options.source, entrypoint=options.entrypoint)

def main():
    options = parse_options()
    reconstruct(options)


if __name__ == '__main__':
    main()
