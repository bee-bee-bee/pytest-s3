# -*- coding: utf-8 -*-

import pytest
from configparser import ConfigParser
from pytest_s3.db import DB


def pytest_addoption(parser):
    group = parser.getgroup('pytest_s3')
    group.addoption(
        '--config_s3',
        action='store',
        # default='config/config.yml',
        help='relative path of config.yml'
    )


@pytest.fixture(scope="session", autouse=False)
def s3cmdopt(request):
    option_config = request.config.getoption("--config_s3")
    if option_config:
        return option_config
    else:
        try:
            ini_config = request.config.inifile.strpath
            config = ConfigParser()
            config.read(ini_config)
            s3_config = config.get('s3', 'config')
            return s3_config
        except Exception as e:
            raise RuntimeError("there is no s3 config in pytest.ini", e)


@pytest.fixture(scope="session", autouse=False)
def s3(s3cmdopt, request):
    return DB(s3cmdopt, request.config.rootdir).s3
