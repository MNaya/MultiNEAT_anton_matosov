#!/usr/bin/python

from __future__ import print_function
from setuptools import setup, Extension
import sys
import os
import psutil

# monkey-patch for parallel compilation
def parallelCCompile(self, sources, output_dir=None, macros=None, include_dirs=None, debug=0, extra_preargs=None, extra_postargs=None, depends=None):
    # those lines are copied from distutils.ccompiler.CCompiler directly
    macros, objects, extra_postargs, pp_opts, build = self._setup_compile(output_dir, macros, include_dirs, sources, depends, extra_postargs)
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)
    # parallel code
    
    N = psutil.cpu_count(logical=False) # number of parallel compilations
    import multiprocessing.pool
    def _single_compile(obj):
        try: src, ext = build[obj]
        except KeyError: return
        self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)
    # convert to list, imap is evaluated on-demand
    list(multiprocessing.pool.ThreadPool(N).imap(_single_compile,objects))
    return objects

import distutils.ccompiler
distutils.ccompiler.CCompiler.compile=parallelCCompile


def getExtensions():
    platform = sys.platform

    is_windows = platform.startswith('win') or platform.startswith('cygwin')
    is_macOS = platform.startswith('darwin')
    is_linux = platform.startswith('linux')

    extensionsList = []
    sources = [
        'src/Genes.cpp',
        'src/Genome.cpp',
        'src/Innovation.cpp',
        'src/NeuralNetwork.cpp',
        'src/Parameters.cpp',
        'src/PhenotypeBehavior.cpp',
        'src/Population.cpp',
        'src/PythonBindings.cpp',
        'src/Random.cpp',
        'src/Species.cpp',
        'src/Substrate.cpp',
        'src/Utils.cpp',
    ]

    compile_args = []

    if is_macOS or is_linux:
        compile_args += ['-march=native', '-g', '-w']

    if is_macOS:
        compile_args += ['-stdlib=libc++', '-std=c++11']
    elif is_linux:
        compile_args += ['-std=gnu++11']
    elif is_windows:
        compile_args += ['/EHsc']

    prefix = os.getenv('PREFIX')
    if prefix and len(prefix) > 0:
        compile_args += ["-I{}/include".format(prefix)]

    is_python_2 = sys.version_info[0] < 3
    python_version_string = "{}{}".format(sys.version_info[0], sys.version_info[1])

    if is_windows:
        if is_python_2:
            raise RuntimeError("Python prior to version 3 is not supported on Windows due to limits of VC++ compiler version")

    libs = ['boost_system', 'boost_serialization',
            'boost_python3', "boost_numpy3"]

    compile_args += ['-DUSE_BOOST_PYTHON']
    compile_args += ['-DBOOST_ALL_NO_LIB'] # Do not autolink since we specify all libs manually and autolink is broken for boost-python 1.67.0 on Windows anyways

    extensionsList.append(Extension('MultiNEAT._MultiNEAT',
                                    sources,
                                    libraries=libs,
                                    extra_compile_args=compile_args))

    return extensionsList


setup(name='multineat',
      version='0.5.3', # Update version in conda/meta.yaml as well
      packages=['MultiNEAT'],
      ext_modules=getExtensions())
