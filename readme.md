## 简介
pytest-s3插件
## 安装

`pip install pytest-s3 -i http://*:8082/private_repository/ --trusted-host *`

## 使用
### 测试用例可使用s3 fixtrue

```python
def test_s3(s3):
    is_file_exist = s3['sqe'].check_file_exist('vehicle_logs/10107/sys_log/20191210/866c718a4b934275ab22d974637041b3/05BF6C4B7175F18F428E9CADCF6A41E4_ADC_log.zip')
```
### 运行测试
需编写pytest.ini文件，置于项目内的根目录上，用于指定s3配置路径。
默认在项目内的根目录下寻找环境对应配置(./config/config.yml)

####pytest.ini
```ini
[s3]
config = config/config.yml
```
或在命令行中通过--config_s3参数指定路径
```bash
pytest --config_s3 config/config.yml
```
####test_config.yml配置如下:
```yaml
s3:
  sqe:
    aws_access_key_id: key_id
    aws_secret_access_key: secret_key
    region_name: name
    bucket: bucket_name
```
## 打包
`python setup.py sdist bdist`  
`twine upload -r my_nexus dist/*`