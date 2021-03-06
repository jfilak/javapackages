#!/usr/bin/python
# Copyright (c) 2014, Red Hat, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of Red Hat nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors:  Michal Srb <msrb@redhat.com>

from javapackages.common.config import get_configs

import subprocess
import lxml.etree
import os


class XMvnResolve(object):
    # TODO:
    # - documentation

    @staticmethod
    def _load_path_from_config():
        configs = get_configs()
        path = None
        for config in configs:
            path = config.get('path', "")
            if os.path.exists(path):
                break
        if not path:
            # default path
            path = "/usr/bin/xmvn-resolve"
        return path

    @staticmethod
    def process_raw_request(raw_request_list):
        binpath = XMvnResolve._load_path_from_config()
        request = XMvnResolve.__join_raw_requests(raw_request_list)
        procargs = [binpath, '--raw-request']
        proc = subprocess.Popen(procargs, shell=False, stdout=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)
        stdout = proc.communicate(input=request)[0]
        proc.wait()
        result = XMvnResolve.__process_results(stdout)
        return result

    @staticmethod
    def __join_raw_requests(raw_request_list):
        request = "<requests>"
        for r in raw_request_list:
            request += r.get_xml()
        request += "</requests>"

        return request

    @staticmethod
    def __process_results(result_xml):
        results = []

        doc = lxml.etree.fromstring(result_xml.encode("UTF-8"))
        nodes = doc.xpath('/results/result')
        for node in nodes:
            if len(node) > 0:
                ns = node.find('./namespace')
                if ns is not None:
                    ns = ns.text
                compat_ver = node.find('./compatVersion')
                if compat_ver is not None:
                    compat_ver = compat_ver.text
                path = node.find('./artifactPath')
                if path is not None:
                    path = path.text
                res = ResolutionResult(namespace=ns or "",
                                       compatVersion=compat_ver or "",
                                       path=path or "")
                results.append(res)
            else:
                results.append(None)
        return results


class ResolutionResult(object):
    def __init__(self, namespace="", compatVersion="", path=""):
        self.namespace = namespace
        self.compatVersion = compatVersion
        self.artifactPath = path

    def __str__(self):
        return "version:" + self.compatVersion + "namespace: " + self.namespace


class ResolutionRequest(object):
    def __init__(self, groupId, artifactId, extension="", classifier="", version=""):
        self.groupId = groupId
        self.artifactId = artifactId
        self.extension = extension
        self.classifier = classifier
        self.version = version

    def get_xml(self):
        return ResolutionRequest.create_raw_request_xml(self.groupId, self.artifactId, self.extension, self.classifier, self.version)

    @staticmethod
    def create_raw_request_xml(groupId, artifactId, extension="", classifier="", version=""):
        template = """
<request>
    <artifact>
        <groupId>{gid}</groupId>
        <artifactId>{aid}</artifactId>{ext}{cla}{ver}
    </artifact>
</request>
"""
        ver = ""
        cla = ""
        ext = ""
        if extension:
            ext = "<extension>{ext}</extension>".format(ext=extension)
        if classifier:
            cla = "<classifier>{cla}</classifier>".format(cla=classifier)
        if version:
            ver = "<version>{ver}</version>".format(ver=version)

        return template.format(gid=groupId, aid=artifactId,
                               ext=ext, cla=cla, ver=ver)

    @classmethod
    def from_artifact(cls, artifact):
        return cls(artifact.artifactId, artifact.groupId,
                   artifact.extension, artifact.classifier, artifact.version)
