#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import argparse
import os
import signal
import json
from time import sleep

from alibabacloud import get_client
from happy_python import dict_to_pretty_json, to_domain_obj

from common import config
from common import hlog

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.dnspod.v20210323 import dnspod_client, models


# noinspection PyUnusedLocal
def sigint_handler(sig, frame):
    hlog.info('\n\n收到 Ctrl+C 信号，退出......')


def check_prefix(domain: str) -> None:
    """
    安全检查，域名必须以_acme-challenge.开头
    :param domain:
    :return:
    """
    prefix = '_acme-challenge.'
    prefix_len = len(prefix)

    assert domain[:prefix_len] == prefix


def add_domain_record(full_domain: str, value: str, root_domain: str, record: str) -> None:
    fn_name = 'add_domain_record'
    hlog.enter_func(fn_name)

    hlog.var('full_domain', full_domain)
    hlog.var('value', value)

    check_prefix(full_domain)

    delete_domain_record(full_domain, root_domain, record)

    # 增加域名解析记录
    hlog.info('增加域名解析记录......')

    if config.platform_type == 'aliyun':
        response = \
            ali_client.add_domain_record(root_domain=root_domain, rr=record, type_='TXT', ttl=600, value=value)

        hlog.var('response', dict_to_pretty_json(response))
    else:
        try:
            req = models.CreateRecordRequest()
            params = {
                "Domain": root_domain,
                "SubDomain": record,
                "RecordType": "TXT",
                "RecordLine": "默认",
                "Value": value,
                "TTL": 600,
            }
            req.from_json_string(json.dumps(params))

            resp = tencent_client.CreateRecord(req)
            hlog.var('response', resp.to_json_string())
        except TencentCloudSDKException as err:
            hlog.error(err)

    # 等待域名解析生效
    sleep(30)
    hlog.exit_func(fn_name)


def delete_domain_record(full_domain: str, root_domain: str, record: str) -> None:
    fn_name = 'delete_domain_record'
    hlog.enter_func(fn_name)

    hlog.var('full_domain', full_domain)

    check_prefix(full_domain)

    if config.platform_type == 'aliyun':
        response = ali_client.describe_sub_domain_records(sub_domain=full_domain)
        hlog.var('response', dict_to_pretty_json(response))

        is_exists_record = bool(response.get('TotalCount'))
        hlog.var('is_exists_record', is_exists_record)

        # 如果域名解析记录已经存在，则删除
        if is_exists_record:
            hlog.info('域名解析记录已经存在，准备删除......')

            for record in response.get('DomainRecords').get('Record'):
                hlog.var('record', record)

                record_id = record.get('RecordId')
                hlog.var('record_id', record_id)

                response = ali_client.delete_domain_record(record_id=record_id)
                hlog.var('response', dict_to_pretty_json(response))

                hlog.info('域名解析记录删除完成')
    else:
        try:
            describe_req = models.DescribeRecordListRequest()
            params = {
                "Domain": root_domain,
                "Subdomain": record,
            }
            describe_req.from_json_string(json.dumps(params))

            describe_resp = tencent_client.DescribeRecordList(describe_req)
            hlog.var('response', describe_resp)

            is_exists_record = bool(describe_resp.RecordCountInfo)
            hlog.var('is_exists_record', is_exists_record)

            # 如果域名解析记录已经存在，则删除
            if is_exists_record:
                hlog.info('域名解析记录已经存在，准备删除......')

                for record in describe_resp.RecordList:
                    record_id = record.RecordId
                    hlog.var('record_id', record_id)

                    delete_req = models.DeleteRecordRequest()
                    params = {
                        "Domain": root_domain,
                        "RecordId": record_id
                    }
                    delete_req.from_json_string(json.dumps(params))

                    delete_resp = tencent_client.DeleteRecord(delete_req)
                    hlog.var('response', delete_resp)

                hlog.info('域名解析记录删除完成')
        except TencentCloudSDKException as err:
            hlog.error(err)

    hlog.exit_func(fn_name)


def main():
    global ali_client
    global tencent_client

    parser = argparse.ArgumentParser(prog='letsencrypt_dns_tool',
                                     description="Let's Encrypt DNS工具",
                                     usage='%(prog)s --auth|--cleanup')

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--auth',
                       help='增加域名解析记录',
                       action='store_true',
                       dest='is_auth')

    group.add_argument('--cleanup',
                       help='删除域名解析记录',
                       action='store_true',
                       dest='is_cleanup')

    args = parser.parse_args()

    domain = os.environ['CERTBOT_DOMAIN']
    value = os.environ['CERTBOT_VALIDATION']

    hlog.info('域名：%s，值：%s' % (domain, value))

    full_domain = '_acme-challenge.' + domain
    domain_obj = to_domain_obj(full_domain)

    if not domain_obj:
        hlog.error('域名%s无效' % full_domain)
        return

    root_domain = domain_obj.get_domain_name()
    record = domain_obj.get_host_name()
    hlog.var('root_domain', root_domain)
    hlog.var('record', record)

    if args.is_auth:
        add_domain_record(full_domain, value, root_domain, record)
    elif args.is_cleanup:
        delete_domain_record(full_domain, root_domain, record)


if __name__ == '__main__':
    # 前台运行收到 CTRL+C 信号，直接退出。
    signal.signal(signal.SIGINT, sigint_handler)

    if config.platform_type == 'aliyun':
        ali_client = get_client(
            'alidns',
            access_key_id=config.access_key_id,
            access_key_secret=config.access_key_secret,
            region_id=config.region_id
        )
    elif config.platform_type == 'tencent':
        cred = credential.Credential(secret_id=config.access_key_id,
                                     secret_key=config.access_key_secret)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "dnspod.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        tencent_client = dnspod_client.DnspodClient(cred, "", clientProfile)
    else:
        hlog.var('暂时不支持' + config.platform_type + '平台')
        exit(1)

    main()
