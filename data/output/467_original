# -*- coding: utf-8 -*-

import hashlib
import json
import os
import time
import zipfile

import requests

import auth
from exceptions import AlaudaInputError
import settings
import util


class Build(object):

    def __init__(self):
        self.api_endpoint, self.token, self.username = auth.load_token()
        self.headers = auth.build_headers(self.token)

    def create(self, repo_name, source, namespace, image_tag, commit_id):
        if not repo_name:
            raise AlaudaInputError(
                'Create build must specify repository name using -rn.'
            )

        namespace = namespace or self.username
        repo_type = self._check_repo_type(repo_name, namespace)
        image_tag = self._check_image_tag(repo_name, namespace, image_tag)

        if repo_type == settings.BUILD_REPO_TYPE['code_repo']:
            self._trigger_build(repo_name, namespace, image_tag, commit_id)
            return True

        if not source:
            raise AlaudaInputError(
                "You need to specify source code path using -p when"
                "your repository's type is FileUpload."
            )
        source = os.path.abspath(source)
        timestamp = int(time.time() * 1000)
        target_name = '{}_{}.zip'.format(repo_name, timestamp)
        target_path = os.path.abspath(
            os.path.join(os.path.join(source, '..'), target_name)
        )

        self._pack(source, target_path)

        (
            upload_auth_headers, upload_bucket, upload_object_key
        ) = self._get_upload_auth_info(target_path)

        try:
            self._upload(
                target_path, upload_auth_headers, upload_bucket,
                upload_object_key
            )
        finally:
            self._clean(target_path)

        self._trigger_build(
            repo_name, namespace, image_tag, commit_id, upload_object_key
        )
        return True

    def _check_repo_type(self, repo_name, namespace):
        print ("[alauda] Checking the repository's type")
        url = (
            self.api_endpoint +
            'repositories/{}/{}'.format(namespace, repo_name)
        )
        response = requests.get(url, headers=self.headers)
        util.check_response(response)

        data = json.loads(response.text)
        if not data['is_automated']:
            raise AlaudaInputError(
                '{} is not an automated buid repo.'.format(repo_name)
            )

        if data['build_config']['code_repo_client'] == 'FileUpload':
            print (
                "[alauda] The repository's client type you specified "
                "is FileUpload"
            )
            return settings.BUILD_REPO_TYPE['file']
        else:
            print (
                "[alauda] The repository's client type you specified "
                "is {}".format(data['build_config']['code_repo_client'])
            )
            return settings.BUILD_REPO_TYPE['code_repo']

    def _check_image_tag(self, repo_name, namespace, image_tag):
        print ('[alauda] Checking if the image tag is valid')
        url = (
            self.api_endpoint +
            'repositories/{}/{}'.format(namespace, repo_name)
        )
        response = requests.get(url, headers=self.headers)
        util.check_response(response)

        data = json.loads(response.text)
        tags = [
            item['docker_repo_tag']
            for item in data['build_config']['tag_configs']
        ]

        if not image_tag and len(tags) == 1:
            print ('[alauda] using {} as the image tag.'.format(tags[0]))
            image_tag = tags[0]
        elif not image_tag and len(tags) > 1:
            raise AlaudaInputError(
                'please specify an image tag using -t, here is the '
                'tag list for your repo: {}'.format(tags)
            )
        elif image_tag and image_tag not in tags:
            raise AlaudaInputError(
                '"{}" is not a valid tag, here is the tag list for your repo: '
                '{}'.format(image_tag, tags)
            )
        return image_tag

    def _pack(self, source, target_path):
        print (
            '[alauda] Packing the source directory to {}'
            .format(target_path)
        )

        if not os.path.isdir(source):
            raise AlaudaInputError(
                '{} is not a valid directory'.format(source)
            )

        with zipfile.ZipFile(target_path, mode='w') as zf:
            for root, dirs, files in os.walk(source):
                for f in files:
                    zf.write(
                        os.path.join(root, f),
                        os.path.relpath(os.path.join(root, f), source),
                        compress_type=zipfile.ZIP_DEFLATED
                    )

    def _get_upload_auth_info(self, target_path):
        print ('[alauda] Applying to upload auth info.')
        with open(target_path, 'rb') as data:
            fingerprint = hashlib.sha256(data.read()).hexdigest()
        params = {
            'action': 's3_upload',
            'fingerprint': fingerprint
        }
        url = self.api_endpoint + 'cloud-storage/aws/auth'
        response = requests.get(url, headers=self.headers, params=params)
        util.check_response(response)
        data = json.loads(response.text)
        return data['auth_headers'], data['bucket'], data['object_key']

    def _upload(
        self, target_path, upload_auth_headers, upload_bucket,
        upload_object_key
    ):
        print (
            '[alauda] Uploading {} to {}'.format(
                target_path, upload_object_key
            )
        )
        with open(target_path, 'rb') as data:
            response = requests.put(
                'http://{}/{}/{}'.format(
                    upload_auth_headers['Host'], upload_bucket,
                    upload_object_key
                ),
                data=data,
                headers=upload_auth_headers
            )
        util.check_response(response)

    def _clean(self, target_path):
        print (
            '[alauda] Cleaning the tmp file {}'.format(target_path)
        )
        os.remove(target_path)

    def _trigger_build(
        self, repo_name, namespace, image_tag, commit_id, upload_object_key=None
    ):
        print (
            '[alauda] Triggering a build on alauda'
        )
        url = self.api_endpoint + 'builds'
        payload = {
            'namespace': namespace,
            'repo_name': repo_name,
            'tag': image_tag
        }
        if upload_object_key:
            payload['code_repo_path'] = upload_object_key
        if commit_id:
            payload['code_commit_id'] = commit_id
        response = requests.post(
            url, headers=self.headers, data=json.dumps(payload)
        )
        util.check_response(response)
