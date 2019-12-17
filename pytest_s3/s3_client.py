# -*- coding:utf-8 -*-
import os
import zipfile
from datetime import datetime

import fire
from boto3.session import Session
from botocore.config import Config

from . import timer


class S3Manager(object):
    def __init__(self,
                 aws_access_key_id,
                 aws_secret_access_key,
                 region_name,
                 bucket):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.bucket = bucket

        self.session = Session(aws_access_key_id=self.aws_access_key_id,
                               aws_secret_access_key=self.aws_secret_access_key,
                               region_name=self.region_name)
        self.s3 = self.session.resource('s3')
        self.client = self.session.client('s3', use_ssl=True, verify=None,
                                          config=Config(signature_version="s3v4"))
        self.file_path = None  # #压缩文件用

    def upload(self, file_path, filename, bucket=None, dozip='1'):
        '''

        :param file_path: 要压缩文件本地目录（多文件的目录）
        :param filename: 上传的文件在S3中存储的文件名
        :param bucket: 篮子名-初始化时已指定
        :param dozip: 是否压缩上传文件 默认压缩
        :return: 是否上传成功
        '''
        if not bucket:
            bucket = self.bucket

        if dozip == '1':
            if not filename.endswith('.zip'):
                filename += '/{time}.zip'.format(time=timer.year_month_day_hour_minute_second())
            else:
                filen,typez = filename.rsplit('.',1)
                filename = filen +'/' + timer.year_month_day_hour_minute_second() + '.zip'
            filename = 'allure_report/'+filename
            if file_path.endswith('/'):
                file_path = file_path[0:-1]
            self.unzip_file('w', file_path)
            self.client.upload_file(file_path + '.zip', bucket, filename)
            os.remove(file_path + '.zip')
        else:
            if os.path.isdir(file_path):
                return 'dir must be zipped!'
            elif os.path.isfile(file_path):
                self.client.upload_file(file_path, bucket, filename)
            else:
                return 'local file path error!'

        if self.check_file_exist(filename, bucket=bucket):
            return filename
        return 'upload fail'

    def download(self, s3_key_name, local_path_name, bucket=None, unzip=True):
        '''

        :param s3_key_name: 在S3上要下载的文件名
        :param local_path_name: 下载到本地的文件名（全路径）
        :param bucket: 篮子-初始化已指定
        :param unzip: 是否采用解压  默认解压（若文件以.zip结尾）
        :return: 是否下载成功
        '''
        if not bucket:
            bucket = self.bucket
        self.client.download_file(bucket, s3_key_name, local_path_name)
        if os.path.exists(local_path_name):
            if unzip:
                if '.zip' in s3_key_name:
                    self.unzip_file('r', local_path_name)
            return 'download success'
        return 'download fail'

    def unzip_file(self, method, file_path, destination=None):
        '''

        :param method:r-解压 w-压缩
        :param file_path: 要执行解压的文件目录/要执行压缩的文件目录
        :param destination: 要执行解压到的文件目录，默认为当前解压文件目录
        :return: None
        '''
        if not destination:
            destination = file_path.rsplit(os.path.sep, 1)[0]

        if method == 'r':
            f = zipfile.ZipFile(file_path, mode=method)
            for file in f.namelist():
                f.extract(file, destination)
            f.close()
        if method == 'w':
            f = zipfile.ZipFile(file_path + '.zip', mode=method)
            # for d in os.listdir(file_path):
            #     f.write(file_path + os.path.sep + d, file_path.rsplit(os.sep, 1)[1] + os.sep + d)
            fp = self.get_all_file_path(file_path,f)
            fp.close()

    def get_all_file_path(self,file_path,fp):
        if not self.file_path:
            self.file_path = file_path
            # print(file_path)
        parents = os.listdir(file_path)
        for parent in parents:
            child = os.path.join(file_path, parent)
            # print(child)
            if os.path.isdir(child):
                self.get_all_file_path(child, fp)
            # print(child)
            else:
                # print(child)
                # print(child.rsplit(file_path+os.sep, 1))
                fp.write(child, child.rsplit(self.file_path+os.sep, 1)[1])
        return fp

    def check_file_exist(self, filename, bucket=None):
        '''
        校验bucket中是否有filename
        :param filename:
        :param bucket:
        :return: bool
        '''
        if not bucket:
            bucket = self.bucket
        for bucket in self.s3.Bucket(bucket).objects.filter(Prefix=filename):
            if bucket.key == filename:
                return True
        return False

    def delete(self, *args, **kwargs):
        '''
        删除key--支持批量删除
        :param args:要删除的key
        :param kwargs:
        :return: delete status
        '''
        objects_to_delete = []
        for obj in args:
            objects_to_delete.append({'Key': obj})
        self.s3.Bucket(self.bucket).delete_objects(Delete={'Objects': objects_to_delete})
        for i in args:
            if not self.check_file_exist(i):
                return 'delete success'
        return 'delete fail'

    def _close(self):
        pass

    def get_keys(self, bucket=None):
        bucket = bucket or self.bucket
        return [bucket.key for bucket in self.s3.Bucket(bucket).objects.all()]

    def list_all_object_by_prefix(self, prefix, start_after='', keys=[]):
        """
        返回指定prefix下所有的对象
        :param prefix:
        :param start_after:
        :param keys:
        :return:
        """
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            StartAfter=start_after
        )

        if 'Contents' not in response:
            return keys

        key_list = response['Contents']
        last_key = key_list[-1]['Key']

        keys.extend(key_list)

        return self.list_all_object_by_prefix(prefix, last_key, keys)

    def list_object_by_prefix(self, prefix):
        """
        最多返回1000个
        :param prefix:
        :return:
        """
        return self.client.list_objects_v2(Bucket=self.bucket,
                                           Prefix=prefix).get('Contents')

    def list_object_pate(self, prefix, page=1, count=100, bucket=None):
        bucket = bucket or self.bucket
        paginator = self.client.get_paginator('list_objects_v2')
        return paginator.paginate(
            Bucket=bucket,
            Prefix=prefix,
            PaginationConfig={
                'MaxItems': count,
                'PageSize': page,
            }
        )

    def get_sign_put_url(self, key):
        """
        获取上传url
        :param key:
        :return:
        """
        key = "%s:%s" % (datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3], key)
        key = key.strip()
        conditions = [
            {'bucket': self.bucket},
            {"acl": "public-read"},
            ["eq", "$Key", key],
            ["starts-with", "$Content-Type", "text"],
        ]
        return self.client.generate_presigned_post(self.bucket, key, {}, conditions, ExpiresIn=3600)

    def get_down_url(self, key,ttl=604800):
        """获取下载url"""
        return self.client.generate_presigned_url('get_object', {'Bucket': self.bucket, 'Key': key}, ttl, 'GET')

    def get_public_url(self, key):
        return self.get_down_url(str(key)).split('?', 1)[0]


def main():
    s3 = S3Manager(aws_access_key_id='AKIAPBCHUVIR4EHFE6KQ',
                 aws_secret_access_key='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',
                 region_name='cn-north-1',
                 bucket='swc-sqe')
    filename = fire.Fire(s3.upload)
    print(s3.get_down_url(filename))


if __name__ == '__main__':
    pass
    # s3 = S3Manager(aws_access_key_id='AKIAPBCHUVIR4EHFE6KQ',
    #              aws_secret_access_key='bLFNmBy294i7jSd/B+dYXgngXDCXAFX5qkctQ5P4',
    #              region_name='cn-north-1',
    #              bucket='swc-sqe')
    # s3.download('allure_report/dummy_cert/2018/12/19/10_33_47.zip','D:\\mytest\\evaluate\\1.zip')
    # s3.unzip_file("w",'D:\\allure\\allure-report')
    # s3.unzip_file("r",'D:\\mytest\\evaluate\\1.zip')
    # print(s3.upload('D:\\allure\\allure-report','dummy_cert',dozip='1'))
    # print(s3.upload(''))
    # print(s3.get_keys())
    # print(len(s3.get_keys()))
    # print(s3.delete('Allure_Report/dummy_cert2018/11/21/18/04/36.zip',
    #                 'Allure_Reportdummy_cert2018/11/21/18/03/02.zip',
    #                 'allure_report/dummy_cert/2018/11/21/18_06_45.zip',
    #                 'allure_report/dummy_cert2018/11/21/18_06_01.zip',
    #                 'dummy_cert.zip'))
    # lists = s3.list_all_object_by_prefix('test_report')
    # print(len(lists))
    # print(list(s3.list_object_pate('test_report')))
    # main()
