#!/usr/bin/env python
# coding=utf-8
import yaml
from pytest_s3.logger import logger
from pytest_s3.s3_client import S3Manager


def singleton(cls):
    def _singleton(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance.__call__ = lambda: instance
        return instance

    return _singleton


@singleton
class DB(object):
    def __init__(self, s3cmdopt, rootdir):
        config_path = '{0}/{1}'.format(rootdir, s3cmdopt)
        with open(config_path) as f:
            self.env = yaml.load(f, Loader=yaml.FullLoader)

    @property
    def s3(self):
        s3_dict = dict()
        try:
            for k, v in self.env.get('s3', {}).items():
                s3_dict[k] = S3Manager(v['aws_access_key_id'],
                                       v['aws_secret_access_key'],
                                       v['region_name'],
                                       v['bucket'])
        except Exception as e:
            logger.error(e)
            raise ConnectionError(e)

        return s3_dict